"""Tests for cosine_to_confidence thresholds (REQ-029-A 3.5)."""

import pytest

from app.confidence import cosine_to_confidence

AUTO = 0.85
SHOW = 0.10


def conf(score: float) -> float:
    return cosine_to_confidence(score, auto_accept=AUTO, show_results=SHOW)


def test_at_auto_accept_threshold_maps_to_085():
    """A cosine exactly at auto_accept yields exactly 0.85 confidence."""
    assert conf(AUTO) == pytest.approx(0.85, abs=1e-3)


def test_at_show_results_threshold_maps_to_010():
    """A cosine exactly at show_results yields exactly 0.10 confidence."""
    assert conf(SHOW) == pytest.approx(0.10, abs=1e-3)


def test_perfect_match_maps_to_one():
    """A cosine of 1.0 yields confidence 1.0."""
    assert conf(1.0) == pytest.approx(1.0, abs=1e-3)


def test_zero_cosine_maps_to_zero():
    """A cosine of 0.0 yields confidence 0.0."""
    assert conf(0.0) == pytest.approx(0.0, abs=1e-3)


def test_monotonic_increasing():
    """Higher cosine always yields higher (or equal) confidence."""
    scores = [0.0, 0.05, 0.1, 0.3, 0.5, 0.7, 0.85, 0.9, 1.0]
    confs = [conf(s) for s in scores]
    assert confs == sorted(confs)


def test_above_auto_accept_in_high_band():
    """Scores above auto_accept land in [0.85, 1.0]."""
    c = conf(0.95)
    assert 0.85 <= c <= 1.0


def test_between_thresholds_in_mid_band():
    """Scores between show_results and auto_accept land in [0.10, 0.85)."""
    c = conf(0.5)
    assert 0.10 <= c < 0.85


def test_below_show_results_in_low_band():
    """Scores below show_results land in [0.0, 0.10)."""
    c = conf(0.05)
    assert 0.0 <= c < 0.10


def test_clamps_out_of_range_input():
    """Inputs outside [0, 1] are clamped."""
    assert conf(-0.5) == pytest.approx(0.0, abs=1e-3)
    assert conf(1.5) == pytest.approx(1.0, abs=1e-3)


def test_degenerate_thresholds_do_not_raise():
    """Inverted/degenerate thresholds are tolerated (no exception, value in [0,1])."""
    c = cosine_to_confidence(0.5, auto_accept=0.2, show_results=0.8)
    assert 0.0 <= c <= 1.0
