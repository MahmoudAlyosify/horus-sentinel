"""Persist normalized findings to the relational store.

Agents write findings here (not into each other's memory). The graph builder and the
report both read from this store, so every claim keeps its evidence trail. Async-safe:
persistence runs in a worker thread to avoid blocking the event loop.
"""

from __future__ import annotations

import json
from collections.abc import Iterable

import anyio
import structlog

from core.db import FindingRecord, session_scope
from schemas.findings import Finding

log = structlog.get_logger("horus.findings")


async def persist_findings(job_id: str, findings: Iterable[Finding]) -> int:
    """Store findings for a job. Returns the number written. Deduplicates by finding id."""
    items = list(findings)
    if not items:
        return 0
    return await anyio.to_thread.run_sync(_persist, job_id, items)


def _persist(job_id: str, findings: list[Finding]) -> int:
    written = 0
    with session_scope() as session:
        for f in findings:
            if session.get(FindingRecord, f.id) is not None:
                continue
            session.add(
                FindingRecord(
                    id=f.id,
                    job_id=job_id,
                    entity_kind=str(f.entity_kind),
                    entity_value=f.entity_value[:512],
                    attributes_json=json.dumps(f.attributes, default=str),
                    related_to=(f.related_to[:512] if f.related_to else None),
                    relationship_label=f.relationship,
                    produced_by=f.produced_by,
                    produced_at=f.produced_at,
                )
            )
            written += 1
    log.info("findings_persisted", job_id=job_id, written=written)
    return written


def load_findings(job_id: str) -> list[Finding]:
    """Rehydrate a job's findings from the store (used by the graph/report builders)."""
    from schemas.findings import EntityKind

    with session_scope() as session:
        rows = session.query(FindingRecord).filter(FindingRecord.job_id == job_id).all()
        result: list[Finding] = []
        for r in rows:
            result.append(
                Finding(
                    id=r.id,
                    entity_kind=EntityKind(r.entity_kind),
                    entity_value=r.entity_value,
                    attributes=json.loads(r.attributes_json or "{}"),
                    related_to=r.related_to,
                    relationship=r.relationship_label,
                    produced_by=r.produced_by,
                    produced_at=r.produced_at,
                )
            )
        return result
