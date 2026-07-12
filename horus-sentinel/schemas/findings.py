"""Normalized findings and tool results.

Core invariant (master plan Part 2.1): agents never pass big blobs to each other.
Every external touch produces an ``Evidence`` record (chain of custody), and every
observation an agent makes is a normalized ``Finding``. The graph and the report are
built from these, so every claim is traceable to a source + timestamp.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from schemas.roe import SourceCategory


def _new_id() -> str:
    return uuid.uuid4().hex


def _utcnow() -> datetime:
    return datetime.utcnow()


class EntityKind(StrEnum):
    """Graph node kinds a finding can assert (mirrors master plan Part 5.1)."""

    ORGANIZATION = "Organization"
    DOMAIN = "Domain"
    SUBDOMAIN = "Subdomain"
    IP = "IP"
    PORT = "Port"  # an open port discovered by active scanning
    SERVICE = "Service"
    TECHNOLOGY = "Technology"
    ENDPOINT = "Endpoint"  # a discovered URL / path (active web crawl)
    CERTIFICATE = "Certificate"
    EMAIL = "Email"
    PERSON = "Person"
    CVE = "CVE"
    CLOUD_ASSET = "CloudAsset"
    REGION = "Region"
    THREAT_ACTOR = "ThreatActor"
    EVENT = "Event"
    INDICATOR = "Indicator"


class Evidence(BaseModel):
    """An immutable chain-of-custody record for one external observation."""

    id: str = Field(default_factory=_new_id)
    source: str = Field(
        ..., description="Tool/source name that produced this (e.g. 'crtsh', 'whois')."
    )
    source_category: SourceCategory
    collected_at: datetime = Field(default_factory=_utcnow)
    summary: str = Field(
        ..., description="Human-readable one-line description of what was observed."
    )
    raw_ref: str | None = Field(
        default=None, description="Reference/hash of the raw payload in the object store."
    )

    @staticmethod
    def digest(payload: Any) -> str:
        """Deterministic digest of a raw payload, for the object-store reference."""
        blob = json.dumps(payload, sort_keys=True, default=str).encode()
        return hashlib.sha256(blob).hexdigest()


class Finding(BaseModel):
    """A single normalized observation asserting an entity (and optionally a relationship)."""

    id: str = Field(default_factory=_new_id)
    entity_kind: EntityKind
    entity_value: str = Field(
        ..., description="The asserted entity's primary value (domain, ip, cve id, ...)."
    )
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Structured attributes of the entity."
    )
    # Optional relationship to a parent entity (builds the graph edge).
    related_to: str | None = Field(default=None, description="entity_value of a related node.")
    relationship: str | None = Field(
        default=None, description="Edge label, e.g. 'HAS_SUBDOMAIN', 'RESOLVES_TO'."
    )
    evidence: list[Evidence] = Field(
        default_factory=list, description="Chain-of-custody backing this finding."
    )
    produced_by: str = Field(..., description="Agent that produced this finding.")
    produced_at: datetime = Field(default_factory=_utcnow)

    def node_key(self) -> str:
        """Stable graph-node identity: kind + normalized value."""
        return f"{self.entity_kind.value}:{self.entity_value.lower()}"


class ToolResult(BaseModel):
    """What every IntelTool returns: normalized findings + the evidence trail."""

    tool: str
    source_category: SourceCategory
    findings: list[Finding] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    cached: bool = Field(
        default=False, description="True if served from cache (politeness + cost story)."
    )
    error: str | None = Field(default=None, description="Populated if the tool failed gracefully.")

    def summary(self) -> str:
        return f"{self.tool}: {len(self.findings)} findings, {len(self.evidence)} evidence records"
