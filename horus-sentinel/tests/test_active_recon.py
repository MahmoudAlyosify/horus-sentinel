"""Active reconnaissance tool tests — port scan, active DNS, compliant web crawl.

Everything runs against local fixtures (a localhost listener, a mocked HTTP host, a stubbed
resolver) — no real external target is ever touched.
"""

import asyncio
from datetime import datetime, timedelta

import httpx
import pytest
import respx

from core.cache import cache
from core.config import settings
from core.db import init_db
from core.findings_store import persist_findings
from schemas.auth import AuthContext
from schemas.findings import EntityKind, Finding
from schemas.roe import RoE, SourceCategory
from schemas.subject import Subject, SubjectType
from tools.active_dns_tool import ActiveDnsTool
from tools.port_scan_tool import PortScanTool
from tools.web_crawl_tool import WebCrawlTool


@pytest.fixture(autouse=True)
async def _setup():
    init_db()
    await cache.clear()
    yield
    await cache.clear()


def _ctx(job_id: str) -> AuthContext:
    roe = RoE(
        subject="example.com",
        enabled_sources=[SourceCategory.ACTIVE_RECON, SourceCategory.WEB_CRAWL],
        in_scope_domains=["example.com"],
        active_authorized=True,
        signed_by="operator",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    return AuthContext(job_id=job_id, roe=roe)


_SUBJECT = Subject(type=SubjectType.DOMAIN, value="example.com")


async def test_port_scan_finds_open_port_on_localhost():
    job = "portjob1"

    # A real listener on an ephemeral port; the tool should detect it open.
    async def handler(reader, writer):
        writer.write(b"HORUS-TEST-BANNER\r\n")
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    async with server:
        await persist_findings(
            job, [Finding(entity_kind=EntityKind.IP, entity_value="127.0.0.1", produced_by="t")]
        )
        old_ports = settings.active_scan_ports
        settings.active_scan_ports = f"{port}"
        try:
            result = await PortScanTool()(_SUBJECT, _ctx(job))
        finally:
            settings.active_scan_ports = old_ports

    kinds = {f.entity_kind for f in result.findings}
    assert EntityKind.PORT in kinds
    port_finding = next(f for f in result.findings if f.entity_kind == EntityKind.PORT)
    assert port_finding.attributes["state"] == "open"
    assert port_finding.attributes["internet_facing"] is True


async def test_port_scan_reports_closed_when_nothing_listens():
    job = "portjob2"
    await persist_findings(
        job, [Finding(entity_kind=EntityKind.IP, entity_value="127.0.0.1", produced_by="t")]
    )
    old_ports, old_to = settings.active_scan_ports, settings.active_scan_timeout_s
    settings.active_scan_ports = "1"  # almost certainly nothing on port 1
    settings.active_scan_timeout_s = 0.3
    try:
        result = await PortScanTool()(_SUBJECT, _ctx(job))
    finally:
        settings.active_scan_ports, settings.active_scan_timeout_s = old_ports, old_to
    assert all(f.entity_kind != EntityKind.PORT for f in result.findings)


async def test_active_dns_emits_subdomain_and_ip(monkeypatch):
    job = "dnsjob1"

    def fake_resolve(base, candidates):
        return {"www.example.com": ["93.184.216.34"]}

    monkeypatch.setattr(ActiveDnsTool, "_resolve_candidates", staticmethod(fake_resolve))
    result = await ActiveDnsTool()(_SUBJECT, _ctx(job))
    kinds = {f.entity_kind for f in result.findings}
    assert EntityKind.SUBDOMAIN in kinds
    assert EntityKind.IP in kinds
    sub = next(f for f in result.findings if f.entity_kind == EntityKind.SUBDOMAIN)
    assert sub.attributes["discovery"] == "active_bruteforce"


async def test_web_crawl_respects_robots_and_extracts():
    job = "crawljob1"
    root = "https://example.com/"
    with respx.mock(assert_all_called=False) as router:
        router.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(200, text="User-agent: *\nDisallow: /secret\n")
        )
        router.get("https://example.com/sitemap.xml").mock(return_value=httpx.Response(404))
        router.get(root).mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html", "server": "nginx"},
                text='<html><a href="/page">p</a><a href="/secret">s</a> '
                "contact hi@example.com</html>",
            )
        )
        router.get("https://example.com/page").mock(
            return_value=httpx.Response(
                200, headers={"content-type": "text/html"}, text="<html>ok</html>"
            )
        )
        secret = router.get("https://example.com/secret").mock(
            return_value=httpx.Response(200, text="secret")
        )

        result = await WebCrawlTool()(_SUBJECT, _ctx(job))

    values = {f.entity_value for f in result.findings}
    kinds = {f.entity_kind for f in result.findings}
    # crawled the root and the allowed link, harvested the email + tech
    assert "https://example.com/" in values
    assert "https://example.com/page" in values
    assert EntityKind.EMAIL in kinds
    assert "nginx" in {
        f.entity_value for f in result.findings if f.entity_kind == EntityKind.TECHNOLOGY
    }
    # robots.txt disallowed /secret — it must NOT have been fetched
    assert not secret.called
    # but the disallowed path is *recorded* as intelligence (noted, not crawled)
    assert any("secret" in v for v in values)


async def test_web_crawl_out_of_scope_is_refused():
    """The tool layer refuses an active crawl against a target not in scope."""
    from schemas.auth import AuthorizationError

    evil = Subject(type=SubjectType.DOMAIN, value="not-mine.com")
    with pytest.raises(AuthorizationError):
        await WebCrawlTool()(evil, _ctx("crawljob2"))
