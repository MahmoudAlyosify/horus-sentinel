"""Job routes — submit an assessment, check its state, list recent jobs.

The POST handler is where the authorization gate becomes visible: a disallowed RoE is
refused with a 403 and a human-readable reason. That refusal is a feature, not an error.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from api.dto import JobCreatedResponse, JobCreateRequest, JobResponse
from core.jobs import job_service
from schemas.auth import AuthorizationError

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
