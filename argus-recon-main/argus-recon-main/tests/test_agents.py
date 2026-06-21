from __future__ import annotations

from tests.test_jobs_api import make_roe

from agents.osint_agent import OsintAgent


async def test_osint_agent_normalizes_dns_and_ct_results():
    async def fake_resolver(domain: str) -> dict[str, list[str]]:
        return {
            "a": ["93.184.216.34"],
            "aaaa": ["2606:2800:220:1:248:1893:25c8:1946"],
            "mx": ["mail.example.com"],
            "txt": ["v=spf1 include:_spf.example.com ~all"],
            "ns": ["ns1.example.com"],
        }

    async def fake_crt(domain: str) -> list[dict[str, object]]:
        return [
            {"name_value": "www.example.com"},
            {"name_value": "api.example.com"},
        ]

    agent = OsintAgent(resolver=fake_resolver, crt_fetcher=fake_crt)
    result = await agent.run("example.com")

    assert result.apex_domain == "example.com"
    assert result.ip_addresses == ["93.184.216.34", "2606:2800:220:1:248:1893:25c8:1946"]
    assert result.mx_hosts == ["mail.example.com"]
    assert result.subdomains == ["www.example.com", "api.example.com"]


async def test_run_osint_endpoint_returns_collected_data(client):
    roe = make_roe()
    create_resp = await client.post(
        "/jobs",
        json={"apex_domain": "example.com", "roe": roe.model_dump(mode="json")},
    )
    assert create_resp.status_code == 201

    job_id = create_resp.json()["job_id"]
    resp = await client.post(f"/jobs/{job_id}/run-osint")

    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == job_id
    assert body["result"]["apex_domain"] == "example.com"
    assert body["result"]["subdomains"]


async def test_run_workflow_endpoint_orchestrates_all_agents(client):
    roe = make_roe(active_scanning_authorized=False)
    create_resp = await client.post(
        "/jobs",
        json={"apex_domain": "example.com", "roe": roe.model_dump(mode="json")},
    )
    assert create_resp.status_code == 201

    job_id = create_resp.json()["job_id"]
    resp = await client.post(f"/jobs/{job_id}/run-workflow")

    if resp.status_code != 200:
        print(f"Error response: {resp.text}")
        print(f"Status code: {resp.status_code}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == job_id
    assert body["status"] == "completed"
    result = body["result"]
    assert "kb_refs" in result
    assert "osint" in result["kb_refs"]
    assert "web" in result["kb_refs"]
    assert "threat_intel" in result["kb_refs"]
    assert "network" not in result["kb_refs"]  # not authorized


async def test_run_workflow_with_active_scanning(client):
    roe = make_roe(active_scanning_authorized=True, allowed_active_tools=["nmap"])
    create_resp = await client.post(
        "/jobs",
        json={"apex_domain": "example.com", "roe": roe.model_dump(mode="json")},
    )
    assert create_resp.status_code == 201

    job_id = create_resp.json()["job_id"]
    resp = await client.post(f"/jobs/{job_id}/run-workflow")

    assert resp.status_code == 200
    body = resp.json()
    result = body["result"]
    assert "network" in result["kb_refs"]  # should be included when authorized
