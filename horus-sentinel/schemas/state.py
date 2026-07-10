"""SentinelState — the shared state object carried through the LangGraph workflow.

Per master plan Part 2.3, the state carries the ``job_id``, the ``AuthContext``, and
*lightweight references* — not big data blobs. Agents write normalized findings to the
Knowledge Plane and record only counts/keys here, keeping every transition small,
resumable, and auditable.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, TypedDict

from schemas.auth import AuthContext
from schemas.subject import Subject


class JobStatus(StrEnum):
    """Lifecycle of a Sentinel job."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    AWAITING_VALIDATION = "awaiting_validation"
    REPORTING = "reporting"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


def _merge_counts(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    """Reducer: sum per-agent finding counts as parallel branches converge."""
    merged = dict(left)
    for key, value in right.items():
        merged[key] = merged.get(key, 0) + value
    return merged


def _extend(left: list[str], right: list[str]) -> list[str]:
    """Reducer: concatenate log lines from converging branches."""
    return [*left, *right]


class SentinelState(TypedDict, total=False):
    """The LangGraph state. ``total=False`` so nodes can populate incrementally."""

    job_id: str
    subject: Subject
    auth: AuthContext
    status: JobStatus
    # Lightweight references only — the graph/DB hold the actual data.
    finding_counts: Annotated[dict[str, int], _merge_counts]
    entity_keys: Annotated[list[str], _extend]
    log: Annotated[list[str], _extend]
    # Reasoning + delivery outputs (references / small structured results).
    report_card_ref: str | None
    validated_by: str | None
    report_path: str | None
    error: str | None
