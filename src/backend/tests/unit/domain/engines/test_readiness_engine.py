"""Unit tests for the readiness engine."""

import pytest

from app.domain.engines.readiness_engine import ReadinessEngine


@pytest.fixture
def engine():
    return ReadinessEngine()


def _make_observation(indicator_key: str, stage: str, days_estimate: int | None = None) -> dict:
    """Helper to create an observation dict."""
    obs = {
        "indicator_key": indicator_key,
        "ripeness_assessment": stage,
    }
    if days_estimate is not None:
        obs["days_to_harvest_estimate"] = days_estimate
    return obs


class TestAssessReadiness:
    """Tests for the assess_readiness method."""

    def test_no_observations_returns_immature(self, engine):
        """No observations means immature with score 0."""
        result = engine.assess_readiness([], {})
        assert result["overall_score"] == 0
        assert result["recommendation"] == "immature"
        assert result["estimated_days"] is None
        assert result["indicators"] == []

    def test_all_peak_returns_optimal(self, engine):
        """All peak observations should give optimal recommendation."""
        observations = [
            _make_observation("trichome", "peak"),
            _make_observation("pistil", "peak"),
            _make_observation("color", "peak"),
        ]
        reliabilities = {
            "trichome": 1.0,
            "pistil": 1.0,
            "color": 1.0,
        }
        result = engine.assess_readiness(observations, reliabilities)
        assert result["overall_score"] == 100.0
        assert result["recommendation"] == "optimal"

    def test_all_immature_returns_immature(self, engine):
        """All immature observations should give immature recommendation."""
        observations = [
            _make_observation("trichome", "immature"),
            _make_observation("pistil", "immature"),
        ]
        reliabilities = {
            "trichome": 1.0,
            "pistil": 1.0,
        }
        result = engine.assess_readiness(observations, reliabilities)
        assert result["overall_score"] == 0.0
        assert result["recommendation"] == "immature"

    def test_mixed_observations_intermediate(self, engine):
        """Mixed observations produce an intermediate score."""
        observations = [
            _make_observation("trichome", "peak"),
            _make_observation("pistil", "immature"),
        ]
        reliabilities = {
            "trichome": 1.0,
            "pistil": 1.0,
        }
        result = engine.assess_readiness(observations, reliabilities)
        # peak=100, immature=0, avg=50
        assert result["overall_score"] == 50.0
        assert result["recommendation"] == "developing"

    def test_overripe_reduces_score(self, engine):
        """Overripe observations score 80 instead of 100."""
        observations = [
            _make_observation("trichome", "overripe"),
        ]
        reliabilities = {"trichome": 1.0}
        result = engine.assess_readiness(observations, reliabilities)
        assert result["overall_score"] == 80.0
        assert result["recommendation"] == "approaching"

    def test_approaching_stage(self, engine):
        """Approaching stage scores 50."""
        observations = [
            _make_observation("trichome", "approaching"),
        ]
        reliabilities = {"trichome": 1.0}
        result = engine.assess_readiness(observations, reliabilities)
        assert result["overall_score"] == 50.0
        assert result["recommendation"] == "developing"

    def test_reliability_weighting(self, engine):
        """Higher reliability indicators have more weight."""
        observations = [
            _make_observation("trichome", "peak"),      # score 100, reliability 0.9
            _make_observation("pistil", "immature"),     # score 0, reliability 0.1
        ]
        reliabilities = {
            "trichome": 0.9,
            "pistil": 0.1,
        }
        result = engine.assess_readiness(observations, reliabilities)
        # weighted = (100*0.9 + 0*0.1) / (0.9 + 0.1) = 90.0
        assert result["overall_score"] == 90.0
        assert result["recommendation"] == "optimal"

    def test_default_reliability(self, engine):
        """Unknown indicator keys get default reliability of 0.5."""
        observations = [
            _make_observation("unknown_indicator", "peak"),
        ]
        result = engine.assess_readiness(observations, {})
        # Default reliability 0.5, score=100, weighted=50/0.5=100
        assert result["overall_score"] == 100.0

    def test_estimated_days_averaged(self, engine):
        """Estimated days are averaged across observations that provide them."""
        observations = [
            _make_observation("trichome", "approaching", days_estimate=10),
            _make_observation("pistil", "approaching", days_estimate=14),
        ]
        reliabilities = {"trichome": 1.0, "pistil": 1.0}
        result = engine.assess_readiness(observations, reliabilities)
        assert result["estimated_days"] == 12  # round((10+14)/2)

    def test_estimated_days_none_when_no_estimates(self, engine):
        """No day estimates means estimated_days is None."""
        observations = [
            _make_observation("trichome", "peak"),
        ]
        result = engine.assess_readiness(observations, {})
        assert result["estimated_days"] is None

    def test_indicators_breakdown(self, engine):
        """The indicators list contains per-indicator details."""
        observations = [
            _make_observation("trichome", "peak"),
        ]
        reliabilities = {"trichome": 0.8}
        result = engine.assess_readiness(observations, reliabilities)
        assert len(result["indicators"]) == 1
        ind = result["indicators"][0]
        assert ind["indicator_key"] == "trichome"
        assert ind["stage"] == "peak"
        assert ind["score"] == 100
        assert ind["reliability"] == 0.8
        assert ind["weighted_contribution"] == 80.0

    def test_all_approaching_gives_developing(self, engine):
        """All approaching (score=50 each) averages to 50, which is 'developing'."""
        observations = [
            _make_observation("a", "approaching"),
            _make_observation("b", "approaching"),
        ]
        reliabilities = {"a": 1.0, "b": 1.0}
        result = engine.assess_readiness(observations, reliabilities)
        assert result["overall_score"] == 50.0
        assert result["recommendation"] == "developing"
