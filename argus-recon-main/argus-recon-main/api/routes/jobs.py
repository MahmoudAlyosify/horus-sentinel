"""
Job submission endpoints.

`POST /jobs` is the front door referenced throughout the architecture doc:
"target + RoE submission" → Scope & Authorization Engine (HARD GATE) →
authorized job. Week 1 stops at "authorized and persisted" — the
Orchestrator (LangGraph) that actually runs agents is wired in week 5.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.network_agent import NetworkAgent
from agents.osint_agent import OsintAgent
from agents.threat_intel_agent import ThreatIntelAgent
from agents.web_agent import WebAgent
from core.authorization import AuthorizationEngine, AuthorizationError, AuthContext
from core.config import settings
from db.models import JobORM, RoERecordORM
from db.session import get_session
from schemas.recon_state import JobStatus, ReconState
from schemas.roe import RoERecord
from workflows.recon_graph import recon_graph

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    apex_domain: str
    roe: RoERecord


class JobResponse(BaseModel):
    job_id: UUID
    apex_domain: str
    status: JobStatus
    active_scanning_authorized: bool
    roe_id: UUID
    created_at: datetime | None = None
    message: str | None = None


class JobRunResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    result: dict[str, Any] | None = None
    message: str | None = None


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def submit_job(
    payload: JobSubmission,
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    """
    Validate the submitted RoE, run the apex domain through the scope gate,
    and persist a new job. Does NOT start collection — that's the
    orchestrator's job (week 5).

    422 — RoE signature invalid or RoE outside its validity window.
    403 — RoE is otherwise valid, but `apex_domain` is not in scope.
    """
    roe = payload.roe

    try:
        ctx = AuthorizationEngine.create_context(roe, settings.roe_signing_key)
    except AuthorizationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        # Apex domain is always checked as "passive" here — this just confirms
        # the target is *in scope at all*. Each agent re-checks with its own
        # classification before it actually does anything.
        ctx.assert_allows("passive", payload.apex_domain)
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    # Persist RoE if we haven't seen this roe_id before (idempotent re-submission).
    existing_roe = await session.get(RoERecordORM, roe.roe_id)
    if existing_roe is None:
        session.add(
            RoERecordORM(
                roe_id=roe.roe_id,
                client_name=roe.client_name,
                authorized_by=roe.authorized_by,
                contact_email=roe.contact_email,
                active_scanning_authorized=roe.active_scanning_authorized,
                valid_from=roe.valid_from,
                valid_until=roe.valid_until,
                signature=roe.signature,
                data=roe.model_dump(mode="json"),
            )
        )

    job_id = uuid4()
    job = JobORM(
        job_id=job_id,
        apex_domain=payload.apex_domain,
        roe_id=roe.roe_id,
        status=JobStatus.AUTHORIZED.value,
    )
    session.add(job)
    await session.commit()

    return JobResponse(
        job_id=job_id,
        apex_domain=payload.apex_domain,
        status=JobStatus.AUTHORIZED,
        active_scanning_authorized=roe.active_scanning_authorized,
        roe_id=roe.roe_id,
        created_at=job.created_at,
        message="Job authorized and queued. Orchestration is not yet wired (week 5).",
    )


@router.post("/{job_id}/run-osint", response_model=JobRunResponse)
async def run_osint(job_id: UUID, session: AsyncSession = Depends(get_session)) -> JobRunResponse:
    job = await session.get(JobORM, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job.status = JobStatus.RUNNING.value
    await session.commit()

    agent = OsintAgent()
    result = await agent.run(job.apex_domain)

    job.status = JobStatus.COMPLETED.value
    await session.commit()

    return JobRunResponse(
        job_id=job.job_id,
        status=JobStatus.COMPLETED,
        result=result.model_dump(mode="json"),
        message="Passive OSINT collection completed.",
    )


@router.post("/{job_id}/run-recon", response_model=JobRunResponse)
async def run_recon(job_id: UUID, session: AsyncSession = Depends(get_session)) -> JobRunResponse:
    job = await session.get(JobORM, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    roe = await session.get(RoERecordORM, job.roe_id)
    if roe is None:
        raise HTTPException(status_code=404, detail=f"RoE {job.roe_id} not found")

    job.status = JobStatus.RUNNING.value
    await session.commit()

    osint_agent = OsintAgent()
    osint_result = await osint_agent.run(job.apex_domain)

    results: dict[str, Any] = {"osint": osint_result.model_dump(mode="json")}

    if roe.active_scanning_authorized:
        network_agent = NetworkAgent()
        network_result = await network_agent.run(osint_result.ip_addresses)
        results["network"] = network_result.model_dump(mode="json")

    web_agent = WebAgent()
    web_result = await web_agent.run([job.apex_domain, *osint_result.subdomains[:5]])
    results["web"] = web_result.model_dump(mode="json")

    threat_agent = ThreatIntelAgent()
    threat_result = await threat_agent.run(
        [
            {"kind": "service", "value": "https"},
            {"kind": "domain", "value": job.apex_domain},
        ]
    )
    results["threat_intel"] = threat_result.model_dump(mode="json")

    job.status = JobStatus.COMPLETED.value
    await session.commit()

    return JobRunResponse(
        job_id=job.job_id,
        status=JobStatus.COMPLETED,
        result=results,
        message="Recon workflow completed with passive agents.",
    )


@router.post("/{job_id}/run-workflow", response_model=JobRunResponse)
async def run_workflow(job_id: UUID, session: AsyncSession = Depends(get_session)) -> JobRunResponse:
    """Run the complete LangGraph orchestration workflow."""
    job = await session.get(JobORM, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    roe_orm = await session.get(RoERecordORM, job.roe_id)
    if roe_orm is None:
        raise HTTPException(status_code=404, detail=f"RoE {job.roe_id} not found")

    job.status = JobStatus.RUNNING.value
    await session.commit()

    try:
        roe_record = RoERecord(**roe_orm.data)
        auth_ctx = AuthContext(job_id=job_id, roe=roe_record)

        initial_state = ReconState(
            job_id=job_id,
            apex_domain=job.apex_domain,
            status=JobStatus.RUNNING,
            auth_context=auth_ctx,
        )

        final_state_dict = await recon_graph.ainvoke(initial_state)
        
        # LangGraph returns a dict-like object, convert to ReconState
        final_state = ReconState(**final_state_dict)

        job.status = JobStatus.COMPLETED.value
        await session.commit()

        return JobRunResponse(
            job_id=job.job_id,
            status=JobStatus.COMPLETED,
            result={
                "kb_refs": final_state.kb_refs,
                "discovered_domains": final_state.discovered_domains,
                "discovered_subdomains": final_state.discovered_subdomains,
                "discovered_ips": final_state.discovered_ips,
            },
            message="Complete LangGraph workflow executed successfully.",
        )

    except Exception as exc:
        job.status = JobStatus.FAILED.value
        await session.commit()
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(exc)}") from exc


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    job = await session.get(JobORM, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    roe = await session.get(RoERecordORM, job.roe_id)

    return JobResponse(
        job_id=job.job_id,
        apex_domain=job.apex_domain,
        status=JobStatus(job.status),
        active_scanning_authorized=roe.active_scanning_authorized if roe else False,
        roe_id=job.roe_id,
        created_at=job.created_at,
    )


@router.get("", response_model=list[JobResponse])
async def list_jobs(session: AsyncSession = Depends(get_session)) -> list[JobResponse]:
    result = await session.execute(select(JobORM).order_by(JobORM.created_at.desc()))
    jobs = result.scalars().all()

    out: list[JobResponse] = []
    for job in jobs:
        roe = await session.get(RoERecordORM, job.roe_id)
        out.append(
            JobResponse(
                job_id=job.job_id,
                apex_domain=job.apex_domain,
                status=JobStatus(job.status),
                active_scanning_authorized=roe.active_scanning_authorized if roe else False,
                roe_id=job.roe_id,
                created_at=job.created_at,
            )
        )
    return out
