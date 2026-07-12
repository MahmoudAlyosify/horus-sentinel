"""Shared, language-aware prompt building + section handling for every brain provider.

The fine-tuned model authors the *prose* sections of the Report Card; providers (Ollama,
Hugging Face) differ only in transport. The prompt, the section splitter, and the offline
synthesis live here so all providers stay consistent — and so Arabic vs. English output is
a single switch (``report_language``), not a per-provider fork.

Design choice: even for Arabic output we keep the four **section anchors in English**
(``EXECUTIVE SUMMARY:`` …). The model writes the *content* in Arabic, but the anchors stay
machine-stable so ``split_sections`` is language-independent and never mis-parses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ReasoningInput:
    """Everything the brain needs to author the narrative — all of it grounded."""

    subject: str
    subgraph: dict[str, Any]
    rag_context: str
    entity_count: int
    top_band: str
    critical_cve_hits: int
    facts: list[str]  # short, human-readable grounded facts for the prompt
    # "defensive" (passive OSINT) or "offensive" (authorized active reconnaissance ran).
    mode: str = "defensive"


# The four narrative sections, keyed to the English anchors the splitter looks for.
_HEADERS: dict[str, tuple[str, ...]] = {
    "executive_summary": ("EXECUTIVE SUMMARY", "EXECUTIVE_SUMMARY"),
    "geopolitical_context": ("GEOPOLITICAL CONTEXT", "GEOPOLITICAL_CONTEXT"),
    "threat_assessment": ("THREAT ASSESSMENT", "THREAT_ASSESSMENT"),
    "conclusion": ("CONCLUSION",),
}

_SYSTEM_EN = (
    "You are HORUS, a senior open-source intelligence analyst. You reason ONLY over the "
    "grounded facts and framework context you are given. You never invent entities, "
    "numbers, or sources."
)
_SYSTEM_AR = (
    "أنت حورس، محلل استخبارات مفتوحة المصدر خبير. تحلّل فقط بالاعتماد على الحقائق المُثبَتة "
    "وسياق الأطر المرجعية المُعطاة لك. لا تختلق كيانات أو أرقامًا أو مصادر."
)


def system_prompt(language: str) -> str:
    """The system message for the given language."""
    return _SYSTEM_AR if language == "ar" else _SYSTEM_EN


_CHAT_SYSTEM_EN = (
    "You are HORUS, a senior geopolitical and open-source intelligence analyst. Answer the "
    "user's question directly, concisely, and professionally in English. State uncertainty "
    "plainly — if you are not sure, say so. Do not fabricate specific figures, dates, or "
    "sources you are not confident about."
)
_CHAT_SYSTEM_AR = (
    "أنت حورس، محلل استخبارات جيوسياسية ومفتوحة المصدر خبير. أجب عن سؤال المستخدم مباشرةً "
    "وبإيجاز ومهنية باللغة العربية الفصحى. وضّح درجة اليقين بصراحة — وإن لم تكن متأكدًا فقل "
    "ذلك. لا تختلق أرقامًا أو تواريخ أو مصادر لست واثقًا منها."
)


def chat_system_prompt(language: str) -> str:
    """System message for the free-form conversational (chat) mode."""
    return _CHAT_SYSTEM_AR if language == "ar" else _CHAT_SYSTEM_EN


def build_intel_prompt(data: ReasoningInput, language: str = "ar") -> str:
    """Structured, grounded instruction asking for the four narrative sections.

    Returns the *user* message. Providers wrap it with ``system_prompt`` as needed.
    """
    facts = "\n".join(f"- {f}" for f in data.facts)
    offensive = getattr(data, "mode", "defensive") == "offensive"
    if language == "ar":
        frame = (
            "هذا تقرير استطلاع هجومي مُصرّح به (المرحلة الأولى من ATT&CK — الاستطلاع TA0043). "
            "ركّز على سطح الهجوم المكتشف (المنافذ المفتوحة، الخدمات، نقاط النهاية) وما قد يفعله "
            "الخصم تاليًا، مع توصيات دفاعية. لا تصف أي استغلال فعلي — الاستطلاع فقط. "
            if offensive
            else ""
        )
        return (
            "باستخدام الحقائق المُثبَتة وسياق الأطر أدناه فقط، اكتب بطاقة تقرير استخباراتي "
            f"موجزة ومهنية. {frame}لا تختلق كيانات أو أرقامًا. اكتب محتوى كل قسم باللغة العربية "
            "الفصحى، لكن أبقِ عناوين الأقسام بالإنجليزية تمامًا كما هي أدناه (أربعة أقسام):\n"
            "EXECUTIVE SUMMARY:\nGEOPOLITICAL CONTEXT:\nTHREAT ASSESSMENT:\nCONCLUSION:\n\n"
            f"الموضوع: {data.subject}\n"
            f"العنوان الرئيسي: {data.entity_count} كيانًا، أعلى نطاق خطورة {data.top_band}، "
            f"عدد الثغرات الحرجة المكشوفة: {data.critical_cve_hits}.\n\n"
            f"الحقائق المُثبَتة:\n{facts}\n\n"
            f"سياق الأطر المرجعية (مُسترجَع):\n{data.rag_context}\n"
        )
    frame = (
        "This is an AUTHORIZED offensive-reconnaissance report (ATT&CK TA0043 Reconnaissance). "
        "Focus on the discovered attack surface (open ports, services, endpoints) and what an "
        "adversary could do next, with defensive recommendations. Describe NO actual "
        "exploitation — reconnaissance only. "
        if offensive
        else ""
    )
    return (
        "Using ONLY the grounded facts and framework context below, write a concise "
        f"intelligence report card. {frame}Do not invent entities or numbers. Output exactly "
        "four sections with these headers:\n"
        "EXECUTIVE SUMMARY:\nGEOPOLITICAL CONTEXT:\nTHREAT ASSESSMENT:\nCONCLUSION:\n\n"
        f"SUBJECT: {data.subject}\n"
        f"HEADLINE: {data.entity_count} entities, top risk band {data.top_band}, "
        f"{data.critical_cve_hits} critical-CVE exposure(s).\n\n"
        f"GROUNDED FACTS:\n{facts}\n\n"
        f"FRAMEWORK CONTEXT (retrieved):\n{data.rag_context}\n"
    )


def split_sections(raw: str) -> dict[str, str]:
    """Best-effort split of the model's text into the four known sections (anchors in EN)."""
    result = dict.fromkeys(_HEADERS, "")
    buffer: dict[str, list[str]] = {k: [] for k in _HEADERS}
    current: str | None = None
    for line in raw.splitlines():
        stripped = line.strip()
        matched = _match_header(stripped)
        if matched:
            current = matched
            after = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            if after:
                buffer[current].append(after)
            continue
        if current:
            buffer[current].append(line)
    for key in result:
        result[key] = "\n".join(buffer[key]).strip()
    if not any(result.values()):
        result["executive_summary"] = raw.strip()
    return result


