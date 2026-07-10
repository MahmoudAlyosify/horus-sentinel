"""Tests for the Rules-of-Engagement model."""

from datetime import datetime, timedelta

from schemas.roe import RoE, SourceCategory


def _sample_roe(**overrides) -> RoE:
    base = {
        "subject": "example.com",
        "enabled_sources": [SourceCategory.PUBLIC_RECORDS],
        "in_scope_domains": ["example.com"],
        "signed_by": "analyst_mahmoud",
        "expires_at": datetime.utcnow() + timedelta(hours=1),
    }
    base.update(overrides)
    return RoE(**base)


def test_valid_roe_is_valid_now():
    assert _sample_roe().is_valid_now() is True


def test_expired_roe_is_invalid():
    roe = _sample_roe(expires_at=datetime.utcnow() - timedelta(hours=1))
    assert roe.is_valid_now() is False


def test_allows_only_enabled_sources():
    roe = _sample_roe(enabled_sources=[SourceCategory.PUBLIC_RECORDS])
    assert roe.allows_source(SourceCategory.PUBLIC_RECORDS) is True
    assert roe.allows_source(SourceCategory.WEB_INFRA) is False
