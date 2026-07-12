"""Render the report in three formats (master plan Part 6.2).

* HTML — the interactive deliverable (embeds the risk-colored Cytoscape graph).
* JSON — the machine-readable export (the full report context).
* PDF  — HTML→PDF via WeasyPrint when it's installed; otherwise skipped non-fatally so
         the platform still produces HTML+JSON on a bare setup.
"""

from __future__ import annotations

import json
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.config import settings

log = structlog.get_logger("horus.reporting")

_TEMPLATES = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_html(context: dict) -> str:
    """Render the 9-section HTML report (Arabic RTL template when report_language == 'ar')."""
    template = "report.ar.html.j2" if settings.report_language == "ar" else "report.html.j2"
    return _env.get_template(template).render(**context)


def render_json(context: dict) -> str:
    """The full report context as pretty JSON."""
    return json.dumps(context, indent=2, default=str)


def render_pdf(html: str, context: dict | None = None) -> bytes | None:
    """Produce a real PDF. Returns None (non-fatal) only if every path fails.

    Order of preference:
      1. The pure-Python fpdf2 generator (Arabic RTL or English LTR, chosen by report_language).
         No system libraries — works on any OS, so this is the primary path for both languages.
      2. WeasyPrint HTML→PDF — a last-resort fallback only if the fpdf2 path somehow fails and
         the native GTK/Pango libs happen to be installed.
    """
    if context is not None:
        try:
            from reporting.arabic_pdf import render_report_pdf

            return render_report_pdf(context, settings.report_language)
        except Exception as exc:  # never let PDF failure break the pipeline
            log.warning("fpdf_report_failed_fallback_weasyprint", error=str(exc))

    try:
        from weasyprint import HTML  # lazy: heavy native deps on some platforms
    except Exception as exc:  # ImportError or missing system libs
        log.info("weasyprint_unavailable_skip_pdf", error=str(exc))
        return None
    try:
        return HTML(string=html).write_pdf()
    except Exception as exc:
        log.warning("pdf_render_failed", error=str(exc))
        return None


def save_reports(job_id: str, context: dict, formats: list[str] | None = None) -> dict[str, str]:
    """Render and write requested formats to the report directory. Returns {fmt: path}."""
    formats = formats or ["html", "json", "pdf"]
    out_dir = Path(settings.report_output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    html = render_html(context) if ("html" in formats or "pdf" in formats) else None

    if "html" in formats and html is not None:
        p = out_dir / f"{job_id}.html"
        p.write_text(html, encoding="utf-8")
        written["html"] = str(p)

    if "json" in formats:
        p = out_dir / f"{job_id}.json"
        p.write_text(render_json(context), encoding="utf-8")
        written["json"] = str(p)

    if "pdf" in formats and html is not None:
        pdf = render_pdf(html, context)
        if pdf is not None:
            p = out_dir / f"{job_id}.pdf"
            p.write_bytes(pdf)
            written["pdf"] = str(p)

    log.info("reports_written", job_id=job_id, formats=list(written))
    return written
