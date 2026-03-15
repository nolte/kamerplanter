from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch

from app.common.enums import CareStyleType, ConfirmAction, ReminderType, WateringMethod
from app.domain.engines.care_reminder_engine import (
    CARE_STYLE_PRESETS,
    FAMILY_CARE_MAP,
    CareReminderEngine,
)
from app.domain.models.care_reminder import CareConfirmation, CareProfile


def _make_profile(**overrides) -> CareProfile:
    defaults = {
        "_key": "prof1",
        "care_style": CareStyleType.TROPICAL,
        "watering_interval_days": 7,
        "winter_watering_multiplier": 1.5,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 14,
        "fertilizing_active_months": [3, 4, 5, 6, 7, 8, 9],
        "repotting_interval_months": 24,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": True,
        "humidity_check_interval_days": 7,
        "adaptive_learning_enabled": True,
        "plant_key": "plant1",
        "created_at": datetime(2024, 6, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return CareProfile(**defaults)


def _make_confirmation(
    reminder_type: ReminderType = ReminderType.WATERING,
    action: ConfirmAction = ConfirmAction.CONFIRMED,
    confirmed_at: datetime | None = None,
    snooze_days: int | None = None,
) -> CareConfirmation:
    return CareConfirmation(
        plant_key="plant1",
        care_profile_key="prof1",
        reminder_type=reminder_type,
        action=action,
        confirmed_at=confirmed_at or datetime.now(UTC),
        snooze_days=snooze_days,
    )


class TestPresets:
    def test_all_care_styles_have_presets(self):
        for style in CareStyleType:
            assert style in CARE_STYLE_PRESETS, f"Missing preset for {style}"

    def test_cactus_long_watering_interval(self):
        preset = CARE_STYLE_PRESETS[CareStyleType.CACTUS]
        assert preset["watering_interval_days"] >= 14

    def test_calathea_bottom_water(self):
        preset = CARE_STYLE_PRESETS[CareStyleType.CALATHEA]
        assert preset["watering_method"] == WateringMethod.BOTTOM_WATER

    def test_calathea_water_quality_hint(self):
        preset = CARE_STYLE_PRESETS[CareStyleType.CALATHEA]
        assert "fluoride" in preset.get("water_quality_hint", "").lower()


class TestFamilyCareMap:
    def test_araceae_maps_to_tropical(self):
        assert FAMILY_CARE_MAP["Araceae"] == CareStyleType.TROPICAL

    def test_orchidaceae_maps_to_orchid(self):
        assert FAMILY_CARE_MAP["Orchidaceae"] == CareStyleType.ORCHID

    def test_cactaceae_maps_to_cactus(self):
        assert FAMILY_CARE_MAP["Cactaceae"] == CareStyleType.CACTUS


class TestCalculateDueDate:
    engine = CareReminderEngine()

    def test_no_previous_confirmation_uses_creation_date(self):
        profile = _make_profile(created_at=datetime(2024, 6, 1, tzinfo=UTC))
        due = self.engine.calculate_due_date(profile, ReminderType.WATERING, None)
        assert due == date(2024, 6, 1)

    @patch("app.domain.engines.care_reminder_engine.date")
    def test_confirmed_adds_interval(self, mock_date):
        mock_date.today.return_value = date(2024, 6, 15)  # summer
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        profile = _make_profile(watering_interval_days=7)
        last = _make_confirmation(
            confirmed_at=datetime(2024, 6, 10, tzinfo=UTC),
        )
        due = self.engine.calculate_due_date(profile, ReminderType.WATERING, last)
        assert due == date(2024, 6, 17)

    def test_snoozed_adds_snooze_days(self):
        profile = _make_profile()
        last = _make_confirmation(
            action=ConfirmAction.SNOOZED,
            confirmed_at=datetime(2024, 6, 10, tzinfo=UTC),
            snooze_days=3,
        )
        due = self.engine.calculate_due_date(profile, ReminderType.WATERING, last)
        assert due == date(2024, 6, 13)

    @patch("app.domain.engines.care_reminder_engine.date")
    def test_winter_multiplier_applied(self, mock_date):
        mock_date.today.return_value = date(2024, 1, 15)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        profile = _make_profile(watering_interval_days=7, winter_watering_multiplier=2.0)
        last = _make_confirmation(confirmed_at=datetime(2024, 1, 1, tzinfo=UTC))
        due = self.engine.calculate_due_date(profile, ReminderType.WATERING, last, hemisphere="north")
        assert due == date(2024, 1, 15)  # 7 * 2.0 = 14 days


class TestCalculateUrgency:
    engine = CareReminderEngine()

    def test_overdue(self):
        yesterday = date.today() - timedelta(days=1)
        assert self.engine.calculate_urgency(yesterday) == "overdue"

    def test_due_today(self):
        assert self.engine.calculate_urgency(date.today()) == "due_today"

    def test_upcoming(self):
        tomorrow = date.today() + timedelta(days=1)
        assert self.engine.calculate_urgency(tomorrow) == "upcoming"

    def test_not_due(self):
        future = date.today() + timedelta(days=5)
        assert self.engine.calculate_urgency(future) == "not_due"

    def test_none_returns_not_due(self):
        assert self.engine.calculate_urgency(None) == "not_due"


class TestShouldGenerateReminder:
    engine = CareReminderEngine()

    def test_dormancy_suppresses_watering(self):
        profile = _make_profile()
        assert self.engine.should_generate_reminder(
            profile, ReminderType.WATERING, "dormancy",
        ) is False

    def test_dormancy_allows_pest_check(self):
        profile = _make_profile()
        assert self.engine.should_generate_reminder(
            profile, ReminderType.PEST_CHECK, "dormancy",
        ) is True

    def test_fertilizing_guard_inactive_month(self):
        profile = _make_profile(fertilizing_active_months=[4, 5, 6, 7, 8])
        assert self.engine.should_generate_reminder(
            profile, ReminderType.FERTILIZING, None, "north", month=1,
            has_nutrient_plan=True,
        ) is False

    def test_fertilizing_guard_active_month(self):
        profile = _make_profile(fertilizing_active_months=[4, 5, 6, 7, 8])
        assert self.engine.should_generate_reminder(
            profile, ReminderType.FERTILIZING, None, "north", month=6,
            has_nutrient_plan=True,
        ) is True

    def test_fertilizing_suppressed_without_nutrient_plan(self):
        profile = _make_profile()
        assert self.engine.should_generate_reminder(
            profile, ReminderType.FERTILIZING, month=6,
            has_nutrient_plan=False,
        ) is False

    def test_fertilizing_toggle_disabled(self):
        profile = _make_profile(auto_create_fertilizing_task=False)
        assert self.engine.should_generate_reminder(
            profile, ReminderType.FERTILIZING, month=6,
            has_nutrient_plan=True,
        ) is False

    def test_repotting_toggle_disabled(self):
        profile = _make_profile(auto_create_repotting_task=False)
        assert self.engine.should_generate_reminder(
            profile, ReminderType.REPOTTING,
        ) is False

    def test_pest_check_toggle_disabled(self):
        profile = _make_profile(auto_create_pest_check_task=False)
        assert self.engine.should_generate_reminder(
            profile, ReminderType.PEST_CHECK,
        ) is False

    def test_humidity_disabled(self):
        profile = _make_profile(humidity_check_enabled=False)
        assert self.engine.should_generate_reminder(
            profile, ReminderType.HUMIDITY_CHECK,
        ) is False

    def test_humidity_enabled(self):
        profile = _make_profile(humidity_check_enabled=True)
        assert self.engine.should_generate_reminder(
            profile, ReminderType.HUMIDITY_CHECK,
        ) is True

    def test_location_check_disabled(self):
        profile = _make_profile(location_check_enabled=False)
        assert self.engine.should_generate_reminder(
            profile, ReminderType.LOCATION_CHECK,
        ) is False

    def test_watering_normal_phase(self):
        profile = _make_profile()
        assert self.engine.should_generate_reminder(
            profile, ReminderType.WATERING, "vegetative",
        ) is True

    def test_watering_suppressed_by_active_plan(self):
        profile = _make_profile()
        assert self.engine.should_generate_reminder(
            profile, ReminderType.WATERING, has_active_watering_plan=True,
        ) is False

    def test_fertilizing_suppressed_by_active_plan(self):
        profile = _make_profile()
        assert self.engine.should_generate_reminder(
            profile, ReminderType.FERTILIZING, has_active_watering_plan=True, month=6,
            has_nutrient_plan=True,
        ) is False

    def test_pest_check_not_suppressed_by_active_plan(self):
        profile = _make_profile()
        assert self.engine.should_generate_reminder(
            profile, ReminderType.PEST_CHECK, has_active_watering_plan=True,
        ) is True


class TestAdaptiveLearning:
    engine = CareReminderEngine()

    def test_disabled_returns_none(self):
        profile = _make_profile(adaptive_learning_enabled=False)
        result = self.engine.apply_adaptive_learning(profile, ReminderType.WATERING, [])
        assert result is None

    def test_non_learning_type_returns_none(self):
        profile = _make_profile()
        result = self.engine.apply_adaptive_learning(profile, ReminderType.PEST_CHECK, [])
        assert result is None

    def test_insufficient_data_returns_none(self):
        profile = _make_profile()
        confirmations = [_make_confirmation(), _make_confirmation()]
        result = self.engine.apply_adaptive_learning(profile, ReminderType.WATERING, confirmations)
        assert result is None

    def test_consistent_8_day_pattern_adjusts_up(self):
        profile = _make_profile(watering_interval_days=7)
        base = datetime(2024, 6, 1, tzinfo=UTC)
        confirmations = [
            _make_confirmation(confirmed_at=base + timedelta(days=i * 8))
            for i in range(5)
        ]
        result = self.engine.apply_adaptive_learning(profile, ReminderType.WATERING, confirmations)
        assert result is not None
        assert result == 8  # +1 from default 7

    def test_consistent_5_day_pattern_adjusts_down(self):
        profile = _make_profile(watering_interval_days=7)
        base = datetime(2024, 6, 1, tzinfo=UTC)
        confirmations = [
            _make_confirmation(confirmed_at=base + timedelta(days=i * 5))
            for i in range(5)
        ]
        result = self.engine.apply_adaptive_learning(profile, ReminderType.WATERING, confirmations)
        assert result is not None
        assert result == 6  # -1 from default 7

    def test_deviation_capped_at_30_percent(self):
        profile = _make_profile(watering_interval_days=10)
        base = datetime(2024, 6, 1, tzinfo=UTC)
        # Very long intervals (20 days) — should be capped at 10*1.3=13
        confirmations = [
            _make_confirmation(confirmed_at=base + timedelta(days=i * 20))
            for i in range(5)
        ]
        result = self.engine.apply_adaptive_learning(profile, ReminderType.WATERING, confirmations)
        assert result is not None
        assert result <= 11  # only +1 step from default 10


class TestAutoGenerateProfile:
    engine = CareReminderEngine()

    def test_araceae_generates_tropical(self):
        profile = self.engine.auto_generate_profile(
            botanical_family="Araceae", plant_key="p1",
        )
        assert profile.care_style == CareStyleType.TROPICAL
        assert profile.auto_generated is True

    def test_cactaceae_generates_cactus(self):
        profile = self.engine.auto_generate_profile(
            botanical_family="Cactaceae", plant_key="p1",
        )
        assert profile.care_style == CareStyleType.CACTUS
        assert profile.watering_interval_days >= 14

    def test_unknown_family_defaults_to_tropical(self):
        profile = self.engine.auto_generate_profile(
            botanical_family="UnknownFamily", plant_key="p1",
        )
        assert profile.care_style == CareStyleType.TROPICAL

    def test_no_family_defaults_to_tropical(self):
        profile = self.engine.auto_generate_profile(plant_key="p1")
        assert profile.care_style == CareStyleType.TROPICAL


class TestHemisphereAwareness:
    engine = CareReminderEngine()

    @patch("app.domain.engines.care_reminder_engine.date")
    def test_southern_hemisphere_winter_in_july(self, mock_date):
        mock_date.today.return_value = date(2024, 7, 15)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        profile = _make_profile(watering_interval_days=7, winter_watering_multiplier=2.0)
        last = _make_confirmation(confirmed_at=datetime(2024, 7, 1, tzinfo=UTC))
        due = self.engine.calculate_due_date(profile, ReminderType.WATERING, last, hemisphere="south")
        assert due == date(2024, 7, 15)  # 7 * 2.0 = 14 days

    @patch("app.domain.engines.care_reminder_engine.date")
    def test_southern_hemisphere_summer_in_january(self, mock_date):
        mock_date.today.return_value = date(2024, 1, 15)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        profile = _make_profile(watering_interval_days=7, winter_watering_multiplier=2.0)
        last = _make_confirmation(confirmed_at=datetime(2024, 1, 1, tzinfo=UTC))
        due = self.engine.calculate_due_date(profile, ReminderType.WATERING, last, hemisphere="south")
        assert due == date(2024, 1, 8)  # no multiplier — summer
