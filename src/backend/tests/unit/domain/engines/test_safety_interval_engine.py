"""Unit tests for the safety interval engine."""

from datetime import datetime, timedelta

import pytest

from app.domain.engines.safety_interval_engine import SafetyIntervalValidator


@pytest.fixture
def engine():
    return SafetyIntervalValidator()


class TestCanHarvest:
    """Tests for the can_harvest method."""

    def test_no_karenz_periods_returns_safe(self, engine):
        """No active karenz periods means harvest is always safe."""
        can, blocking = engine.can_harvest([], datetime.now())
        assert can is True
        assert blocking == []

    def test_expired_karenz_returns_safe(self, engine):
        """A karenz period that ended before the harvest date is not blocking."""
        periods = [
            {
                "active_ingredient": "Neem Oil",
                "applied_at": datetime.now() - timedelta(days=30),
                "safety_interval_days": 14,
            },
        ]
        planned = datetime.now()
        can, blocking = engine.can_harvest(periods, planned)
        assert can is True
        assert blocking == []

    def test_active_karenz_returns_blocked(self, engine):
        """A karenz period that hasn't expired blocks the harvest."""
        applied = datetime.now() - timedelta(days=3)
        periods = [
            {
                "active_ingredient": "Pyrethrin",
                "applied_at": applied,
                "safety_interval_days": 14,
            },
        ]
        planned = datetime.now()
        can, blocking = engine.can_harvest(periods, planned)
        assert can is False
        assert len(blocking) == 1
        assert blocking[0]["active_ingredient"] == "Pyrethrin"
        assert blocking[0]["days_remaining"] > 0

    def test_multiple_periods_mixed_expiry(self, engine):
        """Mix of expired and active periods: only active ones block."""
        now = datetime.now()
        periods = [
            {
                "active_ingredient": "Neem Oil",
                "applied_at": now - timedelta(days=30),
                "safety_interval_days": 7,
            },
            {
                "active_ingredient": "Spinosad",
                "applied_at": now - timedelta(days=2),
                "safety_interval_days": 14,
            },
            {
                "active_ingredient": "Copper Sulfate",
                "applied_at": now - timedelta(days=1),
                "safety_interval_days": 21,
            },
        ]
        can, blocking = engine.can_harvest(periods, now)
        assert can is False
        assert len(blocking) == 2
        ingredients = {b["active_ingredient"] for b in blocking}
        assert "Spinosad" in ingredients
        assert "Copper Sulfate" in ingredients
        assert "Neem Oil" not in ingredients

    def test_all_active_karenz_returns_blocked(self, engine):
        """All karenz periods still active means fully blocked."""
        now = datetime.now()
        periods = [
            {
                "active_ingredient": "A",
                "applied_at": now - timedelta(days=1),
                "safety_interval_days": 10,
            },
            {
                "active_ingredient": "B",
                "applied_at": now - timedelta(days=2),
                "safety_interval_days": 14,
            },
        ]
        can, blocking = engine.can_harvest(periods, now)
        assert can is False
        assert len(blocking) == 2

    def test_karenz_exactly_expired_returns_safe(self, engine):
        """A karenz period that expires exactly at harvest time is safe."""
        now = datetime.now()
        periods = [
            {
                "active_ingredient": "Neem Oil",
                "applied_at": now - timedelta(days=14),
                "safety_interval_days": 14,
            },
        ]
        can, blocking = engine.can_harvest(periods, now)
        assert can is True
        assert blocking == []

    def test_applied_at_as_iso_string(self, engine):
        """applied_at can be an ISO string instead of a datetime object."""
        applied = datetime.now() - timedelta(days=2)
        periods = [
            {
                "active_ingredient": "Test",
                "applied_at": applied.isoformat(),
                "safety_interval_days": 14,
            },
        ]
        can, blocking = engine.can_harvest(periods, datetime.now())
        assert can is False
        assert len(blocking) == 1

    def test_blocking_contains_safe_date(self, engine):
        """Blocking entries include the safe_date as ISO string."""
        applied = datetime(2026, 1, 1, 12, 0, 0)
        periods = [
            {
                "active_ingredient": "Test",
                "applied_at": applied,
                "safety_interval_days": 14,
            },
        ]
        planned = datetime(2026, 1, 10, 12, 0, 0)
        can, blocking = engine.can_harvest(periods, planned)
        assert can is False
        safe_date = datetime.fromisoformat(blocking[0]["safe_date"])
        assert safe_date == datetime(2026, 1, 15, 12, 0, 0)

    def test_days_remaining_calculated_correctly(self, engine):
        """days_remaining should be the difference between safe_date and planned."""
        applied = datetime(2026, 2, 1, 0, 0, 0)
        periods = [
            {
                "active_ingredient": "X",
                "applied_at": applied,
                "safety_interval_days": 20,
            },
        ]
        planned = datetime(2026, 2, 15, 0, 0, 0)
        can, blocking = engine.can_harvest(periods, planned)
        assert can is False
        assert blocking[0]["days_remaining"] == 6


class TestEarliestSafeHarvestDate:
    """Tests for the earliest_safe_harvest_date method."""

    def test_no_periods_returns_none(self, engine):
        """No karenz periods means no constraint."""
        result = engine.earliest_safe_harvest_date([])
        assert result is None

    def test_single_period(self, engine):
        """Single period returns its safe date."""
        applied = datetime(2026, 3, 1, 0, 0, 0)
        periods = [
            {
                "active_ingredient": "A",
                "applied_at": applied,
                "safety_interval_days": 10,
            },
        ]
        result = engine.earliest_safe_harvest_date(periods)
        assert result == datetime(2026, 3, 11, 0, 0, 0)

    def test_multiple_periods_returns_latest_safe_date(self, engine):
        """With multiple periods, the latest safe_date is the earliest safe harvest."""
        now = datetime(2026, 3, 1, 0, 0, 0)
        periods = [
            {
                "active_ingredient": "A",
                "applied_at": now,
                "safety_interval_days": 7,
            },
            {
                "active_ingredient": "B",
                "applied_at": now,
                "safety_interval_days": 21,
            },
            {
                "active_ingredient": "C",
                "applied_at": now,
                "safety_interval_days": 14,
            },
        ]
        result = engine.earliest_safe_harvest_date(periods)
        assert result == now + timedelta(days=21)

    def test_iso_string_applied_at(self, engine):
        """applied_at as ISO string should be parsed correctly."""
        applied = datetime(2026, 4, 1, 8, 0, 0)
        periods = [
            {
                "active_ingredient": "X",
                "applied_at": applied.isoformat(),
                "safety_interval_days": 5,
            },
        ]
        result = engine.earliest_safe_harvest_date(periods)
        assert result == datetime(2026, 4, 6, 8, 0, 0)

    def test_staggered_applications(self, engine):
        """Different application times with different intervals."""
        periods = [
            {
                "active_ingredient": "A",
                "applied_at": datetime(2026, 3, 1, 0, 0, 0),
                "safety_interval_days": 30,
            },
            {
                "active_ingredient": "B",
                "applied_at": datetime(2026, 3, 20, 0, 0, 0),
                "safety_interval_days": 14,
            },
        ]
        result = engine.earliest_safe_harvest_date(periods)
        # A safe_date = March 31, B safe_date = April 3
        assert result == datetime(2026, 4, 3, 0, 0, 0)
