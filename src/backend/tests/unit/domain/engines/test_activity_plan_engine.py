import pytest

from app.common.enums import ActivityCategory, SkillLevel, StressLevel, StressTolerance
from app.domain.engines.activity_plan_engine import ActivityPlanEngine
from app.domain.models.activity import Activity
from app.domain.models.lifecycle import GrowthPhase


def _phase(
    name: str = "vegetative",
    duration: int = 30,
    order: int = 1,
    tolerance: StressTolerance = StressTolerance.MEDIUM,
) -> GrowthPhase:
    return GrowthPhase(
        name=name,
        display_name=name.title(),
        typical_duration_days=duration,
        sequence_order=order,
        stress_tolerance=tolerance,
    )


def _activity(
    name: str = "Topping",
    key: str = "act1",
    category: ActivityCategory = ActivityCategory.TRAINING_HST,
    stress: StressLevel = StressLevel.MEDIUM,
    skill: SkillLevel = SkillLevel.INTERMEDIATE,
    forbidden: list[str] | None = None,
    restricted_sub: list[str] | None = None,
    species_compatible: list[str] | None = None,
    recovery: int = 3,
    sort_order: int = 0,
    duration_min: int | None = 15,
    recovery_by_species: dict[str, int] | None = None,
) -> Activity:
    return Activity(
        _key=key,
        name=name,
        category=category,
        stress_level=stress,
        skill_level=skill,
        forbidden_phases=forbidden or [],
        restricted_sub_phases=restricted_sub or [],
        species_compatible=species_compatible or [],
        recovery_days_default=recovery,
        sort_order=sort_order,
        estimated_duration_minutes=duration_min,
        recovery_days_by_species=recovery_by_species or {},
    )


@pytest.fixture()
def engine():
    return ActivityPlanEngine()


class TestFilterForbiddenPhases:
    def test_excludes_forbidden_phase(self, engine):
        phases = [_phase("flowering")]
        activities = [_activity(forbidden=["flowering"])]
        _wt, templates = engine.generate_plan("TestPlant", phases, activities)
        assert templates == []

    def test_includes_when_not_forbidden(self, engine):
        phases = [_phase("vegetative")]
        activities = [_activity(forbidden=["flowering"])]
        _wt, templates = engine.generate_plan("TestPlant", phases, activities)
        assert len(templates) == 1


class TestFilterRestrictedSubPhases:
    def test_excludes_restricted_sub_phase(self, engine):
        phases = [_phase("late_flowering")]
        activities = [_activity(restricted_sub=["late_flowering"])]
        _wt, templates = engine.generate_plan("TestPlant", phases, activities)
        assert templates == []


class TestSpeciesFilter:
    def test_species_specific_excluded(self, engine):
        phases = [_phase()]
        activities = [_activity(species_compatible=["Cannabis"])]
        _wt, templates = engine.generate_plan("Tomato", phases, activities)
        assert templates == []

    def test_species_specific_included(self, engine):
        phases = [_phase()]
        activities = [_activity(species_compatible=["Cannabis"])]
        _wt, templates = engine.generate_plan("Cannabis", phases, activities)
        assert len(templates) == 1

    def test_empty_compatible_means_all(self, engine):
        phases = [_phase()]
        activities = [_activity(species_compatible=[])]
        _wt, templates = engine.generate_plan("AnyPlant", phases, activities)
        assert len(templates) == 1


class TestSkillLevelFilter:
    def test_advanced_excluded_for_beginner(self, engine):
        phases = [_phase()]
        activities = [_activity(skill=SkillLevel.ADVANCED)]
        _wt, templates = engine.generate_plan("P", phases, activities, skill_level="beginner")
        assert templates == []

    def test_beginner_included_for_advanced(self, engine):
        phases = [_phase()]
        activities = [_activity(skill=SkillLevel.BEGINNER)]
        _wt, templates = engine.generate_plan("P", phases, activities, skill_level="advanced")
        assert len(templates) == 1

    def test_no_filter_defaults_to_intermediate(self, engine):
        phases = [_phase()]
        advanced = [_activity(skill=SkillLevel.ADVANCED)]
        _wt, templates = engine.generate_plan("P", phases, advanced)
        assert templates == []

        intermediate = [_activity(skill=SkillLevel.INTERMEDIATE)]
        _wt2, templates2 = engine.generate_plan("P", phases, intermediate)
        assert len(templates2) == 1


class TestStressGate:
    def test_high_stress_low_tolerance_excluded(self, engine):
        phases = [_phase(tolerance=StressTolerance.LOW)]
        activities = [_activity(stress=StressLevel.HIGH)]
        _wt, templates = engine.generate_plan("P", phases, activities)
        assert templates == []

    def test_low_stress_high_tolerance_included(self, engine):
        phases = [_phase(tolerance=StressTolerance.HIGH)]
        activities = [_activity(stress=StressLevel.LOW)]
        _wt, templates = engine.generate_plan("P", phases, activities)
        assert len(templates) == 1

    def test_medium_stress_medium_tolerance_included(self, engine):
        phases = [_phase(tolerance=StressTolerance.MEDIUM)]
        activities = [_activity(stress=StressLevel.MEDIUM)]
        _wt, templates = engine.generate_plan("P", phases, activities)
        assert len(templates) == 1


