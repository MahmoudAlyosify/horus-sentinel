"""
Job submission endpoints.

`POST /jobs` is the front door referenced throughout the architecture doc:
"target + RoE submission" → Scope & Authorization Engine (HARD GATE) →
authorized job. Week 1 stops at "authorized and persisted" — the
Orchestrator (LangGraph) that actually runs agents is wired in week 5.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.authorization import AuthorizationEngine, AuthorizationError
from core.config import settings
from db.models import JobORM, RoERecordORM
from db.session import get_session
from schemas.recon_state import JobStatus
from schemas.roe import RoERecord

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
