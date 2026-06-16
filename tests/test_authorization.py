from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from core.authorization import (
    ActiveScanningNotAuthorizedError,
    AuthorizationEngine,
    OutOfScopeError,
    RoEExpiredError,
    RoEInvalidSignatureError,
    ToolNotAllowedError,
    sign_roe,
    verify_signature,
)
from schemas.roe import RoERecord, ScopeAsset, ScopeAssetType

SIGNING_KEY = "test-signing-key"


def make_roe(**overrides) -> RoERecord:
    now = datetime.now(UTC)
    defaults = dict(
        client_name="Example Corp",
        authorized_by="CISO",
        contact_email="security@example.com",
        in_scope_assets=[
            ScopeAsset(type=ScopeAssetType.DOMAIN, value="example.com"),
            ScopeAsset(type=ScopeAssetType.CIDR, value="203.0.113.0/24"),
        ],
        excluded_assets=[],
        active_scanning_authorized=False,
        allowed_active_tools=[],
        valid_from=now - timedelta(hours=1),
        valid_until=now + timedelta(days=1),
    )
    defaults.update(overrides)
    roe = RoERecord(**defaults)
    return sign_roe(roe, SIGNING_KEY)


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------


def test_signed_roe_verifies():
    roe = make_roe()
    assert verify_signature(roe, SIGNING_KEY) is True


def test_tampered_roe_fails_verification():
    roe = make_roe()
    tampered = roe.model_copy(update={"client_name": "Attacker-Controlled Corp"})
    assert verify_signature(tampered, SIGNING_KEY) is False


def test_wrong_key_fails_verification():
    roe = make_roe()
    assert verify_signature(roe, "wrong-key") is False


def test_create_context_rejects_invalid_signature():
    roe = make_roe()
    tampered = roe.model_copy(update={"active_scanning_authorized": True})
    with pytest.raises(RoEInvalidSignatureError):
        AuthorizationEngine.create_context(tampered, SIGNING_KEY)


def test_create_context_rejects_expired_roe():
    now = datetime.now(UTC)
    roe = make_roe(
        valid_from=now - timedelta(days=10),
        valid_until=now - timedelta(days=1),
    )
    with pytest.raises(RoEExpiredError):
        AuthorizationEngine.create_context(roe, SIGNING_KEY)


def test_create_context_succeeds_for_valid_roe():
    roe = make_roe()
    ctx = AuthorizationEngine.create_context(roe, SIGNING_KEY)
    assert ctx.roe.roe_id == roe.roe_id


# ---------------------------------------------------------------------------
# Scope matching
# ---------------------------------------------------------------------------


def test_passive_in_scope_domain_allowed():
    ctx = AuthorizationEngine.create_context(make_roe(), SIGNING_KEY)
    ctx.assert_allows("passive", "example.com")  # apex
    ctx.assert_allows("passive", "vpn.example.com")  # subdomain


def test_unrelated_domain_is_out_of_scope():
    ctx = AuthorizationEngine.create_context(make_roe(), SIGNING_KEY)
    with pytest.raises(OutOfScopeError):
        ctx.assert_allows("passive", "not-example.com")

    with pytest.raises(OutOfScopeError):
        ctx.assert_allows("passive", "evilexample.com")  # not a real subdomain


def test_in_scope_cidr_allows_ip():
    ctx = AuthorizationEngine.create_context(make_roe(), SIGNING_KEY)
    ctx.assert_allows("passive", "203.0.113.10")


def test_out_of_range_ip_is_out_of_scope():
    ctx = AuthorizationEngine.create_context(make_roe(), SIGNING_KEY)
    with pytest.raises(OutOfScopeError):
        ctx.assert_allows("passive", "198.51.100.1")


def test_excluded_subdomain_is_blocked_even_if_apex_in_scope():
    roe = make_roe(
        excluded_assets=[
            ScopeAsset(type=ScopeAssetType.DOMAIN, value="cdn.example.com", note="3rd-party CDN"),
        ]
    )
    ctx = AuthorizationEngine.create_context(roe, SIGNING_KEY)
    ctx.assert_allows("passive", "example.com")  # still fine
    with pytest.raises(OutOfScopeError):
        ctx.assert_allows("passive", "cdn.example.com")
    with pytest.raises(OutOfScopeError):
        ctx.assert_allows("passive", "assets.cdn.example.com")  # under the exclusion


# ---------------------------------------------------------------------------
# Passive vs active gate
# ---------------------------------------------------------------------------


def test_active_blocked_when_not_authorized():
    roe = make_roe(active_scanning_authorized=False)
    ctx = AuthorizationEngine.create_context(roe, SIGNING_KEY)

    # passive is fine
    ctx.assert_allows("passive", "example.com")

    with pytest.raises(ActiveScanningNotAuthorizedError):
        ctx.assert_allows("active", "example.com", tool_name="nmap")


def test_active_allowed_when_authorized_with_no_tool_restriction():
    roe = make_roe(active_scanning_authorized=True, allowed_active_tools=[])
    ctx = AuthorizationEngine.create_context(roe, SIGNING_KEY)
    ctx.assert_allows("active", "example.com", tool_name="nmap")
    ctx.assert_allows("active", "203.0.113.10", tool_name="custom-active-tool")


def test_active_tool_allow_list_is_enforced():
    roe = make_roe(active_scanning_authorized=True, allowed_active_tools=["nmap"])
    ctx = AuthorizationEngine.create_context(roe, SIGNING_KEY)

    ctx.assert_allows("active", "example.com", tool_name="nmap")  # allowed

    with pytest.raises(ToolNotAllowedError):
        ctx.assert_allows("active", "example.com", tool_name="some-other-active-tool")


def test_active_scan_still_respects_scope():
    roe = make_roe(active_scanning_authorized=True)
    ctx = AuthorizationEngine.create_context(roe, SIGNING_KEY)
    with pytest.raises(OutOfScopeError):
        ctx.assert_allows("active", "not-example.com", tool_name="nmap")