class TestRecoveryWindow:
    def test_two_hst_separated_by_recovery(self, engine):
        phases = [_phase(duration=30)]
        activities = [
            _activity(name="Topping", key="a1", recovery=5, sort_order=0),
            _activity(name="FIM", key="a2", recovery=5, sort_order=1),
        ]
        _wt, templates = engine.generate_plan("P", phases, activities)
        assert len(templates) == 2
        # Second HST must be offset by at least recovery + 1 from first
        assert templates[1].days_offset >= templates[0].days_offset + 5 + 1


class TestOptionalOverflow:
    def test_marks_overflow_as_optional(self, engine):
        phases = [_phase(duration=5)]
        activities = [
            _activity(name="A1", key="a1", recovery=3, sort_order=0),
            _activity(name="A2", key="a2", recovery=3, sort_order=1),
        ]
        _wt, templates = engine.generate_plan("P", phases, activities)
        overflow = [t for t in templates if t.is_optional]
        assert len(overflow) >= 1
        for t in overflow:
            assert t.enabled is False


class TestEmptyInputs:
    def test_empty_activities(self, engine):
        _wt, templates = engine.generate_plan("P", [_phase()], [])
        assert len(templates) == 0

    def test_empty_phases(self, engine):
        _wt, templates = engine.generate_plan("P", [], [_activity()])
        assert len(templates) == 0


class TestSpeciesRecovery:
    def test_species_specific_recovery(self, engine):
        phases = [_phase(duration=30)]
        activities = [
            _activity(
                name="Topping", key="a1", recovery=3,
                recovery_by_species={"Cannabis": 7},
                sort_order=0,
            ),
            _activity(name="FIM", key="a2", recovery=3, sort_order=1),
        ]
        _wt, templates = engine.generate_plan("Cannabis", phases, activities)
        assert len(templates) == 2
        # First activity uses species-specific recovery of 7
        assert templates[1].days_offset >= templates[0].days_offset + 7 + 1


class TestCategoryOrdering:
    def test_hst_before_lst(self, engine):
        phases = [_phase(duration=30)]
        activities = [
            _activity(
                name="LST", key="a1",
                category=ActivityCategory.TRAINING_LST,
                stress=StressLevel.LOW, sort_order=0,
            ),
            _activity(
                name="HST", key="a2",
                category=ActivityCategory.TRAINING_HST,
                stress=StressLevel.MEDIUM, sort_order=0,
            ),
        ]
        _wt, templates = engine.generate_plan("P", phases, activities)
        # Both HST and LST map to "training" TaskCategory,
        # but HST sorts before LST by category priority
        assert templates[0].name == "HST"
        assert templates[1].name == "LST"


class TestHarvestPrepAtEnd:
    def test_harvest_prep_scheduled_at_end(self, engine):
        phases = [_phase(duration=30)]
        activities = [
            _activity(
                name="Flush", key="a1",
                category=ActivityCategory.HARVEST_PREP,
                stress=StressLevel.NONE, sort_order=0,
            ),
        ]
        _wt, templates = engine.generate_plan("P", phases, activities)
        tt = templates[0]
        # harvest_prep offset should be near end (duration - 2 = 28)
        assert tt.days_offset >= 20


class TestTransplantAtStart:
    def test_transplant_at_day_zero(self, engine):
        phases = [_phase(duration=30)]
        activities = [
            _activity(
                name="Transplant", key="a1",
                category=ActivityCategory.TRANSPLANT,
                stress=StressLevel.MEDIUM, sort_order=0,
                recovery=2,
            ),
        ]
        _wt, templates = engine.generate_plan("P", phases, activities)
        tt = templates[0]
        assert tt.days_offset == 0


class TestPlanTotals:
    def test_total_activities_and_duration(self, engine):
        phases = [_phase(duration=20, order=0), _phase("flowering", 40, 1)]
        activities = [
            _activity(name="A", key="a1", forbidden=[], stress=StressLevel.LOW),
        ]
        wt, templates = engine.generate_plan("P", phases, activities)
        assert len(templates) == 2
        assert wt.total_duration_days == 60


class TestWorkflowTemplateFields:
    def test_auto_generated_flag(self, engine):
        phases = [_phase()]
        activities = [_activity()]
        wt, _templates = engine.generate_plan("P", phases, activities, growth_system="indoor", skill_level="beginner")
        assert wt.auto_generated is True
        assert wt.growth_system == "indoor"
        assert wt.skill_level_filter == "beginner"

    def test_task_template_fields(self, engine):
        phases = [_phase()]
        activities = [_activity(name="Topping", key="act1", recovery=3)]
        _wt, templates = engine.generate_plan("P", phases, activities)
        tt = templates[0]
        assert tt.name == "Topping"
        assert tt.activity_key == "act1"
        assert tt.trigger_phase == "vegetative"
        assert tt.recovery_days == 3
        assert tt.phase_display_name == "Vegetative"
        assert tt.phase_duration_days == 30
        assert tt.phase_stress_tolerance == "medium"
        assert tt.rationale != ""
