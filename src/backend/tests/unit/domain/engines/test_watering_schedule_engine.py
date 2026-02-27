from datetime import date

import pytest

from app.common.enums import ApplicationMethod, ScheduleMode
from app.domain.engines.watering_schedule_engine import WateringScheduleEngine
from app.domain.models.nutrient_plan import WateringSchedule


@pytest.fixture
def engine():
    return WateringScheduleEngine()


@pytest.fixture
def weekday_schedule():
    return WateringSchedule(
        schedule_mode=ScheduleMode.WEEKDAYS,
        weekday_schedule=[0, 2, 4],  # Mon, Wed, Fri
    )


@pytest.fixture
def interval_schedule():
    return WateringSchedule(
        schedule_mode=ScheduleMode.INTERVAL,
        interval_days=3,
    )


class TestIsWateringDue:
    def test_weekday_due(self, engine, weekday_schedule):
        # Monday 2026-02-02 is a Monday (weekday 0)
        monday = date(2026, 2, 2)
        assert engine.is_watering_due(weekday_schedule, monday) is True

    def test_weekday_not_due(self, engine, weekday_schedule):
        # Tuesday 2026-02-03 is a Tuesday (weekday 1)
        tuesday = date(2026, 2, 3)
        assert engine.is_watering_due(weekday_schedule, tuesday) is False

    def test_interval_due_no_last(self, engine, interval_schedule):
        assert engine.is_watering_due(interval_schedule, date(2026, 2, 1)) is True

    def test_interval_due_after_days(self, engine, interval_schedule):
        last = date(2026, 2, 1)
        check = date(2026, 2, 4)  # 3 days later
        assert engine.is_watering_due(interval_schedule, check, last) is True

    def test_interval_not_due_too_soon(self, engine, interval_schedule):
        last = date(2026, 2, 1)
        check = date(2026, 2, 3)  # only 2 days later
        assert engine.is_watering_due(interval_schedule, check, last) is False


class TestGetNextWateringDates:
    def test_weekday_dates(self, engine, weekday_schedule):
        from_date = date(2026, 2, 2)  # Monday
        dates = engine.get_next_watering_dates(weekday_schedule, from_date, days_ahead=7)
        # Mon, Wed, Fri of that week
        assert len(dates) == 3
        assert all(d.weekday() in [0, 2, 4] for d in dates)

    def test_interval_dates(self, engine, interval_schedule):
        from_date = date(2026, 2, 1)
        dates = engine.get_next_watering_dates(
            interval_schedule, from_date, days_ahead=10, last_watering_date=date(2026, 2, 1),
        )
        # Every 3 days: Feb 4, Feb 7, Feb 10
        assert len(dates) == 3

    def test_empty_for_none_interval(self, engine):
        # INTERVAL mode requires interval_days, so this should raise
        with pytest.raises(ValueError, match="interval_days required"):
            WateringSchedule(
                schedule_mode=ScheduleMode.INTERVAL,
                interval_days=None,
            )


class TestResolveDosages:
    def test_resolve_matching_phases(self):
        entries = [
            {"phase_name": "vegetative", "fertilizer_dosages": [{"fertilizer_key": "f1", "ml_per_liter": 2.0}]},
            {"phase_name": "flowering", "fertilizer_dosages": [{"fertilizer_key": "f2", "ml_per_liter": 3.0}]},
        ]
        plants_by_phase = {
            "vegetative": ["plant1", "plant2"],
            "flowering": ["plant3"],
        }
        result = WateringScheduleEngine.resolve_dosages_for_run(entries, plants_by_phase)
        assert "vegetative" in result
        assert result["vegetative"]["plant_keys"] == ["plant1", "plant2"]
        assert "flowering" in result

    def test_resolve_no_matching_phase(self):
        entries = [{"phase_name": "flowering", "fertilizer_dosages": []}]
        plants_by_phase = {"vegetative": ["plant1"]}
        result = WateringScheduleEngine.resolve_dosages_for_run(entries, plants_by_phase)
        assert "flowering" not in result


class TestWateringScheduleValidation:
    def test_weekdays_requires_schedule(self):
        with pytest.raises(ValueError, match="weekday_schedule required"):
            WateringSchedule(schedule_mode=ScheduleMode.WEEKDAYS)

    def test_interval_requires_days(self):
        with pytest.raises(ValueError, match="interval_days required"):
            WateringSchedule(schedule_mode=ScheduleMode.INTERVAL)

    def test_fertigation_not_allowed(self):
        with pytest.raises(ValueError, match="FERTIGATION not allowed"):
            WateringSchedule(
                schedule_mode=ScheduleMode.WEEKDAYS,
                weekday_schedule=[0],
                application_method=ApplicationMethod.FERTIGATION,
            )

    def test_valid_weekday_schedule(self):
        schedule = WateringSchedule(
            schedule_mode=ScheduleMode.WEEKDAYS,
            weekday_schedule=[0, 3, 6],
            preferred_time="08:00",
        )
        assert schedule.schedule_mode == ScheduleMode.WEEKDAYS
        assert schedule.reminder_hours_before == 2

    def test_invalid_weekday_value(self):
        with pytest.raises(ValueError, match="weekday_schedule values must be 0-6"):
            WateringSchedule(
                schedule_mode=ScheduleMode.WEEKDAYS,
                weekday_schedule=[7],
            )
