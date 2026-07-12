"""Brain selector — chooses the transport(s) that author the Report Card narrative.

``brain_backend`` (config) selects the strategy:

* ``hybrid``        → HF online (serverless, then dedicated endpoint if set), then Ollama,
                      then deterministic offline synthesis. Best of both: online when it can,
                      sovereign self-hosted when it must.
* ``hf_serverless`` → HF Inference router only.
* ``hf_endpoint``   → a dedicated HF Inference Endpoint only.
* ``ollama``        → self-hosted Ollama only (nothing leaves the box).

Every transport already degrades to grounded offline synthesis on its own, so a job always
returns a Report Card. The hybrid chain simply prefers a *model-authored* card: it walks the
configured transports and returns the first one whose narrative actually came from a model.
"""

from __future__ import annotations

import structlog

from core.config import settings
from horus_brain.prompting import ReasoningInput
from horus_brain.report_card import ReportCard

log = structlog.get_logger("horus.brain.select")


def _is_model_authored(card: ReportCard) -> bool:
    return card.generated_by != "offline-synthesis"


class Brain:
    """Runtime brain dispatcher. Reads ``settings.brain_backend`` on every call so a token
    saved by the setup wizard takes effect without a restart."""

    async def reason(self, data: ReasoningInput) -> ReportCard:
        transports = self._transports()
        last: ReportCard | None = None
        for transport in transports:
            card = await transport.reason(data)
            if _is_model_authored(card):
                if transport is not transports[0]:
                    log.info("brain_transport_used", transport=getattr(transport, "name", "?"))
                return card
            last = card
        # Nothing model-authored — return the last grounded offline card (always present).
        return last if last is not None else await self._offline_only(data)

    async def health(self) -> dict[str, bool]:
        """Reachability of each configured transport (used by /health and setup status)."""
        out: dict[str, bool] = {}
        for transport in self._transports():
            name = getattr(transport, "name", transport.__class__.__name__)
            health = getattr(transport, "health", None)
            out[name] = bool(await health()) if health else False
        return out

    def active_backend(self) -> str:
        return settings.brain_backend

    @property
    def endpoint(self) -> str:
        """The Ollama generate URL of the local transport.

        Kept so callers/tests that mock the self-hosted endpoint keep working when they hold
        the dispatcher rather than the concrete Ollama provider.
        """
        return f"{settings.ollama_endpoint.rstrip('/')}/api/generate"

    def _transports(self) -> list:
        """Build the ordered transport chain for the active backend (lazy imports)."""
        from horus_brain.hf_provider import HFProvider
        from horus_brain.horus_provider import HorusReasoningProvider

        backend = settings.brain_backend
        if backend == "ollama":
            return [HorusReasoningProvider()]
        if backend == "hf_serverless":
            return [HFProvider("serverless")]
        if backend == "hf_endpoint":
            return [HFProvider("endpoint")]
        # hybrid (default): HF serverless → HF endpoint (if set) → Ollama.
        chain: list = []
        serverless = HFProvider("serverless")
        if serverless.is_configured():
            chain.append(serverless)
        endpoint = HFProvider("endpoint")
        if endpoint.is_configured():
            chain.append(endpoint)
        chain.append(HorusReasoningProvider())
        return chain

    async def _offline_only(self, data: ReasoningInput) -> ReportCard:
        from horus_brain.horus_provider import HorusReasoningProvider

        return await HorusReasoningProvider().reason(data)


_BRAIN = Brain()


def get_brain() -> Brain:
    """The process-wide brain dispatcher."""
    return _BRAIN
