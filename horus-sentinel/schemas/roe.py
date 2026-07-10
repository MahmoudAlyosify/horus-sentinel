"""Rules-of-Engagement (RoE) model — the authorization record every job runs under.

This is the heart of the Control Plane. No job runs without a valid RoE.
See master plan Part 2.2 (design invariants) and Phase 1.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SourceCategory(StrEnum):
    """Categories of OSINT sources an RoE can enable. All are passive."""

    PUBLIC_RECORDS = "public_records"  # WHOIS, DNS, cert transparency
    GEO_EVENTS = "geo_events"  # GTD/GDELT-derived event context
    WEB_INFRA = "web_infra"  # passive fingerprinting, Shodan/Censys
    THREAT_INTEL = "threat_intel"  # reputation feeds, CVE correlation


class Classification(StrEnum):
    """Operation classification. Path C is passive-only by design."""

    PASSIVE = "passive"


class RoE(BaseModel):
    """A signed Rules-of-Engagement record authorizing a Sentinel job."""

    subject: str = Field(
        ..., description="The authorized subject of inquiry (domain, region, entity)."
    )
    enabled_sources: list[SourceCategory] = Field(
        default_factory=list,
        description="Which passive source categories are permitted for this job.",
    )
    in_scope_domains: list[str] = Field(
        default_factory=list,
        description="Owned/authorized domains for any web-facing collection.",
    )
    signed_by: str = Field(..., description="Analyst who authorized this assessment.")
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="RoE is invalid after this time.")

    def is_valid_now(self) -> bool:
        """True if the RoE has not expired."""
        return datetime.utcnow() < self.expires_at

    def allows_source(self, category: SourceCategory) -> bool:
        """True if this RoE permits the given source category."""
        return category in self.enabled_sources
