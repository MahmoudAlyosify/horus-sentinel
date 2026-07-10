"""LangGraph wiring tests — node functions run standalone; the compiled graph is optional.

The node functions are shared with the pure-Python Orchestrator, so we exercise them
directly (no LangGraph runtime needed). Building the compiled StateGraph is only checked
when ``langgraph`` is installed; otherwise the guard must raise a helpful error.
"""

from datetime import datetime, timedelta

import httpx
import pytest
import respx

from core.db import init_db
from horus_brain.horus_provider import horus_provider
from schemas.roe import RoE, SourceCategory
from schemas.subject import Subject, SubjectType
from workflows import sentinel_graph as sg


@pytest.fixture(autouse=True)
def _db():
    init_db()
    from core.cache import cache

    cache._store.clear()


def _state(job_id: str = "graphjob"):
    roe = RoE(
        subject="Sinai",
        enabled_sources=[SourceCategory.GEO_EVENTS],
        signed_by="analyst_test",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    subject = Subject(type=SubjectType.REGION, value="Sinai", year_from=2018, year_to=2019)
    return sg.initial_state(job_id, subject, roe)


async def test_authorize_node_passes():
    out = await sg.authorize_node(_state())
    assert out["status"].value == "authorized"


async def test_geo_event_node_collects():
    out = await sg.geo_event_node(_state("graphjob2"))
    assert "geo_event" in out["finding_counts"]
    assert out["finding_counts"]["geo_event"] > 0


async def test_osint_node_skips_for_region():
    out = await sg.osint_node(_state("graphjob3"))
    assert out["log"] == ["osint skipped"]


async def test_analysis_node_runs_offline():
    state = _state("graphjob4")
    await sg.geo_event_node(state)
    with respx.mock(assert_all_called=False) as router:
        router.post(horus_provider.endpoint).mock(side_effect=httpx.ConnectError("refused"))
        out = await sg.analysis_node(state)
    assert out["status"].value == "awaiting_validation"
    assert out["report_card_ref"] == "graphjob4"


def test_build_graph_guard_or_compiles():
    """If langgraph is present the graph compiles; if not, the guard raises helpfully."""
    if sg.langgraph_available():
        graph = sg.build_sentinel_graph(interrupt_before_report=False)
        assert graph is not None
    else:
        with pytest.raises(RuntimeError, match="langgraph is not installed"):
            sg.build_sentinel_graph()
