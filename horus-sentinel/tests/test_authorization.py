"""Tests for the Scope & Authorization Engine — the hard gate.

The headline behavior a military judge wants to see: a disallowed source or an
out-of-scope subject **raises**. These tests prove it.
"""

from datetime import datetime, timedelta

import pytest

from core.authorization import authorization_engine
from schemas.auth import AuthorizationError
from schemas.roe import RoE, SourceCategory
from schemas.subject import Subject, SubjectType


def _roe(**overrides) -> RoE:
    base = {
        "subject": "example.com",
        "enabled_sources": [SourceCategory.PUBLIC_RECORDS],
        "in_scope_domains": ["example.com"],
        "signed_by": "analyst_mahmoud",
        "expires_at": datetime.utcnow() + timedelta(hours=1),
    }
    base.update(overrides)
    return RoE(**base)


def _domain_subject(value: str = "example.com") -> Subject:
    return Subject(type=SubjectType.DOMAIN, value=value)


def test_authorized_job_returns_context():
    auth = authorization_engine.authorize("job1", _domain_subject(), _roe())
    assert auth.job_id == "job1"
    assert auth.roe.signed_by == "analyst_mahmoud"


def test_expired_roe_is_rejected():
    roe = _roe(expires_at=datetime.utcnow() - timedelta(minutes=1))
    with pytest.raises(AuthorizationError, match="expired"):
        authorization_engine.authorize("job2", _domain_subject(), roe)


def test_no_enabled_sources_is_rejected():
    roe = _roe(enabled_sources=[])
    with pytest.raises(AuthorizationError, match="no sources"):
        authorization_engine.authorize("job3", _domain_subject(), roe)


def test_subject_mismatch_is_rejected():
    roe = _roe(subject="other.com")
    with pytest.raises(AuthorizationError, match="authorizes subject"):
        authorization_engine.authorize("job4", _domain_subject("example.com"), roe)


def test_web_infra_out_of_scope_domain_is_rejected():
    roe = _roe(
        subject="attacker.com",
        enabled_sources=[SourceCategory.WEB_INFRA],
        in_scope_domains=["example.com"],
    )
    with pytest.raises(AuthorizationError, match="in_scope_domains"):
        authorization_engine.authorize("job5", _domain_subject("attacker.com"), roe)


def test_assert_allows_blocks_disabled_source():
    """A tool asking for a source the RoE didn't enable is refused at call time."""
    auth = authorization_engine.authorize("job6", _domain_subject(), _roe())
    with pytest.raises(AuthorizationError, match="not enabled"):
        from schemas.roe import Classification

        auth.assert_allows(Classification.PASSIVE, SourceCategory.WEB_INFRA, _domain_subject())
