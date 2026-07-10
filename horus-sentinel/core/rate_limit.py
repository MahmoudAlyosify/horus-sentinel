"""Per-source rate budgets — a token-bucket the Tool Abstraction Layer enforces centrally.

Design invariant (master plan Part 2.2 #2): no agent can skip the rate limit because it
lives in the shared tool wrapper, not in each tool. In-memory here (fine for a single-node
competition build); a Redis-backed bucket can drop in behind the same interface for prod.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class RateBudget:
    """A simple async token-bucket. ``rate`` tokens refill per ``per`` seconds."""

    rate: float = 5.0  # tokens
    per: float = 1.0  # seconds
    capacity: float | None = None  # burst size; defaults to ``rate``
    _tokens: float = field(default=0.0, init=False)
    _updated: float = field(default_factory=time.monotonic, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        cap = self.capacity if self.capacity is not None else self.rate
        self.capacity = cap
        self._tokens = cap

    async def acquire(self, tokens: float = 1.0) -> None:
        """Block until ``tokens`` are available, then consume them."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                deficit = tokens - self._tokens
                wait = deficit * self.per / self.rate
            await asyncio.sleep(max(wait, 0.001))

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._updated
        self._updated = now
        assert self.capacity is not None
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate / self.per)

    @property
    def available(self) -> float:
        self._refill()
        return self._tokens
