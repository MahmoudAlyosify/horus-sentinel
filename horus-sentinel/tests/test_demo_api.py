"""Guided Demo endpoint test — one click, full offline assessment (Phase 6.6 backend)."""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from api.main import app
from core.config import settings
from core.db import init_db
from horus_brain.horus_provider import horus_provider

client = TestClient(app)


@pytest.fixture(autouse=True)
def _setup(tmp_path, monkeypatch):
    from core.cache import cache

    init_db()
    cache._store.clear()  # isolate the process-wide tool cache between tests
    monkeypatch.setattr(settings, "report_output_dir", str(tmp_path / "reports"))


def test_guided_demo_runs_end_to_end():
    with respx.mock(assert_all_called=False) as router:
        router.post(horus_provider.endpoint).mock(side_effect=httpx.ConnectError("refused"))
        resp = client.post("/demo")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["subject"] == "Sinai"
    assert body["status"] == "completed"
    assert body["entity_count"] > 0
    assert body["report_url"].startswith("/jobs/")

    # The report is retrievable and validated.
    report = client.get(body["report_url"])
    assert report.status_code == 200
    assert report.json()["report_card"]["subject"] == "Sinai"
