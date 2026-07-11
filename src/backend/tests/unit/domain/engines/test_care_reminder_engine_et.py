"""REQ-037 × REQ-022 — the ET net demand suppresses the watering reminder.

An outdoor/greenhouse plant whose materialised net irrigation demand is zero (rain
already covered it) must not receive a watering reminder; indoor plants (no ET
data, ``None``) keep the interval-based behaviour untouched.
"""

from app.common.enums import ReminderType
from app.domain.engines.care_reminder_engine import CareReminderEngine


def _profile():
    return CareReminderEngine().auto_generate_profile(plant_key="p1")


class TestEtWateringSuppression:
    def test_zero_demand_suppresses_watering(self):
        engine = CareReminderEngine()
        assert (
            engine.should_generate_reminder(
                _profile(),
                ReminderType.WATERING,
                irrigation_demand_capped_mm=0.0,
            )
            is False
        )

    def test_positive_demand_does_not_suppress(self):
        engine = CareReminderEngine()
        assert (
            engine.should_generate_reminder(
                _profile(),
                ReminderType.WATERING,
                irrigation_demand_capped_mm=4.0,
            )
            is True
        )

    def test_none_demand_leaves_behaviour_unchanged(self):
        engine = CareReminderEngine()
        with_none = engine.should_generate_reminder(_profile(), ReminderType.WATERING)
        with_explicit_none = engine.should_generate_reminder(
            _profile(), ReminderType.WATERING, irrigation_demand_capped_mm=None
        )
        assert with_none == with_explicit_none is True

    def test_et_suppression_only_targets_watering(self):
        """A zero ET demand must not suppress non-watering reminders."""
        engine = CareReminderEngine()
        assert (
            engine.should_generate_reminder(
                _profile(),
                ReminderType.PEST_CHECK,
                irrigation_demand_capped_mm=0.0,
            )
            is True
        )
