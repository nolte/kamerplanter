"""Unit tests for the harvest readiness and quality scoring engines (REQ-007)."""

from app.domain.engines.quality_scoring_engine import QualityScoringEngine
from app.domain.engines.readiness_engine import ReadinessEngine


class TestReadinessEngine:
    """Tests for ReadinessEngine.assess_readiness — pure-logic harvest readiness."""

    def test_no_observations_returns_immature(self):
        engine = ReadinessEngine()
        result = engine.assess_readiness(observations=[], indicator_reliabilities={})
        assert result["overall_score"] == 0
        assert result["recommendation"] == "immature"
        assert result["estimated_days"] is None
        assert result["indicators"] == []

    def test_single_peak_observation_recommends_optimal(self):
        engine = ReadinessEngine()
        result = engine.assess_readiness(
            observations=[
                {
                    "indicator_key": "trichome_color",
                    "ripeness_assessment": "peak",
                    "days_to_harvest_estimate": 0,
                }
            ],
            indicator_reliabilities={"trichome_color": 1.0},
        )
        assert result["overall_score"] == 100
        assert result["recommendation"] == "optimal"
        assert result["estimated_days"] == 0
        assert len(result["indicators"]) == 1
        assert result["indicators"][0]["stage"] == "peak"

    def test_weighted_score_uses_reliability(self):
        engine = ReadinessEngine()
        # Two observations: a high-reliability "approaching" (50) and a
        # low-reliability "peak" (100). The approaching signal must dominate.
        result = engine.assess_readiness(
            observations=[
                {"indicator_key": "trichome_color", "ripeness_assessment": "approaching"},
                {"indicator_key": "leaf_color", "ripeness_assessment": "peak"},
            ],
            indicator_reliabilities={"trichome_color": 0.9, "leaf_color": 0.1},
        )
        assert 50 < result["overall_score"] < 70
        assert result["recommendation"] in ("developing", "approaching")

    def test_estimated_days_averages_observations(self):
        engine = ReadinessEngine()
        result = engine.assess_readiness(
            observations=[
                {"indicator_key": "a", "ripeness_assessment": "approaching", "days_to_harvest_estimate": 4},
                {"indicator_key": "b", "ripeness_assessment": "approaching", "days_to_harvest_estimate": 8},
            ],
            indicator_reliabilities={"a": 1.0, "b": 1.0},
        )
        assert result["estimated_days"] == 6

    def test_unknown_indicator_uses_default_reliability(self):
        engine = ReadinessEngine()
        result = engine.assess_readiness(
            observations=[{"indicator_key": "unknown", "ripeness_assessment": "peak"}],
            indicator_reliabilities={},
        )
        # Default reliability is 0.5 -> still 100 % weighted contribution / 0.5 weight = 100
        assert result["overall_score"] == 100
        assert result["indicators"][0]["reliability"] == 0.5


class TestQualityScoringEngine:
    """Tests for QualityScoringEngine.calculate_overall_score — quality grade tiers."""

    def test_perfect_inputs_no_defects_grades_a_plus(self):
        engine = QualityScoringEngine()
        score, grade = engine.calculate_overall_score(appearance=100, aroma=100, color=100, defects=[])
        assert score == 100.0
        assert grade == "a_plus"

    def test_mold_defect_drops_grade_significantly(self):
        engine = QualityScoringEngine()
        score, grade = engine.calculate_overall_score(appearance=90, aroma=90, color=90, defects=["mold"])
        # 90*0.3 + 90*0.25 + 90*0.20 + 100*0.25 = 27+22.5+18+25 = 92.5; -50 mold = 42.5 -> "c"
        assert score == 42.5
        assert grade == "c"

    def test_score_clamped_to_zero(self):
        engine = QualityScoringEngine()
        score, grade = engine.calculate_overall_score(
            appearance=20, aroma=20, color=20, defects=["mold", "pests", "hermaphrodite"]
        )
        assert score == 0.0
        assert grade == "d"

    def test_unknown_defect_uses_default_penalty(self):
        engine = QualityScoringEngine()
        score_known, _ = engine.calculate_overall_score(
            appearance=100, aroma=100, color=100, defects=["mechanical_damage"]
        )
        score_unknown, _ = engine.calculate_overall_score(
            appearance=100, aroma=100, color=100, defects=["unknown_defect"]
        )
        # mechanical_damage is 5, default is 5 — both should match
        assert score_known == score_unknown

    def test_grade_thresholds_a_b_c(self):
        engine = QualityScoringEngine()
        # No defects, vary the appearance/aroma/color to land in each band
        _, a = engine.calculate_overall_score(appearance=80, aroma=80, color=80, defects=[])
        _, b = engine.calculate_overall_score(appearance=50, aroma=50, color=50, defects=[])
        _, c = engine.calculate_overall_score(appearance=15, aroma=15, color=15, defects=[])
        assert a == "a"
        assert b == "b"
        assert c == "c"
