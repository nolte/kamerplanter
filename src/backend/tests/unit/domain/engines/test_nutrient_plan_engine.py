import pytest

from app.common.enums import PhaseName
from app.domain.engines.nutrient_plan_engine import NutrientPlanValidator, resolve_effective_entry
from app.domain.models.nutrient_plan import NutrientPlanPhaseEntry


@pytest.fixture
def validator():
    return NutrientPlanValidator()


def _make_entry(**kwargs) -> NutrientPlanPhaseEntry:
    defaults = {
        "plan_key": "p1",
        "phase_name": PhaseName.VEGETATIVE,
        "sequence_order": 1,
        "week_start": 1,
        "week_end": 4,
    }
    defaults.update(kwargs)
    return NutrientPlanPhaseEntry(**defaults)


class TestValidateCompleteness:
    def test_all_phases_covered(self, validator):
        entries = [
            _make_entry(phase_name=PhaseName.GERMINATION, sequence_order=1, week_start=1, week_end=2),
            _make_entry(phase_name=PhaseName.SEEDLING, sequence_order=2, week_start=3, week_end=4),
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=3, week_start=5, week_end=8),
            _make_entry(phase_name=PhaseName.FLOWERING, sequence_order=4, week_start=9, week_end=12),
            _make_entry(phase_name=PhaseName.FLUSHING, sequence_order=5, week_start=13, week_end=14),
            _make_entry(phase_name=PhaseName.DORMANCY, sequence_order=6, week_start=15, week_end=16),
            _make_entry(phase_name=PhaseName.HARVEST, sequence_order=7, week_start=17, week_end=18),
        ]
        result = validator.validate_completeness(entries)
        assert result["complete"] is True
        assert len(result["issues"]) == 0
        assert len(result["hints"]) == 0

    def test_missing_phases_are_hints_not_issues(self, validator):
        entries = [
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=1, week_start=1, week_end=4),
            _make_entry(phase_name=PhaseName.FLOWERING, sequence_order=2, week_start=5, week_end=8),
        ]
        result = validator.validate_completeness(entries)
        assert result["complete"] is True
        assert len(result["issues"]) == 0
        assert any("germination" in h.lower() for h in result["hints"])
        assert len(result["hints"]) == 5  # 7 total phases - 2 used = 5 unused

    def test_week_gap(self, validator):
        entries = [
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=1, week_start=1, week_end=4),
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=2, week_start=7, week_end=10),
        ]
        result = validator.validate_completeness(entries)
        assert result["complete"] is False
        assert any("gap" in i.lower() for i in result["issues"])

    def test_empty_entries(self, validator):
        result = validator.validate_completeness([])
        assert result["complete"] is True  # no issues, just hints
        assert len(result["issues"]) == 0
        assert len(result["hints"]) == 7  # all 7 phases unused

    def test_split_phase_no_false_positive(self, validator):
        """Perennial plan: VEGETATIVE used twice with other phases filling the gap."""
        entries = [
            _make_entry(phase_name=PhaseName.GERMINATION, sequence_order=1, week_start=1, week_end=4),
            _make_entry(phase_name=PhaseName.SEEDLING, sequence_order=2, week_start=5, week_end=8),
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=3, week_start=9, week_end=16),
            _make_entry(phase_name=PhaseName.FLOWERING, sequence_order=4, week_start=17, week_end=24),
            _make_entry(phase_name=PhaseName.HARVEST, sequence_order=5, week_start=25, week_end=28),
            _make_entry(phase_name=PhaseName.FLUSHING, sequence_order=6, week_start=29, week_end=30),
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=7, week_start=31, week_end=40),
            _make_entry(phase_name=PhaseName.DORMANCY, sequence_order=8, week_start=41, week_end=52),
        ]
        result = validator.validate_completeness(entries)
        assert result["complete"] is True
        assert len(result["issues"]) == 0

    def test_cross_phase_gap(self, validator):
        """Gap between FLOWERING and FLUSHING should be detected."""
        entries = [
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=1, week_start=1, week_end=4),
            _make_entry(phase_name=PhaseName.FLOWERING, sequence_order=2, week_start=5, week_end=8),
            _make_entry(phase_name=PhaseName.FLUSHING, sequence_order=3, week_start=11, week_end=12),
        ]
        result = validator.validate_completeness(entries)
        assert result["complete"] is False
        assert any("gap" in i.lower() for i in result["issues"])

    def test_cross_phase_overlap(self, validator):
        """Overlap between VEGETATIVE and FLOWERING should be detected."""
        entries = [
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=1, week_start=1, week_end=6),
            _make_entry(phase_name=PhaseName.FLOWERING, sequence_order=2, week_start=5, week_end=10),
        ]
        result = validator.validate_completeness(entries)
        assert result["complete"] is False
        assert any("overlap" in i.lower() for i in result["issues"])


