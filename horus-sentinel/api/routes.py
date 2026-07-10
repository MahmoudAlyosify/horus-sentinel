"""Job routes — submit an assessment, check its state, list recent jobs.

The POST handler is where the authorization gate becomes visible: a disallowed RoE is
refused with a 403 and a human-readable reason. That refusal is a feature, not an error.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from api.dto import (
    EnqueueResponse,
    JobCreatedResponse,
    JobCreateRequest,
    JobResponse,
    RunResponse,
    ValidationRequest,
    ValidationResponse,
)
from core.analysis_store import load_analysis
from core.config import settings
from core.jobs import job_service
from schemas.auth import AuthorizationError
from schemas.state import JobStatus
from workflows.orchestrator import orchestrator
from workflows.worker import enqueue_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "",
    response_model=JobCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    responses={403: {"description": "Refused by the authorization gate (by design)."}},
)
async def create_job(req: JobCreateRequest) -> JobCreatedResponse:
    """Authorize and enqueue an assessment. Refuses out-of-scope requests with 403."""
    try:
        job_id, _auth = job_service.create_job(req.subject, req.roe)
    except AuthorizationError as exc:
        # A designed refusal — not a server error.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return JobCreatedResponse(id=job_id, status="authorized")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    """Retrieve a job by id."""
    view = job_service.get_job(job_id)
    if view is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found."
        )
    return JobResponse(**view.__dict__)


@router.get("", response_model=list[JobResponse])
async def list_jobs(limit: int = 50) -> list[JobResponse]:
    """List recent jobs (most recent first)."""
    return [JobResponse(**v.__dict__) for v in job_service.list_jobs(limit=limit)]


@router.post("/{job_id}/run", response_model=RunResponse)
async def run_job(job_id: str) -> RunResponse:
    """Run collection + reasoning for a job. Stops at the human-validation checkpoint."""
    if job_service.get_job(job_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found."
        )
    summary = await orchestrator.run(job_id)
    return RunResponse(
        job_id=job_id,
        status=summary.status,
        entity_count=summary.entity_count,
        agents_run=summary.agents_run,
        skipped_stages=summary.skipped_stages,
        critical_cve_hits=summary.critical_cve_hits,
        errors=summary.errors,
    )


@router.post(
    "/{job_id}/enqueue", response_model=EnqueueResponse, status_code=status.HTTP_202_ACCEPTED
)
async def enqueue(job_id: str) -> EnqueueResponse:
    """Queue a job for asynchronous processing by a worker (Phase 5.2)."""
    if job_service.get_job(job_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found."
        )
    await enqueue_job(job_id)
    return EnqueueResponse(job_id=job_id, queue_backend=settings.queue_backend)


@router.get("/{job_id}/report")
async def get_report(job_id: str) -> dict[str, Any]:
    """Return the drafted Report Card + rendered graph for a job."""
    if job_service.get_job(job_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found."
        )
    loaded = load_analysis(job_id)
    if loaded is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job {job_id} has no analysis yet — run the pipeline first.",
        )
    card, graph = loaded
    return {"report_card": card.model_dump(mode="json"), "graph": graph}


@router.post("/{job_id}/validate", response_model=ValidationResponse)
async def validate_job(job_id: str, req: ValidationRequest) -> ValidationResponse:
    """Record an analyst validation action — a report is FINAL only after 'validate'."""
    if job_service.get_job(job_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found."
        )
    try:
        new_status = job_service.record_validation(job_id, req.action, req.analyst, req.note)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ValidationResponse(
        job_id=job_id,
        action=req.action,
        new_status=str(new_status),
        is_final=new_status == JobStatus.COMPLETED,
    )
