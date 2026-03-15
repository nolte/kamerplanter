import pytest
from pydantic import ValidationError

from app.common.enums import ActivityCategory, SkillLevel, StressLevel
from app.domain.models.activity import Activity


class TestActivityModel:
    def test_minimal_creation(self):
        a = Activity(name="Test Activity")
        assert a.name == "Test Activity"
        assert a.category == ActivityCategory.GENERAL
        assert a.stress_level == StressLevel.NONE
        assert a.skill_level == SkillLevel.BEGINNER
        assert a.recovery_days_default == 0
        assert a.is_system is False
        assert a.forbidden_phases == []
        assert a.restricted_sub_phases == []
        assert a.tools_required == []
        assert a.species_compatible == []
        assert a.tags == []

    def test_full_creation(self):
        a = Activity(
            name="Topping",
            name_de="Topping",
            description="Remove apical meristem",
            description_de="Haupttrieb kappen",
            category=ActivityCategory.TRAINING_HST,
            stress_level=StressLevel.HIGH,
            skill_level=SkillLevel.INTERMEDIATE,
            recovery_days_default=5,
            recovery_days_by_species={"cannabis": 7},
            forbidden_phases=["flowering", "harvest"],
            tools_required=["scissors"],
            estimated_duration_minutes=5,
            requires_photo=True,
            is_system=True,
            sort_order=1,
            tags=["hst"],
        )
        assert a.category == ActivityCategory.TRAINING_HST
        assert a.recovery_days_by_species == {"cannabis": 7}
        assert a.forbidden_phases == ["flowering", "harvest"]
        assert a.is_system is True

    def test_name_validation(self):
        with pytest.raises(ValidationError):
            Activity(name="")

    def test_recovery_days_non_negative(self):
        with pytest.raises(ValidationError):
            Activity(name="Test", recovery_days_default=-1)

    def test_estimated_duration_minimum(self):
        with pytest.raises(ValidationError):
            Activity(name="Test", estimated_duration_minutes=0)

    def test_sort_order_non_negative(self):
        with pytest.raises(ValidationError):
            Activity(name="Test", sort_order=-1)

    def test_key_alias(self):
        a = Activity(_key="123", name="Test")
        assert a.key == "123"

    def test_model_dump_by_alias(self):
        a = Activity(name="Test")
        data = a.model_dump(by_alias=True)
        assert "_key" in data
