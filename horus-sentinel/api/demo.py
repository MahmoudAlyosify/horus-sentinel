"""Guided Demo endpoint (master plan Phase 6.6).

One click → a full assessment on a pre-authorized, safe subject, with zero setup. Uses a
REGION subject served entirely from the local geo-event corpus, so the demo is fully
offline and deterministic — no network, no keys, no external calls. This is the moment a
judge runs HORUS themselves and watches it work.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter

from api.dto import DemoResponse
from schemas.roe import RoE, SourceCategory
from schemas.subject import Subject, SubjectType
from workflows.orchestrator import orchestrator

router = APIRouter(prefix="/demo", tags=["demo"])

# A pre-authorized, safe, fully-offline demo subject (the model's home turf).
_DEMO_SUBJECT = Subject(type=SubjectType.REGION, value="Sinai", year_from=2018, year_to=2019)


def _demo_roe() -> RoE:
    return RoE(
        subject="Sinai",
        enabled_sources=[SourceCategory.GEO_EVENTS, SourceCategory.THREAT_INTEL],
        signed_by="guided_demo",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )


@router.post("", response_model=DemoResponse)
async def run_guided_demo() -> DemoResponse:
    """Create, run, auto-validate and report a full assessment on the safe demo subject."""
    from core.jobs import job_service

    job_id, _ = job_service.create_job(_DEMO_SUBJECT, _demo_roe())
    summary = await orchestrator.run_full(
        job_id, auto_validate_by="guided_demo", formats=["html", "json"]
    )
    return DemoResponse(
        job_id=job_id,
        subject=_DEMO_SUBJECT.value,
        status=summary.status,
        entity_count=summary.entity_count,
        critical_cve_hits=summary.critical_cve_hits,
        report_html=summary.report_paths.get("html"),
        report_url=f"/jobs/{job_id}/report",
    )
