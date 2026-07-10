"""Async job worker (master plan Phase 5.2).

Pulls job ids off the queue and runs the checkpointed pipeline with ``resume=True`` — so a
job that was killed mid-run continues from where it stopped rather than restarting. Runs
as a standalone process (``python -m workflows.worker``) or in-process on API startup when
``WORKER_ENABLED=true``.
"""

from __future__ import annotations

import asyncio

import structlog

from core.config import settings
from core.db import init_db
from core.queue import RedisJobQueue, job_queue
from schemas.state import JobStatus
from workflows.orchestrator import orchestrator

log = structlog.get_logger("horus.worker")


class Worker:
    """Consumes jobs from the queue and runs them to the validation checkpoint."""

    def __init__(self) -> None:
        self._stop = asyncio.Event()

    async def process_one(self, timeout: float | None = None) -> str | None:
        """Pull one job and run it (resumable). Returns the processed job id, or None on idle."""
        job_id = await job_queue.dequeue(timeout or settings.worker_poll_timeout)
        if job_id is None:
            return None
        try:
            summary = await orchestrator.run(job_id, resume=True)
            log.info(
                "worker_job_done",
                job_id=job_id,
                status=summary.status,
                ran=summary.agents_run,
                skipped=summary.skipped_stages,
            )
        except Exception as exc:
            log.warning("worker_job_failed", job_id=job_id, error=str(exc))
        finally:
            await job_queue.ack(job_id)
        return job_id

    async def run_forever(self) -> None:
        """Loop until stopped, processing jobs as they arrive."""
        init_db()
        # Crash recovery: return any in-flight ids from a previous run to the queue.
        if isinstance(job_queue, RedisJobQueue):
            moved = await job_queue.requeue_stale()
            if moved:
                log.info("requeued_stale_jobs", count=moved)
        log.info("worker_started", backend=settings.queue_backend)
        while not self._stop.is_set():
            await self.process_one()

    def stop(self) -> None:
        self._stop.set()


async def enqueue_job(job_id: str) -> None:
    """Submit a job id for asynchronous processing."""
    await job_queue.enqueue(job_id)


# Terminal statuses a worker should not re-run.
_TERMINAL = {JobStatus.COMPLETED.value, JobStatus.REJECTED.value}


def main() -> None:
    """Standalone entry point: ``python -m workflows.worker``."""
    worker = Worker()
    try:
        asyncio.run(worker.run_forever())
    except KeyboardInterrupt:
        log.info("worker_stopped")


if __name__ == "__main__":
    main()
