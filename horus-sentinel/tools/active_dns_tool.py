"""Active DNS / subdomain enumeration — ACTIVE reconnaissance (authorized targets only).

Unlike the passive ``DnsTool`` (which reads an already-public record set), this tool actively
brute-forces candidate subdomains from a wordlist and resolves each one. It therefore sends
many queries derived from the target and only ever runs against an authorized, in-scope asset
(the Tool Abstraction Layer + Authorization Engine enforce this; an out-of-scope call raises).

Discovered subdomains become graph nodes (``Subdomain -[RESOLVES_TO]-> IP``) that feed the
port scanner and the offensive analysis.
"""

from __future__ import annotations

import anyio
import structlog

from core.config import settings
from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding, ToolResult
from schemas.roe import Classification, SourceCategory
from schemas.subject import Subject
from tools.base import IntelTool

log = structlog.get_logger("horus.tool.active_dns")


class ActiveDnsTool(IntelTool):
    """Brute-force subdomain discovery against an authorized domain."""

    name = "active_dns"
    classification = Classification.ACTIVE
    source_category = SourceCategory.ACTIVE_RECON
    cache_ttl = 900

    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        candidates = [w.strip() for w in settings.active_dns_wordlist.split(",") if w.strip()]
        base = subject.value.lower().lstrip(".")
        resolved = await anyio.to_thread.run_sync(self._resolve_candidates, base, candidates)

        findings: list[Finding] = []
        evidence: list[Evidence] = []
        for host, ips in resolved.items():
            ev = Evidence(
                source=self.name,
                source_category=self.source_category,
                summary=f"Active DNS: {host} resolves to {', '.join(ips)}",
            )
            evidence.append(ev)
            findings.append(
                Finding(
                    entity_kind=EntityKind.SUBDOMAIN,
                    entity_value=host,
                    attributes={"discovery": "active_bruteforce", "resolved_ips": ips},
                    related_to=base,
                    relationship="HAS_SUBDOMAIN",
                    evidence=[ev],
                    produced_by=self.name,
                )
            )
            for ip in ips:
                findings.append(
                    Finding(
                        entity_kind=EntityKind.IP,
                        entity_value=ip,
                        attributes={"discovery": "active_bruteforce"},
                        related_to=host,
                        relationship="RESOLVES_TO",
                        evidence=[ev],
                        produced_by=self.name,
                    )
                )
        log.info("active_dns_complete", target=base, tried=len(candidates), found=len(resolved))
        return ToolResult(
            tool=self.name,
            source_category=self.source_category,
            findings=findings,
            evidence=evidence,
        )

    @staticmethod
    def _resolve_candidates(base: str, candidates: list[str]) -> dict[str, list[str]]:
        """Resolve each ``<candidate>.<base>`` A record. Missing dnspython → empty."""
        try:
            import dns.resolver  # lazy: keep importable without dnspython
        except ImportError:
            log.warning("dnspython_missing")
            return {}

        resolver = dns.resolver.Resolver()
        resolver.lifetime = 3.0
        resolver.timeout = 3.0
        found: dict[str, list[str]] = {}
        for word in candidates:
            host = f"{word}.{base}"
            try:
                answers = resolver.resolve(host, "A")
                found[host] = [r.to_text().strip('"') for r in answers]
            except Exception:  # NXDOMAIN / NoAnswer / timeout — candidate simply doesn't exist
                continue
        return found
