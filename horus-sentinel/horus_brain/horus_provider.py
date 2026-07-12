"""The provider bridge — wraps the self-hosted fine-tuned model (master plan Part 4.3).

``HorusReasoningProvider`` is the **Ollama** transport: it turns grounded facts (a subgraph
+ retrieved framework context) into the *prose* sections of the Report Card by calling the
Ollama-served fine-tuned model (VPC-internal, port 11434). If the model is unreachable it
falls back to a deterministic, still-grounded synthesis so the pipeline runs anywhere.

The online Hugging Face transport lives in ``horus_brain.hf_provider``; the runtime picks a
transport (or a hybrid chain) in ``horus_brain.brain``. The model never invents entities or
scores — those come from the graph and the risk engine (invariants #4/#5).
"""

from __future__ import annotations

import httpx
import structlog

from core.config import settings
from horus_brain.prompting import (
    ReasoningInput,
    build_intel_prompt,
    offline_sections,
    split_sections,
)
from horus_brain.report_card import ReportCard

log = structlog.get_logger("horus.brain")

# Re-exported for backwards compatibility (tests + callers import these here).
_split_sections = split_sections

__all__ = ["HorusReasoningProvider", "ReasoningInput", "_split_sections", "horus_provider"]


class HorusReasoningProvider:
    """Wraps the fine-tuned Llama-3-8B served by Ollama. Same Report Card DNA, graph-grounded."""

    name = "horus-selfhosted"

    def __init__(self) -> None:
        self.endpoint = f"{settings.ollama_endpoint.rstrip('/')}/api/generate"
        self.model = settings.horus_model_name

    async def reason(self, data: ReasoningInput) -> ReportCard:
        """Produce the narrative sections of the Report Card (findings attached upstream)."""
        prompt = self.build_intel_prompt(data)
        raw = await self._call_ollama(prompt)
        if raw is not None:
            sections = split_sections(raw)
            generated_by = self.model
        else:
            sections = offline_sections(data, settings.report_language)
            generated_by = "offline-synthesis"
            log.info("brain_offline_fallback", subject=data.subject, transport="ollama")
        return _card_from_sections(data, generated_by, sections)

    def build_intel_prompt(self, data: ReasoningInput) -> str:
        """Structured, grounded prompt (language from settings.report_language)."""
        return build_intel_prompt(data, settings.report_language)

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


def _card_from_sections(
    data: ReasoningInput, generated_by: str, sections: dict[str, str]
) -> ReportCard:
    """Assemble a ReportCard from split narrative sections + headline metrics."""
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


# Process-wide brain. A lazy hybrid dispatcher (HF online → Ollama → offline synthesis),
# selected by settings.brain_backend. Imported late to avoid a circular import.
from horus_brain.brain import get_brain  # noqa: E402

horus_provider = get_brain()
