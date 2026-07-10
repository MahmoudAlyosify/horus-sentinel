"""Job queue abstraction (master plan Phase 5.2).

Decouples job submission from execution so workers can pull and run assessments — and, with
Postgres stage-checkpointing, resume a job after a mid-run kill. Two interchangeable
backends behind one async interface:

* ``InMemoryJobQueue`` — an ``asyncio.Queue`` (default; zero-dep, used in tests and the MVP).
* ``RedisJobQueue`` — a reliable Redis list (``LPUSH`` + ``BRPOPLPUSH`` into a processing
  list for at-least-once delivery). The ``redis`` package is imported lazily.

The rest of the system depends only on ``JobQueue``; the backend is chosen by settings.
"""

from __future__ import annotations

import asyncio
from typing import Protocol

import structlog

from core.config import settings

log = structlog.get_logger("horus.queue")


class JobQueue(Protocol):
    async def enqueue(self, job_id: str) -> None: ...
    async def dequeue(self, timeout: float) -> str | None: ...
    async def ack(self, job_id: str) -> None: ...
    async def size(self) -> int: ...


class InMemoryJobQueue:
    """A process-local queue backed by ``asyncio.Queue``. Perfect for the MVP and tests."""

    def __init__(self) -> None:
        self._q: asyncio.Queue[str] = asyncio.Queue()

    async def enqueue(self, job_id: str) -> None:
        await self._q.put(job_id)
        log.info("job_enqueued", job_id=job_id, backend="memory")

    async def dequeue(self, timeout: float) -> str | None:
        try:
            return await asyncio.wait_for(self._q.get(), timeout=timeout)
        except TimeoutError:
            return None

    async def ack(self, job_id: str) -> None:
        # asyncio.Queue has no processing list; task is done once dequeued.
        return None

    async def size(self) -> int:
        return self._q.qsize()


class RedisJobQueue:
    """A Redis-list queue with at-least-once semantics via a processing list."""

    def __init__(self, url: str, name: str) -> None:
        import redis.asyncio as redis  # lazy: keep the module importable without redis

        self._redis = redis.from_url(url, decode_responses=True)
        self._name = name
        self._processing = f"{name}:processing"

    async def enqueue(self, job_id: str) -> None:
        await self._redis.lpush(self._name, job_id)
        log.info("job_enqueued", job_id=job_id, backend="redis")

    async def dequeue(self, timeout: float) -> str | None:
        # Reliable pop: move the id to a processing list so a crash doesn't lose it.
        job_id: str | None = await self._redis.brpoplpush(
            self._name, self._processing, timeout=int(timeout)
        )
        return job_id

    async def ack(self, job_id: str) -> None:
        await self._redis.lrem(self._processing, 1, job_id)

    async def requeue_stale(self) -> int:
        """Move any ids left in the processing list back to the main queue (crash recovery)."""
        moved = 0
        while (await self._redis.rpoplpush(self._processing, self._name)) is not None:
            moved += 1
        return moved

    async def size(self) -> int:
        return int(await self._redis.llen(self._name))


def _build_queue() -> JobQueue:
    if settings.queue_backend.lower() == "redis":
        try:
            q = RedisJobQueue(settings.redis_url, settings.queue_name)
            log.info("queue_backend", backend="redis")
            return q
        except Exception as exc:  # redis missing / bad url -> in-memory fallback
            log.warning("redis_queue_unavailable_fallback_memory", error=str(exc))
    return InMemoryJobQueue()


# Process-wide queue instance (lazily importable; safe without redis installed).
job_queue: JobQueue = _build_queue()
