"""Unit tests for NotificationService (REQ-030)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.engines.notification_engine import NotificationEngine
from app.domain.models.notification import (
    ChannelPreference,
    Notification,
    NotificationPreferences,
    NotificationStatus,
)
from app.domain.services.notification_service import NotificationService


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
