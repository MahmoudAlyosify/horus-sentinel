"""Certificate Transparency tool (crt.sh) — passive subdomain discovery.

Certificate Transparency logs are public append-only records of every TLS certificate
issued. Querying crt.sh for a domain reveals subdomains an organization has published
certificates for — a passive, high-signal source that touches no target infrastructure.
"""

from __future__ import annotations

from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding, ToolResult
from schemas.roe import SourceCategory
from schemas.subject import Subject
from tools.base import IntelTool
from tools.http import get_json

_CRTSH_URL = "https://crt.sh/"


class CrtShTool(IntelTool):
    """Discover subdomains and certificates from Certificate Transparency logs."""

    name = "crtsh"
    source_category = SourceCategory.PUBLIC_RECORDS
    cache_ttl = 43200

    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        data = await get_json(_CRTSH_URL, params={"q": f"%.{subject.value}", "output": "json"})
        if not data:
            return ToolResult(
                tool=self.name,
                source_category=self.source_category,
                error="no certificate transparency data (network error or none found)",
            )

        subdomains: set[str] = set()
        issuers: set[str] = set()
        for entry in data:
            issuers.add(entry.get("issuer_name", "").strip())
            for name in str(entry.get("name_value", "")).splitlines():
                name = name.strip().lstrip("*.").lower()
                if name.endswith(subject.value.lower()) and name != subject.value.lower():
                    subdomains.add(name)

        ev = Evidence(
            source=self.name,
            source_category=self.source_category,
            summary=(
                f"crt.sh: {len(subdomains)} subdomains, "
                f"{len(data)} certificates for {subject.value}"
            ),
            raw_ref=Evidence.digest(sorted(subdomains)),
        )
        findings: list[Finding] = [
            Finding(
                entity_kind=EntityKind.SUBDOMAIN,
                entity_value=sub,
                attributes={"discovered_via": "certificate_transparency"},
                related_to=subject.value,
                relationship="HAS_SUBDOMAIN",
                evidence=[ev],
                produced_by=self.name,
            )
            for sub in sorted(subdomains)
        ]
        if issuers:
            findings.append(
                Finding(
                    entity_kind=EntityKind.CERTIFICATE,
                    entity_value=f"ct:{subject.value}",
                    attributes={
                        "issuers": sorted(i for i in issuers if i),
                        "cert_count": len(data),
                    },
                    related_to=subject.value,
                    relationship="HAS_CERTIFICATE",
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
