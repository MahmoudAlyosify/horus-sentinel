"""AuthContext — the per-job scope guard threaded through every tool call.

Design invariant (master plan Part 2.2 #2, #3): no external call bypasses the Tool
Abstraction Layer, and no job runs without an authorization record. The ``AuthContext``
is the lightweight object every ``IntelTool`` consults via ``ctx.assert_allows(...)``
*before* it touches any source. If a call is out of scope it **raises** — refusal is a
designed control, not an afterthought.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.roe import Classification, RoE, SourceCategory
from schemas.subject import Subject, SubjectType


class AuthorizationError(Exception):
    """Raised when a tool call is not permitted by the job's RoE. This is by design."""


class AuthContext(BaseModel):
    """Immutable authorization context bound to a single job's RoE."""

    job_id: str = Field(..., description="The job this context authorizes.")
    roe: RoE = Field(..., description="The signed Rules-of-Engagement for this job.")

    def assert_allows(
        self,
        classification: Classification,
        source_category: SourceCategory,
        subject: Subject,
    ) -> None:
        """Hard gate. Raises ``AuthorizationError`` if the call is not permitted.

        Enforces, in order: RoE validity, passive-only classification, source enablement,
        and subject scope (owned-domain checks for web-facing collection).
        """
        if not self.roe.is_valid_now():
            raise AuthorizationError(
                f"RoE expired at {self.roe.expires_at.isoformat()}; job {self.job_id} cannot collect."
            )

        # Path C is passive-only. Anything else is a hard stop.
        if classification != Classification.PASSIVE:
            raise AuthorizationError(
                f"Classification '{classification}' is not permitted — HORUS Sentinel is passive-only."
            )

        if not self.roe.allows_source(source_category):
            raise AuthorizationError(
                f"Source category '{source_category.value}' is not enabled in the RoE for job {self.job_id}."
            )

        self._assert_subject_in_scope(source_category, subject)

    def _assert_subject_in_scope(self, source_category: SourceCategory, subject: Subject) -> None:
        """Web-facing collection is confined to owned/authorized domains."""
        if source_category != SourceCategory.WEB_INFRA:
            return
        if subject.type in (SubjectType.DOMAIN, SubjectType.ORGANIZATION):
            target = subject.value.lower()
            allowed = {d.lower() for d in self.roe.in_scope_domains}
            in_scope = any(target == d or target.endswith(f".{d}") for d in allowed)
            if not in_scope:
                raise AuthorizationError(
                    f"Subject '{subject.value}' is not within in_scope_domains for web-infra collection."
                )
