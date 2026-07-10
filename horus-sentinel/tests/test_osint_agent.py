"""OSINT agent tests — DNS monkeypatched, HTTP sources mocked with respx (no network)."""

from datetime import datetime, timedelta

import httpx
import pytest
import respx

from agents.osint_agent import OsintAgent
from core.cache import cache
from core.db import init_db
from schemas.auth import AuthContext
from schemas.findings import EntityKind
from schemas.roe import RoE, SourceCategory
from schemas.subject import Subject, SubjectType
from tools.dns_tool import DnsTool


@pytest.fixture(autouse=True)
async def _setup():
    init_db()
    await cache.clear()
    yield
    await cache.clear()


def _ctx(job_id: str) -> AuthContext:
    roe = RoE(
        subject="example.com",
        enabled_sources=[SourceCategory.PUBLIC_RECORDS],
        in_scope_domains=["example.com"],
        signed_by="analyst_test",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    return AuthContext(job_id=job_id, roe=roe)


_FAKE_DNS = {
    "A": ["93.184.216.34"],
    "AAAA": [],
    "MX": ["10 mail.example.com."],
    "TXT": ["v=spf1 -all"],
    "NS": ["a.iana-servers.net."],
    "CNAME": [],
}

_FAKE_CRTSH = [
    {"issuer_name": "Let's Encrypt", "name_value": "www.example.com\napi.example.com"},
    {"issuer_name": "Let's Encrypt", "name_value": "*.example.com"},
]

_FAKE_RDAP = {
    "handle": "EXAMPLE-COM",
    "status": ["client transfer prohibited"],
    "events": [{"eventAction": "registration", "eventDate": "1995-08-14T04:00:00Z"}],
    "entities": [
        {
            "roles": ["registrar"],
            "vcardArray": ["vcard", [["fn", {}, "text", "ICANN Registrar"]]],
        }
    ],
    "nameservers": [{"ldhName": "a.iana-servers.net"}],
}


async def test_osint_agent_builds_entity_picture(monkeypatch):
    monkeypatch.setattr(DnsTool, "_resolve_all", staticmethod(lambda domain: _FAKE_DNS))

    with respx.mock(assert_all_called=False) as router:
        router.get("https://crt.sh/").mock(return_value=httpx.Response(200, json=_FAKE_CRTSH))
        router.get("https://rdap.org/domain/example.com").mock(
            return_value=httpx.Response(200, json=_FAKE_RDAP)
        )
        subject = Subject(type=SubjectType.DOMAIN, value="example.com")
        agent = OsintAgent()
        result = await agent.collect(subject, _ctx("osintjob1"))

    kinds = {k.split(":")[0] for k in result.entity_keys}
    assert "Domain" in kinds
    assert "IP" in kinds  # from DNS A record
    assert "Subdomain" in kinds  # from crt.sh
    assert "Email" in kinds  # inferred email pattern
    assert result.persisted == result.findings_count


async def test_osint_agent_ip_resolves_from_domain(monkeypatch):
    monkeypatch.setattr(DnsTool, "_resolve_all", staticmethod(lambda domain: _FAKE_DNS))
    with respx.mock(assert_all_called=False) as router:
        router.get("https://crt.sh/").mock(return_value=httpx.Response(200, json=[]))
        router.get("https://rdap.org/domain/example.com").mock(
            return_value=httpx.Response(404, json={})
        )
        subject = Subject(type=SubjectType.DOMAIN, value="example.com")
        agent = OsintAgent()
        result = await agent.collect(subject, _ctx("osintjob2"))

    ip_keys = [k for k in result.entity_keys if k.startswith("IP:")]
    assert "IP:93.184.216.34" in ip_keys


async def test_osint_agent_survives_source_outage(monkeypatch):
    """Every HTTP source failing must not crash the agent — DNS still yields the domain."""
    monkeypatch.setattr(DnsTool, "_resolve_all", staticmethod(lambda domain: _FAKE_DNS))
    with respx.mock(assert_all_called=False) as router:
        router.get("https://crt.sh/").mock(side_effect=httpx.ConnectError("down"))
        router.get("https://rdap.org/domain/example.com").mock(
            side_effect=httpx.ConnectError("down")
        )
        subject = Subject(type=SubjectType.DOMAIN, value="example.com")
        agent = OsintAgent()
        result = await agent.collect(subject, _ctx("osintjob3"))

    assert result.findings_count > 0  # DNS + inferred email still produced
    kinds = {k.split(":")[0] for k in result.entity_keys}
    assert "Domain" in kinds
    assert EntityKind.DOMAIN.value == "Domain"
