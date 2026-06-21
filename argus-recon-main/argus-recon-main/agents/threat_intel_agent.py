"""Threat intelligence enrichment agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ThreatIntelResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assets: list[dict[str, object]]


class ThreatIntelAgent:
    """Attach basic enrichment hints and known CVE references to discovered assets."""

    async def run(self, assets: list[dict[str, object]]) -> ThreatIntelResult:
        enriched: list[dict[str, object]] = []
        for asset in assets:
            kind = str(asset.get("kind", "unknown"))
            value = str(asset.get("value", ""))
            if kind == "service" and value == "https":
                enriched.append(
                    {
                        "asset": value,
                        "reputation": "neutral",
                        "reputation_score": 0.1,
                        "known_cves": [{"product": "generic-web-service", "cve": "CVE-2024-0000", "cvss": 7.5}],
                    }
                )
            else:
                enriched.append({"asset": value, "reputation": "neutral", "reputation_score": 0.1, "known_cves": []})
        return ThreatIntelResult(assets=enriched)
