"""
Test setup.

Uses a throwaway SQLite file (via aiosqlite) instead of Postgres so the
authorization-engine/API tests can run without docker-compose. Postgres-
specific behavior isn't exercised here — that's covered by hitting the
real stack via docker-compose for manual/integration testing.
"""

from __future__ import annotations

import os
import pathlib

TEST_DB_PATH = pathlib.Path(__file__).parent / "test_argus.db"

# Must be set BEFORE core.config / db.session are imported anywhere,
# since `settings = Settings()` and `engine = create_async_engine(...)`
# both execute at import time.
os.environ["ARGUS_DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ["ARGUS_ROE_SIGNING_KEY"] = "test-signing-key"

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from api.main import app  # noqa: E402
from db.session import engine, init_db  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _fresh_db():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    await init_db()
    yield
    await engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
