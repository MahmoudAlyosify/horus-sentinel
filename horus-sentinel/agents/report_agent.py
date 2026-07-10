"""Reporting Agent — one job → one structured, evidence-backed deliverable (Part 6).

Assembles the 9-section report context and renders it to HTML / JSON / PDF. Records the
HTML path on the job so the UI/API can serve it. The chain-of-custody appendix (Part 6.1
section 9) makes the report defensible: what ran, when, under what authorization, and who
validated it.
"""
from __future__ import annotations

import structlog

from core.jobs import job_service
from reporting.context import build_report_context
from reporting.renderer import save_reports

log = structlog.get_logger("horus.agent.report")


class ReportAgent:
    """Turns a completed assessment into the intelligence report deliverable."""

    name = "report"

    def generate(self, job_id: str, formats: list[str] | None = None) -> dict[str, str]:
        """Build + render the report. Returns {format: path}. Records the HTML path on the job."""
        context = build_report_context(job_id)
        written = save_reports(job_id, context, formats)
        primary = written.get("html") or written.get("pdf") or written.get("json")
        if primary:
            job_service.set_report_path(job_id, primary)
        log.info("report_generated", job_id=job_id, formats=list(written))
        return written


report_agent = ReportAgent()
