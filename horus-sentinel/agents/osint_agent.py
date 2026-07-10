"""OSINT Collection Agent — builds the base entity picture from public records.

Master plan Part 3.1. For a domain subject it runs DNS, RDAP (WHOIS) and Certificate
Transparency, then infers a likely corporate email pattern from what was discovered.
Everything is passive public-records collection.
"""

from __future__ import annotations

from agents.base import BaseAgent
from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding
from schemas.roe import SourceCategory
from schemas.subject import Subject
from tools.crtsh_tool import CrtShTool
from tools.dns_tool import DnsTool
from tools.rdap_tool import RdapTool


class OsintAgent(BaseAgent):
    """Passive public-records collection: DNS + RDAP + Certificate Transparency."""

    name = "osint"

    def __init__(self) -> None:
        super().__init__(tools=[DnsTool(), RdapTool(), CrtShTool()])

    def post_process(
        self, subject: Subject, ctx: AuthContext, findings: list[Finding]
    ) -> list[Finding]:
        """Infer a corporate email pattern for domain subjects (informational)."""
        if subject.type.value != "domain":
            return []
        pattern = f"{{first}}.{{last}}@{subject.value}"
        ev = Evidence(
            source=self.name,
            source_category=SourceCategory.PUBLIC_RECORDS,
            summary=f"Inferred common corporate email pattern for {subject.value}",
        )
        return [
            Finding(
                entity_kind=EntityKind.EMAIL,
                entity_value=pattern,
                attributes={"inferred": True, "confidence": "low"},
                related_to=subject.value,
                relationship="LIKELY_EMAIL_PATTERN",
                evidence=[ev],
                produced_by=self.name,
            )
        ]
