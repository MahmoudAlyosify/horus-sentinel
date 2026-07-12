"""Pipeline orchestrator — runs the whole assessment end to end (master plan Part 2.3/5.2).

Pure-Python driver that runs the same fan-out/converge flow as the LangGraph definition
(``workflows.sentinel_graph``), so the platform runs everywhere without the LangGraph
runtime. It executes the pipeline as an ordered list of **checkpointed stages**: each stage
that finishes is recorded on the job, so a run started with ``resume=True`` skips the
stages already done — a job **resumes after a mid-run kill** (findings persist; the graph
is rebuilt from them).

Order (Part 2.3):  authorize → osint → {geo_event, web_infra} → threat_intel → analysis
                   → [human validation] → report
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

import structlog

from agents.active_recon_agent import ActiveReconAgent
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

Stage = tuple[str, Callable[[], Awaitable[None]]]


@dataclass
class RunSummary:
    """A compact record of what a pipeline run produced."""

    job_id: str
    status: str
    entity_count: int = 0
    agents_run: list[str] = field(default_factory=list)
    skipped_stages: list[str] = field(default_factory=list)
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

    # ---- stage builders -----------------------------------------------------
    def _stages(
        self, job_id: str, subject: Subject, roe: RoE, auth: AuthContext, summary: RunSummary
    ) -> list[Stage]:
        """The ordered, checkpointable stages for this subject + RoE."""
        stages: list[Stage] = []

        # osint first — it seeds domains/IPs the later agents build on.
        if subject.type == SubjectType.DOMAIN and roe.allows_source(SourceCategory.PUBLIC_RECORDS):
            stages.append(("osint", self._collector(OsintAgent(), subject, auth, summary, "osint")))
        # geo_event (region) and web_infra (domain) are mutually exclusive by subject type.
        if subject.type == SubjectType.REGION and roe.allows_source(SourceCategory.GEO_EVENTS):
            stages.append(
                ("geo_event", self._collector(GeoEventAgent(), subject, auth, summary, "geo_event"))
            )
        if subject.type == SubjectType.DOMAIN and roe.allows_source(SourceCategory.WEB_INFRA):
            stages.append(
                ("web_infra", self._collector(WebInfraAgent(), subject, auth, summary, "web_infra"))
            )
        # active_recon (GATED): active scanning/enumeration/crawl, only when the RoE authorizes
        # active ops on an in-scope target. Runs after osint so it inherits resolved IPs.
        if subject.type in (SubjectType.DOMAIN, SubjectType.ORGANIZATION) and roe.has_active_sources():
            stages.append(
                ("active_recon", self._collector(ActiveReconAgent(), subject, auth, summary, "active_recon"))
            )
        # threat_intel converges last — it enriches whatever the eyes discovered.
        if roe.allows_source(SourceCategory.THREAT_INTEL):
            stages.append(
                (
                    "threat_intel",
                    self._collector(ThreatIntelAgent(), subject, auth, summary, "threat_intel"),
                )
            )
        # analysis is always the final collection-side stage.
        stages.append(("analysis", self._analysis_stage(job_id, subject, summary)))
        return stages

    def _collector(
        self, agent, subject: Subject, auth: AuthContext, summary: RunSummary, name: str
    ) -> Callable[[], Awaitable[None]]:
        async def _run() -> None:
            res = await agent.collect(subject, auth)
            summary.agents_run.append(name)
            summary.errors += res.errors

        return _run

    def _analysis_stage(
        self, job_id: str, subject: Subject, summary: RunSummary
    ) -> Callable[[], Awaitable[None]]:
        async def _run() -> None:
            job_service.set_status(job_id, JobStatus.ANALYZING)
            card, graph = await analysis_agent.analyze(job_id, subject.value)
            await save_analysis(job_id, card, graph)
            summary.entity_count = card.entity_count
            summary.critical_cve_hits = card.critical_cve_hits

        return _run

    # ---- run ----------------------------------------------------------------
    async def run(self, job_id: str, resume: bool = False) -> RunSummary:
        """Execute the checkpointed pipeline, stopping at the human-validation checkpoint.

        With ``resume=True`` any stage already recorded on the job is skipped — this is how
        a job continues after a mid-run kill.
        """
        subject, roe, auth = self._load(job_id)
        summary = RunSummary(job_id=job_id, status=JobStatus.COLLECTING.value)
        completed = set(job_service.completed_stages(job_id)) if resume else set()

        try:
            job_service.set_status(job_id, JobStatus.COLLECTING)
            for name, factory in self._stages(job_id, subject, roe, auth, summary):
                if name in completed:
                    summary.skipped_stages.append(name)
                    log.info("stage_skipped_resume", job_id=job_id, stage=name)
                    continue
                await factory()
                job_service.mark_stage_complete(job_id, name)

            summary.status = JobStatus.AWAITING_VALIDATION.value
            job_service.set_status(job_id, JobStatus.AWAITING_VALIDATION)
            log.info(
                "pipeline_paused_for_validation",
                job_id=job_id,
                ran=summary.agents_run,
                skipped=summary.skipped_stages,
            )
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
