"""HORUS Sentinel — API entry point.

Exposes the Control Plane: a health probe plus job submission/retrieval. Submitting a
job runs it through the Authorization Engine first (a disallowed request is refused with
a 403), then persists it. Collection and reasoning are driven by the orchestrator.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router as jobs_router
from core.config import settings
from core.db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create tables on startup so the platform runs with zero manual DB setup."""
    init_db()
    yield


app = FastAPI(
    title="HORUS Sentinel",
    description="Autonomous multi-agent OSINT & threat-intelligence platform.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(jobs_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {
        "status": "ok",
        "service": "horus-sentinel",
        "env": settings.app_env,
        "brain_model": settings.horus_model_name,
    }


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    """Root — points to the interactive docs."""
    return {
        "message": "HORUS Sentinel API. See /docs for the interactive API.",
        "tagline": "ARGUS's hundred eyes gather; the Eye of HORUS judges.",
    }
