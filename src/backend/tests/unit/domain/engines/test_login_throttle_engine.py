from datetime import UTC, datetime, timedelta

import pytest

from app.domain.engines.login_throttle_engine import LoginThrottleEngine


@pytest.fixture
def engine():
    return LoginThrottleEngine()


class TestCheckAllowed:
    def test_no_lockout(self, engine):
        assert engine.check_allowed(0, None) is True

    def test_below_threshold(self, engine):
        assert engine.check_allowed(4, None) is True

    def test_locked_but_expired(self, engine):
        past = datetime.now(UTC) - timedelta(minutes=1)
        assert engine.check_allowed(5, past) is True

    def test_locked_and_active(self, engine):
        future = datetime.now(UTC) + timedelta(minutes=10)
        assert engine.check_allowed(5, future) is False


class TestCalculateLockout:
    def test_below_threshold(self, engine):
        assert engine.calculate_lockout(0) is None
        assert engine.calculate_lockout(4) is None

    def test_at_threshold(self, engine):
        result = engine.calculate_lockout(5)
        assert result is not None
        expected_min = datetime.now(UTC) + timedelta(minutes=14)
        expected_max = datetime.now(UTC) + timedelta(minutes=16)
        assert expected_min < result < expected_max

    def test_exponential_backoff(self, engine):
        lock5 = engine.calculate_lockout(5)
        lock6 = engine.calculate_lockout(6)
        assert lock5 is not None
        assert lock6 is not None
        assert lock6 > lock5

    def test_max_lockout_cap(self, engine):
        result = engine.calculate_lockout(20)
        assert result is not None
        max_expected = datetime.now(UTC) + timedelta(minutes=241)
        assert result < max_expected


class TestShouldLock:
    def test_below_threshold(self, engine):
        assert engine.should_lock(0) is False
        assert engine.should_lock(4) is False

    def test_at_threshold(self, engine):
        assert engine.should_lock(5) is True

    def test_above_threshold(self, engine):
        assert engine.should_lock(10) is True


class TestGetLockoutMinutes:
    def test_no_lockout(self, engine):
        assert engine.get_lockout_minutes(None) == 0

    def test_expired_lockout(self, engine):
        past = datetime.now(UTC) - timedelta(minutes=5)
        assert engine.get_lockout_minutes(past) == 0

    def test_active_lockout(self, engine):
        future = datetime.now(UTC) + timedelta(minutes=10)
        result = engine.get_lockout_minutes(future)
        assert 9 <= result <= 11
