"""Real intelligence-report PDF — pure-Python, no system libraries, Arabic (RTL) or English (LTR).

WeasyPrint needs GTK/Pango native libs that are painful (often impossible) on Windows; this
generator uses ``fpdf2`` + ``arabic-reshaper`` + ``python-bidi`` with a bundled Amiri OFL font,
so a genuine, correctly-shaped PDF is produced on any OS (Windows, Linux, Docker) with zero
extra install. The Amiri font also covers Latin, so the same engine renders an English report.
It emits the same nine sections as the HTML report (master plan Part 6); labels, direction and
shaping switch on ``language`` (``ar`` → RTL Arabic, ``en`` → LTR English).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import arabic_reshaper
import structlog
from bidi.algorithm import get_display
from fpdf import FPDF

log = structlog.get_logger("horus.reporting.pdf")

_FONT_DIR = Path(__file__).resolve().parent / "fonts"
_AMIRI = _FONT_DIR / "Amiri-Regular.ttf"
_AMIRI_BOLD = _FONT_DIR / "Amiri-Bold.ttf"

# Risk band → (Arabic label, English label, RGB). Matches the HTML palette.
_BANDS: dict[str, tuple[str, str, tuple[int, int, int]]] = {
    "Critical": ("حرجة", "Critical", (215, 38, 61)),
    "High": ("عالية", "High", (244, 96, 54)),
    "Medium": ("متوسطة", "Medium", (200, 150, 8)),
    "Low": ("منخفضة", "Low", (46, 139, 87)),
    "Info": ("معلوماتية", "Info", (108, 117, 125)),
}

_INK = (20, 30, 48)
_MUTED = (120, 135, 160)
_LINE = (205, 214, 228)
_PANEL = (244, 247, 252)
_ACCENT = (13, 40, 68)

# All human-readable strings, keyed by language. Section titles are per-language; anchors in
# the HTML report stay English, but the PDF is a self-contained localized deliverable.
_L: dict[str, dict[str, str]] = {
    "ar": {
        "header": "حورس سنتينل — تقرير استخبارات مفتوحة المصدر",
        "footer": "سرّي — للاستخدام المصرّح به فقط · صفحة",
        "subject": "الموضوع",
        "validated": "مُعتمد",
        "draft": "مسودة — بانتظار التحقق",
        "job_line": "رقم المهمة: {job} · التوليد: {ts} · الحالة: {status}",
        "sec1": "الملخص التنفيذي",
        "m_entities": "كيان مُرتبَط",
        "m_topband": "أعلى نطاق خطورة",
        "m_cves": "ثغرة حرجة مكشوفة",
        "m_findings": "نتيجة ذات أولوية",
        "no_analysis": "لم يُولَّد تحليل بعد لهذه المهمة.",
        "analysis_by": "التحليل بواسطة",
        "sec2": "الموضوع والنطاق",
        "kv_subject": "الموضوع",
        "kv_signed": "مصرّح به من",
        "kv_expiry": "انتهاء التفويض",
        "kv_sources": "المصادر المُفعّلة",
        "kv_scope": "النطاقات ضمن التفويض",
        "sec3": "الكيانات المكتشفة",
        "entities_count": "{n} كيان",
        "th_kind": "النوع",
        "th_value": "القيمة",
        "th_source": "المصدر",
        "th_collected": "وقت الجمع",
        "more_entities": "… و{n} كيانًا إضافيًا (انظر تصدير JSON).",
        "sec4": "السياق والتعرّض",
        "sec5": "إثراء الاستخبارات التهديدية",
        "sig_intro": "خدمات عامة تشغّل تقنيات بها ثغرة حرجة معروفة:",
        "th_service": "الخدمة",
        "th_tech": "التقنية",
        "no_sig": "لا توجد ثغرات حرجة مُرتبطة بخدمات عامة.",
        "sec6": "رسم المعرفة الاستخباراتي",
        "graph_line": "{nodes} عقدة · {edges} علاقة · مُلوَّن حسب الخطورة (الخريطة التفاعلية في نسخة HTML).",
        "sec7": "تحليل المخاطر",
        "th_entity": "الكيان",
        "th_score": "الدرجة",
        "th_band": "النطاق",
        "sec8": "النتائج ذات الأولوية والتوصيات",
        "no_findings": "لا توجد نتائج ذات أولوية.",
        "adj": "تعديل النموذج (±1، مُسجَّل): {key}: من {frm} إلى {to} — {reason}",
        "sev": "خطورة",
        "framework": "الإطار المرجعي",
        "recommendation": "التوصية",
        "evidence": "الأدلة: {n} سجل مصدري",
        "sec9": "الملحق — سلسلة الحيازة",
        "custody_intro": "كل اتصال خارجي، بالترتيب، مع نسب المصدر ووقته.",
        "th_tool": "الأداة",
        "th_cache": "الذاكرة",
        "th_time": "الوقت",
        "th_subject": "الموضوع",
        "cache_hit": "إصابة",
        "cache_fetch": "جلب",
        "auth_line": "التفويض: موقّع من {signer}، ينتهي {exp}.",
        "val_log": "سجل تحقق المحلل:",
        "th_action": "الإجراء",
        "th_analyst": "المحلل",
        "th_note": "ملاحظة",
        "no_val": "⚠ لا يوجد تحقق من محلل — التقرير غير نهائي.",
    },
    "en": {
        "header": "HORUS Sentinel — Open-Source Intelligence Report",
        "footer": "CONFIDENTIAL — authorized use only · page",
        "subject": "Subject",
        "validated": "Validated",
        "draft": "Draft — pending validation",
        "job_line": "Job: {job} · Generated: {ts} · Status: {status}",
        "sec1": "Executive Summary",
        "m_entities": "entities",
        "m_topband": "top risk band",
        "m_cves": "critical CVEs",
        "m_findings": "prioritized findings",
        "no_analysis": "No analysis has been generated for this job yet.",
        "analysis_by": "Analysis by",
        "sec2": "Subject & Scope",
        "kv_subject": "Subject",
        "kv_signed": "Authorized by",
        "kv_expiry": "Authorization expiry",
        "kv_sources": "Enabled sources",
        "kv_scope": "In-scope domains",
        "sec3": "Discovered Entities",
        "entities_count": "{n} entities",
        "th_kind": "Kind",
        "th_value": "Value",
        "th_source": "Source",
        "th_collected": "Collected at",
        "more_entities": "… and {n} more entities (see the JSON export).",
        "sec4": "Context & Exposure",
        "sec5": "Threat-Intel Enrichment",
        "sig_intro": "Public services running technologies with a known critical vulnerability:",
        "th_service": "Service",
        "th_tech": "Technology",
        "no_sig": "No critical vulnerabilities linked to public services.",
        "sec6": "Intelligence Knowledge Graph",
        "graph_line": "{nodes} nodes · {edges} edges · risk-colored (interactive map in the HTML report).",
        "sec7": "Risk Analysis",
        "th_entity": "Entity",
        "th_score": "Score",
        "th_band": "Band",
        "sec8": "Prioritized Findings & Recommendations",
        "no_findings": "No prioritized findings.",
        "adj": "Model adjustment (±1, logged): {key}: {frm} → {to} — {reason}",
        "sev": "severity",
        "framework": "Framework",
        "recommendation": "Recommendation",
        "evidence": "Evidence: {n} source records",
        "sec9": "Appendix — Chain of Custody",
        "custody_intro": "Every external touch, in order, with source attribution and time.",
        "th_tool": "Tool",
        "th_cache": "Cache",
        "th_time": "Time",
        "th_subject": "Subject",
        "cache_hit": "hit",
        "cache_fetch": "fetch",
        "auth_line": "Authorization: signed by {signer}, expires {exp}.",
        "val_log": "Analyst validation log:",
        "th_action": "Action",
        "th_analyst": "Analyst",
        "th_note": "Note",
        "no_val": "⚠ No analyst validation — the report is not final.",
    },
}

_TYPE = {
    "ar": {"domain": "نطاق", "region": "منطقة", "org": "منظمة", "entity": "كيان"},
    "en": {"domain": "domain", "region": "region", "org": "organization", "entity": "entity"},
}


def _has_arabic(s: str) -> bool:
    return any("؀" <= c <= "ۿ" or "ݐ" <= c <= "ݿ" for c in str(s))


def shape(text: Any) -> str:
    """Shape + reorder for RTL only when the text contains Arabic; leave Latin untouched."""
    s = str(text)
    if _has_arabic(s):
        return get_display(arabic_reshaper.reshape(s))
    return s


# Backwards-compatible alias (older callers/tests import ``ar``).
ar = shape


class _Report(FPDF):
    """A4 report with a localized header/footer and the Amiri font family (Arabic + Latin)."""

    def __init__(self, subject_value: str, language: str = "ar") -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.subject_value = subject_value
        self.lang = language if language in _L else "ar"
        self._s = _L[self.lang]
        self.rtl = self.lang == "ar"
        self.A = "R" if self.rtl else "L"  # primary text alignment
        self.set_auto_page_break(auto=True, margin=18)
        self.add_font("Amiri", "", str(_AMIRI))
        self.add_font("Amiri", "B", str(_AMIRI_BOLD))
        self.set_margins(16, 16, 16)

    def _band_label(self, band: str) -> str:
        row = _BANDS.get(band)
        if not row:
            return band
        return row[0] if self.rtl else row[1]

    def header(self) -> None:
        self.set_fill_color(*_ACCENT)
        self.rect(0, 0, self.w, 24, "F")
        self.set_xy(16, 7)
        self.set_font("Amiri", "B", 15)
        self.set_text_color(255, 255, 255)
        self.cell(
            self.w - 32, 10, shape(self._s["header"]), align=self.A, new_x="LMARGIN", new_y="NEXT"
        )
        self.set_text_color(*_INK)
        self.set_y(30)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Amiri", "", 8)
        self.set_text_color(*_MUTED)
        self.cell(0, 8, shape(f"{self._s['footer']} {self.page_no()}"), align="C")

    # ---- building blocks ----------------------------------------------------
    def section_title(self, num: int, title: str) -> None:
        if self.get_y() > self.h - 40:
            self.add_page()
        self.ln(3)
        self.set_fill_color(*_ACCENT)
        self.set_text_color(255, 255, 255)
        self.set_font("Amiri", "B", 12)
        label = f"{title}  .{num}" if self.rtl else f"{num}.  {title}"
        self.cell(0, 9, shape(label), align=self.A, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*_INK)
        self.ln(1)

    def prose(self, text: str) -> None:
        if not text:
            return
        self.set_font("Amiri", "", 11)
        self.set_text_color(*_INK)
        # Align each paragraph by its own script so an English answer in an Arabic report
        # (or vice versa) still reads correctly.
        for para in str(text).split("\n"):
            if not para.strip():
                self.ln(2)
                continue
            a = "R" if _has_arabic(para) else "L"
            self.multi_cell(0, 7, shape(para), align=a, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def muted(self, text: str) -> None:
        self.set_font("Amiri", "", 9)
        self.set_text_color(*_MUTED)
        self.multi_cell(0, 6, shape(text), align=self.A, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*_INK)

    def kv_row(self, key: str, value: str) -> None:
        self.set_font("Amiri", "", 10)
        w = self.w - self.l_margin - self.r_margin
        # In RTL the value sits left and the key right; in LTR the key sits left, value right.
        first_w, second_w = (w * 0.68, w * 0.32) if self.rtl else (w * 0.32, w * 0.68)
        first_txt, second_txt = (value, key) if self.rtl else (key, value)
        first_bold, second_bold = (False, True) if self.rtl else (True, False)
        self.set_font("Amiri", "B" if first_bold else "", 10)
        self.set_text_color(*(_ACCENT if first_bold else _INK))
        self.multi_cell(
            first_w,
            7,
            shape(first_txt),
            align=self.A,
            border="B",
            new_x="LEFT" if self.rtl else "RIGHT",
            new_y="TOP",
            max_line_height=7,
        )
        self.set_font("Amiri", "B" if second_bold else "", 10)
        self.set_text_color(*(_ACCENT if second_bold else _INK))
        self.multi_cell(
            second_w,
            7,
            shape(second_txt),
            align=self.A,
            border="B",
            new_x="LMARGIN",
            new_y="NEXT",
            max_line_height=7,
        )
        self.set_text_color(*_INK)

    def metrics(self, pairs: list[tuple[str, str]]) -> None:
        self.set_font("Amiri", "B", 10)
        w = (self.w - self.l_margin - self.r_margin) / len(pairs)
        y0 = self.get_y()
        # Lay tiles right→left for RTL, left→right for LTR.
        if self.rtl:
            x = self.w - self.r_margin - w
            step = -w
        else:
            x = self.l_margin
            step = w
        for value, label in pairs:
            self.set_fill_color(*_PANEL)
            self.set_draw_color(*_LINE)
            self.rect(x, y0, w - 2, 18, "DF")
            self.set_xy(x, y0 + 2)
            self.set_font("Amiri", "B", 14)
            self.set_text_color(*_ACCENT)
            self.cell(w - 2, 8, shape(value), align="C", new_x="LEFT", new_y="NEXT")
            self.set_xy(x, y0 + 10)
            self.set_font("Amiri", "", 8)
            self.set_text_color(*_MUTED)
            self.cell(w - 2, 6, shape(label), align="C")
            x += step
        self.set_xy(self.l_margin, y0 + 21)
        self.set_text_color(*_INK)

    def table(self, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
        """Simple table: cells aligned to the reading direction, columns laid accordingly."""
        total = self.w - self.l_margin - self.r_margin
        col_w = [total * fr for fr in widths]
        self.set_font("Amiri", "B", 9)
        self.set_fill_color(*_ACCENT)
        self.set_text_color(255, 255, 255)
        if self.rtl:
            x0 = self.w - self.r_margin
            positions = []
            x = x0
            for w_ in col_w:
                x -= w_
                positions.append(x)
        else:
            positions = []
            x = self.l_margin
            for w_ in col_w:
                positions.append(x)
                x += w_
        for pos, w_, h_ in zip(positions, col_w, headers, strict=False):
            self.set_xy(pos, self.get_y())
            self.cell(w_, 7, shape(h_), align="C", fill=True, border=0)
        self.ln(7)
        self.set_text_color(*_INK)
        self.set_font("Amiri", "", 9)
        fill = False
        for row in rows:
            if self.get_y() > self.h - 24:
                self.add_page()
            self.set_fill_color(*(_PANEL if fill else (255, 255, 255)))
            y = self.get_y()
            for pos, w_, cell in zip(positions, col_w, row, strict=False):
                self.set_xy(pos, y)
                self.cell(w_, 6.5, shape(cell), align=self.A, fill=True, border="B")
            self.ln(6.5)
            fill = not fill
        self.ln(2)

    def finding(self, f: dict[str, Any]) -> None:
        band = f.get("risk_band", "Info")
        color = _BANDS.get(band, ("", band, _MUTED))[2]
        if self.get_y() > self.h - 40:
            self.add_page()
        y0 = self.get_y()
        edge_x = self.w - self.r_margin if self.rtl else self.l_margin
        self.set_draw_color(*color)
        self.set_line_width(1.2)
        self.line(edge_x, y0, edge_x, y0 + 6)
        self.set_line_width(0.2)
        self.set_font("Amiri", "B", 10)
        self.multi_cell(
            0,
            6.5,
            shape(
                f"{f.get('title', '')}  —  {self._s['sev']} {self._band_label(band)} "
                f"({f.get('risk_score', 0):.1f})"
            ),
            align=self.A,
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.muted(f.get("why_it_matters", ""))
        fw = f.get("framework")
        if fw:
            self.set_font("Amiri", "", 9)
            self.set_text_color(*_INK)
            self.multi_cell(
                0,
                6,
                shape(
                    f"{self._s['framework']}: {fw.get('technique_id', '')} "
                    f"{fw.get('technique_name', '')} "
                    + (f"· {fw.get('tactic')}" if fw.get("tactic") else "")
                ),
                align=self.A,
                new_x="LMARGIN",
                new_y="NEXT",
            )
        self.set_font("Amiri", "B", 9)
        self.set_text_color(*_ACCENT)
        self.multi_cell(
            0,
            6,
            shape(f"{self._s['recommendation']}: {f.get('recommendation', '')}"),
            align=self.A,
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.set_text_color(*_INK)
        ev = f.get("evidence_ids") or []
        if ev:
            self.muted(self._s["evidence"].format(n=len(ev)))
        self.ln(1)


def _subj(context: dict) -> tuple[str, str]:
    s = context.get("subject")
    value = getattr(s, "value", None) or (s.get("value") if isinstance(s, dict) else "")
    stype = getattr(s, "type", None) or (s.get("type") if isinstance(s, dict) else "")
    return str(value), str(getattr(stype, "value", stype))


def _roe(context: dict) -> dict[str, Any]:
    r = context.get("roe")
    if isinstance(r, dict):
        return r
    return {
        "signed_by": getattr(r, "signed_by", ""),
        "expires_at": getattr(r, "expires_at", ""),
        "enabled_sources": [getattr(s, "value", s) for s in getattr(r, "enabled_sources", [])],
        "in_scope_domains": list(getattr(r, "in_scope_domains", [])),
    }


def render_report_pdf(context: dict, language: str = "ar") -> bytes:
    """Render the full nine-section intelligence report to PDF bytes (Arabic RTL or English LTR)."""
    lang = language if language in _L else "ar"
    s = _L[lang]
    sep = "، " if lang == "ar" else ", "
    subject_value, subject_type = _subj(context)
    roe = _roe(context)
    card = context.get("report_card") or {}
    pdf = _Report(subject_value, lang)
    pdf.add_page()

    # Title block
    pdf.set_font("Amiri", "B", 13)
    pdf.set_text_color(*_ACCENT)
    pdf.cell(
        0,
        9,
        shape(f"{s['subject']}: {subject_value}  ({_TYPE[lang].get(subject_type, subject_type)})"),
        align=pdf.A,
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_font("Amiri", "", 9)
    pdf.set_text_color(*_MUTED)
    status = s["validated"] if context.get("validated_by") else s["draft"]
    pdf.cell(
        0,
        6,
        shape(
            s["job_line"].format(
                job=context.get("job_id", ""),
                ts=str(context.get("generated_at", ""))[:19],
                status=status,
            )
        ),
        align=pdf.A,
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_text_color(*_INK)
    pdf.ln(2)

    # 1. Executive summary
    pdf.section_title(1, s["sec1"])
    pdf.metrics(
        [
            (str(context.get("entity_count", 0)), s["m_entities"]),
            (pdf._band_label(card.get("top_band", "Info")), s["m_topband"]),
            (str(card.get("critical_cve_hits", 0)), s["m_cves"]),
            (str(len(card.get("prioritized_findings", []))), s["m_findings"]),
        ]
    )
    pdf.prose(card.get("executive_summary", s["no_analysis"]))
    if card.get("generated_by"):
        pdf.muted(f"{s['analysis_by']}: {card.get('generated_by')}")

    # 2. Subject & scope
    pdf.section_title(2, s["sec2"])
    pdf.kv_row(s["kv_subject"], f"{subject_value} ({_TYPE[lang].get(subject_type, subject_type)})")
    pdf.kv_row(s["kv_signed"], str(roe.get("signed_by", "")))
    pdf.kv_row(s["kv_expiry"], str(roe.get("expires_at", ""))[:19])
    pdf.kv_row(s["kv_sources"], sep.join(str(x) for x in roe.get("enabled_sources", [])) or "—")
    pdf.kv_row(s["kv_scope"], sep.join(roe.get("in_scope_domains", [])) or "—")

    # 3. Discovered entities
    entities = context.get("entities", [])
    pdf.section_title(3, s["sec3"])
    hist = context.get("kind_histogram", {})
    pdf.muted(
        s["entities_count"].format(n=context.get("entity_count", 0))
        + " · "
        + sep.join(f"{v} {k}" for k, v in hist.items())
    )
    if entities:
        rows = [
            [
                e.get("kind", ""),
                str(e.get("value", "")),
                e.get("produced_by", ""),
                str(e.get("produced_at", ""))[:19],
            ]
            for e in entities[:40]
        ]
        pdf.table(
            [s["th_kind"], s["th_value"], s["th_source"], s["th_collected"]],
            rows,
            [0.18, 0.37, 0.22, 0.23],
        )
        if len(entities) > 40:
            pdf.muted(s["more_entities"].format(n=len(entities) - 40))

    # 4. Context & exposure
    pdf.section_title(4, s["sec4"])
    pdf.prose(card.get("geopolitical_context", ""))
    pdf.prose(card.get("threat_assessment", ""))

    # 5. Threat-intel enrichment
    pdf.section_title(5, s["sec5"])
    hits = context.get("signature_hits", [])
    if hits:
        pdf.prose(s["sig_intro"])
        rows = [
            [
                str(h.get("ip", "")),
                str(h.get("service", "")),
                str(h.get("technology", "")),
                str(h.get("cve", "")),
                str(h.get("cvss", "")),
            ]
            for h in hits
        ]
        pdf.table(
            ["IP", s["th_service"], s["th_tech"], "CVE", "CVSS"],
            rows,
            [0.24, 0.18, 0.24, 0.22, 0.12],
        )
    else:
        pdf.muted(s["no_sig"])

    # 6. Knowledge graph (summary — the interactive map lives in the HTML report)
    graph = context.get("graph", {"nodes": [], "edges": []})
    pdf.section_title(6, s["sec6"])
    pdf.muted(
        s["graph_line"].format(nodes=len(graph.get("nodes", [])), edges=len(graph.get("edges", [])))
    )

    # 7. Risk analysis
    pdf.section_title(7, s["sec7"])
    risk = context.get("risk_rows", [])[:20]
    if risk:
        rows = [
            [
                str(r.get("value", "")),
                r.get("kind", ""),
                f"{r.get('risk_score', 0):.1f}",
                pdf._band_label(r.get("risk_band", "Info")),
            ]
            for r in risk
        ]
        pdf.table(
            [s["th_entity"], s["th_kind"], s["th_score"], s["th_band"]],
            rows,
            [0.4, 0.24, 0.16, 0.20],
        )

    # 8. Prioritized findings
    pdf.section_title(8, s["sec8"])
    findings = card.get("prioritized_findings", [])
    if findings:
        for f in findings:
            pdf.finding(f)
    else:
        pdf.muted(s["no_findings"])
    for adj in card.get("band_adjustments", []):
        pdf.muted(
            s["adj"].format(
                key=adj.get("entity_key", ""),
                frm=pdf._band_label(adj.get("from_band", "")),
                to=pdf._band_label(adj.get("to_band", "")),
                reason=adj.get("reason", ""),
            )
        )

    # 9. Chain of custody
    pdf.section_title(9, s["sec9"])
    pdf.muted(s["custody_intro"])
    audit = context.get("audit", [])
    if audit:
        rows = [
            [
                a.get("tool", ""),
                a.get("source_category", ""),
                str(a.get("subject", "")),
                s["cache_hit"] if a.get("cache_hit") else s["cache_fetch"],
                str(a.get("recorded_at", ""))[:19],
            ]
            for a in audit
        ]
        pdf.table(
            [s["th_tool"], s["th_source"], s["th_subject"], s["th_cache"], s["th_time"]],
            rows,
            [0.18, 0.2, 0.24, 0.13, 0.25],
        )
    pdf.muted(
        s["auth_line"].format(
            signer=roe.get("signed_by", ""), exp=str(roe.get("expires_at", ""))[:19]
        )
    )
    validations = context.get("validations", [])
    if validations:
        pdf.prose(s["val_log"])
        rows = [
            [
                v.get("action", ""),
                v.get("analyst", ""),
                v.get("note", "") or "—",
                str(v.get("recorded_at", ""))[:19],
            ]
            for v in validations
        ]
        pdf.table(
            [s["th_action"], s["th_analyst"], s["th_note"], s["th_time"]],
            rows,
            [0.2, 0.24, 0.31, 0.25],
        )
    else:
        pdf.muted(s["no_val"])

    return bytes(pdf.output())


def render_arabic_pdf(context: dict) -> bytes:
    """Backwards-compatible Arabic entry point (kept for existing callers)."""
    return render_report_pdf(context, "ar")
