"""
Tool Abstraction Layer (section 2.4).

Every external integration (WHOIS, crt.sh, Shodan, Censys, Nmap, VirusTotal,
...) subclasses `ReconTool`. This is where the non-negotiable controls live
so individual agents/tools cannot bypass them:

  1. auth gate     — AuthContext.assert_allows(classification, target, name)
  2. cache         — avoid re-querying slow-changing public sources
  3. rate limit    — per-source token bucket
  4. audit logging — chain of custody, including cache hits

Concrete tools (tools/whois_tool.py, tools/crtsh_tool.py, ...) are built in
week 2+; this file just establishes the contract every one of them follows.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict

from core.audit import audit_log
from core.authorization import AuthContext, Classification
from core.cache import cache
from core.rate_limit import RateBudget
from schemas.target import Target


class ToolResult(BaseModel):
    """Base class for tool outputs. Subclass per tool with typed fields
    (see e.g. the JSON examples in whitepaper sections 3.1-3.4)."""

    model_config = ConfigDict(extra="allow")

    def summary(self) -> dict[str, Any]:
        """
        Small, structured representation written to the audit log.
        Override in subclasses to avoid dumping large payloads into
        audit_log rows — e.g. counts/flags rather than full record lists.
        """
        return self.model_dump(mode="json")


class ReconTool(ABC):
    """
    Base class for every external data-source integration.

    Subclasses set the class attributes below and implement `run()`.
    `__call__` enforces auth/cache/rate-limit/audit around `run()` — do not
    override `__call__`.
    """

    name: str
    classification: Classification  # "passive" | "active" — drives the auth gate
    rate_limit: RateBudget
    cache_ttl: int = 3600  # seconds; tune per source (CT logs slow, TI fast)

    @abstractmethod
    async def run(self, target: Target, ctx: AuthContext) -> ToolResult:
        """Perform the actual external call. No auth/cache/rate-limit/audit
        here — `__call__` handles all of that."""
        ...

    def cache_key(self, target: Target) -> str:
        return f"{self.name}:{target.value}"

    async def __call__(self, target: Target, ctx: AuthContext) -> ToolResult:
        # 1. HARD GATE — raises AuthorizationError subclass if disallowed.
        ctx.assert_allows(self.classification, target.value, tool_name=self.name)

        # 2. Cache (politeness + cost control).
        cache_key = self.cache_key(target)
        if (cached := await cache.get(cache_key)) is not None:
            await audit_log.record(
                tool_name=self.name,
                classification=self.classification,
                target=target.value,
                job_id=ctx.job_id,
                summary={"cache_hit": True, **cached.summary()},
            )
            return cached

        # 3. Rate limit (per-source token bucket).
        await self.rate_limit.acquire()

        # 4. Run + audit (chain of custody) + cache the result.
        result = await self.run(target, ctx)
        await audit_log.record(
            tool_name=self.name,
            classification=self.classification,
            target=target.value,
            job_id=ctx.job_id,
            summary={"cache_hit": False, **result.summary()},
        )
        await cache.set(cache_key, result, ttl=self.cache_ttl)
        return result
