"""Job service — create, authorize, and retrieve assessment jobs (Phase 1.4).

Thin layer over the relational store. Creating a job runs it through the Authorization
Engine first: a disallowed RoE never becomes a runnable job — it is rejected and recorded
as such. This is the "watch it refuse a disallowed source — that's by design" demo.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, select

from core.authorization import authorization_engine
from core.db import AuditRecord, FindingRecord, JobRecord, ValidationRecord, session_scope
from schemas.auth import AuthContext, AuthorizationError
from schemas.roe import RoE
from schemas.state import JobStatus
from schemas.subject import Subject

# Analyst validation actions (master plan Part 4.5).
VALIDATE = "validate"
FLAG = "flag"
EDIT = "edit"


@dataclass
class JobView:
    """A read model of a job for API responses."""

    id: str
    status: str
    subject: dict[str, Any]
    roe: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    report_path: str | None
    validated_by: str | None
    error: str | None
    audit_count: int
    finding_count: int


class JobService:
    """Create/authorize/retrieve jobs. All persistence goes through here."""

    def create_job(self, subject: Subject, roe: RoE) -> tuple[str, AuthContext]:
        """Authorize and persist a new job.

        Raises ``AuthorizationError`` if the RoE does not permit the subject — the caller
        (API) turns that into a 403 with the refusal reason.
        """
        job_id = uuid.uuid4().hex
        # Hard gate first — an unauthorized job is never persisted as runnable.
        auth = authorization_engine.authorize(job_id, subject, roe)

        with session_scope() as session:
            session.add(
                JobRecord(
                    id=job_id,
                    status=JobStatus.AUTHORIZED.value,
                    subject_json=subject.model_dump_json(),
                    roe_json=roe.model_dump_json(),
                )
            )
        return job_id, auth

    def set_status(self, job_id: str, status: JobStatus, error: str | None = None) -> None:
        with session_scope() as session:
            job = session.get(JobRecord, job_id)
            if job is None:
                raise KeyError(job_id)
            job.status = status.value
            if error is not None:
                job.error = error

    def record_validation(
        self, job_id: str, action: str, analyst: str, note: str | None = None
    ) -> JobStatus:
        """Record an analyst action. A report is FINAL (COMPLETED) only after 'validate'.

        This is the human-in-the-loop control (master plan Part 4.5): the model drafts, the
        analyst is authoritative. Returns the job's new status.
        """
        if action not in (VALIDATE, FLAG, EDIT):
            raise ValueError(f"Unknown validation action '{action}'.")
        with session_scope() as session:
            job = session.get(JobRecord, job_id)
            if job is None:
                raise KeyError(job_id)
            session.add(ValidationRecord(job_id=job_id, action=action, analyst=analyst, note=note))
            if action == VALIDATE:
                job.validated_by = analyst
                job.status = JobStatus.COMPLETED.value
            elif action == FLAG:
                job.status = JobStatus.REJECTED.value
            else:  # edit — still needs a validate before it can be final
                job.status = JobStatus.AWAITING_VALIDATION.value
            return JobStatus(job.status)

    def get_job(self, job_id: str) -> JobView | None:
        with session_scope() as session:
            job = session.get(JobRecord, job_id)
            if job is None:
                return None
            audit_count = session.scalar(
                select(func.count()).select_from(AuditRecord).where(AuditRecord.job_id == job_id)
            )
            finding_count = session.scalar(
                select(func.count())
                .select_from(FindingRecord)
                .where(FindingRecord.job_id == job_id)
            )
            return JobView(
                id=job.id,
                status=job.status,
                subject=job.subject(),
                roe=job.roe(),
                created_at=job.created_at,
                updated_at=job.updated_at,
                report_path=job.report_path,
                validated_by=job.validated_by,
                error=job.error,
                audit_count=int(audit_count or 0),
                finding_count=int(finding_count or 0),
            )

    def list_jobs(self, limit: int = 50) -> list[JobView]:
        with session_scope() as session:
            rows = session.scalars(
                select(JobRecord).order_by(JobRecord.created_at.desc()).limit(limit)
            ).all()
            return [self._view_from(session, j) for j in rows]

    @staticmethod
    def _view_from(session: Any, job: JobRecord) -> JobView:
        audit_count = session.scalar(
            select(func.count()).select_from(AuditRecord).where(AuditRecord.job_id == job.id)
        )
        finding_count = session.scalar(
            select(func.count()).select_from(FindingRecord).where(FindingRecord.job_id == job.id)
        )
        return JobView(
            id=job.id,
            status=job.status,
            subject=job.subject(),
            roe=job.roe(),
            created_at=job.created_at,
            updated_at=job.updated_at,
            report_path=job.report_path,
            validated_by=job.validated_by,
            error=job.error,
            audit_count=int(audit_count or 0),
            finding_count=int(finding_count or 0),
        )


job_service = JobService()

__all__ = ["JobService", "JobView", "job_service", "AuthorizationError"]
