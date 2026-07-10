"""The provider bridge — wraps the self-hosted fine-tuned model (master plan Part 4.3).

``HorusReasoningProvider`` turns grounded facts (a subgraph + retrieved framework context)
into the *prose* sections of the Report Card. It calls the Ollama-served fine-tuned model
when reachable (VPC-internal, port 11434); if the model is unreachable it falls back to a
deterministic, still-grounded synthesis so the pipeline runs end-to-end anywhere.

The model never invents entities or scores — those come from the graph and the risk engine
(invariant #4/#5). The model synthesizes and explains what the eyes already saw.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
import structlog

from core.config import settings
from horus_brain.report_card import ReportCard

log = structlog.get_logger("horus.brain")


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


class HorusReasoningProvider:
    """Wraps the fine-tuned Llama-3-8B served by Ollama. Same Report Card DNA, graph-grounded."""

    name = "horus-selfhosted"

    def __init__(self) -> None:
        self.endpoint = f"{settings.ollama_endpoint.rstrip('/')}/api/generate"
        self.model = settings.horus_model_name

    async def reason(self, data: ReasoningInput) -> ReportCard:
        """Produce the narrative sections of the Report Card (findings are attached upstream)."""
        prompt = self.build_intel_prompt(data)
        raw = await self._call_ollama(prompt)
        if raw is not None:
            sections = _split_sections(raw)
            generated_by = self.model
        else:
            sections = _offline_sections(data)
            generated_by = "offline-synthesis"
            log.info("brain_offline_fallback", subject=data.subject)

        return ReportCard(
            subject=data.subject,
            generated_by=generated_by,
            executive_summary=sections["executive_summary"],
            geopolitical_context=sections["geopolitical_context"],
            threat_assessment=sections["threat_assessment"],
            conclusion=sections["conclusion"],
            entity_count=data.entity_count,
            top_band=data.top_band,
            critical_cve_hits=data.critical_cve_hits,
        )

    def build_intel_prompt(self, data: ReasoningInput) -> str:
        """Structured, grounded prompt asking for the four narrative sections."""
        facts = "\n".join(f"- {f}" for f in data.facts)
        return (
            "You are HORUS, an intelligence analyst. Using ONLY the grounded facts and "
            "framework context below, write a concise intelligence report card. Do not "
            "invent entities or numbers. Output exactly four sections with these headers:\n"
            "EXECUTIVE SUMMARY:\nGEOPOLITICAL CONTEXT:\nTHREAT ASSESSMENT:\nCONCLUSION:\n\n"
            f"SUBJECT: {data.subject}\n"
            f"HEADLINE: {data.entity_count} entities, top risk band {data.top_band}, "
            f"{data.critical_cve_hits} critical-CVE exposure(s).\n\n"
            f"GROUNDED FACTS:\n{facts}\n\n"
            f"FRAMEWORK CONTEXT (retrieved):\n{data.rag_context}\n"
        )

    async def _call_ollama(self, prompt: str) -> str | None:
        """Call the Ollama generate endpoint. Returns None on any error (triggers fallback)."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": settings.ollama_temperature},
        }
        # Short connect timeout so an absent server falls back fast (good demo UX); a long
        # read timeout so a real generation has time to finish.
        timeout = httpx.Timeout(settings.ollama_timeout_s, connect=5.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(self.endpoint, json=payload)
                resp.raise_for_status()
                return str(resp.json().get("response", "")).strip() or None
        except (httpx.HTTPError, ValueError) as exc:
            log.info("ollama_unreachable", error=str(exc), endpoint=self.endpoint)
            return None

    async def health(self) -> bool:
        """True if the Ollama server responds to a tags query (used by /health)."""
        base = settings.ollama_endpoint.rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{base}/api/tags")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False


# ---- section handling -------------------------------------------------------

_HEADERS = {
    "executive_summary": ("EXECUTIVE SUMMARY", "EXECUTIVE_SUMMARY"),
    "geopolitical_context": ("GEOPOLITICAL CONTEXT", "GEOPOLITICAL_CONTEXT"),
    "threat_assessment": ("THREAT ASSESSMENT", "THREAT_ASSESSMENT"),
    "conclusion": ("CONCLUSION",),
}


def _split_sections(raw: str) -> dict[str, str]:
    """Best-effort split of the model's text into the four known sections."""
    result = dict.fromkeys(_HEADERS, "")
    lines = raw.splitlines()
    current: str | None = None
    buffer: dict[str, list[str]] = {k: [] for k in _HEADERS}
    for line in lines:
        stripped = line.strip()
        matched = _match_header(stripped)
        if matched:
            current = matched
            # keep any inline text after the header colon
            after = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            if after:
                buffer[current].append(after)
            continue
        if current:
            buffer[current].append(line)
    for key in result:
        result[key] = "\n".join(buffer[key]).strip()
    # If nothing matched, dump everything into the executive summary.
    if not any(result.values()):
        result["executive_summary"] = raw.strip()
    return result


def _match_header(line: str) -> str | None:
    upper = line.upper()
    for key, variants in _HEADERS.items():
        for v in variants:
            if upper.startswith(v):
                return key
    return None


def _offline_sections(data: ReasoningInput) -> dict[str, str]:
    """Deterministic, grounded narrative when the model is unreachable."""
    facts = " ".join(data.facts) if data.facts else "No collected facts available."
    geo_facts = [f for f in data.facts if "instability" in f.lower() or "modalit" in f.lower()]
    return {
        "executive_summary": (
            f"Assessment of {data.subject}: {data.entity_count} entities correlated into the "
            f"intelligence graph, with a top risk band of {data.top_band} and "
            f"{data.critical_cve_hits} critical-CVE exposure(s). "
            "This is an automated grounded synthesis pending model-backed narration."
        ),
        "geopolitical_context": (
            " ".join(geo_facts)
            if geo_facts
            else "No geopolitical event context was in scope for this subject."
        ),
        "threat_assessment": (
            f"Findings for {data.subject} were correlated and risk-scored deterministically. "
            f"Key grounded facts: {facts}"
        ),
        "conclusion": (
            f"Prioritized findings and recommendations for {data.subject} follow, each mapped "
            "to an established framework and traceable to source evidence. Analyst validation "
            "is required before this report is final."
        ),
    }


# Process-wide provider instance.
horus_provider = HorusReasoningProvider()
