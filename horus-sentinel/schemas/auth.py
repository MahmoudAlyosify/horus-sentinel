"""AuthContext — the per-job scope guard threaded through every tool call.

Design invariant (master plan Part 2.2 #2, #3): no external call bypasses the Tool
Abstraction Layer, and no job runs without an authorization record. The ``AuthContext``
is the lightweight object every ``IntelTool`` consults via ``ctx.assert_allows(...)``
*before* it touches any source. If a call is out of scope it **raises** — refusal is a
designed control, not an afterthought.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.roe import ACTIVE_SOURCE_CATEGORIES, Classification, RoE, SourceCategory
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

        Enforces, in order: RoE validity, source enablement, classification rules, and
        subject scope. **Active reconnaissance is gated hardest**: it runs only when the RoE
        explicitly authorizes active ops *and* the target is inside ``in_scope_domains``.
        An active call against an out-of-scope target always raises — by design.
        """
        if not self.roe.is_valid_now():
            raise AuthorizationError(
                f"RoE expired at {self.roe.expires_at.isoformat()}; job {self.job_id} cannot collect."
            )

        if not self.roe.allows_source(source_category):
            raise AuthorizationError(
                f"Source category '{source_category.value}' is not enabled in the RoE for job {self.job_id}."
            )

        if classification == Classification.ACTIVE:
            self._assert_active_authorized(source_category, subject)

        self._assert_subject_in_scope(source_category, subject)

    def _assert_active_authorized(self, source_category: SourceCategory, subject: Subject) -> None:
        """Active reconnaissance requires an explicit authorization flag + an in-scope target."""
        if not self.roe.active_authorized:
            raise AuthorizationError(
                f"Active source '{source_category.value}' requires active_authorized=True in the "
                f"RoE for job {self.job_id} — active reconnaissance is opt-in and audited."
            )
        # Active ops are only ever permitted against explicitly authorized assets.
        if subject.type not in (SubjectType.DOMAIN, SubjectType.ORGANIZATION):
            raise AuthorizationError(
                f"Active reconnaissance is only permitted for domain/organization targets, "
                f"not subject type '{subject.type.value}'."
            )
        if not self._target_in_scope(subject):
            raise AuthorizationError(
                f"Active target '{subject.value}' is not within in_scope_domains "
                f"{sorted(self.roe.in_scope_domains)} — active recon never runs out of scope."
            )

    def _assert_subject_in_scope(self, source_category: SourceCategory, subject: Subject) -> None:
        """Web-facing collection (passive web-infra + all active recon) stays on owned assets."""
        scoped = {SourceCategory.WEB_INFRA, *ACTIVE_SOURCE_CATEGORIES}
        if source_category not in scoped:
            return
        if subject.type in (
            SubjectType.DOMAIN,
            SubjectType.ORGANIZATION,
        ) and not self._target_in_scope(subject):
            raise AuthorizationError(
                f"Subject '{subject.value}' is not within in_scope_domains for "
                f"'{source_category.value}' collection."
            )

    def _target_in_scope(self, subject: Subject) -> bool:
        """True if the subject is one of, or a subdomain of, an in-scope domain."""
        target = subject.value.lower()
        allowed = {d.lower() for d in self.roe.in_scope_domains}
        return any(target == d or target.endswith(f".{d}") for d in allowed)
