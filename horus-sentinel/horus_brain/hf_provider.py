"""Hugging Face online transport for the HORUS brain (master plan Part 4.3, online mode).

Calls the fine-tuned ``Horus-OSINT`` model hosted on Hugging Face, using the analyst's
token (collected by the first-run setup wizard). Two modes:

* ``serverless`` — the HF Inference router: ``router.huggingface.co/hf-inference/models/<id>``.
* ``endpoint``   — a dedicated Inference Endpoint URL the analyst deployed.

Both speak the Text-Generation-Inference (TGI) ``{"inputs", "parameters"}`` shape. Because
the model is a Llama-3 chat fine-tune, we apply the Llama-3 chat template ourselves so the
online transport behaves like the Ollama one (which applies it via the Modelfile).

Sovereignty note: this sends the (already-public) grounded facts to HF's cloud. For a
data-sovereign deployment use the Ollama transport — same Report Card, nothing leaves the box.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from core.config import settings
from horus_brain.prompting import (
    ReasoningInput,
    build_intel_prompt,
    offline_sections,
    split_sections,
    system_prompt,
)
from horus_brain.report_card import ReportCard

log = structlog.get_logger("horus.brain.hf")

_SERVERLESS_BASE = "https://router.huggingface.co/hf-inference/models"


def _llama3_chat(system: str, user: str) -> str:
    """Wrap system+user messages in the Llama-3 chat template TGI expects for a chat fine-tune."""
    return (
        "<|begin_of_text|>"
        "<|start_header_id|>system<|end_header_id|>\n\n"
        f"{system}<|eot_id|>"
        "<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user}<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>\n\n"
    )


class HFProvider:
    """Online HF transport. ``mode`` is 'serverless' or 'endpoint'."""

    def __init__(self, mode: str = "serverless") -> None:
        self.mode = mode
        self.model = settings.hf_model_id
        self.name = f"hf-{mode}:{self.model}"

    @property
    def endpoint(self) -> str:
        if self.mode == "endpoint":
            return settings.hf_endpoint_url.rstrip("/")
        return f"{_SERVERLESS_BASE}/{self.model}"

    def is_configured(self) -> bool:
        """True if this transport has what it needs to make a real call."""
        if not settings.hf_token:
            return False
        if self.mode == "endpoint":
            return bool(settings.hf_endpoint_url)
        return True

    async def reason(self, data: ReasoningInput) -> ReportCard:
        """Produce the narrative sections via the online model; offline-synthesis on failure."""
        raw = await self._generate(data)
        if raw is not None:
            sections = split_sections(raw)
            generated_by = f"{self.model} (HF {self.mode})"
        else:
            sections = offline_sections(data, settings.report_language)
            generated_by = "offline-synthesis"
            log.info("brain_offline_fallback", subject=data.subject, transport=self.name)
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

    async def _generate(self, data: ReasoningInput) -> str | None:
        """POST to the HF transport. Returns generated text, or None on any error."""
        if not self.is_configured():
            return None
        lang = settings.report_language
        prompt = _llama3_chat(system_prompt(lang), build_intel_prompt(data, lang))
        payload: dict[str, Any] = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": settings.hf_max_new_tokens,
                "temperature": settings.ollama_temperature,
                "return_full_text": False,
            },
            "options": {"wait_for_model": True},
        }
        headers = {"Authorization": f"Bearer {settings.hf_token}"}
        timeout = httpx.Timeout(settings.hf_timeout_s, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(self.endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                return _extract_text(resp.json())
        except (httpx.HTTPError, ValueError) as exc:
            log.info("hf_unreachable", error=str(exc), endpoint=self.endpoint, mode=self.mode)
            return None

    async def health(self) -> bool:
        """True if the HF transport is reachable and authorized (used by /health, setup)."""
        if not self.is_configured():
            return False
        headers = {"Authorization": f"Bearer {settings.hf_token}"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # A tiny generation is the only universal reachability probe across HF modes.
                resp = await client.post(
                    self.endpoint,
                    json={"inputs": "ping", "parameters": {"max_new_tokens": 1}},
                    headers=headers,
                )
                return resp.status_code < 500 and resp.status_code != 404
        except httpx.HTTPError:
            return False


def _extract_text(body: Any) -> str | None:
    """Pull generated text out of the several shapes HF transports return."""
    # TGI text-generation: [{"generated_text": "..."}]
    if isinstance(body, list) and body:
        first = body[0]
        if isinstance(first, dict) and "generated_text" in first:
            return str(first["generated_text"]).strip() or None
    if isinstance(body, dict):
        # Single dict: {"generated_text": "..."}  or an error payload.
        if "generated_text" in body:
            return str(body["generated_text"]).strip() or None
        # OpenAI-compatible chat shape (some endpoints): {"choices":[{"message":{"content"}}]}
        choices = body.get("choices")
        if isinstance(choices, list) and choices:
            msg = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
            content = msg.get("content") or choices[0].get("text")
            if content:
                return str(content).strip() or None
    return None
