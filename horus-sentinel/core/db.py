"""Relational persistence — jobs, RoE, audit, findings (master plan Part 5 / Phase 1.4).

SQLAlchemy 2.0, synchronous. Defaults to a SQLite file so the platform runs with zero
infrastructure; point ``DATABASE_URL`` at Postgres for the full stack. Async callers
(tools, orchestrator) persist via ``anyio.to_thread.run_sync`` to avoid blocking the loop.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from core.config import settings


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


class JobRecord(Base):
    """One authorized assessment run."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    subject_json: Mapped[str] = mapped_column(Text)
    roe_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    report_path: Mapped[str | None] = mapped_column(String(512), default=None)
    validated_by: Mapped[str | None] = mapped_column(String(128), default=None)
    error: Mapped[str | None] = mapped_column(Text, default=None)

    audit_entries: Mapped[list[AuditRecord]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    findings: Mapped[list[FindingRecord]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    def subject(self) -> dict[str, Any]:
        return json.loads(self.subject_json)

    def roe(self) -> dict[str, Any]:
        return json.loads(self.roe_json)


class AuditRecord(Base):
    """Chain-of-custody: one row per external touch (master plan Part 2.4)."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    tool: Mapped[str] = mapped_column(String(64))
    source_category: Mapped[str] = mapped_column(String(32))
    subject_value: Mapped[str] = mapped_column(String(256))
    summary: Mapped[str] = mapped_column(Text)
    cache_hit: Mapped[bool] = mapped_column(default=False)
    signed_by: Mapped[str] = mapped_column(String(128))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)

    job: Mapped[JobRecord] = relationship(back_populates="audit_entries")


class AnalysisRecord(Base):
    """The reasoning artifact for a job: the Report Card + rendered graph (Phase 4/5)."""

    __tablename__ = "analysis"

    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), primary_key=True)
    report_card_json: Mapped[str] = mapped_column(Text)
    graph_json: Mapped[str] = mapped_column(Text, default="{}")
    generated_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ValidationRecord(Base):
    """The analyst's validation action — a report is not FINAL without one (Part 4.5)."""

    __tablename__ = "validation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    action: Mapped[str] = mapped_column(String(16))  # validate | flag | edit
    analyst: Mapped[str] = mapped_column(String(128))
    note: Mapped[str | None] = mapped_column(Text, default=None)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class FindingRecord(Base):
    """Persisted normalized finding (mirrors schemas.findings.Finding)."""

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    entity_kind: Mapped[str] = mapped_column(String(32), index=True)
    entity_value: Mapped[str] = mapped_column(String(512), index=True)
    attributes_json: Mapped[str] = mapped_column(Text, default="{}")
    related_to: Mapped[str | None] = mapped_column(String(512), default=None)
    relationship_label: Mapped[str | None] = mapped_column(String(64), default=None)
    produced_by: Mapped[str] = mapped_column(String(64))
    produced_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    job: Mapped[JobRecord] = relationship(back_populates="findings")


# SQLite needs check_same_thread off for the threadpool; other backends ignore it.
_connect_args = {"check_same_thread": False} if settings.sqlalchemy_url.startswith("sqlite") else {}
engine = create_engine(settings.sqlalchemy_url, future=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def init_db() -> None:
    """Create all tables. Idempotent — safe to call on startup."""
    Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Any]:
    """Transactional session context. Commits on success, rolls back on error."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
