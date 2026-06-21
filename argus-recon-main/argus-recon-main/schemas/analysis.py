"""
Pydantic schemas for Analysis Agent results.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing import Any, List, Dict


class Finding(BaseModel):
    id: str
    title: str
    summary: str
    evidence_refs: List[str] = []
    score: float | None = None


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str
    findings: List[Finding]
    rag_refs: Dict[str, Any] = {}
    overall_score: float | None = None
