"""Smoke tests for the API skeleton."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_root_ok():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "HORUS Sentinel" in resp.json()["message"]
