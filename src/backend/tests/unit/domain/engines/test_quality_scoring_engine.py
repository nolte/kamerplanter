"""Unit tests for the quality scoring engine."""

import pytest

from app.domain.engines.quality_scoring_engine import (
    APPEARANCE_WEIGHT,
    AROMA_WEIGHT,
    BASE_WEIGHT,
    COLOR_WEIGHT,
    DEFECT_PENALTIES,
    QualityScoringEngine,
)


@pytest.fixture
def engine():
    return QualityScoringEngine()


class TestCalculateOverallScore:
    """Tests for the calculate_overall_score method."""

    def test_perfect_scores_grade_a_plus(self, engine):
        """All 100s with no defects should produce A+ grade."""
        score, grade = engine.calculate_overall_score(100.0, 100.0, 100.0, [])
        assert score == 100.0
        assert grade == "a_plus"

    def test_good_scores_grade_a(self, engine):
        """Good scores (mid-range) should produce A grade."""
        # With 75 across the board: 75*(0.30+0.25+0.20) + 100*0.25 = 75*0.75 + 25 = 56.25 + 25 = 81.25
        score, grade = engine.calculate_overall_score(75.0, 75.0, 75.0, [])
        assert score >= 75
        assert grade == "a"

    def test_medium_scores_grade_b(self, engine):
        """Medium scores should produce B grade."""
        # With 50 across the board: 50*0.75 + 100*0.25 = 37.5 + 25 = 62.5
        score, grade = engine.calculate_overall_score(50.0, 50.0, 50.0, [])
        assert score >= 55
        assert grade == "b"

    def test_low_scores_grade_c(self, engine):
        """Low scores should produce C grade."""
        # With 20 across the board: 20*0.75 + 100*0.25 = 15 + 25 = 40
        score, grade = engine.calculate_overall_score(20.0, 20.0, 20.0, [])
        assert score >= 35
        assert grade == "c"

    def test_zero_scores_grade_d(self, engine):
        """Zero scores across the board produce D grade."""
        # 0*0.75 + 100*0.25 = 25
        score, grade = engine.calculate_overall_score(0.0, 0.0, 0.0, [])
        assert score < 35
        assert grade == "d"

    def test_defect_mold_heavy_penalty(self, engine):
        """Mold defect subtracts 50 points from the weighted score."""
        score_clean, _ = engine.calculate_overall_score(100.0, 100.0, 100.0, [])
        score_mold, grade = engine.calculate_overall_score(100.0, 100.0, 100.0, ["mold"])
        assert score_clean - score_mold == DEFECT_PENALTIES["mold"]

    def test_multiple_defects_accumulate(self, engine):
        """Multiple defects subtract cumulatively."""
        score_clean, _ = engine.calculate_overall_score(100.0, 100.0, 100.0, [])
        defects = ["nutrient_burn", "mechanical_damage"]
        score_defected, _ = engine.calculate_overall_score(100.0, 100.0, 100.0, defects)
        expected_penalty = DEFECT_PENALTIES["nutrient_burn"] + DEFECT_PENALTIES["mechanical_damage"]
        assert score_clean - score_defected == expected_penalty

    def test_score_clamped_to_zero(self, engine):
        """Score cannot go below 0 even with extreme penalties."""
        score, grade = engine.calculate_overall_score(0.0, 0.0, 0.0, ["mold", "hermaphrodite", "pests"])
        assert score == 0.0
        assert grade == "d"

    def test_score_clamped_to_100(self, engine):
        """Score cannot exceed 100 even if weights somehow produce higher."""
        score, grade = engine.calculate_overall_score(100.0, 100.0, 100.0, [])
        assert score <= 100.0

    def test_grade_boundary_at_90(self, engine):
        """Exactly 90 should give A+ grade."""
        # We need to find inputs that produce exactly 90
        # weighted = app*0.3 + aro*0.25 + col*0.2 + 100*0.25
        # 90 = app*0.3 + aro*0.25 + col*0.2 + 25
        # 65 = app*0.3 + aro*0.25 + col*0.2
        # If all equal x: 0.75x = 65 => x = 86.67
        score, grade = engine.calculate_overall_score(86.67, 86.67, 86.67, [])
        # Should be very close to 90
        assert grade == "a_plus"

    def test_grade_boundary_at_75(self, engine):
        """Score of exactly 75 should give A grade."""
        # 75 = x*0.75 + 25 => x = 66.67
        score, grade = engine.calculate_overall_score(66.67, 66.67, 66.67, [])
        assert grade == "a"

    def test_unknown_defect_uses_default_penalty(self, engine):
        """An unknown defect identifier uses the default penalty of 5."""
        score_clean, _ = engine.calculate_overall_score(100.0, 100.0, 100.0, [])
        score_unknown, _ = engine.calculate_overall_score(100.0, 100.0, 100.0, ["unknown_defect"])
        assert score_clean - score_unknown == 5.0

    def test_weights_sum_to_one(self):
        """Verify the weight constants sum to 1.0."""
        total = APPEARANCE_WEIGHT + AROMA_WEIGHT + COLOR_WEIGHT + BASE_WEIGHT
        assert abs(total - 1.0) < 1e-9
