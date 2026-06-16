"""
Rules-of-Engagement (RoE) data models.

The RoE record is the single source of truth for what ARGUS is allowed to
touch and how. It is produced/signed out-of-band (or via scripts/sign_roe.py
for local dev) and submitted alongside a job. The Scope & Authorization
Engine (core/authorization.py) validates and enforces it; these models only
define shape + basic field-level validation.
"""

from __future__ import annotations

import ipaddress
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ScopeAssetType(str, Enum):
    """How a scope entry should be matched against a discovered/target value."""

    DOMAIN = "domain"  # exact domain + all subdomains (suffix match)
    IP = "ip"          # single IP address
    CIDR = "cidr"      # IP network range


class ScopeAsset(BaseModel):
    """
    A single in-scope or excluded asset.

    DOMAIN entries are treated as "this domain and everything under it":
    a DOMAIN entry of `example.com` covers `example.com`, `www.example.com`,
    `api.dev.example.com`, etc.
    """

    type: ScopeAssetType
    value: str
    note: str | None = Field(
        default=None, description="Optional human-readable reason for this entry"
    )

    @field_validator("value")
    @classmethod
    def normalize_value(cls, v: str, info) -> str:
        v = v.strip()
        asset_type = info.data.get("type")

        if asset_type == ScopeAssetType.DOMAIN:
            v = v.lower().rstrip(".")
            # Treat "*.example.com" the same as "example.com" — DOMAIN
            # entries already imply "and all subdomains".
            if v.startswith("*."):
                v = v[2:]
            if not v or " " in v:
                raise ValueError(f"Invalid domain scope value: {v!r}")
            return v

        if asset_type == ScopeAssetType.IP:
            try:
                ipaddress.ip_address(v)
            except ValueError as exc:
                raise ValueError(f"Invalid IP scope value: {v!r}") from exc
            return v

        if asset_type == ScopeAssetType.CIDR:
            try:
                ipaddress.ip_network(v, strict=False)
            except ValueError as exc:
                raise ValueError(f"Invalid CIDR scope value: {v!r}") from exc
            return v

        return v


class RoERecord(BaseModel):
    """
    A signed Rules-of-Engagement record.

    `signature` is an HMAC-SHA256 hex digest over the canonical JSON of every
    other field, computed/verified with `core.authorization.compute_signature`
    / `verify_signature` using the deployment's ROE signing key. This is
    intentionally simple (HMAC, not full PKI) — it's enough to (a) detect
    accidental/unauthorized edits to an RoE record after it was approved, and
    (b) give the audit trail a tamper-evidence story. It is NOT a substitute
    for an out-of-band, legally-signed engagement contract.
    """

    model_config = ConfigDict(extra="forbid")

    roe_id: UUID = Field(default_factory=uuid4)

    client_name: str
    authorized_by: str = Field(
        description="Name/role of the person who approved this RoE"
    )
    contact_email: str

    in_scope_assets: list[ScopeAsset] = Field(
        description="Assets ARGUS is permitted to touch (passive always, "
        "active only if active_scanning_authorized=True)"
    )
    excluded_assets: list[ScopeAsset] = Field(
        default_factory=list,
        description="Carve-outs within the in-scope set (e.g. a third-party "
        "CDN subdomain) — always out of scope regardless of in_scope_assets",
    )

    active_scanning_authorized: bool = Field(
        default=False,
        description="Master gate for any agent/tool classified 'active' "
        "(e.g. Nmap). Passive collection is unaffected by this flag.",
    )
    allowed_active_tools: list[str] = Field(
        default_factory=list,
        description="If non-empty AND active_scanning_authorized=True, "
        "restricts active tooling to this allow-list (e.g. ['nmap']). "
        "If empty, any active tool is permitted once "
        "active_scanning_authorized=True.",
    )

    valid_from: datetime
    valid_until: datetime

    signed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    signature: str = Field(
        default="", description="HMAC-SHA256 hex digest, see class docstring"
    )

    notes: str | None = None

    @field_validator("valid_from", "valid_until", "signed_at")
    @classmethod
    def ensure_tz_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v

    @model_validator(mode="after")
    def check_validity_window(self) -> RoERecord:
        if self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be after valid_from")
        if not self.in_scope_assets:
            raise ValueError("RoE must declare at least one in-scope asset")
        return self

    def is_currently_valid(self, now: datetime | None = None) -> bool:
        """Time-window check only — does NOT verify the signature."""
        now = now or datetime.now(UTC)
        return self.valid_from <= now <= self.valid_until
