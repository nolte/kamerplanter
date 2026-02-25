from app.domain.calculators.photoperiod_calculator import (
    calculate_dli,
    calculate_transition_schedule,
    is_long_day_triggered,
    is_short_day_triggered,
)


class TestTransitionSchedule:
    def test_7_day_transition(self):
        schedule = calculate_transition_schedule(18.0, 12.0, 7)
        assert len(schedule) == 7
        assert schedule[0]["photoperiod_hours"] < 18.0
        assert schedule[-1]["photoperiod_hours"] == 12.0

    def test_1_day_transition(self):
        schedule = calculate_transition_schedule(18.0, 12.0, 1)
        assert len(schedule) == 1
        assert schedule[0]["photoperiod_hours"] == 12.0

    def test_increasing_photoperiod(self):
        schedule = calculate_transition_schedule(12.0, 18.0, 3)
        assert schedule[-1]["photoperiod_hours"] == 18.0
        assert schedule[0]["photoperiod_hours"] > 12.0

    def test_has_lights_on_off(self):
        schedule = calculate_transition_schedule(18.0, 12.0, 3)
        for entry in schedule:
            assert "lights_on" in entry
            assert "lights_off" in entry


class TestDLI:
    def test_typical_calculation(self):
        dli = calculate_dli(400, 18.0)
        expected = 400 * 18.0 * 3600 / 1_000_000
        assert abs(dli - expected) < 0.01

    def test_zero_ppfd(self):
        assert calculate_dli(0, 18.0) == 0.0

    def test_zero_hours(self):
        assert calculate_dli(400, 0.0) == 0.0


class TestPhotoperiodTriggers:
    def test_short_day_triggered(self):
        assert is_short_day_triggered(10.0, 12.0) is True

    def test_short_day_not_triggered(self):
        assert is_short_day_triggered(14.0, 12.0) is False

    def test_long_day_triggered(self):
        assert is_long_day_triggered(14.0, 12.0) is True

    def test_long_day_not_triggered(self):
        assert is_long_day_triggered(10.0, 12.0) is False
