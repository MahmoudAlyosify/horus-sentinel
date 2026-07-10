"""Chain-of-custody audit logging (master plan Part 2.2 #5, Part 2.4).

Every external touch is recorded here — to structured logs always, and to the relational
store when a job context is present. This is what makes a HORUS report defensible: every
claim is traceable to a source, a time, and the authorization it ran under.
"""

from __future__ import annotations

import anyio
import structlog

from core.db import AuditRecord, session_scope
from schemas.auth import AuthContext
from schemas.findings import ToolResult
from schemas.roe import SourceCategory
from schemas.subject import Subject

log = structlog.get_logger("horus.audit")


class AuditLog:
    """Records external touches. Safe to call from async code."""

    async def record(
        self,
        tool: str,
        source_category: SourceCategory,
        subject: Subject,
        ctx: AuthContext,
        result: ToolResult,
    ) -> None:
        """Persist one chain-of-custody entry and emit a structured log line."""
        log.info(
            "external_touch",
            job_id=ctx.job_id,
            tool=tool,
            source_category=source_category.value,
            subject=subject.value,
            cache_hit=result.cached,
            summary=result.summary(),
            signed_by=ctx.roe.signed_by,
        )
        await anyio.to_thread.run_sync(self._persist, tool, source_category, subject, ctx, result)

    @staticmethod
    def _persist(
        tool: str,
        source_category: SourceCategory,
        subject: Subject,
        ctx: AuthContext,
        result: ToolResult,
    ) -> None:
        try:
            with session_scope() as session:
                session.add(
                    AuditRecord(
                        job_id=ctx.job_id,
                        tool=tool,
                        source_category=source_category.value,
                        subject_value=subject.value[:256],
                        summary=result.summary(),
                        cache_hit=result.cached,
                        signed_by=ctx.roe.signed_by,
                    )
                )
        except Exception as exc:  # never let audit persistence crash collection
            log.warning("audit_persist_failed", error=str(exc), tool=tool)


# Process-wide audit sink used by the Tool Abstraction Layer.
audit_log = AuditLog()
