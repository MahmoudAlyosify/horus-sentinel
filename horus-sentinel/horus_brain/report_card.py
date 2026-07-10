"""The Intelligence Report Card — the structured output DNA of the HORUS model.

The fine-tuned model already produces a sectioned card (GEOPOLITICAL CONTEXT → THREAT
ASSESSMENT → CONCLUSION). Here that becomes a typed artifact whose *prose* the model
authors, but whose *prioritized findings* are built deterministically from the graph and
the risk engine — so every claim stays traceable (master plan Part 4.1, invariant #4/#5).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.utcnow()


class FrameworkMapping(BaseModel):
    """A mapping of a finding to a framework technique (ATT&CK / geo taxonomy)."""

    framework: str = "MITRE ATT&CK"
    technique_id: str
    technique_name: str
    tactic: str = ""


class PrioritizedFinding(BaseModel):
    """One prioritized item: evidence → why it matters → mapping → recommendation → score."""

    title: str
    entity_key: str
    why_it_matters: str
    framework: FrameworkMapping | None = None
    recommendation: str
    risk_band: str
    risk_score: float
    evidence_ids: list[str] = Field(default_factory=list)


class BandAdjustment(BaseModel):
    """A logged, bounded (±1) model adjustment to a band (invariant Part 2.2 #4)."""

    entity_key: str
    from_band: str
    to_band: str
    delta: int
    reason: str


class ReportCard(BaseModel):
    """The full structured reasoning artifact for one subject."""

    subject: str
    generated_by: str = Field(..., description="Model name, or 'offline-synthesis' fallback.")
    generated_at: datetime = Field(default_factory=_utcnow)

    executive_summary: str = ""
    geopolitical_context: str = ""
    threat_assessment: str = ""
    conclusion: str = ""

    prioritized_findings: list[PrioritizedFinding] = Field(default_factory=list)
    band_adjustments: list[BandAdjustment] = Field(default_factory=list)

    # Headline metrics for the executive summary block.
    entity_count: int = 0
    top_band: str = "Info"
    critical_cve_hits: int = 0

    def top_findings(self, n: int = 5) -> list[PrioritizedFinding]:
        return self.prioritized_findings[:n]
