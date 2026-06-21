"""
Tool-result cache (section 2.4 / 4.1).

In-memory + per-process for week 1, behind the same get/set/ttl interface
the Redis-backed implementation will use once Redis is wired in for the
task queue (week 3+). Purpose: avoid re-querying slow-changing public
sources (CT logs, WHOIS) within `cache_ttl`, per ReconTool.
"""

from __future__ import annotations

import time
from typing import Any


class ToolCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        self._store[key] = (time.monotonic() + ttl, value)

    async def clear(self) -> None:
        """Test helper — not used in production code paths."""
        self._store.clear()


cache = ToolCache()
