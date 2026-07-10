"""RDAP tool — modern, keyless WHOIS over HTTP (passive public records).

RDAP is the IETF successor to WHOIS: a structured JSON registration record served over
HTTPS by the registries themselves. Using RDAP keeps the tool dependency-free (just HTTP)
and returns clean structured data — registrar, key dates, nameservers, status.
"""

from __future__ import annotations

from typing import Any

from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding, ToolResult
from schemas.roe import SourceCategory
from schemas.subject import Subject
from tools.base import IntelTool
from tools.http import get_json

# Public RDAP bootstrap — resolves the right registry for any TLD.
_RDAP_BOOTSTRAP = "https://rdap.org/domain/{domain}"


class RdapTool(IntelTool):
    """Fetch the RDAP (WHOIS) registration record for a domain subject."""

    name = "rdap"
    source_category = SourceCategory.PUBLIC_RECORDS
    cache_ttl = 86400  # registration data changes rarely

    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        data = await get_json(_RDAP_BOOTSTRAP.format(domain=subject.value))
        if not data:
            return ToolResult(
                tool=self.name,
                source_category=self.source_category,
                error="no RDAP record (network error or unregistered domain)",
            )

        attrs = self._extract(data)
        ev = Evidence(
            source=self.name,
            source_category=self.source_category,
            summary=(
                f"RDAP for {subject.value}: registrar={attrs.get('registrar', 'n/a')}, "
                f"created={attrs.get('registration_date', 'n/a')}"
            ),
            raw_ref=Evidence.digest(data),
        )
        findings = [
            Finding(
                entity_kind=EntityKind.DOMAIN,
                entity_value=subject.value,
                attributes=attrs,
                evidence=[ev],
                produced_by=self.name,
            )
        ]
        # Nameservers become infrastructure references on the graph.
        for ns in attrs.get("nameservers", []):
            findings.append(
                Finding(
                    entity_kind=EntityKind.DOMAIN,
                    entity_value=ns.lower(),
                    attributes={"role": "nameserver"},
                    related_to=subject.value,
                    relationship="USES_NAMESERVER",
                    evidence=[ev],
                    produced_by=self.name,
                )
            )
        return ToolResult(
            tool=self.name,
            source_category=self.source_category,
            findings=findings,
            evidence=[ev],
        )

    @staticmethod
    def _extract(data: dict[str, Any]) -> dict[str, Any]:
        """Pull the fields analysts care about out of the RDAP JSON."""
        events = {e.get("eventAction"): e.get("eventDate") for e in data.get("events", [])}
        registrar = None
        for entity in data.get("entities", []):
            if "registrar" in entity.get("roles", []):
                registrar = _vcard_name(entity)
                break
        nameservers = [
            ns.get("ldhName", "").rstrip(".")
            for ns in data.get("nameservers", [])
            if ns.get("ldhName")
        ]
        return {
            "handle": data.get("handle"),
            "registrar": registrar,
            "status": data.get("status", []),
            "registration_date": events.get("registration"),
            "expiration_date": events.get("expiration"),
            "last_changed": events.get("last changed"),
            "nameservers": nameservers,
        }


def _vcard_name(entity: dict[str, Any]) -> str | None:
    """Best-effort registrar name from an RDAP vCard array."""
    try:
        for item in entity["vcardArray"][1]:
            if item[0] == "fn":
                return str(item[3])
    except (KeyError, IndexError, TypeError):
        pass
    handle: str | None = entity.get("handle")
    return handle
