"""API tests for job submission — the Control Plane over HTTP (Phase 1.4)."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from api.main import app
from core.db import init_db

client = TestClient(app)


def _payload(**roe_overrides) -> dict:
    roe = {
        "subject": "example.com",
        "enabled_sources": ["public_records"],
        "in_scope_domains": ["example.com"],
        "signed_by": "analyst_mahmoud",
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
    }
    roe.update(roe_overrides)
    return {
        "subject": {"type": "domain", "value": "example.com"},
        "roe": roe,
    }


def setup_module() -> None:
    init_db()


def test_create_and_get_job():
    resp = client.post("/jobs", json=_payload())
    assert resp.status_code == 201, resp.text
    job_id = resp.json()["id"]
    assert resp.json()["status"] == "authorized"

    got = client.get(f"/jobs/{job_id}")
    assert got.status_code == 200
    body = got.json()
    assert body["id"] == job_id
    assert body["subject"]["value"] == "example.com"
    assert body["status"] == "authorized"


def test_disallowed_source_is_refused_with_403():
    # Enable web_infra for an out-of-scope subject -> the gate refuses.
    payload = _payload(
        subject="attacker.com",
        enabled_sources=["web_infra"],
        in_scope_domains=["example.com"],
    )
    payload["subject"] = {"type": "domain", "value": "attacker.com"}
    resp = client.post("/jobs", json=payload)
    assert resp.status_code == 403
    assert "in_scope_domains" in resp.json()["detail"]


def test_expired_roe_is_refused():
    payload = _payload(expires_at=(datetime.utcnow() - timedelta(hours=1)).isoformat())
    resp = client.post("/jobs", json=payload)
    assert resp.status_code == 403
    assert "expired" in resp.json()["detail"].lower()


def test_get_missing_job_404():
    resp = client.get("/jobs/does-not-exist")
    assert resp.status_code == 404