def _match_header(line: str) -> str | None:
    upper = line.upper().lstrip("#* ").strip()
    for key, variants in _HEADERS.items():
        for v in variants:
            if upper.startswith(v):
                return key
    return None


def offline_sections(data: ReasoningInput, language: str = "ar") -> dict[str, str]:
    """Deterministic, grounded narrative when no model is reachable (Arabic or English)."""
    facts = " ".join(data.facts) if data.facts else ""
    geo_facts = [f for f in data.facts if "instability" in f.lower() or "modalit" in f.lower()]
    if language == "ar":
        return {
            "executive_summary": (
                f"تقييم {data.subject}: تم ربط {data.entity_count} كيانًا داخل رسم المعرفة "
                f"الاستخباراتي، بأعلى نطاق خطورة {data.top_band} و{data.critical_cve_hits} "
                "ثغرة حرجة مكشوفة. هذا تركيب آلي مُستند إلى الأدلة، في انتظار السرد المدعوم "
                "بالنموذج."
            ),
            "geopolitical_context": (
                " ".join(geo_facts)
                if geo_facts
                else "لا يوجد سياق أحداث جيوسياسية ضمن نطاق هذا الموضوع."
            ),
            "threat_assessment": (
                f"تم ربط النتائج الخاصة بـ {data.subject} وتسجيل درجات الخطورة بشكل حتمي. "
                + (f"أبرز الحقائق المُثبَتة: {facts}" if facts else "لا توجد حقائق مجمَّعة متاحة.")
            ),
            "conclusion": (
                f"تلي ذلك النتائج ذات الأولوية والتوصيات الخاصة بـ {data.subject}، كلٌّ منها "
                "مربوط بإطار مرجعي مُعتمَد وقابل للتتبع إلى أدلة مصدرية. يلزم تحقُّق المحلل "
                "قبل اعتماد هذا التقرير نهائيًا."
            ),
        }
    return {
        "executive_summary": (
            f"Assessment of {data.subject}: {data.entity_count} entities correlated into the "
            f"intelligence graph, with a top risk band of {data.top_band} and "
            f"{data.critical_cve_hits} critical-CVE exposure(s). This is an automated grounded "
            "synthesis pending model-backed narration."
        ),
        "geopolitical_context": (
            " ".join(geo_facts)
            if geo_facts
            else "No geopolitical event context was in scope for this subject."
        ),
        "threat_assessment": (
            f"Findings for {data.subject} were correlated and risk-scored deterministically. "
            + (f"Key grounded facts: {facts}" if facts else "No collected facts available.")
        ),
        "conclusion": (
            f"Prioritized findings and recommendations for {data.subject} follow, each mapped "
            "to an established framework and traceable to source evidence. Analyst validation "
            "is required before this report is final."
        ),
    }
