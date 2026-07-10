"""API tests for the report + validation endpoints (Phase 4.5)."""

from datetime import datetime, timedelta

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from agents.analysis_agent import analysis_agent
from api.main import app
from core.analysis_store import save_analysis
from core.db import init_db
from core.findings_store import persist_findings
from horus_brain.horus_provider import horus_provider
from schemas.findings import EntityKind, Finding

client = TestClient(app)


def _payload() -> dict:
    return {
        "subject": {"type": "domain", "value": "example.com"},
        "roe": {
            "subject": "example.com",
            "enabled_sources": ["public_records"],
            "in_scope_domains": ["example.com"],
            "signed_by": "analyst_mahmoud",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        },
    }


@pytest.fixture(autouse=True)
def _db():
    init_db()


async def _analyzed_job() -> str:
    resp = client.post("/jobs", json=_payload())
    job_id = resp.json()["id"]
    await persist_findings(
        job_id,
        [
            Finding(entity_kind=EntityKind.DOMAIN, entity_value="example.com", produced_by="t"),
            Finding(
                entity_kind=EntityKind.SUBDOMAIN,
                entity_value="api.example.com",
                related_to="example.com",
                relationship="HAS_SUBDOMAIN",
                produced_by="t",
            ),
        ],
    )
    with respx.mock(assert_all_called=False) as router:
        router.post(horus_provider.endpoint).mock(side_effect=httpx.ConnectError("refused"))
        card, graph = await analysis_agent.analyze(job_id, "example.com")
    await save_analysis(job_id, card, graph)
    return job_id


async def test_report_endpoint_returns_card_and_graph():
    job_id = await _analyzed_job()
    resp = client.get(f"/jobs/{job_id}/report")
    assert resp.status_code == 200
    body = resp.json()
    assert body["report_card"]["subject"] == "example.com"
    assert "nodes" in body["graph"]


def test_report_missing_analysis_returns_409():
    resp = client.post("/jobs", json=_payload())
    job_id = resp.json()["id"]
    got = client.get(f"/jobs/{job_id}/report")
    assert got.status_code == 409


async def test_validate_endpoint_finalizes():
    job_id = await _analyzed_job()
    resp = client.post(
        f"/jobs/{job_id}/validate",
        json={"action": "validate", "analyst": "analyst_mirna", "note": "ok"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_final"] is True
    assert body["new_status"] == "completed"


async def test_flag_endpoint_not_final():
    job_id = await _analyzed_job()
    resp = client.post(
        f"/jobs/{job_id}/validate",
        json={"action": "flag", "analyst": "analyst_sondos", "note": "fp"},
    )
    assert resp.json()["is_final"] is False
