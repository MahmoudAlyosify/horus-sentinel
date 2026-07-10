"""Tests for the deterministic risk-scoring engine (master plan Part 4.4)."""

import pytest

from scoring.engine import (
    RiskBand,
    RiskInputs,
    RiskWeights,
    adjust_band,
    band_for,
    compute_score,
)


def test_zero_inputs_is_info():
    result = compute_score(RiskInputs())
    assert result.score == 0.0
    assert result.band == RiskBand.INFO


def test_max_inputs_is_critical():
    result = compute_score(RiskInputs(1.0, 1.0, 1.0, 1.0))
    assert result.score == 100.0
    assert result.band == RiskBand.CRITICAL


def test_score_is_deterministic():
    inputs = RiskInputs(exposure=0.5, threat_context=0.8, reputation=0.3, criticality=0.6)
    a = compute_score(inputs)
    b = compute_score(inputs)
    assert a.score == b.score
    assert a.components == b.components


def test_weighted_combination_matches_formula():
    # default weights: 0.30, 0.30, 0.20, 0.20
    inputs = RiskInputs(exposure=1.0, threat_context=0.0, reputation=0.0, criticality=0.0)
    result = compute_score(inputs)
    assert result.score == pytest.approx(30.0)
    assert result.components["exposure"] == pytest.approx(30.0)


def test_inputs_are_clamped():
    result = compute_score(RiskInputs(exposure=5.0, threat_context=-1.0))
    assert result.inputs["exposure"] == 1.0
    assert result.inputs["threat_context"] == 0.0


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, RiskBand.INFO),
        (19.9, RiskBand.INFO),
        (20, RiskBand.LOW),
        (40, RiskBand.MEDIUM),
        (60, RiskBand.HIGH),
        (80, RiskBand.CRITICAL),
        (100, RiskBand.CRITICAL),
    ],
)
def test_band_thresholds(score, expected):
    assert band_for(score) == expected


def test_band_adjustment_is_bounded_to_one_step():
    # The model can nudge ±1 band, never more (invariant Part 2.2 #4).
    assert adjust_band(RiskBand.MEDIUM, 1) == RiskBand.HIGH
    assert adjust_band(RiskBand.MEDIUM, -1) == RiskBand.LOW
    assert adjust_band(RiskBand.MEDIUM, 5) == RiskBand.HIGH  # clamped to +1
    assert adjust_band(RiskBand.MEDIUM, -5) == RiskBand.LOW  # clamped to -1
    assert adjust_band(RiskBand.CRITICAL, 1) == RiskBand.CRITICAL  # can't exceed top
    assert adjust_band(RiskBand.INFO, -1) == RiskBand.INFO  # can't go below bottom


def test_weights_must_sum_to_one():
    bad = RiskWeights(exposure=0.5, threat_context=0.5, reputation=0.5, criticality=0.5)
    with pytest.raises(ValueError, match="sum to 1.0"):
        compute_score(RiskInputs(0.5, 0.5, 0.5, 0.5), weights=bad)
