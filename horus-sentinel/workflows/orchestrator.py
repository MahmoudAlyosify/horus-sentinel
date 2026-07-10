"""Pipeline orchestrator — runs the whole assessment end to end (master plan Part 2.3).

Pure-Python driver that runs the same fan-out/converge flow as the LangGraph definition
(``workflows.sentinel_graph``), so the platform runs everywhere without requiring the
LangGraph runtime. It rebuilds the AuthContext from the persisted job, runs only the
agents the RoE + subject type warrant, then hands off to the brain and (post-validation)
the reporting agent. Status is checkpointed to the DB at every stage — resumable.

Order (Part 2.3):  authorize → osint → {geo_event, web_infra} → threat_intel → analysis
                   → [human validation] → report
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import structlog

from agents.analysis_agent import analysis_agent
from agents.geo_event_agent import GeoEventAgent
from agents.osint_agent import OsintAgent
from agents.report_agent import report_agent
from agents.threat_intel_agent import ThreatIntelAgent
from agents.web_infra_agent import WebInfraAgent
from core.analysis_store import save_analysis
from core.authorization import authorization_engine
from core.jobs import job_service
from schemas.auth import AuthContext
from schemas.roe import RoE, SourceCategory
from schemas.state import JobStatus
from schemas.subject import Subject, SubjectType

log = structlog.get_logger("horus.orchestrator")


@dataclass
class RunSummary:
    """A compact record of what a pipeline run produced."""

    job_id: str
    status: str
    entity_count: int = 0
    agents_run: list[str] = field(default_factory=list)
    critical_cve_hits: int = 0
    report_paths: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class Orchestrator:
    """Drives collection → reasoning → (validation) → reporting for one job."""

    def _load(self, job_id: str) -> tuple[Subject, RoE, AuthContext]:
        view = job_service.get_job(job_id)
        if view is None:
            raise KeyError(job_id)
        subject = Subject(**view.subject)
        roe = RoE(**view.roe)
        auth = authorization_engine.authorize(job_id, subject, roe)
        return subject, roe, auth

    async def run_collection(self, job_id: str) -> RunSummary:
        """Run the enabled collection agents in the fan-out/converge order."""
        subject, roe, auth = self._load(job_id)
        summary = RunSummary(job_id=job_id, status=JobStatus.COLLECTING.value)
        job_service.set_status(job_id, JobStatus.COLLECTING)

        # osint first — it seeds domains/IPs the later agents build on.
        if subject.type == SubjectType.DOMAIN and roe.allows_source(SourceCategory.PUBLIC_RECORDS):
            res = await OsintAgent().collect(subject, auth)
            summary.agents_run.append("osint")
            summary.errors += res.errors

        # geo_event and web_infra can run concurrently once osint is done.
        parallel = []
        if subject.type == SubjectType.REGION and roe.allows_source(SourceCategory.GEO_EVENTS):
            parallel.append(("geo_event", GeoEventAgent().collect(subject, auth)))
        if subject.type == SubjectType.DOMAIN and roe.allows_source(SourceCategory.WEB_INFRA):
            parallel.append(("web_infra", WebInfraAgent().collect(subject, auth)))
        if parallel:
            results = await asyncio.gather(*(c for _, c in parallel))
            for (name, _), res in zip(parallel, results, strict=True):
                summary.agents_run.append(name)
                summary.errors += res.errors

        # threat_intel converges last — it enriches whatever the eyes discovered.
        if roe.allows_source(SourceCategory.THREAT_INTEL):
            res = await ThreatIntelAgent().collect(subject, auth)
            summary.agents_run.append("threat_intel")
            summary.errors += res.errors

        log.info("collection_complete", job_id=job_id, agents=summary.agents_run)
        return summary

    async def run_analysis(self, job_id: str, summary: RunSummary | None = None) -> RunSummary:
        """Run the HORUS brain over the correlated graph and persist the draft report card."""
        subject, _, _ = self._load(job_id)
        summary = summary or RunSummary(job_id=job_id, status=JobStatus.ANALYZING.value)
        job_service.set_status(job_id, JobStatus.ANALYZING)

        card, graph = await analysis_agent.analyze(job_id, subject.value)
        await save_analysis(job_id, card, graph)

        summary.entity_count = card.entity_count
        summary.critical_cve_hits = card.critical_cve_hits
        summary.status = JobStatus.AWAITING_VALIDATION.value
        job_service.set_status(job_id, JobStatus.AWAITING_VALIDATION)
        log.info("analysis_persisted", job_id=job_id, entities=card.entity_count)
        return summary

    async def run(self, job_id: str) -> RunSummary:
        """Collection + reasoning. Stops at AWAITING_VALIDATION (the human checkpoint)."""
        try:
            summary = await self.run_collection(job_id)
            summary = await self.run_analysis(job_id, summary)
            return summary
        except Exception as exc:
            job_service.set_status(job_id, JobStatus.FAILED, error=str(exc))
            log.warning("pipeline_failed", job_id=job_id, error=str(exc))
            raise

    def generate_report(self, job_id: str, formats: list[str] | None = None) -> dict[str, str]:
        """Render the report deliverable (called after validation, or for a draft).

        A report is FINAL (COMPLETED) only if an analyst has validated; otherwise the job
        returns to AWAITING_VALIDATION with a draft available.
        """
        job_service.set_status(job_id, JobStatus.REPORTING)
        paths = report_agent.generate(job_id, formats)
        view = job_service.get_job(job_id)
        final = JobStatus.COMPLETED if view and view.validated_by else JobStatus.AWAITING_VALIDATION
        job_service.set_status(job_id, final)
        return paths

    async def run_full(
        self, job_id: str, auto_validate_by: str | None = None, formats: list[str] | None = None
    ) -> RunSummary:
        """Convenience end-to-end run for the Guided Demo: collect → analyze → (validate) → report."""
        summary = await self.run(job_id)
        if auto_validate_by:
            job_service.record_validation(
                job_id, "validate", auto_validate_by, note="Auto-validated (guided demo)."
            )
        summary.report_paths = self.generate_report(job_id, formats)
        view = job_service.get_job(job_id)
        summary.status = view.status if view else summary.status
        return summary


orchestrator = Orchestrator()
