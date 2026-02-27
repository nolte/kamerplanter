"""Unit tests for the inspection scheduler engine."""

from datetime import datetime, timedelta

import pytest

from app.domain.engines.inspection_scheduler import (
    BASE_INTERVAL_DAYS,
    PHASE_MULTIPLIERS,
    PRESSURE_MULTIPLIERS,
    InspectionScheduler,
)


@pytest.fixture
def engine():
    return InspectionScheduler()


class TestNextInspectionDate:
    """Tests for the next_inspection_date method."""

    def test_no_last_inspection_returns_now(self, engine):
        """If no inspection has been done, next inspection is effectively now."""
        result = engine.next_inspection_date(None, "vegetative", "none")
        # Should be very close to now (within a second)
        assert abs((result - datetime.now()).total_seconds()) < 2

    def test_vegetative_no_pressure(self, engine):
        """Vegetative phase with no pressure: base interval * 1.0 * 1.0 = 7 days."""
        last = datetime(2026, 3, 1, 10, 0, 0)
        result = engine.next_inspection_date(last, "vegetative", "none")
        expected = last + timedelta(days=BASE_INTERVAL_DAYS * 1.0 * 1.0)
        assert result == expected

    def test_flowering_no_pressure(self, engine):
        """Flowering phase with no pressure: base * 0.5 * 1.0 = 3.5 days."""
        last = datetime(2026, 3, 1, 10, 0, 0)
        result = engine.next_inspection_date(last, "flowering", "none")
        expected_days = BASE_INTERVAL_DAYS * PHASE_MULTIPLIERS["flowering"] * PRESSURE_MULTIPLIERS["none"]
        expected = last + timedelta(days=expected_days)
        assert result == expected

    def test_harvest_phase_high_pressure(self, engine):
        """Harvest phase with high pressure: most frequent inspections."""
        last = datetime(2026, 3, 1, 10, 0, 0)
        result = engine.next_inspection_date(last, "harvest", "high")
        expected_days = max(1, BASE_INTERVAL_DAYS * PHASE_MULTIPLIERS["harvest"] * PRESSURE_MULTIPLIERS["high"])
        expected = last + timedelta(days=expected_days)
        assert result == expected
        # Should be very frequent
        assert (result - last).total_seconds() / 86400 < 2

    def test_seedling_medium_pressure(self, engine):
        """Seedling with medium pressure."""
        last = datetime(2026, 3, 1, 10, 0, 0)
        result = engine.next_inspection_date(last, "seedling", "medium")
        expected_days = BASE_INTERVAL_DAYS * PHASE_MULTIPLIERS["seedling"] * PRESSURE_MULTIPLIERS["medium"]
        expected = last + timedelta(days=expected_days)
        assert result == expected

    def test_unknown_phase_defaults_to_1(self, engine):
        """Unknown phase uses multiplier 1.0 as default."""
        last = datetime(2026, 3, 1, 10, 0, 0)
        result = engine.next_inspection_date(last, "unknown_phase", "none")
        expected = last + timedelta(days=BASE_INTERVAL_DAYS * 1.0 * 1.0)
        assert result == expected

    def test_critical_pressure_very_frequent(self, engine):
        """Critical pressure leads to very frequent inspections."""
        last = datetime(2026, 3, 1, 10, 0, 0)
        result = engine.next_inspection_date(last, "vegetative", "critical")
        expected_days = BASE_INTERVAL_DAYS * PHASE_MULTIPLIERS["vegetative"] * PRESSURE_MULTIPLIERS["critical"]
        expected = last + timedelta(days=expected_days)
        assert result == expected

    def test_minimum_interval_is_one_day(self, engine):
        """Even extreme multipliers cannot go below 1 day."""
        last = datetime(2026, 3, 1, 10, 0, 0)
        result = engine.next_inspection_date(last, "harvest", "critical")
        days = (result - last).total_seconds() / 86400
        assert days >= 1.0


class TestCalculateUrgency:
    """Tests for the calculate_urgency method."""

    def test_overdue(self, engine):
        """A past due date is overdue."""
        now = datetime(2026, 3, 10, 12, 0, 0)
        next_due = datetime(2026, 3, 8, 12, 0, 0)
        result = engine.calculate_urgency(next_due, now=now)
        assert result["is_overdue"] is True
        assert result["days_until_due"] < 0
        assert result["urgency_level"] == "overdue"

    def test_due_today(self, engine):
        """Due within the same day is 'due_today'."""
        now = datetime(2026, 3, 10, 12, 0, 0)
        next_due = datetime(2026, 3, 10, 18, 0, 0)
        result = engine.calculate_urgency(next_due, now=now)
        assert result["is_overdue"] is False
        assert result["urgency_level"] == "due_today"

    def test_due_soon(self, engine):
        """Due within 1-3 days is 'due_soon'."""
        now = datetime(2026, 3, 10, 12, 0, 0)
        next_due = datetime(2026, 3, 12, 0, 0, 0)
        result = engine.calculate_urgency(next_due, now=now)
        assert result["is_overdue"] is False
        assert result["urgency_level"] == "due_soon"

    def test_scheduled(self, engine):
        """Due in more than 3 days is 'scheduled'."""
        now = datetime(2026, 3, 10, 12, 0, 0)
        next_due = datetime(2026, 3, 20, 12, 0, 0)
        result = engine.calculate_urgency(next_due, now=now)
        assert result["is_overdue"] is False
        assert result["urgency_level"] == "scheduled"
        assert result["days_until_due"] > 3

    def test_default_now(self, engine):
        """Without explicit now, uses current time."""
        next_due = datetime.now() + timedelta(days=10)
        result = engine.calculate_urgency(next_due)
        assert result["is_overdue"] is False
        assert result["urgency_level"] == "scheduled"
