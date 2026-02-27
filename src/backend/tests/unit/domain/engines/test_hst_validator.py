"""Unit tests for the HST (High Stress Training) validator engine."""

from datetime import datetime, timedelta

import pytest

from app.domain.engines.hst_validator import (
    FORBIDDEN_ALL_FLOWER,
    FORBIDDEN_MID_FLOWER,
    RECOVERY_DAYS,
    HSTValidator,
)


@pytest.fixture
def engine():
    return HSTValidator()


def _make_hst_task(name: str, days_ago: int) -> dict:
    """Helper to create an HST task dict completed N days ago."""
    return {
        "name": name,
        "completed_at": datetime.now() - timedelta(days=days_ago),
    }


class TestNonHSTTask:
    """Tests for tasks that are not HST-restricted."""

    def test_non_hst_task_always_allowed(self, engine):
        """A task that is not in any forbidden set is always allowed."""
        result = engine.validate("watering", "flowering", [])
        assert result["can_perform"] is True
        assert result["reason"] == ""

    def test_lst_in_flowering_allowed(self, engine):
        """Low Stress Training (LST) is not HST and is allowed in flowering."""
        result = engine.validate("lst", "flowering", [])
        assert result["can_perform"] is True

    def test_defoliation_light_in_flowering_allowed(self, engine):
        """Light defoliation (not heavy) is allowed in flowering."""
        result = engine.validate("light_defoliation", "flowering", [])
        assert result["can_perform"] is True


class TestFloweringPhaseRestrictions:
    """Tests for tasks forbidden during flowering."""

    def test_topping_in_vegetative_allowed(self, engine):
        """Topping in vegetative phase is allowed."""
        result = engine.validate("topping", "vegetative", [])
        assert result["can_perform"] is True

    def test_topping_in_flowering_blocked(self, engine):
        """Topping in flowering phase is forbidden."""
        result = engine.validate("topping", "flowering", [])
        assert result["can_perform"] is False
        assert "forbidden" in result["reason"].lower()

    def test_fim_in_flowering_blocked(self, engine):
        """FIM in flowering phase is forbidden."""
        result = engine.validate("fim", "flowering", [])
        assert result["can_perform"] is False

    def test_mainlining_in_flowering_blocked(self, engine):
        """Mainlining in flowering is forbidden."""
        result = engine.validate("mainlining", "flowering", [])
        assert result["can_perform"] is False

    def test_heavy_defoliation_in_flowering_blocked(self, engine):
        """Heavy defoliation in flowering is forbidden."""
        result = engine.validate("heavy_defoliation", "flowering", [])
        assert result["can_perform"] is False

    def test_all_forbidden_flower_tasks_covered(self, engine):
        """Every task in FORBIDDEN_ALL_FLOWER is blocked during flowering."""
        for task in FORBIDDEN_ALL_FLOWER:
            result = engine.validate(task, "flowering", [])
            assert result["can_perform"] is False, f"{task} should be blocked in flowering"


class TestMidFlowerRestrictions:
    """Tests for tasks forbidden only in mid/late flowering."""

    def test_supercropping_in_early_flowering_allowed(self, engine):
        """Supercropping in early flowering (just 'flowering') is allowed."""
        result = engine.validate("supercropping", "flowering", [])
        assert result["can_perform"] is True

    def test_supercropping_in_mid_flower_blocked(self, engine):
        """Supercropping in mid_flower is blocked."""
        result = engine.validate("supercropping", "mid_flower", [])
        assert result["can_perform"] is False
        assert "mid/late" in result["reason"].lower()

    def test_transplant_in_late_flower_blocked(self, engine):
        """Transplant in late_flower is blocked."""
        result = engine.validate("transplant", "late_flower", [])
        assert result["can_perform"] is False

    def test_supercropping_in_ripening_blocked(self, engine):
        """Supercropping in ripening is blocked (mid/late keyword)."""
        result = engine.validate("supercropping", "ripening", [])
        assert result["can_perform"] is False

    def test_all_forbidden_mid_flower_tasks_covered(self, engine):
        """Every task in FORBIDDEN_MID_FLOWER is blocked during mid_flower."""
        for task in FORBIDDEN_MID_FLOWER:
            result = engine.validate(task, "mid_flower", [])
            assert result["can_perform"] is False, f"{task} should be blocked in mid_flower"


class TestRecoveryWindow:
    """Tests for recovery time after recent HST."""

    def test_recent_hst_within_recovery_blocked(self, engine):
        """A recent HST task within the recovery window blocks new HST."""
        recent = [_make_hst_task("topping", days_ago=2)]
        result = engine.validate("supercropping", "vegetative", recent, species_name="Cannabis Sativa")
        assert result["can_perform"] is False
        assert "recover" in result["reason"].lower()
        assert result["recovery_status"] is not None
        assert result["recovery_status"]["recovered"] is False

    def test_hst_after_recovery_period_allowed(self, engine):
        """An HST task after the recovery period is allowed."""
        recent = [_make_hst_task("topping", days_ago=10)]
        result = engine.validate("supercropping", "vegetative", recent, species_name="Cannabis Sativa")
        assert result["can_perform"] is True
        assert result["recovery_status"]["recovered"] is True

    def test_cannabis_recovery_7_days(self, engine):
        """Cannabis species use 7-day recovery window."""
        # 5 days ago: well within 7-day window, at least 1 full day remaining
        recent = [_make_hst_task("topping", days_ago=5)]
        result = engine.validate("supercropping", "vegetative", recent, species_name="Cannabis Indica")
        assert result["can_perform"] is False
        assert result["recovery_status"]["days_remaining"] > 0

    def test_tomato_recovery_3_days(self, engine):
        """Tomato species use 3-day recovery window."""
        # 4 days ago: outside 3-day window
        recent = [_make_hst_task("topping", days_ago=4)]
        result = engine.validate("supercropping", "vegetative", recent, species_name="Tomato Roma")
        assert result["can_perform"] is True

    def test_pepper_recovery_5_days(self, engine):
        """Pepper species use 5-day recovery window."""
        recent = [_make_hst_task("topping", days_ago=3)]
        result = engine.validate("supercropping", "vegetative", recent, species_name="Bell Pepper")
        assert result["can_perform"] is False

    def test_unknown_species_uses_default(self, engine):
        """Unknown species uses default recovery of 5 days."""
        assert RECOVERY_DAYS["default"] == 5
        recent = [_make_hst_task("topping", days_ago=4)]
        result = engine.validate("supercropping", "vegetative", recent, species_name="Unknown Plant")
        assert result["can_perform"] is False

    def test_no_recent_hst_no_recovery(self, engine):
        """No recent HST means no recovery check needed."""
        result = engine.validate("topping", "vegetative", [])
        assert result["can_perform"] is True
        assert result["recovery_status"] is None

    def test_task_name_normalized(self, engine):
        """Task names with spaces/hyphens are normalized to underscores."""
        result = engine.validate("heavy defoliation", "flowering", [])
        assert result["can_perform"] is False

        result2 = engine.validate("heavy-defoliation", "flowering", [])
        assert result2["can_perform"] is False
