"""Real Arabic (RTL) PDF intelligence report — pure-Python, no system libraries.

WeasyPrint needs GTK/Pango native libs that are painful on Windows; this generator uses
``fpdf2`` + ``arabic-reshaper`` + ``python-bidi`` with a bundled Amiri OFL font, so a genuine,
correctly-shaped right-to-left Arabic PDF is produced on any OS (Windows, Linux, Docker) with
zero extra install. It renders the same nine sections as the HTML report (master plan Part 6).
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

# Risk band → (Arabic label, RGB). Matches the HTML palette.
_BANDS: dict[str, tuple[str, tuple[int, int, int]]] = {
    "Critical": ("حرجة", (215, 38, 61)),
    "High": ("عالية", (244, 96, 54)),
    "Medium": ("متوسطة", (200, 150, 8)),
    "Low": ("منخفضة", (46, 139, 87)),
    "Info": ("معلوماتية", (108, 117, 125)),
}

_INK = (20, 30, 48)
_MUTED = (120, 135, 160)
_LINE = (205, 214, 228)
_PANEL = (244, 247, 252)
_ACCENT = (13, 40, 68)


def ar(text: Any) -> str:
    """Shape + reorder a string for correct right-to-left Arabic rendering."""
    return get_display(arabic_reshaper.reshape(str(text)))


def _band_label(band: str) -> str:
    return _BANDS.get(band, (band, _MUTED))[0]


class _Report(FPDF):
    """A4 report with an Arabic header/footer and the Amiri font family."""

    def __init__(self, subject_value: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.subject_value = subject_value
        self.set_auto_page_break(auto=True, margin=18)
        self.add_font("Amiri", "", str(_AMIRI))
        self.add_font("Amiri", "B", str(_AMIRI_BOLD))
        self.set_margins(16, 16, 16)

    def header(self) -> None:
        self.set_fill_color(*_ACCENT)
        self.rect(0, 0, self.w, 24, "F")
        self.set_xy(16, 7)
        self.set_font("Amiri", "B", 15)
        self.set_text_color(255, 255, 255)
        self.cell(
            self.w - 32, 10, ar("حورس سنتينل — تقرير استخبارات مفتوحة المصدر"),
            align="R", new_x="LMARGIN", new_y="NEXT",
        )
        self.set_text_color(*_INK)
        self.set_y(30)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Amiri", "", 8)
        self.set_text_color(*_MUTED)
        self.cell(
            0, 8,
            ar(f"سرّي — للاستخدام المصرّح به فقط · صفحة {self.page_no()}"),
            align="C",
        )

    # ---- building blocks (all RTL) -----------------------------------------
    def section_title(self, num: int, title: str) -> None:
        if self.get_y() > self.h - 40:
            self.add_page()
        self.ln(3)
        self.set_fill_color(*_ACCENT)
        self.set_text_color(255, 255, 255)
        self.set_font("Amiri", "B", 12)
        self.cell(0, 9, ar(f"{title}  .{num}"), align="R", fill=True,
                  new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*_INK)
        self.ln(1)

    def prose(self, text: str) -> None:
        if not text:
            return
        self.set_font("Amiri", "", 11)
        self.set_text_color(*_INK)
        self.multi_cell(0, 7, ar(text), align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def muted(self, text: str) -> None:
        self.set_font("Amiri", "", 9)
        self.set_text_color(*_MUTED)
        self.multi_cell(0, 6, ar(text), align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*_INK)

    def kv_row(self, key: str, value: str) -> None:
        self.set_font("Amiri", "", 10)
        w = self.w - self.l_margin - self.r_margin
        # value cell (left), key cell (right) — RTL reading order.
        self.set_text_color(*_INK)
        self.multi_cell(w * 0.68, 7, ar(value), align="R", border="B",
                        new_x="LEFT", new_y="TOP", max_line_height=7)
        self.set_font("Amiri", "B", 10)
        self.set_text_color(*_ACCENT)
        self.multi_cell(w * 0.32, 7, ar(key), align="R", border="B",
                        new_x="LMARGIN", new_y="NEXT", max_line_height=7)
        self.set_text_color(*_INK)

    def band_chip(self, band: str) -> None:
        label, color = _BANDS.get(band, (band, _MUTED))
        self.set_font("Amiri", "B", 10)
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.cell(26, 7, ar(label), align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*_INK)

    def metrics(self, pairs: list[tuple[str, str]]) -> None:
        self.set_font("Amiri", "B", 10)
        w = (self.w - self.l_margin - self.r_margin) / len(pairs)
        y0 = self.get_y()
        x = self.w - self.r_margin - w
        for value, label in pairs:
            self.set_xy(x, y0)
            self.set_fill_color(*_PANEL)
            self.set_draw_color(*_LINE)
            self.rect(x, y0, w - 2, 18, "DF")
            self.set_xy(x, y0 + 2)
            self.set_font("Amiri", "B", 14)
            self.set_text_color(*_ACCENT)
            self.cell(w - 2, 8, ar(value), align="C", new_x="LEFT", new_y="NEXT")
            self.set_xy(x, y0 + 10)
            self.set_font("Amiri", "", 8)
            self.set_text_color(*_MUTED)
            self.cell(w - 2, 6, ar(label), align="C")
            x -= w
        self.set_xy(self.l_margin, y0 + 21)
        self.set_text_color(*_INK)

    def table(self, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
        """Simple RTL table: headers/cells are right-aligned, columns laid right→left."""
        total = self.w - self.l_margin - self.r_margin
        col_w = [total * fr for fr in widths]
        self.set_font("Amiri", "B", 9)
        self.set_fill_color(*_ACCENT)
        self.set_text_color(255, 255, 255)
        x = self.w - self.r_margin
        for w_, h_ in zip(col_w, headers, strict=False):
            x -= w_
            self.set_xy(x, self.get_y())
            self.cell(w_, 7, ar(h_), align="C", fill=True, border=0)
        self.ln(7)
        self.set_text_color(*_INK)
        self.set_font("Amiri", "", 9)
        fill = False
        for row in rows:
            if self.get_y() > self.h - 24:
                self.add_page()
            self.set_fill_color(*(_PANEL if fill else (255, 255, 255)))
            x = self.w - self.r_margin
            y = self.get_y()
            for w_, cell in zip(col_w, row, strict=False):
                x -= w_
                self.set_xy(x, y)
                self.cell(w_, 6.5, ar(cell), align="R", fill=True, border="B")
            self.ln(6.5)
            fill = not fill
        self.ln(2)

    def finding(self, f: dict[str, Any]) -> None:
        band = f.get("risk_band", "Info")
        _, color = _BANDS.get(band, (band, _MUTED))
        if self.get_y() > self.h - 40:
            self.add_page()
        y0 = self.get_y()
        self.set_draw_color(*color)
        self.set_line_width(1.2)
        self.line(self.w - self.r_margin, y0, self.w - self.r_margin, y0 + 6)
        self.set_line_width(0.2)
        self.set_font("Amiri", "B", 10)
        self.multi_cell(0, 6.5, ar(f"{f.get('title', '')}  —  خطورة {_band_label(band)} "
                                   f"({f.get('risk_score', 0):.1f})"),
                        align="R", new_x="LMARGIN", new_y="NEXT")
        self.muted(f.get("why_it_matters", ""))
        fw = f.get("framework")
        if fw:
            self.set_font("Amiri", "", 9)
            self.set_text_color(*_INK)
            self.multi_cell(
                0, 6,
                ar(f"الإطار المرجعي: {fw.get('technique_id', '')} "
                   f"{fw.get('technique_name', '')} "
                   + (f"· {fw.get('tactic')}" if fw.get("tactic") else "")),
                align="R", new_x="LMARGIN", new_y="NEXT",
            )
        self.set_font("Amiri", "B", 9)
        self.set_text_color(*_ACCENT)
        self.multi_cell(0, 6, ar(f"التوصية: {f.get('recommendation', '')}"),
                        align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*_INK)
        ev = f.get("evidence_ids") or []
        if ev:
            self.muted(f"الأدلة: {len(ev)} سجل مصدري")
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


_TYPE_AR = {"domain": "نطاق", "region": "منطقة", "org": "منظمة", "entity": "كيان"}


def render_arabic_pdf(context: dict) -> bytes:
    """Render the full nine-section Arabic RTL intelligence report to PDF bytes."""
    subject_value, subject_type = _subj(context)
    roe = _roe(context)
    card = context.get("report_card") or {}
    pdf = _Report(subject_value)
    pdf.add_page()

    # Title block
    pdf.set_font("Amiri", "B", 13)
    pdf.set_text_color(*_ACCENT)
    pdf.cell(0, 9, ar(f"الموضوع: {subject_value}  ({_TYPE_AR.get(subject_type, subject_type)})"),
             align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Amiri", "", 9)
    pdf.set_text_color(*_MUTED)
    status_ar = "مُعتمد" if context.get("validated_by") else "مسودة — بانتظار التحقق"
    pdf.cell(0, 6, ar(f"رقم المهمة: {context.get('job_id', '')} · التوليد: "
                      f"{str(context.get('generated_at', ''))[:19]} · الحالة: {status_ar}"),
             align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*_INK)
    pdf.ln(2)

    # 1. Executive summary
    pdf.section_title(1, "الملخص التنفيذي")
    pdf.metrics([
        (str(context.get("entity_count", 0)), "كيان مُرتبَط"),
        (_band_label(card.get("top_band", "Info")), "أعلى نطاق خطورة"),
        (str(card.get("critical_cve_hits", 0)), "ثغرة حرجة مكشوفة"),
        (str(len(card.get("prioritized_findings", []))), "نتيجة ذات أولوية"),
    ])
    pdf.prose(card.get("executive_summary", "لم يُولَّد تحليل بعد لهذه المهمة."))
    if card.get("generated_by"):
        pdf.muted(f"التحليل بواسطة: {card.get('generated_by')}")

    # 2. Subject & scope
    pdf.section_title(2, "الموضوع والنطاق")
    pdf.kv_row("الموضوع", f"{subject_value} ({_TYPE_AR.get(subject_type, subject_type)})")
    pdf.kv_row("مصرّح به من", str(roe.get("signed_by", "")))
    pdf.kv_row("انتهاء التفويض", str(roe.get("expires_at", ""))[:19])
    pdf.kv_row("المصادر المُفعّلة", "، ".join(str(s) for s in roe.get("enabled_sources", [])) or "—")
    pdf.kv_row("النطاقات ضمن التفويض", "، ".join(roe.get("in_scope_domains", [])) or "—")

    # 3. Discovered entities
    entities = context.get("entities", [])
    pdf.section_title(3, "الكيانات المكتشفة")
    hist = context.get("kind_histogram", {})
    pdf.muted(f"{context.get('entity_count', 0)} كيان · "
              + "، ".join(f"{v} {k}" for k, v in hist.items()))
    if entities:
        rows = [[e.get("kind", ""), str(e.get("value", "")), e.get("produced_by", ""),
                 str(e.get("produced_at", ""))[:19]] for e in entities[:40]]
        pdf.table(["النوع", "القيمة", "المصدر", "وقت الجمع"], rows, [0.18, 0.37, 0.22, 0.23])
        if len(entities) > 40:
            pdf.muted(f"… و{len(entities) - 40} كيانًا إضافيًا (انظر تصدير JSON).")

    # 4. Context & exposure
    pdf.section_title(4, "السياق والتعرّض")
    pdf.prose(card.get("geopolitical_context", ""))
    pdf.prose(card.get("threat_assessment", ""))

    # 5. Threat-intel enrichment
    pdf.section_title(5, "إثراء الاستخبارات التهديدية")
    hits = context.get("signature_hits", [])
    if hits:
        pdf.prose("خدمات عامة تشغّل تقنيات بها ثغرة حرجة معروفة:")
        rows = [[str(h.get("ip", "")), str(h.get("service", "")), str(h.get("technology", "")),
                 str(h.get("cve", "")), str(h.get("cvss", ""))] for h in hits]
        pdf.table(["IP", "الخدمة", "التقنية", "CVE", "CVSS"], rows,
                  [0.24, 0.18, 0.24, 0.22, 0.12])
    else:
        pdf.muted("لا توجد ثغرات حرجة مُرتبطة بخدمات عامة.")

    # 6. Knowledge graph (summary — the interactive map lives in the HTML report)
    graph = context.get("graph", {"nodes": [], "edges": []})
    pdf.section_title(6, "رسم المعرفة الاستخباراتي")
    pdf.muted(f"{len(graph.get('nodes', []))} عقدة · {len(graph.get('edges', []))} علاقة · "
              "مُلوَّن حسب الخطورة (الخريطة التفاعلية في نسخة HTML).")

    # 7. Risk analysis
    pdf.section_title(7, "تحليل المخاطر")
    risk = context.get("risk_rows", [])[:20]
    if risk:
        rows = [[str(r.get("value", "")), r.get("kind", ""), f"{r.get('risk_score', 0):.1f}",
                 _band_label(r.get("risk_band", "Info"))] for r in risk]
        pdf.table(["الكيان", "النوع", "الدرجة", "النطاق"], rows, [0.4, 0.24, 0.16, 0.20])

    # 8. Prioritized findings
    pdf.section_title(8, "النتائج ذات الأولوية والتوصيات")
    findings = card.get("prioritized_findings", [])
    if findings:
        for f in findings:
            pdf.finding(f)
    else:
        pdf.muted("لا توجد نتائج ذات أولوية.")
    for adj in card.get("band_adjustments", []):
        pdf.muted(f"تعديل النموذج (±1، مُسجَّل): {adj.get('entity_key', '')}: "
                  f"من {_band_label(adj.get('from_band', ''))} إلى {_band_label(adj.get('to_band', ''))}"
                  f" — {adj.get('reason', '')}")

    # 9. Chain of custody
    pdf.section_title(9, "الملحق — سلسلة الحيازة")
    pdf.muted("كل اتصال خارجي، بالترتيب، مع نسب المصدر ووقته.")
    audit = context.get("audit", [])
    if audit:
        rows = [[a.get("tool", ""), a.get("source_category", ""), str(a.get("subject", "")),
                 "إصابة" if a.get("cache_hit") else "جلب", str(a.get("recorded_at", ""))[:19]]
                for a in audit]
        pdf.table(["الأداة", "المصدر", "الموضوع", "الذاكرة", "الوقت"], rows,
                  [0.18, 0.2, 0.24, 0.13, 0.25])
    pdf.muted(f"التفويض: موقّع من {roe.get('signed_by', '')}، ينتهي {str(roe.get('expires_at', ''))[:19]}.")
    validations = context.get("validations", [])
    if validations:
        pdf.prose("سجل تحقق المحلل:")
        rows = [[v.get("action", ""), v.get("analyst", ""), v.get("note", "") or "—",
                 str(v.get("recorded_at", ""))[:19]] for v in validations]
        pdf.table(["الإجراء", "المحلل", "ملاحظة", "الوقت"], rows, [0.2, 0.24, 0.31, 0.25])
    else:
        pdf.muted("⚠ لا يوجد تحقق من محلل — التقرير غير نهائي.")

    out = pdf.output()
    return bytes(out)
