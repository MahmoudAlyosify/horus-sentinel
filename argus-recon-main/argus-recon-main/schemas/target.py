"""Target model — what a ReconTool/agent is being asked to act on."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AssetKind(str, Enum):
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    IP = "ip"
    CIDR = "cidr"
    URL = "url"


class Target(BaseModel):
    """
    A single thing an agent/tool is about to query or probe.

    `value` is the raw string (domain name, IP, CIDR, URL) that gets passed
    to `AuthContext.assert_allows()` for scope/classification checks.
    """

    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    value: str
    kind: AssetKind
    source: str | None = None  # e.g. "crt.sh", "shodan" — provenance of discovery
