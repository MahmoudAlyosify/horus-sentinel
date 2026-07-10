"""Reputation enrichment tool — AbuseIPDB (passive reputation lookup).

Master plan Part 3.4. Attaches a normalized reputation score to a discovered IP. Reads
pre-collected reputation data via the AbuseIPDB API — no packets to the target. Requires
an API key; without one it degrades gracefully (returns an informative, non-fatal error)
so the platform still runs on a bare $0 setup.
"""

from __future__ import annotations

from core.config import settings
from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding, ToolResult
from schemas.roe import SourceCategory
from schemas.subject import Subject
from tools.base import IntelTool
from tools.http import get_json

_ABUSEIPDB = "https://api.abuseipdb.com/api/v2/check"


class ReputationTool(IntelTool):
    """Look up an IP's abuse reputation. Subject value is the IP address."""

    name = "reputation"
    source_category = SourceCategory.THREAT_INTEL
    cache_ttl = 21600

    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        if not settings.abuseipdb_api_key:
            return ToolResult(
                tool=self.name,
                source_category=self.source_category,
                error="ABUSEIPDB_API_KEY not set — reputation enrichment skipped (non-fatal)",
            )

        data = await get_json(
            _ABUSEIPDB,
            params={"ipAddress": subject.value, "maxAgeInDays": 90},
            headers={"Key": settings.abuseipdb_api_key},
        )
        payload = (data or {}).get("data") if isinstance(data, dict) else None
        if not payload:
            return ToolResult(
                tool=self.name,
                source_category=self.source_category,
                error=f"no reputation data for {subject.value}",
            )

        score = payload.get("abuseConfidenceScore", 0)
        ev = Evidence(
            source=self.name,
            source_category=self.source_category,
            summary=f"AbuseIPDB {subject.value}: confidence={score}, reports={payload.get('totalReports', 0)}",
            raw_ref=Evidence.digest(payload),
        )
        finding = Finding(
            entity_kind=EntityKind.INDICATOR,
            entity_value=f"reputation:{subject.value}",
            attributes={
                "ip": subject.value,
                "abuse_confidence": score,
                "total_reports": payload.get("totalReports", 0),
                "country": payload.get("countryCode"),
                "isp": payload.get("isp"),
                "normalized_reputation": round(score / 100.0, 3),
            },
            related_to=subject.value,
            relationship="HAS_INDICATOR",
            evidence=[ev],
            produced_by=self.name,
        )
        return ToolResult(
            tool=self.name,
            source_category=self.source_category,
            findings=[finding],
            evidence=[ev],
        )
