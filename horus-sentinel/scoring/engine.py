"""Deterministic risk-scoring engine (master plan Part 4.4).

The score is a pure function of four normalized sub-scores and fixed weights:

    RiskScore = w_e·Exposure + w_t·ThreatContext + w_i·ReputationIntel + w_c·Criticality

Determinism is the whole point: the same inputs always produce the same score and band.
The HORUS model may *explain* the score and adjust it by at most one band (``adjust_band``),
never invent it. Every piece here is side-effect-free and unit-tested.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from core.config import settings


class RiskBand(StrEnum):
    """Human-facing severity bands, ordered low→high by ``ORDER``."""

    INFO = "Info"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# Band ordering for bounded adjustment and comparisons.
_BAND_ORDER: list[RiskBand] = [
    RiskBand.INFO,
    RiskBand.LOW,
    RiskBand.MEDIUM,
    RiskBand.HIGH,
    RiskBand.CRITICAL,
]


@dataclass(frozen=True)
class RiskWeights:
    """The four component weights. Must sum to 1.0."""

    exposure: float = settings.w_exposure
    threat_context: float = settings.w_threat_context
    reputation: float = settings.w_reputation
    criticality: float = settings.w_criticality

    def validate(self) -> None:
        total = self.exposure + self.threat_context + self.reputation + self.criticality
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Risk weights must sum to 1.0, got {total}")


@dataclass(frozen=True)
class RiskInputs:
    """The four normalized sub-scores, each in [0, 1]."""

    exposure: float = 0.0
    threat_context: float = 0.0
    reputation: float = 0.0
    criticality: float = 0.0

    def clamped(self) -> RiskInputs:
        return RiskInputs(
            exposure=_clamp01(self.exposure),
            threat_context=_clamp01(self.threat_context),
            reputation=_clamp01(self.reputation),
            criticality=_clamp01(self.criticality),
        )


@dataclass
class ScoreResult:
    """The computed score, its band, and the component breakdown for the report."""

    score: float  # 0–100
    band: RiskBand
    components: dict[str, float] = field(default_factory=dict)  # weighted contributions (0–100)
    inputs: dict[str, float] = field(default_factory=dict)  # raw sub-scores (0–1)

    def explain(self) -> str:
        parts = ", ".join(f"{k}={v:.1f}" for k, v in self.components.items())
        return f"{self.band} ({self.score:.1f}/100) from [{parts}]"


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def band_for(score: float) -> RiskBand:
    """Map a 0–100 score to a band. Fixed thresholds → reproducible."""
    if score >= 80:
        return RiskBand.CRITICAL
    if score >= 60:
        return RiskBand.HIGH
    if score >= 40:
        return RiskBand.MEDIUM
    if score >= 20:
        return RiskBand.LOW
    return RiskBand.INFO


def compute_score(inputs: RiskInputs, weights: RiskWeights | None = None) -> ScoreResult:
    """Deterministically combine sub-scores into a 0–100 score + band."""
    w = weights or RiskWeights()
    w.validate()
    ci = inputs.clamped()

    contributions = {
        "exposure": w.exposure * ci.exposure * 100,
        "threat_context": w.threat_context * ci.threat_context * 100,
        "reputation": w.reputation * ci.reputation * 100,
        "criticality": w.criticality * ci.criticality * 100,
    }
    score = round(sum(contributions.values()), 2)
    return ScoreResult(
        score=score,
        band=band_for(score),
        components={k: round(v, 2) for k, v in contributions.items()},
        inputs={
            "exposure": ci.exposure,
            "threat_context": ci.threat_context,
            "reputation": ci.reputation,
            "criticality": ci.criticality,
        },
    )


def adjust_band(band: RiskBand, delta: int) -> RiskBand:
    """Move a band by at most ±1 step (master plan invariant Part 2.2 #4).

    The HORUS model may nudge a score's band up or down by one, with a logged reason.
    Anything beyond ±1 is clamped — the model cannot fabricate severity.
    """
    delta = max(-1, min(1, delta))
    idx = _BAND_ORDER.index(band)
    new_idx = max(0, min(len(_BAND_ORDER) - 1, idx + delta))
    return _BAND_ORDER[new_idx]