class TestResolveEffectiveEntry:
    """Tests for perennial cycle restart logic."""

    @pytest.fixture
    def perennial_entries(self):
        """Houseplant plan: rooting(1-8) → juvenile(9-16) → vegetative(17-40) → dormancy(41-52)
        cycle_restart_from_sequence=3 means entries 3+4 repeat.
        """
        return [
            _make_entry(phase_name=PhaseName.SEEDLING, sequence_order=1, week_start=1, week_end=8),
            _make_entry(phase_name=PhaseName.SEEDLING, sequence_order=2, week_start=9, week_end=16),
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=3, week_start=17, week_end=40),
            _make_entry(phase_name=PhaseName.DORMANCY, sequence_order=4, week_start=41, week_end=52),
        ]

    def test_direct_match_first_cycle(self, perennial_entries):
        """Week 20 should match VEGETATIVE entry directly."""
        result = resolve_effective_entry(perennial_entries, "vegetative", 20, cycle_restart_from_sequence=3)
        assert result is not None
        assert result.phase_name == PhaseName.VEGETATIVE

    def test_direct_match_dormancy(self, perennial_entries):
        """Week 45 should match DORMANCY entry directly."""
        result = resolve_effective_entry(perennial_entries, "dormancy", 45, cycle_restart_from_sequence=3)
        assert result is not None
        assert result.phase_name == PhaseName.DORMANCY

    def test_cycle_restart_year_2_vegetative(self, perennial_entries):
        """Week 60 (year 2) should map into recurring VEGETATIVE entry.
        Recurring range: weeks 17-52 (36 weeks). Week 60 = 8 past end.
        offset = (60-52-1) % 36 = 7. effective_week = 17+7 = 24 → VEGETATIVE (17-40).
        """
        result = resolve_effective_entry(perennial_entries, "vegetative", 60, cycle_restart_from_sequence=3)
        assert result is not None
        assert result.phase_name == PhaseName.VEGETATIVE

    def test_cycle_restart_year_2_dormancy(self, perennial_entries):
        """Week 88 (year 2 late) should map into recurring DORMANCY entry.
        offset = (88-52-1) % 36 = 35. effective_week = 17+35 = 52 → DORMANCY (41-52).
        """
        result = resolve_effective_entry(perennial_entries, "dormancy", 88, cycle_restart_from_sequence=3)
        assert result is not None
        assert result.phase_name == PhaseName.DORMANCY

    def test_cycle_restart_year_3(self, perennial_entries):
        """Week 100 (year 3) should still resolve via cycle restart.
        offset = (100-52-1) % 36 = 47 % 36 = 11. effective_week = 17+11 = 28 → VEGETATIVE (17-40).
        """
        result = resolve_effective_entry(perennial_entries, "vegetative", 100, cycle_restart_from_sequence=3)
        assert result is not None
        assert result.phase_name == PhaseName.VEGETATIVE

    def test_no_cycle_restart_returns_none(self, perennial_entries):
        """Without cycle_restart, week 60 should return None."""
        result = resolve_effective_entry(perennial_entries, "vegetative", 60, cycle_restart_from_sequence=None)
        assert result is None

    def test_linear_plan_not_affected(self):
        """Linear cannabis plan should work as before."""
        entries = [
            _make_entry(phase_name=PhaseName.GERMINATION, sequence_order=1, week_start=1, week_end=2),
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=2, week_start=3, week_end=6),
            _make_entry(phase_name=PhaseName.FLOWERING, sequence_order=3, week_start=7, week_end=14),
        ]
        result = resolve_effective_entry(entries, "vegetative", 5, cycle_restart_from_sequence=None)
        assert result is not None
        assert result.phase_name == PhaseName.VEGETATIVE

    def test_linear_plan_past_end_returns_none(self):
        """Linear plan week past end should return None."""
        entries = [
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=1, week_start=1, week_end=4),
            _make_entry(phase_name=PhaseName.FLOWERING, sequence_order=2, week_start=5, week_end=10),
        ]
        result = resolve_effective_entry(entries, "flowering", 15, cycle_restart_from_sequence=None)
        assert result is None

    def test_fallback_to_week_range_ignoring_phase_name(self):
        """If phase name doesn't match, fall back to week range."""
        entries = [
            _make_entry(phase_name=PhaseName.VEGETATIVE, sequence_order=1, week_start=1, week_end=10),
        ]
        result = resolve_effective_entry(entries, "flowering", 5, cycle_restart_from_sequence=None)
        assert result is not None
        assert result.phase_name == PhaseName.VEGETATIVE

    def test_cycle_restart_first_week_after_end(self, perennial_entries):
        """Week 53 = first week of second cycle.
        offset = (53-52-1) % 36 = 0. effective_week = 17+0 = 17 → VEGETATIVE (17-40).
        """
        result = resolve_effective_entry(perennial_entries, "vegetative", 53, cycle_restart_from_sequence=3)
        assert result is not None
        assert result.phase_name == PhaseName.VEGETATIVE
