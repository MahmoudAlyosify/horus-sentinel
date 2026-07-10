"""DNS lookup tool — passive public-records collection.

Resolves the standard record set (A/AAAA/MX/TXT/NS/CNAME) for a domain via public
resolvers. This is passive: it reads DNS, the internet's public phone book, and never
touches the subject's own infrastructure.
"""

from __future__ import annotations

import anyio
import structlog

from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding, ToolResult
from schemas.roe import SourceCategory
from schemas.subject import Subject
from tools.base import IntelTool

log = structlog.get_logger("horus.tool.dns")

_RECORD_TYPES = ("A", "AAAA", "MX", "TXT", "NS", "CNAME")


class DnsTool(IntelTool):
    """Resolve DNS records for a domain subject."""

    name = "dns"
    source_category = SourceCategory.PUBLIC_RECORDS
    cache_ttl = 1800

    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        records = await anyio.to_thread.run_sync(self._resolve_all, subject.value)
        findings: list[Finding] = []
        evidence: list[Evidence] = []

        for rtype, values in records.items():
            if not values:
                continue
            ev = Evidence(
                source=self.name,
                source_category=self.source_category,
                summary=f"{rtype} records for {subject.value}: {', '.join(values[:5])}",
            )
            evidence.append(ev)
            # A/AAAA records assert IP nodes resolved from the domain.
            if rtype in ("A", "AAAA"):
                for ip in values:
                    findings.append(
                        Finding(
                            entity_kind=EntityKind.IP,
                            entity_value=ip,
                            attributes={"record_type": rtype},
                            related_to=subject.value,
                            relationship="RESOLVES_TO",
                            evidence=[ev],
                            produced_by=self.name,
                        )
                    )

        # The domain itself, annotated with its record set.
        domain_attrs = {rt.lower(): records.get(rt, []) for rt in _RECORD_TYPES}
        findings.insert(
            0,
            Finding(
                entity_kind=EntityKind.DOMAIN,
                entity_value=subject.value,
                attributes=domain_attrs,
                evidence=list(evidence),
                produced_by=self.name,
            ),
        )
        return ToolResult(
            tool=self.name,
            source_category=self.source_category,
            findings=findings,
            evidence=evidence,
        )

    @staticmethod
    def _resolve_all(domain: str) -> dict[str, list[str]]:
        """Blocking DNS resolution (run in a worker thread). Missing dnspython -> empty."""
        try:
            import dns.resolver  # lazy: keep the module importable without dnspython
        except ImportError:
            log.warning("dnspython_missing")
            return {}

        resolver = dns.resolver.Resolver()
        resolver.lifetime = 5.0
        out: dict[str, list[str]] = {}
        for rtype in _RECORD_TYPES:
            try:
                answers = resolver.resolve(domain, rtype)
                out[rtype] = [r.to_text().strip('"') for r in answers]
            except Exception:  # NXDOMAIN, NoAnswer, timeout — all non-fatal
                out[rtype] = []
        return out
