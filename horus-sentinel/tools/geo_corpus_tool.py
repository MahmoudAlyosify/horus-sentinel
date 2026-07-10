"""Geo-Event corpus tool — the model's home turf (GTD/GDELT-derived context).

Master plan Part 3.2. For a region + timeframe it queries the local geo-event corpus and
returns instability indicators, dominant attack modalities, primary target categories,
actor references and a threat-context summary. This is prime RAG material for the HORUS
brain — the exact kind of signal the model was fine-tuned to reason over.

The corpus is a local file (no network): fully passive. It reads ``GEO_CORPUS_PATH`` if
present, otherwise the bundled sample, so the agent always runs.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import structlog

from core.config import settings
from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding, ToolResult
from schemas.roe import SourceCategory
from schemas.subject import Subject
from tools.base import IntelTool

log = structlog.get_logger("horus.tool.geo")

_SAMPLE = Path(__file__).resolve().parent.parent / "data" / "geo_corpus.sample.json"


@lru_cache(maxsize=1)
def _load_corpus() -> list[dict[str, Any]]:
    """Load the corpus once. Prefers GEO_CORPUS_PATH; falls back to the bundled sample."""
    for candidate in (Path(settings.geo_corpus_path), _SAMPLE):
        try:
            if candidate.exists():
                data = json.loads(candidate.read_text(encoding="utf-8"))
                records = data.get("records", data) if isinstance(data, dict) else data
                log.info("geo_corpus_loaded", path=str(candidate), records=len(records))
                return records
        except (OSError, ValueError) as exc:
            log.warning("geo_corpus_load_failed", path=str(candidate), error=str(exc))
    log.warning("geo_corpus_unavailable")
    return []


class GeoCorpusTool(IntelTool):
    """Query the geo-event corpus for a region + timeframe."""

    name = "geo_corpus"
    source_category = SourceCategory.GEO_EVENTS
    cache_ttl = 86400

    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        records = _load_corpus()
        region = subject.value.strip().lower()
        y_from = subject.year_from or 0
        y_to = subject.year_to or 9999

        matches = [
            r
            for r in records
            if str(r.get("region", "")).lower() == region
            and y_from <= int(r.get("year", 0)) <= y_to
        ]
        if not matches:
            return ToolResult(
                tool=self.name,
                source_category=self.source_category,
                error=f"no geo-event records for region '{subject.value}' in {y_from}-{y_to}",
            )

        findings: list[Finding] = []
        evidence: list[Evidence] = []
        for rec in matches:
            ev = Evidence(
                source=self.name,
                source_category=self.source_category,
                summary=(
                    f"{rec.get('region')} {rec.get('year')}: instability="
                    f"{rec.get('instability_index')}, events={rec.get('event_count')}"
                ),
                raw_ref=Evidence.digest(rec),
            )
            evidence.append(ev)
            findings.append(
                Finding(
                    entity_kind=EntityKind.EVENT,
                    entity_value=f"{rec.get('region')}:{rec.get('year')}",
                    attributes={
                        "year": rec.get("year"),
                        "instability_index": rec.get("instability_index"),
                        "event_count": rec.get("event_count"),
                        "dominant_modalities": rec.get("dominant_modalities", []),
                        "primary_target_categories": rec.get("primary_target_categories", []),
                        "threat_context_summary": rec.get("threat_context_summary", ""),
                    },
                    related_to=subject.value,
                    relationship="HAS_EVENT",
                    evidence=[ev],
                    produced_by=self.name,
                )
            )
            # Actor references become ThreatActor nodes linked to the event.
            for actor in rec.get("actor_references", []):
                findings.append(
                    Finding(
                        entity_kind=EntityKind.THREAT_ACTOR,
                        entity_value=actor,
                        attributes={"region": rec.get("region"), "year": rec.get("year")},
                        related_to=f"{rec.get('region')}:{rec.get('year')}",
                        relationship="ASSOCIATED_WITH",
                        evidence=[ev],
                        produced_by=self.name,
                    )
                )

        # The region node itself, so the graph has an anchor.
        findings.insert(
            0,
            Finding(
                entity_kind=EntityKind.REGION,
                entity_value=subject.value,
                attributes={
                    "country_code": subject.country_code or matches[0].get("country_code"),
                    "years": sorted({int(r.get("year", 0)) for r in matches}),
                },
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
