"""
Chain-of-custody audit log (section 2.4 / 8.1 #9).

Every `ReconTool.__call__` writes one row here *after* a tool actually runs
(cache hits are intentionally also logged — see tools/base.py — because
"we looked at this asset at time T" is itself part of the chain of custody).

This module owns its own DB session per write so tool code doesn't need to
thread a session through every agent call.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from db.models import AuditLogORM
from db.session import async_session_factory


class AuditLog:
    async def record(
        self,
        tool_name: str,
        classification: str,
        target: str,
        job_id: UUID,
        summary: dict[str, Any],
    ) -> None:
        """Append one chain-of-custody row. Never raises into caller logic
        on its own — but DB errors WILL propagate, since a failed audit
        write should not be silently swallowed for a regulated engagement."""
        async with async_session_factory() as session:
            session.add(
                AuditLogORM(
                    job_id=job_id,
                    tool_name=tool_name,
                    classification=classification,
                    target=target,
                    summary=summary,
                )
            )
            await session.commit()


audit_log = AuditLog()
