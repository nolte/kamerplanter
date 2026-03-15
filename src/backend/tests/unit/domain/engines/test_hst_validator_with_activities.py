from datetime import datetime, timedelta

from app.common.enums import ActivityCategory, SkillLevel, StressLevel
from app.domain.engines.hst_validator import HSTValidator
from app.domain.models.activity import Activity


def _make_activity(**kwargs) -> Activity:
    defaults = {
        "name": "Test",
        "category": ActivityCategory.GENERAL,
        "stress_level": StressLevel.NONE,
        "skill_level": SkillLevel.BEGINNER,
        "recovery_days_default": 0,
    }
    defaults.update(kwargs)
    return Activity(**defaults)


class TestHSTValidatorWithActivities:
    def setup_method(self):
        self.validator = HSTValidator()

    def test_forbidden_phase_from_activity(self):
        topping = _make_activity(
            name="Topping",
            forbidden_phases=["flowering", "harvest"],
            recovery_days_default=5,
        )
        result = self.validator.validate(
            "Topping",
            "flowering",
            [],
            activities=[topping],
        )
        assert result["can_perform"] is False
        assert "forbidden" in result["reason"]

    def test_restricted_sub_phase_from_activity(self):
        sc = _make_activity(
            name="Supercropping",
            restricted_sub_phases=["mid_flower", "late_flower"],
            recovery_days_default=5,
        )
        result = self.validator.validate(
            "Supercropping",
            "mid_flower",
            [],
            activities=[sc],
        )
        assert result["can_perform"] is False

    def test_allowed_in_vegetative_from_activity(self):
        topping = _make_activity(
            name="Topping",
            forbidden_phases=["flowering", "harvest"],
            recovery_days_default=5,
        )
        result = self.validator.validate(
            "Topping",
            "vegetative",
            [],
            activities=[topping],
        )
        assert result["can_perform"] is True

    def test_recovery_days_by_species(self):
        topping = _make_activity(
            name="Topping",
            recovery_days_default=5,
            recovery_days_by_species={"cannabis": 7},
        )
        recent = [{"name": "Topping", "completed_at": (datetime.now() - timedelta(days=3)).isoformat()}]
        result = self.validator.validate(
            "Topping",
            "vegetative",
            recent,
            species_name="Cannabis Sativa",
            activities=[topping],
        )
        assert result["can_perform"] is False
        assert result["recovery_status"]["days_remaining"] > 0

    def test_recovery_complete(self):
        topping = _make_activity(
            name="Topping",
            recovery_days_default=5,
        )
        recent = [{"name": "Topping", "completed_at": (datetime.now() - timedelta(days=10)).isoformat()}]
        result = self.validator.validate(
            "Topping",
            "vegetative",
            recent,
            activities=[topping],
        )
        assert result["can_perform"] is True

    def test_fallback_to_constants_when_activity_not_found(self):
        # Activity list provided but doesn't contain matching activity
        other = _make_activity(name="LST", recovery_days_default=0)
        result = self.validator.validate(
            "Topping",
            "flowering",
            [],
            activities=[other],
        )
        # Falls back to constants — Topping is in FORBIDDEN_ALL_FLOWER
        assert result["can_perform"] is False

    def test_fallback_to_constants_when_no_activities(self):
        # No activities parameter (None) — pure backward compat
        result = self.validator.validate("Topping", "flowering", [])
        assert result["can_perform"] is False

    def test_activity_name_matching_case_insensitive(self):
        topping = _make_activity(
            name="Topping",
            forbidden_phases=["flowering"],
        )
        result = self.validator.validate(
            "topping",
            "flowering",
            [],
            activities=[topping],
        )
        assert result["can_perform"] is False
