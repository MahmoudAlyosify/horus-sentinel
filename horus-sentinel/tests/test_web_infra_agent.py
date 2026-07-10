"""Web/Infra agent test — mocked HTTPS fetch; verifies the exposure chain forms."""

from datetime import datetime, timedelta

import httpx
import pytest
import respx

from agents.web_infra_agent import WebInfraAgent
from core.cache import cache
from core.db import init_db
from core.findings_store import load_findings, persist_findings
from graph.knowledge_graph import KnowledgeGraph
from schemas.auth import AuthContext
from schemas.findings import EntityKind, Finding
from schemas.roe import RoE, SourceCategory
from schemas.subject import Subject, SubjectType


@pytest.fixture(autouse=True)
async def _setup():
    init_db()
    await cache.clear()
    yield
    await cache.clear()


def _ctx(job_id: str) -> AuthContext:
    roe = RoE(
        subject="example.com",
        enabled_sources=[SourceCategory.WEB_INFRA],
        in_scope_domains=["example.com"],
        signed_by="analyst_test",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    return AuthContext(job_id=job_id, roe=roe)


async def test_web_infra_builds_exposure_chain():
    job = "webjob1"
    # Seed a resolved IP as if the OSINT agent had already run.
    await persist_findings(
        job,
        [Finding(entity_kind=EntityKind.IP, entity_value="93.184.216.34", produced_by="osint")],
    )

    headers = {
        "server": "nginx",
        "x-powered-by": "PHP/8.1",
        "strict-transport-security": "max-age=1",
    }
    with respx.mock(assert_all_called=False) as router:
        router.get("https://example.com").mock(
            return_value=httpx.Response(200, headers=headers, text="<html></html>")
        )
        subject = Subject(type=SubjectType.DOMAIN, value="example.com")
        result = await WebInfraAgent().collect(subject, _ctx(job))

    kinds = {k.split(":")[0] for k in result.entity_keys}
    assert "Service" in kinds
    assert "Technology" in kinds

    # Build the graph from everything persisted and confirm IP -[EXPOSES]-> Service.
    graph = KnowledgeGraph.from_findings(load_findings(job))
    assert graph.g.has_edge("IP:93.184.216.34", "Service:example.com:443")
    # Service -[RUNS]-> Technology(nginx)
    assert graph.g.has_edge("Service:example.com:443", "Technology:nginx")


async def test_web_infra_graceful_on_fetch_failure():
    job = "webjob2"
    with respx.mock(assert_all_called=False) as router:
        router.get("https://example.com").mock(side_effect=httpx.ConnectError("down"))
        subject = Subject(type=SubjectType.DOMAIN, value="example.com")
        result = await WebInfraAgent().collect(subject, _ctx(job))
    assert any("could not fetch" in e for e in result.errors)
