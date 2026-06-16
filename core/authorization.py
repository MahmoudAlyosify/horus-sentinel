"""
Scope & Authorization Engine.

This module is the "HARD GATE" from the architecture diagram (section 2.1).
Every ReconTool routes through `AuthContext.assert_allows()` before it is
allowed to touch a target. Nothing downstream of this module should need to
re-implement scope or classification logic.

Three responsibilities:

1. RoE integrity   — `compute_signature` / `verify_signature` (HMAC-SHA256)
2. Scope matching  — `ScopeMatcher` (domain suffix / IP / CIDR matching,
                      with exclusions)
3. The gate itself — `AuthContext.assert_allows()` + `AuthorizationEngine`
                      (constructs a verified AuthContext from a submitted RoE)
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict

from schemas.roe import RoERecord, ScopeAsset, ScopeAssetType

Classification = Literal["passive", "active"]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AuthorizationError(Exception):
    """Base class for every authorization-gate failure."""


class RoEInvalidSignatureError(AuthorizationError):
    """The submitted RoE's signature does not match its content."""


class RoEExpiredError(AuthorizationError):
    """The RoE is outside its valid_from/valid_until window."""


class OutOfScopeError(AuthorizationError):
    """The target is not covered by any in-scope asset (or is excluded)."""


class ActiveScanningNotAuthorizedError(AuthorizationError):
    """The RoE does not set active_scanning_authorized=True."""


class ToolNotAllowedError(AuthorizationError):
    """active_scanning_authorized=True, but this tool isn't on the allow-list."""


# ---------------------------------------------------------------------------
# RoE signing
# ---------------------------------------------------------------------------


def _canonical_payload(roe: RoERecord) -> bytes:
    """
    Deterministic JSON representation of every field except `signature`,
    used as the HMAC message. Sorted keys + ISO timestamps via mode="json"
    make this stable across process restarts and re-serialization.
    """
    payload = roe.model_dump(exclude={"signature"}, mode="json")
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_signature(roe: RoERecord, signing_key: str) -> str:
    """HMAC-SHA256 hex digest of the RoE content (excluding `signature`)."""
    digest = hmac.new(
        key=signing_key.encode("utf-8"),
        msg=_canonical_payload(roe),
        digestmod=hashlib.sha256,
    )
    return digest.hexdigest()


def verify_signature(roe: RoERecord, signing_key: str) -> bool:
    """Constant-time comparison of `roe.signature` against the expected HMAC."""
    if not roe.signature:
        return False
    expected = compute_signature(roe, signing_key)
    return hmac.compare_digest(expected, roe.signature)


def sign_roe(roe: RoERecord, signing_key: str) -> RoERecord:
    """Return a copy of `roe` with `signature` populated."""
    signature = compute_signature(roe, signing_key)
    return roe.model_copy(update={"signature": signature})


# ---------------------------------------------------------------------------
# Scope matching
# ---------------------------------------------------------------------------


