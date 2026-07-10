"""LangGraph orchestration (master plan Part 2.3).

The stateful fan-out/converge graph: nodes are agents, edges are transitions, a shared
``SentinelState`` carries the job_id + AuthContext + lightweight references. Conditional
edges implement policy (an agent runs only if its source is enabled). A checkpointer makes
long jobs resumable and every transition auditable.

``langgraph`` is imported lazily inside ``build_sentinel_graph`` so the rest of the platform
(and the pure-Python ``Orchestrator``) runs without the LangGraph runtime installed. On the
full stack, ``build_sentinel_graph()`` returns a compiled graph that runs end to end and can
checkpoint to Postgres.
"""
from __future__ import annotations

from typing import Any

import structlog

from agents.analysis_agent import analysis_agent
from agents.geo_event_agent import GeoEventAgent
from agents.osint_agent import OsintAgent
from agents.report_agent import report_agent
from agents.threat_intel_agent import ThreatIntelAgent
from agents.web_infra_agent import WebInfraAgent
from core.analysis_store import save_analysis
from core.authorization import authorization_engine
from schemas.roe import RoE, SourceCategory
from schemas.state import JobStatus, SentinelState
from schemas.subject import Subject, SubjectType

log = structlog.get_logger("horus.graph")


def langgraph_available() -> bool:
    try:
        import langgraph  # noqa: F401
    except ImportError:
        return False
    return True


# ---- node implementations (shared shape: state -> partial state) ------------


async def authorize_node(state: SentinelState) -> dict[str, Any]:
    subject: Subject = state["subject"]
    auth = state["auth"]
    authorization_engine.authorize(auth.job_id, subject, auth.roe)
    return {"status": JobStatus.AUTHORIZED, "log": ["authorized"]}


async def osint_node(state: SentinelState) -> dict[str, Any]:
    subject, auth = state["subject"], state["auth"]
    if subject.type != SubjectType.DOMAIN or not auth.roe.allows_source(
        SourceCategory.PUBLIC_RECORDS
    ):
        return {"log": ["osint skipped"]}
    res = await OsintAgent().collect(subject, auth)
    return {"finding_counts": {"osint": res.findings_count}, "log": ["osint done"]}


async def geo_event_node(state: SentinelState) -> dict[str, Any]:
    subject, auth = state["subject"], state["auth"]
    if subject.type != SubjectType.REGION or not auth.roe.allows_source(SourceCategory.GEO_EVENTS):
        return {"log": ["geo_event skipped"]}
    res = await GeoEventAgent().collect(subject, auth)
    return {"finding_counts": {"geo_event": res.findings_count}, "log": ["geo_event done"]}


async def web_infra_node(state: SentinelState) -> dict[str, Any]:
    subject, auth = state["subject"], state["auth"]
    if subject.type != SubjectType.DOMAIN or not auth.roe.allows_source(SourceCategory.WEB_INFRA):
        return {"log": ["web_infra skipped"]}
    res = await WebInfraAgent().collect(subject, auth)
    return {"finding_counts": {"web_infra": res.findings_count}, "log": ["web_infra done"]}


async def threat_intel_node(state: SentinelState) -> dict[str, Any]:
    subject, auth = state["subject"], state["auth"]
    if not auth.roe.allows_source(SourceCategory.THREAT_INTEL):
        return {"log": ["threat_intel skipped"]}
    res = await ThreatIntelAgent().collect(subject, auth)
    return {"finding_counts": {"threat_intel": res.findings_count}, "log": ["threat_intel done"]}


async def analysis_node(state: SentinelState) -> dict[str, Any]:
    subject, auth = state["subject"], state["auth"]
    card, graph = await analysis_agent.analyze(auth.job_id, subject.value)
    await save_analysis(auth.job_id, card, graph)
    return {
        "status": JobStatus.AWAITING_VALIDATION,
        "report_card_ref": auth.job_id,
        "log": [f"analysis by {card.generated_by}"],
    }


async def report_node(state: SentinelState) -> dict[str, Any]:
    auth = state["auth"]
    paths = report_agent.generate(auth.job_id)
    return {
        "status": JobStatus.COMPLETED,
        "report_path": paths.get("html"),
        "log": ["report generated"],
    }


def initial_state(job_id: str, subject: Subject, roe: RoE) -> SentinelState:
    """Seed a SentinelState for a run."""
    from schemas.auth import AuthContext

    return {
        "job_id": job_id,
        "subject": subject,
        "auth": AuthContext(job_id=job_id, roe=roe),
        "status": JobStatus.PENDING,
        "finding_counts": {},
        "entity_keys": [],
        "log": [],
    }


def build_sentinel_graph(checkpointer: Any | None = None, interrupt_before_report: bool = True):
    """Build & compile the LangGraph. Raises if langgraph is not installed.

    ``interrupt_before_report`` pauses the graph before the report node so a human analyst
    validates first (master plan Part 4.5) — resume the graph to emit the report.
    """
    if not langgraph_available():
        raise RuntimeError(
            "langgraph is not installed. Use workflows.orchestrator.Orchestrator for the "
            "MVP path, or `pip install langgraph` on the full stack."
        )
    from langgraph.graph import END, StateGraph

    g = StateGraph(SentinelState)
    g.add_node("authorize", authorize_node)
    g.add_node("osint", osint_node)
    g.add_node("geo_event", geo_event_node)
    g.add_node("web_infra", web_infra_node)
    g.add_node("threat_intel", threat_intel_node)
    g.add_node("analysis", analysis_node)
    g.add_node("report", report_node)

    g.set_entry_point("authorize")
    g.add_edge("authorize", "osint")
    g.add_edge("osint", "geo_event")
    g.add_edge("osint", "web_infra")
    g.add_edge("geo_event", "threat_intel")
    g.add_edge("web_infra", "threat_intel")
    g.add_edge("threat_intel", "analysis")
    g.add_edge("analysis", "report")
    g.add_edge("report", END)

    compile_kwargs: dict[str, Any] = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    if interrupt_before_report:
        compile_kwargs["interrupt_before"] = ["report"]
    return g.compile(**compile_kwargs)
