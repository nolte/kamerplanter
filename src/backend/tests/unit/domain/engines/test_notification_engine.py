"""Unit tests for NotificationEngine quiet-hours bypass (Issue #409, F4).

Solitary unit tests: the repositories, channel registry and Redis client are the
owned I/O boundary and are doubled with mocks. The focus is the quiet-hours
gate — a ``frost_forecast_warning`` (proactive, high urgency) must be delivered
immediately during quiet hours, consistent with the reactive ``weather.frost``.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.engines.notification_engine import (
    _QUIET_HOURS_BYPASS_TYPES,
    NotificationEngine,
)
from app.domain.models.notification import (
    ChannelPreference,
    ChannelResult,
    Notification,
    NotificationPreferences,
    NotificationUrgency,
    QuietHoursPreference,
)


def _prefs() -> NotificationPreferences:
    return NotificationPreferences(
        user_key="u1",
        channels={"home_assistant": ChannelPreference(enabled=True, priority=10)},
        quiet_hours=QuietHoursPreference(enabled=True, start="22:00", end="07:00"),
    )


@pytest.fixture
def channel():
    ch = MagicMock()
    ch.channel_key = "home_assistant"
    ch.supports_actions = True
    ch.supports_batching = False
    ch.send = AsyncMock(return_value=ChannelResult(channel_key="home_assistant", success=True))
    return ch


@pytest.fixture
def engine(channel):
    preference_repo = MagicMock()
    preference_repo.get_by_user.return_value = _prefs()

    notification_repo = MagicMock()
    notification_repo.create.side_effect = lambda notif: notif

    registry = MagicMock()
    registry.get.return_value = channel
    registry.all_keys.return_value = ["home_assistant"]

    redis = MagicMock()
    redis.get.return_value = None  # never a Redis duplicate

    eng = NotificationEngine(
        notification_repo=notification_repo,
        preference_repo=preference_repo,
        channel_registry=registry,
        redis_client=redis,
    )
    # Force the quiet-hours window so the bypass decision is the only variable.
    eng._is_quiet_hours = MagicMock(return_value=True)  # type: ignore[method-assign]
    return eng


def _notification(notification_type: str) -> Notification:
    return Notification(
        notification_type=notification_type,
        title="Frost warning",
        body="Frost expected tonight.",
        urgency=NotificationUrgency.HIGH,
        group_key="frost-forecast:site1:2026-07-09",
    )


class TestQuietHoursBypassTypes:
    def test_frost_forecast_warning_is_a_bypass_type(self):
        assert "frost_forecast_warning" in _QUIET_HOURS_BYPASS_TYPES

    def test_reactive_weather_frost_still_bypasses(self):
        assert "weather.frost" in _QUIET_HOURS_BYPASS_TYPES


class TestNotifyDuringQuietHours:
    @pytest.mark.asyncio
    async def test_frost_forecast_warning_delivered_immediately(self, engine, channel):
        result = await engine.notify("u1", "t1", _notification("frost_forecast_warning"))

        assert result["status"] == "delivered"
        assert result["channels_sent"] == ["home_assistant"]
        channel.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_non_bypass_type_is_queued(self, engine, channel):
        result = await engine.notify("u1", "t1", _notification("care.watering.due"))

        assert result["status"] == "queued_quiet_hours"
        channel.send.assert_not_awaited()
