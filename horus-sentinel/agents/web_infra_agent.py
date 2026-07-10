"""Web / Infrastructure Fingerprinting Agent (master plan Part 3.3).

Characterizes the public technology footprint of a web-facing subject, then wires the
discovered service to the domain's already-resolved IPs so the graph carries the full
IP -[EXPOSES]-> Service -[RUNS]-> Technology chain that the signature CVE query walks.
Passive: one polite request, and only against owned/in-scope domains (enforced upstream).
"""

from __future__ import annotations

from agents.base import BaseAgent
from core.findings_store import load_findings
from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding
from schemas.roe import SourceCategory
from schemas.subject import Subject
from tools.fingerprint_tool import WebInfraTool


class WebInfraAgent(BaseAgent):
    """Passive fingerprinting for a web-facing domain subject."""

    name = "web_infra"

    def __init__(self) -> None:
        super().__init__(tools=[WebInfraTool()])

    def post_process(
        self, subject: Subject, ctx: AuthContext, findings: list[Finding]
    ) -> list[Finding]:
        """Attach the fingerprinted service to each resolved IP as an EXPOSES edge."""
        service = next((f for f in findings if f.entity_kind == EntityKind.SERVICE), None)
        if service is None:
            return []
        prior = load_findings(ctx.job_id)
        ips = sorted({f.entity_value for f in prior if f.entity_kind == EntityKind.IP})
        ev = Evidence(
            source=self.name,
            source_category=SourceCategory.WEB_INFRA,
            summary=f"Service {service.entity_value} exposed on resolved IPs: {', '.join(ips) or 'none'}",
        )
        return [
            Finding(
                entity_kind=EntityKind.SERVICE,
                entity_value=service.entity_value,
                attributes={"internet_facing": True},
                related_to=ip,
                relationship="EXPOSES",
                evidence=[ev],
                produced_by=self.name,
            )
            for ip in ips
        ]
