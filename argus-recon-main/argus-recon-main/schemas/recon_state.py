"""
ReconState — the shared state object that will flow through the LangGraph
orchestration graph (section 2.3, wired up in week 5).

Defined now because the authorization gate, job records, and API responses
all need to agree on its shape from week 1 onward. Per the architecture
principle in section 4.3, this stays SMALL: agents write findings to the
Knowledge Base and only leave *references* here, never large blobs.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.authorization import AuthContext


class JobStatus(str, Enum):
    PENDING = "pending"          # submitted, not yet authorized
    REJECTED = "rejected"         # failed authorization (bad sig/expired/out of scope)
    AUTHORIZED = "authorized"      # passed the gate, queued for the orchestrator
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReconState(BaseModel):
    """
    LangGraph state. `auth_context` is what every agent node calls
    `.assert_allows(...)` on before invoking a ReconTool.
    """

    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    apex_domain: str
    status: JobStatus = JobStatus.PENDING

    auth_context: AuthContext

    # Lightweight, append-only references — NOT the findings themselves.
    # The Knowledge Base (Postgres/Neo4j/Chroma/object store) is the source
    # of truth; agents read full records from there using these refs.
    discovered_domains: list[str] = Field(default_factory=list)
    discovered_subdomains: list[str] = Field(default_factory=list)
    discovered_ips: list[str] = Field(default_factory=list)
    kb_refs: dict[str, Any] = Field(default_factory=dict)

    errors: list[str] = Field(default_factory=list)

    @property
    def active_scanning_authorized(self) -> bool:
        """Convenience accessor used by conditional edges (section 2.3)."""
        return self.auth_context.roe.active_scanning_authorized
