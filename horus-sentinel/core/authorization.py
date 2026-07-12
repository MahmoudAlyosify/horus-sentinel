"""Scope & Authorization Engine — the hard gate every job passes through first.

This is the #1 credibility signal for a military audience (master plan Phase 1, Part 2.2
#3). No job runs without a valid RoE, and no collection happens outside the authorized
scope. The engine is deliberately small and total: it either returns an ``AuthContext``
or it raises. There is no "warn and continue" path.
"""

from __future__ import annotations

import structlog

from schemas.auth import AuthContext, AuthorizationError
from schemas.roe import ACTIVE_SOURCE_CATEGORIES, Classification, RoE, SourceCategory
from schemas.subject import Subject, SubjectType

log = structlog.get_logger("horus.authz")


class AuthorizationEngine:
    """Validates an RoE against a subject and mints the per-job AuthContext."""

    def authorize(self, job_id: str, subject: Subject, roe: RoE) -> AuthContext:
        """Validate the RoE for this subject and return a bound AuthContext.

        Raises ``AuthorizationError`` (rejecting the job) if:
          * the RoE has already expired,
          * no sources are enabled,
          * the RoE authorizes a different subject, or
          * a web-facing subject is not covered by ``in_scope_domains``.
        """
        if not roe.is_valid_now():
            raise AuthorizationError(
                f"RoE for job {job_id} is expired (expires_at={roe.expires_at.isoformat()})."
            )

        if not roe.enabled_sources:
            raise AuthorizationError(
                f"RoE for job {job_id} enables no sources — nothing is authorized to run."
            )

        self._assert_subject_matches_roe(subject, roe)
        self._assert_web_scope(subject, roe)
        self._assert_active_scope(subject, roe)

        log.info(
            "job_authorized",
            job_id=job_id,
            subject=subject.value,
            subject_type=subject.type.value,
            enabled_sources=[s.value for s in roe.enabled_sources],
            active=roe.has_active_sources(),
            signed_by=roe.signed_by,
        )
        return AuthContext(job_id=job_id, roe=roe)

    @staticmethod
    def _assert_subject_matches_roe(subject: Subject, roe: RoE) -> None:
        """The RoE names the subject it authorizes; it must match the job's subject."""
        if roe.subject.strip().lower() != subject.value.strip().lower():
            raise AuthorizationError(
                f"RoE authorizes subject '{roe.subject}', not '{subject.value}'."
            )

    @staticmethod
    def _assert_web_scope(subject: Subject, roe: RoE) -> None:
        """If web-infra collection is enabled for a web-facing subject, it must be owned."""
        if SourceCategory.WEB_INFRA not in roe.enabled_sources:
            return
        if subject.type in (SubjectType.DOMAIN, SubjectType.ORGANIZATION):
            target = subject.value.lower()
            allowed = {d.lower() for d in roe.in_scope_domains}
            if not any(target == d or target.endswith(f".{d}") for d in allowed):
                raise AuthorizationError(
                    f"web_infra is enabled but '{subject.value}' is not in in_scope_domains "
                    f"{sorted(allowed)} — passive infra collection is confined to owned assets."
                )

    @staticmethod
    def _assert_active_scope(subject: Subject, roe: RoE) -> None:
        """Reject an active-recon job up front unless it is explicitly, narrowly authorized.

        This fails at job creation (→ 403) so an out-of-scope active request never even
        reaches the collection plane. Active recon needs, together:
          * ``active_authorized=True`` (an explicit second sign-off), and
          * a domain/organization target that is inside ``in_scope_domains``.
        """
        if not roe.has_active_sources():
            return
        active = sorted(s.value for s in roe.enabled_sources if s in ACTIVE_SOURCE_CATEGORIES)
        if not roe.active_authorized:
            raise AuthorizationError(
                f"Active sources {active} are enabled but active_authorized is False — "
                "active reconnaissance requires explicit authorization."
            )
        if subject.type not in (SubjectType.DOMAIN, SubjectType.ORGANIZATION):
            raise AuthorizationError(
                f"Active sources {active} are enabled but subject type "
                f"'{subject.type.value}' cannot be an active target (domain/org only)."
            )
        target = subject.value.lower()
        allowed = {d.lower() for d in roe.in_scope_domains}
        if not any(target == d or target.endswith(f".{d}") for d in allowed):
            raise AuthorizationError(
                f"Active sources {active} are enabled but target '{subject.value}' is not in "
                f"in_scope_domains {sorted(allowed)} — active recon is confined to authorized assets."
            )


# The single passive classification for Path C, exposed for callers building tool calls.
PASSIVE = Classification.PASSIVE

# Process-wide engine instance.
authorization_engine = AuthorizationEngine()
