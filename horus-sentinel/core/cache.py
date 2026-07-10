"""Cache abstraction — politeness toward public sources + the $5 cost story.

The Tool Abstraction Layer checks this before every external call and stores every
result, so re-querying a public source is a cache hit (master plan Part 2.4). In-memory
TTL implementation here; the same async interface fronts Redis in production.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any


class TTLCache:
    """A minimal async in-memory cache with per-entry TTL."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at < time.monotonic():
                self._store.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        async with self._lock:
            self._store[key] = (time.monotonic() + ttl, value)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()


# Process-wide default cache used by the Tool Abstraction Layer.
cache = TTLCache()