class ScopeMatcher:
    """
    Compiles an RoE's in_scope_assets / excluded_assets into fast lookup
    structures and answers "is this value in scope?".

    Cheap to construct (no I/O); built fresh per `assert_allows` call so
    AuthContext stays a plain, fully-serializable Pydantic model — important
    once this is checkpointed as part of ReconState (section 2.3).
    """

    def __init__(self, roe: RoERecord) -> None:
        in_domains, in_ips, in_nets = self._split(roe.in_scope_assets)
        ex_domains, ex_ips, ex_nets = self._split(roe.excluded_assets)

        self._in_domains = in_domains
        self._in_ips = in_ips
        self._in_nets = in_nets
        self._ex_domains = ex_domains
        self._ex_ips = ex_ips
        self._ex_nets = ex_nets

    @staticmethod
    def _split(
        assets: list[ScopeAsset],
    ) -> tuple[set[str], set[str], list[ipaddress.IPv4Network | ipaddress.IPv6Network]]:
        domains: set[str] = set()
        ips: set[str] = set()
        nets: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []

        for asset in assets:
            if asset.type == ScopeAssetType.DOMAIN:
                domains.add(asset.value)
            elif asset.type == ScopeAssetType.IP:
                ips.add(asset.value)
            elif asset.type == ScopeAssetType.CIDR:
                nets.append(ipaddress.ip_network(asset.value, strict=False))

        return domains, ips, nets

    @staticmethod
    def _is_ip(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
        try:
            return ipaddress.ip_address(value)
        except ValueError:
            return None

    @staticmethod
    def _matches_domain(host: str, domains: set[str]) -> bool:
        host = host.lower().rstrip(".")
        return any(host == d or host.endswith("." + d) for d in domains)

    def _matches_ip(
        self,
        ip: ipaddress.IPv4Address | ipaddress.IPv6Address,
        ips: set[str],
        nets: list[ipaddress.IPv4Network | ipaddress.IPv6Network],
    ) -> bool:
        if str(ip) in ips:
            return True
        return any(ip in net for net in nets)

    def is_excluded(self, value: str) -> bool:
        ip = self._is_ip(value)
        if ip is not None:
            return self._matches_ip(ip, self._ex_ips, self._ex_nets)
        return self._matches_domain(value, self._ex_domains)

    def is_in_scope(self, value: str) -> bool:
        """True if `value` (domain/host or IP/CIDR string) is authorized."""
        if self.is_excluded(value):
            return False

        ip = self._is_ip(value)
        if ip is not None:
            return self._matches_ip(ip, self._in_ips, self._in_nets)

        return self._matches_domain(value, self._in_domains)


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------


class AuthContext(BaseModel):
    """
    Carried inside ReconState and handed to every ReconTool call.

    Deliberately holds only serializable data (job_id + the RoE record
    itself) — `ScopeMatcher` is rebuilt on demand inside `assert_allows`,
    so this model can be checkpointed by LangGraph/Postgres without custom
    (de)serialization.
    """

    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    roe: RoERecord

    def assert_allows(
        self,
        classification: Classification,
        target: str,
        tool_name: str | None = None,
    ) -> None:
        """
        Raise an `AuthorizationError` subclass if `target` may not be touched
        by a tool of the given `classification`. Returns None (no exception)
        if the operation is permitted.

        This is the single choke point referenced by `ReconTool.__call__`
        (section 2.4) — every external integration calls this before doing
        any network I/O.
        """
        if not self.roe.is_currently_valid():
            raise RoEExpiredError(
                f"RoE {self.roe.roe_id} is not currently valid "
                f"(valid {self.roe.valid_from.isoformat()} .. "
                f"{self.roe.valid_until.isoformat()})"
            )

        matcher = ScopeMatcher(self.roe)
        if not matcher.is_in_scope(target):
            raise OutOfScopeError(
                f"Target '{target}' is not within the authorized scope of "
                f"RoE {self.roe.roe_id}"
            )

        if classification == "active":
            if not self.roe.active_scanning_authorized:
                raise ActiveScanningNotAuthorizedError(
                    f"Active scanning is not authorized under RoE "
                    f"{self.roe.roe_id}; blocked target '{target}'"
                    + (f" (tool={tool_name})" if tool_name else "")
                )

            allow_list = self.roe.allowed_active_tools
            if tool_name and allow_list and tool_name not in allow_list:
                raise ToolNotAllowedError(
                    f"Tool '{tool_name}' is not in allowed_active_tools "
                    f"{allow_list} for RoE {self.roe.roe_id}"
                )


class AuthorizationEngine:
    """Validates a submitted RoE and produces an AuthContext, or raises."""

    @staticmethod
    def create_context(
        roe: RoERecord,
        signing_key: str,
        job_id: UUID | None = None,
    ) -> AuthContext:
        """
        Verify signature + validity window, then return an AuthContext.

        Raises:
            RoEInvalidSignatureError: signature doesn't match content.
            RoEExpiredError: outside valid_from/valid_until.
        """
        if not verify_signature(roe, signing_key):
            raise RoEInvalidSignatureError(
                f"RoE {roe.roe_id} failed signature verification"
            )

        if not roe.is_currently_valid():
            raise RoEExpiredError(
                f"RoE {roe.roe_id} is outside its validity window "
                f"({roe.valid_from.isoformat()} .. {roe.valid_until.isoformat()})"
            )

        return AuthContext(job_id=job_id or uuid4(), roe=roe)
