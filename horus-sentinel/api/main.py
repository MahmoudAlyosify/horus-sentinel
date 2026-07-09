"""HORUS Sentinel — API entry point.

Day-1 skeleton: a health endpoint that confirms the app runs.
Job submission (POST /jobs) arrives in Phase 1.
"""
from __future__ import annotations

from fastapi import FastAPI

from core.config import settings

app = FastAPI(
    title="HORUS Sentinel",
    description="Autonomous multi-agent OSINT & threat-intelligence platform.",
    version="0.1.0",
)


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
