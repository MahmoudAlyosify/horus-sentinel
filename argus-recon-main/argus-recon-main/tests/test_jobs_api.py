from __future__ import annotations

from datetime import UTC, datetime, timedelta

from core.authorization import sign_roe
from schemas.roe import RoERecord, ScopeAsset, ScopeAssetType

SIGNING_KEY = "test-signing-key"  # matches ARGUS_ROE_SIGNING_KEY set in conftest


def make_roe(**overrides) -> RoERecord:
    now = datetime.now(UTC)
    defaults = dict(
        client_name="Example Corp",
        authorized_by="CISO",
        contact_email="security@example.com",
        in_scope_assets=[ScopeAsset(type=ScopeAssetType.DOMAIN, value="example.com")],
        excluded_assets=[],
        active_scanning_authorized=False,
        allowed_active_tools=[],
        valid_from=now - timedelta(hours=1),
        valid_until=now + timedelta(days=1),
    )
    defaults.update(overrides)
    roe = RoERecord(**defaults)
    return sign_roe(roe, SIGNING_KEY)


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_submit_job_in_scope_succeeds(client):
    roe = make_roe()
    resp = await client.post(
        "/jobs",
        json={"apex_domain": "example.com", "roe": roe.model_dump(mode="json")},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "authorized"
    assert body["apex_domain"] == "example.com"
    assert body["active_scanning_authorized"] is False
    assert body["roe_id"] == str(roe.roe_id)


async def test_submit_job_out_of_scope_is_rejected(client):
    roe = make_roe()  # only example.com is in scope
    resp = await client.post(
        "/jobs",
        json={"apex_domain": "not-example.com", "roe": roe.model_dump(mode="json")},
    )
    assert resp.status_code == 403


async def test_submit_job_with_invalid_signature_is_rejected(client):
    roe = make_roe()
    tampered = roe.model_dump(mode="json")
    tampered["client_name"] = "Someone Else"  # signature no longer matches

    resp = await client.post(
        "/jobs",
        json={"apex_domain": "example.com", "roe": tampered},
    )
    assert resp.status_code == 422


async def test_submit_job_with_expired_roe_is_rejected(client):
    now = datetime.now(UTC)
    roe = make_roe(valid_from=now - timedelta(days=10), valid_until=now - timedelta(days=1))

    resp = await client.post(
        "/jobs",
        json={"apex_domain": "example.com", "roe": roe.model_dump(mode="json")},
    )
    assert resp.status_code == 422


async def test_get_job_round_trips(client):
    roe = make_roe(active_scanning_authorized=True, allowed_active_tools=["nmap"])
    create_resp = await client.post(
        "/jobs",
        json={"apex_domain": "example.com", "roe": roe.model_dump(mode="json")},
    )
    assert create_resp.status_code == 201
    job_id = create_resp.json()["job_id"]

    get_resp = await client.get(f"/jobs/{job_id}")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["job_id"] == job_id
    assert body["active_scanning_authorized"] is True


async def test_get_unknown_job_is_404(client):
    resp = await client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_list_jobs(client):
    roe = make_roe()
    await client.post(
        "/jobs",
        json={"apex_domain": "example.com", "roe": roe.model_dump(mode="json")},
    )
    resp = await client.get("/jobs")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
