"""Rules-of-Engagement (RoE) model — the authorization record every job runs under.

This is the heart of the Control Plane. No job runs without a valid RoE.
See master plan Part 2.2 (design invariants) and Phase 1.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


def now_utc() -> datetime:
    return datetime.now(UTC)


class SourceCategory(StrEnum):
    """Categories of sources an RoE can enable.

    The first four are **passive** (already-public data; nothing touches the target). The
    ``ACTIVE_*`` categories are **active reconnaissance** — they send traffic to the target,
    so they are permitted only against explicitly authorized, in-scope assets you own or are
    cleared to test. The Authorization Engine enforces this (out-of-scope → refused).
    """

    PUBLIC_RECORDS = "public_records"  # WHOIS, DNS, cert transparency (passive)
    GEO_EVENTS = "geo_events"  # GTD/GDELT-derived event context (passive)
    WEB_INFRA = "web_infra"  # passive fingerprinting, Shodan/Censys (passive)
    THREAT_INTEL = "threat_intel"  # reputation feeds, CVE correlation (passive)
    # --- active reconnaissance (authorized, in-scope targets only) ---
    ACTIVE_RECON = "active_recon"  # port scan + service/banner fingerprint + active DNS enum
    WEB_CRAWL = "web_crawl"  # authenticated crawler/scraper (content discovery)


# Active categories touch the target directly — they require explicit authorization.
ACTIVE_SOURCE_CATEGORIES = frozenset({SourceCategory.ACTIVE_RECON, SourceCategory.WEB_CRAWL})


class Classification(StrEnum):
    """Operation classification.

    ``PASSIVE`` consumes only already-public data. ``ACTIVE`` sends traffic to the target and
    is gated hard by the Authorization Engine to explicitly authorized, in-scope assets.
    """

    PASSIVE = "passive"
    ACTIVE = "active"


class RoE(BaseModel):
    """A signed Rules-of-Engagement record authorizing a Sentinel job."""

    subject: str = Field(
        ..., description="The authorized subject of inquiry (domain, region, entity)."
    )
    enabled_sources: list[SourceCategory] = Field(
        default_factory=list,
        description="Which source categories are permitted for this job.",
    )
    in_scope_domains: list[str] = Field(
        default_factory=list,
        description="Owned/authorized domains for web-facing collection AND every active-recon target.",
    )
    active_authorized: bool = Field(
        default=False,
        description=(
            "Explicit second authorization that ACTIVE reconnaissance (traffic to the target) "
            "is permitted. Active sources are refused unless this is True AND the target is in "
            "in_scope_domains — active ops never run outside authorized scope."
        ),
    )
    signed_by: str = Field(..., description="Analyst who authorized this assessment.")
    issued_at: datetime = Field(default_factory=now_utc)
    expires_at: datetime = Field(..., description="RoE is invalid after this time.")

    def is_valid_now(self) -> bool:
        """True if the RoE has not expired."""
        now = now_utc()
        if self.expires_at.tzinfo is None:
            now = now.replace(tzinfo=None)
        return now < self.expires_at

    def allows_source(self, category: SourceCategory) -> bool:
        """True if this RoE permits the given source category."""
        return category in self.enabled_sources

    def has_active_sources(self) -> bool:
        """True if any enabled source is active reconnaissance (traffic to the target)."""
        return any(s in ACTIVE_SOURCE_CATEGORIES for s in self.enabled_sources)
