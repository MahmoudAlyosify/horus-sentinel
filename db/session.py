"""
Async SQLAlchemy engine + session factory.

For week 1 we use `Base.metadata.create_all` on startup instead of Alembic —
fine for the MVP/local-dev loop. Alembic migrations are a "week 8 polish"
item (section 9, week 8) once the schema has settled.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings
from db.base import Base

engine = create_async_engine(settings.database_url, echo=False, future=True)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db() -> None:
    """Create all tables if they don't exist. Called from the app lifespan."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a transactional session per request."""
    async with async_session_factory() as session:
        yield session
