"""
FastAPI app entrypoint.

Run locally with:  uvicorn api.main:app --reload
Or via Docker:     docker compose up
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import health, jobs
from db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="ARGUS — Autonomous Reconnaissance & Ground-truth Understanding System",
    description=(
        "Multi-agent EASM platform. Every active operation is gated behind "
        "the Scope & Authorization Engine — passive-by-default, "
        "active-by-exception."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(jobs.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "ARGUS", "status": "ok", "docs": "/docs"}
