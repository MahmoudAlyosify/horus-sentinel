"""Active-recon authorization tests — the safety gate is the headline control.

Proves the Authorization Engine + AuthContext refuse active reconnaissance unless it is
explicitly authorized AND aimed at an in-scope target. An out-of-scope active request never
reaches the collection plane.
"""

from datetime import datetime, timedelta

import pytest

from core.authorization import authorization_engine
from schemas.auth import AuthContext, AuthorizationError
from schemas.roe import Classification, RoE, SourceCategory
from schemas.subject import Subject, SubjectType


def _exp() -> datetime:
    return datetime.utcnow() + timedelta(hours=1)


def _roe(**kw) -> RoE:
    base = {
        "subject": "mytarget.com",
        "enabled_sources": [SourceCategory.ACTIVE_RECON, SourceCategory.WEB_CRAWL],
        "in_scope_domains": ["mytarget.com"],
        "active_authorized": True,
        "signed_by": "operator",
        "expires_at": _exp(),
    }
    base.update(kw)
    return RoE(**base)


_DOMAIN = Subject(type=SubjectType.DOMAIN, value="mytarget.com")


def test_active_allowed_when_authorized_and_in_scope():
    ctx = authorization_engine.authorize("j1", _DOMAIN, _roe())
    assert ctx.roe.has_active_sources()
    # Tool-level gate also passes for the in-scope target.
    ctx.assert_allows(Classification.ACTIVE, SourceCategory.ACTIVE_RECON, _DOMAIN)


def test_active_refused_out_of_scope():
    roe = _roe(in_scope_domains=["someone-else.com"])
    with pytest.raises(AuthorizationError):
        authorization_engine.authorize("j2", _DOMAIN, roe)


def test_active_refused_without_authorization_flag():
    roe = _roe(active_authorized=False)
    with pytest.raises(AuthorizationError):
        authorization_engine.authorize("j3", _DOMAIN, roe)


def test_active_refused_on_region_subject():
    region = Subject(type=SubjectType.REGION, value="Sinai", year_from=2018, year_to=2019)
    roe = _roe(subject="Sinai", in_scope_domains=["Sinai"])
    with pytest.raises(AuthorizationError):
        authorization_engine.authorize("j4", region, roe)


def test_tool_gate_refuses_out_of_scope_active_target():
    """Even with a valid active RoE, a tool call against a different host raises."""
    ctx = AuthContext(job_id="j5", roe=_roe())
    evil = Subject(type=SubjectType.DOMAIN, value="not-authorized.com")
    with pytest.raises(AuthorizationError):
        ctx.assert_allows(Classification.ACTIVE, SourceCategory.ACTIVE_RECON, evil)


def test_subdomain_of_in_scope_is_allowed():
    ctx = AuthContext(job_id="j6", roe=_roe())
    sub = Subject(type=SubjectType.DOMAIN, value="api.mytarget.com")
    # a subdomain of an in-scope domain is in scope
    ctx.assert_allows(Classification.ACTIVE, SourceCategory.ACTIVE_RECON, sub)


def test_passive_still_works_unchanged():
    """Passive sources are unaffected by the active gate."""
    roe = RoE(
        subject="example.com",
        enabled_sources=[SourceCategory.PUBLIC_RECORDS],
        in_scope_domains=[],
        signed_by="a",
        expires_at=_exp(),
    )
    ctx = authorization_engine.authorize(
        "j7", Subject(type=SubjectType.DOMAIN, value="example.com"), roe
    )
    ctx.assert_allows(
        Classification.PASSIVE,
        SourceCategory.PUBLIC_RECORDS,
        Subject(type=SubjectType.DOMAIN, value="example.com"),
    )
