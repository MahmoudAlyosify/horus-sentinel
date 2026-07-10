"""Queue + worker + resume-after-kill tests (master plan Phase 5.2)."""

from datetime import datetime, timedelta

import httpx
import pytest
import respx

from agents.analysis_agent import analysis_agent
from core.db import init_db
from core.jobs import job_service
from core.queue import InMemoryJobQueue
from horus_brain.horus_provider import horus_provider
from schemas.roe import RoE, SourceCategory
from schemas.state import JobStatus
from schemas.subject import Subject, SubjectType
from workflows.orchestrator import orchestrator
from workflows.worker import Worker, enqueue_job


@pytest.fixture(autouse=True)
def _setup():
    init_db()
    from core.cache import cache

    cache._store.clear()


@pytest.fixture
def _offline_brain():
    with respx.mock(assert_all_called=False) as router:
        router.post(horus_provider.endpoint).mock(side_effect=httpx.ConnectError("refused"))
        yield router


def _region_job() -> str:
    subject = Subject(type=SubjectType.REGION, value="Sinai", year_from=2018, year_to=2019)
    roe = RoE(
        subject="Sinai",
        enabled_sources=[SourceCategory.GEO_EVENTS, SourceCategory.THREAT_INTEL],
        signed_by="analyst_test",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    job_id, _ = job_service.create_job(subject, roe)
    return job_id


async def test_inmemory_queue_roundtrip():
    q = InMemoryJobQueue()
    await q.enqueue("j1")
    await q.enqueue("j2")
    assert await q.size() == 2
    assert await q.dequeue(1.0) == "j1"
    assert await q.dequeue(1.0) == "j2"
    assert await q.dequeue(0.05) is None  # empty -> None after timeout


async def test_worker_processes_enqueued_job(_offline_brain):
    job_id = _region_job()
    await enqueue_job(job_id)
    processed = await Worker().process_one(timeout=2.0)
    assert processed == job_id
    assert job_service.get_job(job_id).status == JobStatus.AWAITING_VALIDATION.value


async def test_stage_checkpoints_are_recorded(_offline_brain):
    job_id = _region_job()
    await orchestrator.run(job_id)
    done = job_service.completed_stages(job_id)
    assert "geo_event" in done
    assert "threat_intel" in done
    assert "analysis" in done


async def test_resume_after_mid_run_kill(monkeypatch, _offline_brain):
    """A job killed during analysis resumes: collection stages are skipped, analysis re-runs."""
    job_id = _region_job()

    calls = {"n": 0}
    real_analyze = analysis_agent.analyze

    async def flaky(jid: str, subj: str):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated mid-run kill")
        return await real_analyze(jid, subj)

    monkeypatch.setattr(analysis_agent, "analyze", flaky)

    # First run dies during the analysis stage.
    with pytest.raises(RuntimeError, match="mid-run kill"):
        await orchestrator.run(job_id)

    done = job_service.completed_stages(job_id)
    assert "geo_event" in done  # collection was checkpointed
    assert "analysis" not in done  # analysis did not complete
    assert job_service.get_job(job_id).status == JobStatus.FAILED.value

    # Resume: collection stages skipped, analysis runs again and succeeds.
    summary = await orchestrator.run(job_id, resume=True)
    assert "geo_event" in summary.skipped_stages
    assert "threat_intel" in summary.skipped_stages
    assert summary.status == JobStatus.AWAITING_VALIDATION.value
    assert calls["n"] == 2  # analysis attempted once (killed) + once (resume)
    assert "analysis" in job_service.completed_stages(job_id)


def test_redis_queue_importable_or_skipped():
    """RedisJobQueue constructs only when the redis package is present (graceful otherwise)."""
    try:
        import redis.asyncio  # noqa: F401
    except ImportError:
        pytest.skip("redis not installed — the queue falls back to in-memory (by design)")
    from core.queue import RedisJobQueue

    q = RedisJobQueue("redis://localhost:6379/0", "horus:test")
    assert q._name == "horus:test"
    assert q._processing == "horus:test:processing"


async def test_resume_does_not_recollect(monkeypatch, _offline_brain):
    """On resume, a completed collection agent is not invoked again."""
    job_id = _region_job()
    await orchestrator.run(job_id)  # full run to AWAITING_VALIDATION

    # If we resume, geo_event must be skipped — prove it by making the agent blow up.
    from agents import geo_event_agent as gea

    def _boom(*_a, **_k):
        raise AssertionError("geo_event should not run again on resume")

    monkeypatch.setattr(gea.GeoEventAgent, "collect", _boom)
    summary = await orchestrator.run(job_id, resume=True)
    assert "geo_event" in summary.skipped_stages
