"""
ORM models for the relational store (section 4.2):

- roe_records — every submitted RoE, signature + validity window + full JSON
- jobs        — one row per recon job, linked to the RoE it was authorized under
- audit_log   — chain-of-custody: every tool invocation against a target

`audit_log` is append-only by convention (core/audit.py only ever inserts).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class RoERecordORM(Base):
    __tablename__ = "roe_records"

    roe_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    client_name: Mapped[str] = mapped_column(String(255))
    authorized_by: Mapped[str] = mapped_column(String(255))
    contact_email: Mapped[str] = mapped_column(String(255))

    active_scanning_authorized: Mapped[bool]
    valid_from: Mapped[datetime]
    valid_until: Mapped[datetime]
    signature: Mapped[str] = mapped_column(String(64))

    # Full RoE payload (in_scope_assets, excluded_assets, allowed_active_tools,
    # notes, etc.) — stored verbatim for the audit appendix (section 8.1 #9).
    data: Mapped[dict] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(), server_default="CURRENT_TIMESTAMP"
    )

    jobs: Mapped[list[JobORM]] = relationship(back_populates="roe")


class JobORM(Base):
    __tablename__ = "jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    apex_domain: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")

    roe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roe_records.roe_id"))
    roe: Mapped[RoERecordORM] = relationship(back_populates="jobs")

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(), server_default="CURRENT_TIMESTAMP"
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(),
        server_default="CURRENT_TIMESTAMP",
        onupdate=lambda: datetime.now(),
    )


class AuditLogORM(Base):
    """
    One row per `ReconTool.__call__` invocation (section 2.4) —
    chain of custody for the report appendix (section 8.1 #9).
    """

    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_job_id_timestamp", "job_id", "timestamp"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    job_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    tool_name: Mapped[str] = mapped_column(String(64))
    classification: Mapped[str] = mapped_column(String(16))  # "passive" | "active"
    target: Mapped[str] = mapped_column(String(512))

    timestamp: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(), server_default="CURRENT_TIMESTAMP"
    )

    # Tool-provided summary (ToolResult.summary()) — small, structured.
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
