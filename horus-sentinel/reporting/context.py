"""Assemble the full report context (master plan Part 6 — the 9 sections).

Pulls every piece a defensible intelligence product needs — subject & RoE, discovered
entities with source + timestamp, geo/infra context, enrichment, the risk-colored graph,
per-finding risk, prioritized recommendations, and the chain-of-custody appendix — into a
single dict the renderers turn into HTML / PDF / JSON. Every claim keeps its evidence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.analysis_store import load_analysis
from core.db import AuditRecord, JobRecord, ValidationRecord, session_scope
from core.findings_store import load_findings
from graph.knowledge_graph import KnowledgeGraph
from scoring.graph_scoring import apply_scores


def build_report_context(job_id: str) -> dict[str, Any]:
    """Build the complete, evidence-backed context for one job's report."""
    with session_scope() as session:
        job = session.get(JobRecord, job_id)
        if job is None:
            raise KeyError(job_id)
        subject = job.subject()
        roe = job.roe()
        audit_rows = [
            {
                "tool": a.tool,
                "source_category": a.source_category,
                "subject": a.subject_value,
                "summary": a.summary,
                "cache_hit": a.cache_hit,
                "signed_by": a.signed_by,
                "recorded_at": a.recorded_at.isoformat(),
            }
            for a in session.query(AuditRecord)
            .filter(AuditRecord.job_id == job_id)
            .order_by(AuditRecord.recorded_at)
            .all()
        ]
        validations = [
            {
                "action": v.action,
                "analyst": v.analyst,
                "note": v.note,
                "recorded_at": v.recorded_at.isoformat(),
            }
            for v in session.query(ValidationRecord)
            .filter(ValidationRecord.job_id == job_id)
            .order_by(ValidationRecord.recorded_at)
            .all()
        ]
        job_status = job.status
        validated_by = job.validated_by

    findings = load_findings(job_id)
    graph = KnowledgeGraph.from_findings(findings)
    apply_scores(graph)

    loaded = load_analysis(job_id)
    card = loaded[0] if loaded else None
    cytoscape = loaded[1] if loaded else graph.to_cytoscape()

    # Section 3 — discovered entities with source + timestamp.
    entities = [
        {
            "kind": f.entity_kind.value,
            "value": f.entity_value,
            "produced_by": f.produced_by,
            "produced_at": f.produced_at.isoformat(),
            "attributes": f.attributes,
        }
        for f in findings
    ]

    # Section 7 — per-node risk.
    risk_rows = sorted(
        (
            {
                "key": k,
                "kind": d["kind"],
                "value": d["value"],
                "risk_score": d.get("risk_score", 0.0),
                "risk_band": d.get("risk_band", "Info"),
            }
            for k, d in graph.g.nodes(data=True)
        ),
        key=lambda r: r["risk_score"],
        reverse=True,
    )

    signature_hits = graph.public_services_with_critical_cve(min_cvss=9.0)

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "job_id": job_id,
        "job_status": job_status,
        "validated_by": validated_by,
        "subject": subject,
        "roe": roe,
        "report_card": card.model_dump(mode="json") if card else None,
        "entities": entities,
        "entity_count": len(entities),
        "kind_histogram": graph.kind_histogram(),
        "risk_rows": risk_rows,
        "signature_hits": signature_hits,
        "graph": cytoscape,
        "audit": audit_rows,
        "validations": validations,
    }
