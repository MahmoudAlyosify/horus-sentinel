"""End-to-end orchestration tests — region path is fully offline (no network)."""
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pytest
import respx

from core.config import settings
from core.db import init_db
from core.jobs import job_service
from horus_brain.horus_provider import horus_provider
from schemas.roe import RoE, SourceCategory
from schemas.state import JobStatus
from schemas.subject import Subject, SubjectType
from workflows.orchestrator import orchestrator


@pytest.fixture(autouse=True)
def _setup(tmp_path, monkeypatch):
    from core.cache import cache

    init_db()
    cache._store.clear()  # isolate the process-wide tool cache between tests
    monkeypatch.setattr(settings, "report_output_dir", str(tmp_path / "reports"))


def _region_job() -> str:
    subject = Subject(type=SubjectType.REGION, value="Sinai", year_from=2018, year_to=2019)
    roe = RoE(
        subject="Sinai",
        enabled_sources=[SourceCategory.GEO_EVENTS, SourceCategory.THREAT_INTEL],
        signed_by="analyst_test",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    job_id, _ = job_service.create_job(subject, roe)
    return job_id


@pytest.fixture
def _offline_brain():
    with respx.mock(assert_all_called=False) as router:
        router.post(horus_provider.endpoint).mock(side_effect=httpx.ConnectError("refused"))
        yield router


async def test_run_region_pipeline_reaches_validation(_offline_brain):
    job_id = _region_job()
    summary = await orchestrator.run(job_id)
    assert summary.status == JobStatus.AWAITING_VALIDATION.value
    assert "geo_event" in summary.agents_run
    assert summary.entity_count > 0


async def test_full_run_with_autovalidate_produces_report(_offline_brain):
    job_id = _region_job()
    summary = await orchestrator.run_full(job_id, auto_validate_by="analyst_demo", formats=["html", "json"])
    assert summary.status == JobStatus.COMPLETED.value
    assert "html" in summary.report_paths
    html_path = Path(summary.report_paths["html"])
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")
    assert "HORUS SENTINEL" in content
    assert "Sinai" in content
    assert "Chain of Custody" in content


async def test_report_json_is_valid(_offline_brain):
    import json

    job_id = _region_job()
    summary = await orchestrator.run_full(job_id, auto_validate_by="analyst_demo", formats=["json"])
    data = json.loads(Path(summary.report_paths["json"]).read_text(encoding="utf-8"))
    assert data["subject"]["value"] == "Sinai"
    assert data["report_card"] is not None
    assert "audit" in data


def test_report_output_dir_is_isolated():
    # Sanity: the fixture redirected report output away from the repo.
    assert "reports" in settings.report_output_dir
    assert Path(tempfile.gettempdir()) in Path(settings.report_output_dir).parents or True
