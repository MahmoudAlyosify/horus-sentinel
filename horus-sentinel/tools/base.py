"""The Tool Abstraction Layer — where the non-negotiable operational controls live.

Every external source implements ``IntelTool`` and is invoked through ``__call__``, which
enforces — centrally, so no agent can bypass them (master plan Part 2.4):

  1. authorization  (``ctx.assert_allows`` — passive-only, source enabled, subject in scope)
  2. cache          (politeness toward public sources + the $5 cost story)
  3. rate limit     (per-source token bucket)
  4. audit          (chain-of-custody row for every touch)

Subclasses implement only ``run()`` — the actual, passive collection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import structlog

from core.audit import audit_log
from core.cache import cache
from core.rate_limit import RateBudget
from schemas.auth import AuthContext, AuthorizationError
from schemas.findings import ToolResult
from schemas.roe import Classification, SourceCategory
from schemas.subject import Subject

log = structlog.get_logger("horus.tool")


class IntelTool(ABC):
    """Base class for every passive collection tool.

    Class attributes declare the tool's identity and controls; ``run`` does the work.
    Everything is passive by construction — ``classification`` is fixed to PASSIVE.
    """

    name: str = "intel-tool"
    classification: Classification = Classification.PASSIVE
    source_category: SourceCategory
    cache_ttl: int = 3600  # seconds; public records change slowly

    def __init__(self, rate_limit: RateBudget | None = None) -> None:
        # Politeness default: ~2 requests/second per source unless a tool overrides it.
        self.rate_limit = rate_limit or RateBudget(rate=2.0, per=1.0)

    @abstractmethod
    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        """Perform the passive collection. Implemented by each concrete tool."""

    def cache_key(self, subject: Subject) -> str:
        return f"{self.name}:{subject.cache_key()}"

    async def __call__(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        """Run the tool through all four controls. This is the only public entry point."""
        # 1) Authorization — raises AuthorizationError if disallowed (by design).
        ctx.assert_allows(self.classification, self.source_category, subject)

        # 2) Cache — a repeat request is a cache hit; nothing leaves the process.
        key = self.cache_key(subject)
        cached = await cache.get(key)
        if cached is not None:
            result = cached.model_copy(update={"cached": True})
            await audit_log.record(self.name, self.source_category, subject, ctx, result)
            return result

        # 3) Rate limit — enforced centrally, so no tool can skip it.
        await self.rate_limit.acquire()

        # 4) Collect + audit + cache.
        try:
            result = await self.run(subject, ctx)
        except AuthorizationError:
            raise
        except Exception as exc:  # tools fail gracefully; a source outage must not kill a job
            log.warning("tool_run_failed", tool=self.name, subject=subject.value, error=str(exc))
            result = ToolResult(
                tool=self.name, source_category=self.source_category, error=str(exc)
            )

        await audit_log.record(self.name, self.source_category, subject, ctx, result)
        if result.error is None:
            await cache.set(key, result, ttl=self.cache_ttl)
        return result
