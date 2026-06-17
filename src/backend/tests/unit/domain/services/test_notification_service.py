"""Unit tests for NotificationService (REQ-030)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.exceptions import ValidationError
from app.domain.engines.notification_engine import NotificationEngine
from app.domain.models.notification import (
    ChannelPreference,
    Notification,
    NotificationPreferences,
    NotificationStatus,
)
from app.domain.services.notification_service import (
    MAX_PWA_SUBSCRIPTIONS_PER_USER,
    NotificationService,
)


@pytest.fixture
def mock_engine():
    engine = MagicMock(spec=NotificationEngine)
    engine.notify = AsyncMock(
        return_value={
            "status": "delivered",
            "notification_key": "notif_123",
            "channels_sent": ["home_assistant"],
            "channels_failed": [],
        }
    )
    engine.notify_batch = AsyncMock(return_value={"status": "batch_complete", "sent": 3, "failed": 0})
    engine._channel_registry = MagicMock()
    engine._channel_registry.get_available.return_value = []
    return engine


@pytest.fixture
def mock_notification_repo():
    repo = MagicMock()
    repo.list_for_user.return_value = []
    repo.count_unread.return_value = 0
    repo.get.return_value = None
    repo.mark_read.return_value = None
    repo.mark_acted.return_value = None
    return repo


@pytest.fixture
def mock_preference_repo():
    repo = MagicMock()
    repo.get_by_user.return_value = None
    repo.upsert.return_value = NotificationPreferences(user_key="user_1")
    return repo


@pytest.fixture
def service(mock_engine, mock_notification_repo, mock_preference_repo):
    return NotificationService(
        engine=mock_engine,
        notification_repo=mock_notification_repo,
        preference_repo=mock_preference_repo,
    )


class TestListNotifications:
    def test_list_all(self, service, mock_notification_repo):
        notif = Notification(
            key="n1",
            notification_type="care.watering",
            title="Water plant",
            body="Monstera needs water",
            user_key="user_1",
            tenant_key="tenant_1",
            status=NotificationStatus.DELIVERED,
        )
        mock_notification_repo.list_for_user.return_value = [notif]

        result = service.list_notifications("user_1", "tenant_1")

        assert len(result) == 1
        assert result[0].title == "Water plant"
        mock_notification_repo.list_for_user.assert_called_once()

    def test_list_unread_only(self, service, mock_notification_repo):
        service.list_notifications("user_1", "tenant_1", unread_only=True)

        call_kwargs = mock_notification_repo.list_for_user.call_args
        assert call_kwargs.kwargs.get("status") == NotificationStatus.DELIVERED


class TestCountUnread:
    def test_count(self, service, mock_notification_repo):
        mock_notification_repo.count_unread.return_value = 5

        result = service.count_unread("user_1", "tenant_1")

        assert result == 5


class TestMarkRead:
    def test_mark_read_success(self, service, mock_notification_repo):
        notif = Notification(
            key="n1",
            notification_type="care.watering",
            title="Test",
            body="Test",
            tenant_key="tenant_1",
            status=NotificationStatus.DELIVERED,
        )
        mock_notification_repo.get.return_value = notif
        mock_notification_repo.mark_read.return_value = notif

        result = service.mark_read("n1", "tenant_1")

        assert result is not None
        mock_notification_repo.mark_read.assert_called_once()

    def test_mark_read_not_found(self, service, mock_notification_repo):
        mock_notification_repo.get.return_value = None

        result = service.mark_read("n_missing", "tenant_1")

        assert result is None

    def test_mark_read_wrong_tenant(self, service, mock_notification_repo):
        notif = Notification(
            key="n1",
            notification_type="care.watering",
            title="Test",
            body="Test",
            tenant_key="other_tenant",
            status=NotificationStatus.DELIVERED,
        )
        mock_notification_repo.get.return_value = notif

        result = service.mark_read("n1", "tenant_1")

        assert result is None


class TestMarkActed:
    def test_mark_acted_success(self, service, mock_notification_repo):
        notif = Notification(
            key="n1",
            notification_type="care.watering",
            title="Test",
            body="Test",
            tenant_key="tenant_1",
            status=NotificationStatus.DELIVERED,
        )
        mock_notification_repo.get.return_value = notif
        mock_notification_repo.mark_acted.return_value = notif

        result = service.mark_acted("n1", "tenant_1", "confirm_watering")

        assert result is not None

    def test_mark_acted_wrong_tenant(self, service, mock_notification_repo):
        notif = Notification(
            key="n1",
            notification_type="care.watering",
            title="Test",
            body="Test",
            tenant_key="other_tenant",
            status=NotificationStatus.DELIVERED,
        )
        mock_notification_repo.get.return_value = notif

        result = service.mark_acted("n1", "tenant_1", "confirm_watering")

        assert result is None


class TestPreferences:
    def test_get_preferences_defaults(self, service, mock_preference_repo):
        mock_preference_repo.get_by_user.return_value = None

        prefs = service.get_preferences("user_1")

        assert isinstance(prefs, NotificationPreferences)
        # Default has home_assistant channel enabled
        assert "home_assistant" in prefs.channels

    def test_get_preferences_existing(self, service, mock_preference_repo):
        existing = NotificationPreferences(
            user_key="user_1",
            channels={
                "email": ChannelPreference(enabled=True, priority=5),
            },
        )
        mock_preference_repo.get_by_user.return_value = existing

        prefs = service.get_preferences("user_1")

        assert "email" in prefs.channels

    def test_update_preferences(self, service, mock_preference_repo):
        new_prefs = NotificationPreferences(
            user_key="user_1",
            channels={
                "home_assistant": ChannelPreference(enabled=True, priority=1),
                "email": ChannelPreference(enabled=True, priority=2),
            },
        )

        service.update_preferences("user_1", new_prefs)

        mock_preference_repo.upsert.assert_called_once()
        call_args = mock_preference_repo.upsert.call_args[0][0]
        assert call_args.user_key == "user_1"


class TestSendCareNotifications:
    @pytest.mark.asyncio
    async def test_empty_tasks(self, service):
        result = await service.send_care_notifications("tenant_1", [])

        assert result["status"] == "empty"
        assert result["users_notified"] == 0

    @pytest.mark.asyncio
    async def test_sends_batched_by_user(self, service, mock_engine):
        tasks = [
            {
                "user_key": "user_1",
                "plant_key": "p1",
                "plant_name": "Monstera",
                "reminder_type": "watering",
                "urgency": "due_today",
                "due_date": "2026-03-21",
            },
            {
                "user_key": "user_1",
                "plant_key": "p2",
                "plant_name": "Ficus",
                "reminder_type": "watering",
                "urgency": "due_today",
                "due_date": "2026-03-21",
            },
            {
                "user_key": "user_2",
                "plant_key": "p3",
                "plant_name": "Basilikum",
                "reminder_type": "fertilizing",
                "urgency": "overdue",
                "due_date": "2026-03-19",
            },
        ]

        result = await service.send_care_notifications("tenant_1", tasks)

        assert result["status"] == "complete"
        assert result["users_notified"] == 2
        assert mock_engine.notify_batch.call_count == 2


class TestSendTestNotification:
    @pytest.mark.asyncio
    async def test_send_test_unknown_channel(self, service, mock_engine):
        mock_engine._channel_registry.get.return_value = None

        result = await service.send_test("user_1", "tenant_1", "unknown")

        assert result["status"] == "error"
        assert "not found" in result["error"]


class TestPwaSubscriptions:
    @pytest.fixture(autouse=True)
    def _bypass_ssrf_validation(self):
        """Treat synthetic ``https://push/...`` endpoints as safe.

        The real validator does DNS resolution + IP-range rejection; the
        dedicated SSRF tests below exercise it instead of stubbing it.
        """
        with patch(
            "app.domain.services.notification_service.validate_push_endpoint",
            side_effect=lambda endpoint: endpoint,
        ):
            yield

    @pytest.fixture
    def echo_preference_repo(self):
        """Preference repo that starts empty and echoes upserted prefs back."""
        repo = MagicMock()
        repo.get_by_user.return_value = None
        repo.upsert.side_effect = lambda prefs: prefs
        return repo

    @pytest.fixture
    def echo_service(self, mock_engine, mock_notification_repo, echo_preference_repo):
        return NotificationService(
            engine=mock_engine,
            notification_repo=mock_notification_repo,
            preference_repo=echo_preference_repo,
        )

    def test_subscribe_creates_channel_and_enables(self, echo_service):
        endpoint = echo_service.subscribe_pwa(
            user_key="user_1",
            endpoint="https://push/a",
            p256dh="pub",
            auth="auth",
            user_agent="Firefox",
        )

        assert endpoint == "https://push/a"
        stored = echo_service._preference_repo.upsert.call_args.args[0]
        pwa = stored.channels["pwa"]
        assert pwa.enabled is True
        subs = pwa.config["subscriptions"]
        assert len(subs) == 1
        assert subs[0]["endpoint"] == "https://push/a"
        assert subs[0]["user_agent"] == "Firefox"

    def test_subscribe_dedupes_by_endpoint(self, mock_engine, mock_notification_repo):
        existing = NotificationPreferences(
            user_key="user_1",
            channels={
                "pwa": ChannelPreference(
                    enabled=True,
                    config={"subscriptions": [{"endpoint": "https://push/a", "p256dh": "old", "auth": "old"}]},
                )
            },
        )
        repo = MagicMock()
        repo.get_by_user.return_value = existing
        repo.upsert.side_effect = lambda prefs: prefs
        service = NotificationService(
            engine=mock_engine,
            notification_repo=mock_notification_repo,
            preference_repo=repo,
        )

        service.subscribe_pwa(
            user_key="user_1",
            endpoint="https://push/a",
            p256dh="new",
            auth="new",
        )

        stored = repo.upsert.call_args.args[0]
        subs = stored.channels["pwa"].config["subscriptions"]
        # Still exactly one entry for the endpoint, with the new keys.
        assert len(subs) == 1
        assert subs[0]["p256dh"] == "new"

    def test_unsubscribe_removes_endpoint(self, mock_engine, mock_notification_repo):
        existing = NotificationPreferences(
            user_key="user_1",
            channels={
                "pwa": ChannelPreference(
                    enabled=True,
                    config={
                        "subscriptions": [
                            {"endpoint": "https://push/a", "p256dh": "x", "auth": "y"},
                            {"endpoint": "https://push/b", "p256dh": "x", "auth": "y"},
                        ]
                    },
                )
            },
        )
        repo = MagicMock()
        repo.get_by_user.return_value = existing
        repo.upsert.side_effect = lambda prefs: prefs
        service = NotificationService(
            engine=mock_engine,
            notification_repo=mock_notification_repo,
            preference_repo=repo,
        )

        removed = service.unsubscribe_pwa(user_key="user_1", endpoint="https://push/a")

        assert removed is True
        stored = repo.upsert.call_args.args[0]
        subs = stored.channels["pwa"].config["subscriptions"]
        assert [s["endpoint"] for s in subs] == ["https://push/b"]

    def test_unsubscribe_missing_channel_returns_false(self, echo_service):
        removed = echo_service.unsubscribe_pwa(user_key="user_1", endpoint="https://push/x")
        assert removed is False
        echo_service._preference_repo.upsert.assert_not_called()

    def test_subscribe_rejects_ssrf_endpoint(self, echo_service):
        """SEC-001 — an SSRF-unsafe endpoint surfaces as a validation error,
        is never stored, and never reaches the preference repo."""
        # Re-stub the validator to reject this specific endpoint (overrides the
        # autouse bypass for this call).
        with (
            patch(
                "app.domain.services.notification_service.validate_push_endpoint",
                side_effect=ValidationError("Push endpoint resolves to a non-routable address."),
            ),
            pytest.raises(ValidationError),
        ):
            echo_service.subscribe_pwa(
                user_key="user_1",
                endpoint="https://169.254.169.254/x",
                p256dh="pub",
                auth="auth",
            )

        echo_service._preference_repo.upsert.assert_not_called()

    def test_subscribe_caps_subscriptions_keeping_newest(self, mock_engine, mock_notification_repo):
        """SEC-003 — adding more than the cap of distinct endpoints retains only
        the newest MAX, evicting the oldest (FIFO)."""
        # Stateful repo — persist upserted prefs so subscriptions accumulate
        # across calls (mirrors real persistence).
        store: dict[str, object] = {}

        repo = MagicMock()
        repo.get_by_user.side_effect = lambda user_key: store.get(user_key)

        def _upsert(prefs):
            store[prefs.user_key] = prefs
            return prefs

        repo.upsert.side_effect = _upsert
        service = NotificationService(
            engine=mock_engine,
            notification_repo=mock_notification_repo,
            preference_repo=repo,
        )

        total = MAX_PWA_SUBSCRIPTIONS_PER_USER + 5
        for i in range(total):
            service.subscribe_pwa(
                user_key="user_1",
                endpoint=f"https://push/{i}",
                p256dh="pub",
                auth="auth",
            )

        stored = repo.upsert.call_args.args[0]
        subs = stored.channels["pwa"].config["subscriptions"]
        endpoints = [s["endpoint"] for s in subs]

        assert len(subs) == MAX_PWA_SUBSCRIPTIONS_PER_USER
        # Oldest evicted, newest retained.
        assert endpoints[-1] == f"https://push/{total - 1}"
        assert "https://push/0" not in endpoints
        assert endpoints[0] == f"https://push/{total - MAX_PWA_SUBSCRIPTIONS_PER_USER}"
