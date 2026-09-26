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


@pytest.mark.asyncio
async def test_a_failed_batch_channel_logs_no_push_endpoint_path(engine, channel) -> None:
    """#1796: a channel's error detail can carry a push endpoint whose path is the device token."""
    import structlog.testing

    token = "dEvIcE-ToKeN-1796"
    channel.supports_batching = True
    channel.send_batch = AsyncMock(
        return_value=ChannelResult(
            channel_key="home_assistant",
            success=False,
            error=f"https://fcm.googleapis.com/fcm/send/{token} | https://push.example/x?auth={token}: boom",
        )
    )

    with structlog.testing.capture_logs() as logs:
        await engine.notify_batch("u1", "t1", [_notification("care_watering")])

    (entry,) = [e for e in logs if e["event"] == "batch_channel_failed"]
    assert token not in repr(logs)
    assert "fcm.googleapis.com" in entry["error"]


# ── #1827: expired Web-Push subscriptions are pruned ──────────────────────────


class _Prefs:
    """An in-memory preference repository: what ``upsert`` stores, ``get_by_user`` returns."""

    def __init__(self, prefs: NotificationPreferences) -> None:
        self.stored = prefs
        self.upserts = 0
        self.removals = 0

    def get_by_user(self, user_key: str) -> NotificationPreferences:
        return self.stored.model_copy(deep=True)

    def upsert(self, prefs: NotificationPreferences) -> NotificationPreferences:
        self.upserts += 1
        self.stored = prefs.model_copy(deep=True)
        return self.stored

    def remove_subscriptions(self, user_key: str, channel_key: str, endpoints: list[str]) -> int:
        """What the Arango repository does in one UPDATE (its AQL is held by an integration test)."""
        pref = self.stored.channels.get(channel_key)
        if pref is None:
            return 0
        current = pref.config.get("subscriptions", [])
        kept = [s for s in current if s.get("endpoint") not in set(endpoints)]
        pref.config["subscriptions"] = kept
        self.removals += 1
        return len(current) - len(kept)


_LIVE = "https://fcm.googleapis.com/fcm/send/live-1827"
_GONE = "https://fcm.googleapis.com/fcm/send/gone-1827"


def _pwa_world(monkeypatch: pytest.MonkeyPatch):
    """The real PWA channel with pywebpush replaced: ``_GONE`` answers 410, ``_LIVE`` is delivered."""
    from app.data_access.external import pwa_notification_channel as pwa
    from app.domain.engines.notification_channel_registry import NotificationChannelRegistry
    from app.domain.models.notification import ChannelPreference

    class _WebPushException(Exception):  # noqa: N818 — mirrors pywebpush.WebPushException
        def __init__(self, status_code: int) -> None:
            super().__init__("push failed")
            self.response = MagicMock(status_code=status_code)

    def webpush(*, subscription_info, **_kwargs):
        if subscription_info["endpoint"] == _GONE:
            raise _WebPushException(410)

    monkeypatch.setattr(pwa, "_import_pywebpush", lambda: (webpush, _WebPushException))
    monkeypatch.setattr(pwa, "is_safe_push_endpoint", lambda _endpoint: True)
    registry = NotificationChannelRegistry()
    registry.register(pwa.PwaNotificationChannel("vapid-private-key-1827", "ops@example.org"))
    prefs = _prefs()
    prefs.quiet_hours.enabled = False  # delivery now, whatever the wall clock says
    prefs.channels["pwa"] = ChannelPreference(
        enabled=True,
        config={
            "subscriptions": [
                {"endpoint": _GONE, "p256dh": "k", "auth": "a"},
                {"endpoint": _LIVE, "p256dh": "k", "auth": "a"},
            ]
        },
    )
    repo = _Prefs(prefs)
    notifications = MagicMock()
    notifications.create.side_effect = lambda n: n
    redis = MagicMock()
    redis.get.return_value = None
    return NotificationEngine(notifications, repo, registry, redis), repo


def _stored_endpoints(repo: _Prefs) -> list[str]:
    return [s["endpoint"] for s in repo.stored.channels["pwa"].config["subscriptions"]]


@pytest.mark.asyncio
async def test_a_send_with_an_expired_and_a_live_subscription_keeps_only_the_live_one(monkeypatch) -> None:
    import structlog.testing

    engine, repo = _pwa_world(monkeypatch)
    repo.stored.channels = {"pwa": repo.stored.channels["pwa"]}

    with structlog.testing.capture_logs() as logs:
        result = await engine.notify("u1", "t1", _notification("care.watering.due"))

    assert result["channels_sent"] == ["pwa"]
    assert _stored_endpoints(repo) == [_LIVE]
    assert "gone-1827" not in repr(logs)
    (pruned,) = [e for e in logs if e["event"] == "push_subscriptions_pruned"]
    assert pruned["pruned"] == 1


@pytest.mark.asyncio
async def test_the_batch_path_prunes_too(monkeypatch) -> None:
    engine, repo = _pwa_world(monkeypatch)
    repo.stored.channels = {"pwa": repo.stored.channels["pwa"]}

    await engine.notify_batch("u1", "t1", [_notification("care.watering.due")])

    assert _stored_endpoints(repo) == [_LIVE]


def test_a_result_without_expired_endpoints_writes_nothing() -> None:
    repo = _Prefs(_prefs())
    engine = NotificationEngine(MagicMock(), repo, MagicMock(), MagicMock())

    pruned = engine.prune_expired_subscriptions("u1", ChannelResult(channel_key="pwa", success=True))

    assert pruned == 0
    assert repo.upserts == 0 and repo.removals == 0


def test_pruning_never_rewrites_the_whole_preferences_document() -> None:
    """#1892 security review: a read-then-upsert could recreate preferences an erasure removed meanwhile.

    The double stands for a document that is gone by the time a write arrives:
    ``upsert`` would insert it again (with the remaining subscriptions and the
    rest of the channel config); ``remove_subscriptions`` finds nothing.
    """

    class _ErasedMeanwhile(_Prefs):
        recreated = False

        def upsert(self, prefs: NotificationPreferences) -> NotificationPreferences:
            self.recreated = True  # recorded, not raised: the engine swallows a failed write
            return prefs

        def remove_subscriptions(self, user_key: str, channel_key: str, endpoints: list[str]) -> int:
            return 0

    prefs = _prefs()
    from app.domain.models.notification import ChannelPreference

    prefs.channels["pwa"] = ChannelPreference(enabled=True, config={"subscriptions": [{"endpoint": _GONE}]})
    repo = _ErasedMeanwhile(prefs)
    engine = NotificationEngine(MagicMock(), repo, MagicMock(), MagicMock())

    pruned = engine.prune_expired_subscriptions(
        "u1", ChannelResult(channel_key="pwa", success=False, expired_endpoints=[_GONE])
    )

    assert pruned == 0
    assert not repo.recreated, "the prune wrote the whole preferences document back"
