"""
Per-source rate limiting (section 2.4 / 4.1).

`RateBudget` is a simple async token bucket. Each `ReconTool` subclass
declares its own budget (e.g. crt.sh: 1 req/sec, Shodan: per their plan
limits) so a single slow/abusive source can't starve the others and so
ARGUS stays a polite citizen of third-party APIs/ToS.

This is in-memory and per-process for week 1. Once the Redis-backed task
queue lands (week 3+), this gets a Redis-backed implementation behind the
same interface so budgets are shared across worker processes — agents and
tools should depend on the `RateBudget` interface, not this implementation.
"""

from __future__ import annotations

import asyncio
import time


class RateBudget:
    """Token bucket: `rate` tokens/second, holding at most `burst` tokens."""

    def __init__(self, rate: float, burst: float | None = None) -> None:
        if rate <= 0:
            raise ValueError("rate must be > 0")
        self.rate = rate
        self.burst = burst if burst is not None else max(1.0, rate)
        self._tokens = self.burst
        self._updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._updated_at
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._updated_at = now

    async def acquire(self, tokens: float = 1.0) -> None:
        """Block until `tokens` are available, then consume them."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                deficit = tokens - self._tokens
                wait_for = deficit / self.rate
            await asyncio.sleep(wait_for)
