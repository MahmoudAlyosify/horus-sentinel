from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from core.authorization import (
    ActiveScanningNotAuthorizedError,
    AuthContext,
    OutOfScopeError,
    sign_roe,
)
from core.cache import cache
from core.rate_limit import RateBudget
from db.models import AuditLogORM
from db.session import async_session_factory
from schemas.roe import RoERecord, ScopeAsset, ScopeAssetType
from schemas.target import AssetKind, Target
from tools.base import ReconTool, ToolResult

SIGNING_KEY = "test-signing-key"


class DummyResult(ToolResult):
    hits: int = 0

    def summary(self) -> dict:
        return {"hits": self.hits}


class DummyPassiveTool(ReconTool):
    name = "dummy_passive"
    classification = "passive"
    rate_limit = RateBudget(rate=1000, burst=1000)  # effectively unthrottled for tests
    cache_ttl = 60

    def __init__(self) -> None:
        self.calls = 0

    async def run(self, target: Target, ctx: AuthContext) -> DummyResult:
        self.calls += 1
        return DummyResult(hits=self.calls)


class DummyActiveTool(ReconTool):
    name = "dummy_active"
    classification = "active"
    rate_limit = RateBudget(rate=1000, burst=1000)

    async def run(self, target: Target, ctx: AuthContext) -> DummyResult:
        return DummyResult(hits=1)


def make_ctx(**overrides) -> AuthContext:
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
    roe = sign_roe(RoERecord(**defaults), SIGNING_KEY)
    return AuthContext(job_id=uuid4(), roe=roe)


@pytest.fixture(autouse=True)
async def _clear_cache():
    await cache.clear()
    yield
    await cache.clear()


async def test_passive_tool_runs_and_audits():
    ctx = make_ctx()
    tool = DummyPassiveTool()
    target = Target(job_id=ctx.job_id, value="www.example.com", kind=AssetKind.SUBDOMAIN)

    result = await tool(target, ctx)
    assert result.hits == 1
    assert tool.calls == 1

    async with async_session_factory() as session:
        rows = (
            (await session.execute(select(AuditLogORM).where(AuditLogORM.job_id == ctx.job_id)))
            .scalars()
            .all()
        )
    assert len(rows) == 1
    assert rows[0].tool_name == "dummy_passive"
    assert rows[0].classification == "passive"
    assert rows[0].summary == {"cache_hit": False, "hits": 1}


async def test_cache_hit_skips_run_but_still_audits():
    ctx = make_ctx()
    tool = DummyPassiveTool()
    target = Target(job_id=ctx.job_id, value="www.example.com", kind=AssetKind.SUBDOMAIN)

    first = await tool(target, ctx)
    second = await tool(target, ctx)

    assert tool.calls == 1  # run() only called once — second was a cache hit
    assert first.hits == second.hits == 1

    async with async_session_factory() as session:
        rows = (
            (await session.execute(select(AuditLogORM).where(AuditLogORM.job_id == ctx.job_id)))
            .scalars()
            .all()
        )
    assert len(rows) == 2
    assert [r.summary["cache_hit"] for r in rows] == [False, True]


async def test_out_of_scope_target_is_blocked_before_run():
    ctx = make_ctx()
    tool = DummyPassiveTool()
    target = Target(job_id=ctx.job_id, value="not-example.com", kind=AssetKind.DOMAIN)

    with pytest.raises(OutOfScopeError):
        await tool(target, ctx)

    assert tool.calls == 0  # never reached run()


async def test_active_tool_blocked_when_roe_not_authorized():
    ctx = make_ctx(active_scanning_authorized=False)
    tool = DummyActiveTool()
    target = Target(job_id=ctx.job_id, value="example.com", kind=AssetKind.DOMAIN)

    with pytest.raises(ActiveScanningNotAuthorizedError):
        await tool(target, ctx)


async def test_active_tool_allowed_when_roe_authorizes_it():
    ctx = make_ctx(active_scanning_authorized=True, allowed_active_tools=["dummy_active"])
    tool = DummyActiveTool()
    target = Target(job_id=ctx.job_id, value="example.com", kind=AssetKind.DOMAIN)

    result = await tool(target, ctx)
    assert result.hits == 1
