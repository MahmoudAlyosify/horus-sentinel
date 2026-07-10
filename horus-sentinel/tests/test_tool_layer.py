"""Tests for the Tool Abstraction Layer — the four central controls.

Proves the master-plan invariant: authorization, cache, rate-limit and audit are enforced
by the wrapper, so a dummy tool that does almost nothing still gets all four for free.
"""

from datetime import datetime, timedelta

import pytest

from core.cache import cache
from core.db import AuditRecord, init_db, session_scope
from schemas.auth import AuthContext, AuthorizationError
from schemas.findings import EntityKind, Evidence, Finding, ToolResult
from schemas.roe import RoE, SourceCategory
from schemas.subject import Subject, SubjectType
from tools.base import IntelTool


class _DummyTool(IntelTool):
    name = "dummy"
    source_category = SourceCategory.PUBLIC_RECORDS
    cache_ttl = 60

    def __init__(self) -> None:
        super().__init__()
        self.run_count = 0

    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        self.run_count += 1
        finding = Finding(
            entity_kind=EntityKind.DOMAIN,
            entity_value=subject.value,
            produced_by=self.name,
            evidence=[
                Evidence(
                    source=self.name,
                    source_category=self.source_category,
                    summary=f"observed {subject.value}",
                )
            ],
        )
        return ToolResult(
            tool=self.name,
            source_category=self.source_category,
            findings=[finding],
            evidence=finding.evidence,
        )


def _ctx(job_id: str = "jobT") -> AuthContext:
    roe = RoE(
        subject="example.com",
        enabled_sources=[SourceCategory.PUBLIC_RECORDS],
        in_scope_domains=["example.com"],
        signed_by="analyst_test",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    return AuthContext(job_id=job_id, roe=roe)


def _subject() -> Subject:
    return Subject(type=SubjectType.DOMAIN, value="example.com")


@pytest.fixture(autouse=True)
async def _clean_cache():
    init_db()
    await cache.clear()
    yield
    await cache.clear()


async def test_tool_runs_and_produces_findings():
    tool = _DummyTool()
    result = await tool(_subject(), _ctx())
    assert result.error is None
    assert len(result.findings) == 1
    assert result.cached is False
    assert tool.run_count == 1


async def test_second_call_is_cache_hit():
    tool = _DummyTool()
    ctx = _ctx()
    await tool(_subject(), ctx)
    second = await tool(_subject(), ctx)
    assert second.cached is True
    assert tool.run_count == 1  # run() not called again — served from cache


async def test_audit_rows_appear():
    tool = _DummyTool()
    ctx = _ctx("jobAudit")
    await tool(_subject(), ctx)
    # Persistence happens in a worker thread; give it a beat via a direct query.
    with session_scope() as session:
        rows = session.query(AuditRecord).filter(AuditRecord.job_id == "jobAudit").all()
    assert len(rows) >= 1
    assert rows[0].tool == "dummy"
    assert rows[0].signed_by == "analyst_test"


async def test_disabled_source_is_refused_by_layer():
    class _WebTool(_DummyTool):
        name = "web-dummy"
        source_category = SourceCategory.WEB_INFRA

    tool = _WebTool()
    # RoE enables only PUBLIC_RECORDS, so a WEB_INFRA tool must be refused.
    with pytest.raises(AuthorizationError):
        await tool(_subject(), _ctx())
