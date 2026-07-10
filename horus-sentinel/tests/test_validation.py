"""Human-validation checkpoint tests (master plan Part 4.5)."""

from datetime import datetime, timedelta

import pytest

from core.db import init_db
from core.jobs import job_service
from schemas.roe import RoE, SourceCategory
from schemas.state import JobStatus
from schemas.subject import Subject, SubjectType


@pytest.fixture(autouse=True)
def _db():
    init_db()


def _make_job() -> str:
    subject = Subject(type=SubjectType.DOMAIN, value="example.com")
    roe = RoE(
        subject="example.com",
        enabled_sources=[SourceCategory.PUBLIC_RECORDS],
        in_scope_domains=["example.com"],
        signed_by="analyst_test",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    job_id, _ = job_service.create_job(subject, roe)
    return job_id


def test_validate_marks_report_final():
    job_id = _make_job()
    status = job_service.record_validation(job_id, "validate", "analyst_mirna", "looks good")
    assert status == JobStatus.COMPLETED
    view = job_service.get_job(job_id)
    assert view.validated_by == "analyst_mirna"


def test_flag_rejects_report():
    job_id = _make_job()
    status = job_service.record_validation(job_id, "flag", "analyst_sondos", "false positive")
    assert status == JobStatus.REJECTED
    assert job_service.get_job(job_id).validated_by is None


def test_edit_keeps_report_non_final():
    job_id = _make_job()
    status = job_service.record_validation(job_id, "edit", "analyst_mahmoud", "tweak wording")
    assert status == JobStatus.AWAITING_VALIDATION
    # Report is not final until a validate action is recorded.
    assert job_service.get_job(job_id).validated_by is None


def test_unknown_action_rejected():
    job_id = _make_job()
    with pytest.raises(ValueError, match="Unknown validation action"):
        job_service.record_validation(job_id, "approve", "x")
