"""Request/response DTOs for the API surface."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from schemas.roe import RoE
from schemas.subject import Subject


class JobCreateRequest(BaseModel):
    """Submit a new assessment: a subject + the RoE that authorizes it."""

    subject: Subject
    roe: RoE


class JobResponse(BaseModel):
    """A job's current state."""

    id: str
    status: str
    subject: dict[str, Any]
    roe: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    report_path: str | None = None
    validated_by: str | None = None
    error: str | None = None
    audit_count: int = 0
    finding_count: int = 0


class JobCreatedResponse(BaseModel):
    """Returned when a job is accepted (authorized)."""

    id: str
    status: str
    message: str = "Job authorized and queued."


class ErrorResponse(BaseModel):
    """A structured refusal — the authorization gate speaking."""

    detail: str
    reason: str = "authorization_denied"


class ValidationRequest(BaseModel):
    """An analyst's validation action on a drafted report (master plan Part 4.5)."""

    action: str = Field(..., description="validate | flag | edit")
    analyst: str = Field(..., description="The analyst signing off.")
    note: str | None = Field(
        default=None, description="Optional note (required in spirit for flag/edit)."
    )


class ValidationResponse(BaseModel):
    """Result of recording a validation action."""

    job_id: str
    action: str
    new_status: str
    is_final: bool


class RunResponse(BaseModel):
    """Summary of a pipeline run (collection + reasoning)."""

    job_id: str
    status: str
    entity_count: int = 0
    agents_run: list[str] = Field(default_factory=list)
    critical_cve_hits: int = 0
    errors: list[str] = Field(default_factory=list)


class DemoResponse(BaseModel):
    """Result of the one-click Guided Demo (Phase 6.6) — a full assessment, zero setup."""

    job_id: str
    subject: str
    status: str
    entity_count: int
    critical_cve_hits: int
    report_html: str | None = None
    report_url: str
