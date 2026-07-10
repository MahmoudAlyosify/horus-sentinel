"""Persist and retrieve the reasoning artifact (Report Card + rendered graph)."""

from __future__ import annotations

import json

import anyio

from core.db import AnalysisRecord, session_scope
from horus_brain.report_card import ReportCard


async def save_analysis(job_id: str, card: ReportCard, graph_cytoscape: dict) -> None:
    """Store the Report Card + Cytoscape graph for a job (upsert)."""
    await anyio.to_thread.run_sync(_save, job_id, card, graph_cytoscape)


def _save(job_id: str, card: ReportCard, graph_cytoscape: dict) -> None:
    with session_scope() as session:
        rec = session.get(AnalysisRecord, job_id)
        card_json = card.model_dump_json()
        graph_json = json.dumps(graph_cytoscape, default=str)
        if rec is None:
            session.add(
                AnalysisRecord(
                    job_id=job_id,
                    report_card_json=card_json,
                    graph_json=graph_json,
                    generated_by=card.generated_by,
                )
            )
        else:
            rec.report_card_json = card_json
            rec.graph_json = graph_json
            rec.generated_by = card.generated_by


def load_analysis(job_id: str) -> tuple[ReportCard, dict] | None:
    """Rehydrate the Report Card + graph for a job, or None if not analyzed yet."""
    with session_scope() as session:
        rec = session.get(AnalysisRecord, job_id)
        if rec is None:
            return None
        card = ReportCard.model_validate_json(rec.report_card_json)
        graph = json.loads(rec.graph_json or "{}")
        return card, graph
