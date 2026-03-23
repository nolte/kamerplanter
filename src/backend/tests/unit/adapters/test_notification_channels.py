"""Tests for notification channel adapters."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.data_access.external.apprise_notification_channel import (
    AppriseNotificationChannel,
)
from app.data_access.external.email_notification_channel import (
    EmailNotificationChannel,
)
from app.data_access.external.ha_notification_channel import (
    HomeAssistantNotificationChannel,
)
from app.data_access.external.inapp_notification_channel import (
    InAppNotificationChannel,
)
from app.domain.models.notification import (
    Notification,
    NotificationAction,
    NotificationUrgency,
)


def _make_notification(**overrides) -> Notification:
    defaults = {
        "_key": "notif_123",
        "tenant_key": "t1",
        "user_key": "u1",
        "notification_type": "care_watering",
        "title": "Water your plants",
        "body": "Tomato needs watering",
        "urgency": NotificationUrgency.NORMAL,
    }
    defaults.update(overrides)
    return Notification(**defaults)


# ── InApp Channel ────────────────────────────────────────────────────


class TestInAppNotificationChannel:
    @pytest.fixture
    def channel(self):
        return InAppNotificationChannel()

    def test_properties(self, channel):
        assert channel.channel_key == "in_app"
        assert channel.supports_actions is False
        assert channel.supports_batching is False

    @pytest.mark.asyncio
    async def test_send_always_succeeds(self, channel):
        notification = _make_notification()
        result = await channel.send(notification, {})
        assert result.success is True
        assert result.channel_key == "in_app"
        assert result.error is None


# ── Email Channel ────────────────────────────────────────────────────


class TestEmailNotificationChannel:
    @pytest.fixture
    def mock_email_service(self):
        service = MagicMock()
        service.send_notification_email = MagicMock()
        return service

    @pytest.fixture
    def channel(self, mock_email_service):
        return EmailNotificationChannel(mock_email_service)

    def test_properties(self, channel):
        assert channel.channel_key == "email"
        assert channel.supports_actions is False
        assert channel.supports_batching is True

    @pytest.mark.asyncio
    async def test_send_success(self, channel, mock_email_service):
        notification = _make_notification()
        config = {"email": "user@example.com"}

        result = await channel.send(notification, config)

        assert result.success is True
        mock_email_service.send_notification_email.assert_called_once()
        call_args = mock_email_service.send_notification_email.call_args
        assert call_args[0][0] == "user@example.com"
        assert "Water your plants" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_send_no_email_in_config(self, channel):
        notification = _make_notification()
        result = await channel.send(notification, {})
        assert result.success is False
        assert "No email address" in result.error

    @pytest.mark.asyncio
    async def test_send_exception_caught(self, channel, mock_email_service):
        mock_email_service.send_notification_email.side_effect = (
            ConnectionError("SMTP down")
        )
        notification = _make_notification()
        config = {"email": "user@example.com"}

        result = await channel.send(notification, config)

        assert result.success is False
        assert "SMTP down" in result.error

    @pytest.mark.asyncio
    async def test_send_batch_success(self, channel, mock_email_service):
        notifications = [
            _make_notification(title="Task 1"),
            _make_notification(title="Task 2"),
        ]
        config = {"email": "user@example.com"}

        result = await channel.send_batch(notifications, config)

        assert result.success is True
        mock_email_service.send_notification_email.assert_called_once()
        call_args = mock_email_service.send_notification_email.call_args
        assert "2 Benachrichtigungen" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_send_batch_empty(self, channel):
        result = await channel.send_batch([], {})
        assert result.success is True


# ── HomeAssistant Channel ────────────────────────────────────────────


class TestHomeAssistantNotificationChannel:
    @pytest.fixture
    def mock_ha(self):
        ha = MagicMock()
        ha.fire_event = AsyncMock(return_value={"message": "ok"})
        ha.create_persistent_notification = AsyncMock()
        ha.dismiss_persistent_notification = AsyncMock()
        ha.call_service = AsyncMock(return_value=[])
        return ha

    @pytest.fixture
    def channel(self, mock_ha):
        return HomeAssistantNotificationChannel(mock_ha)

    def test_properties(self, channel):
        assert channel.channel_key == "home_assistant"
        assert channel.supports_actions is True
        assert channel.supports_batching is True

    @pytest.mark.asyncio
    async def test_send_fires_event(self, channel, mock_ha):
        notification = _make_notification()
        result = await channel.send(notification, {})

        assert result.success is True
        mock_ha.fire_event.assert_called_once()
        args = mock_ha.fire_event.call_args
        assert args[0][0] == "kamerplanter_notification"

    @pytest.mark.asyncio
    async def test_send_custom_event_type(self, channel, mock_ha):
        notification = _make_notification(
            ha_event_type="kamerplanter_care_due",
        )
        await channel.send(notification, {})

        args = mock_ha.fire_event.call_args
        assert args[0][0] == "kamerplanter_care_due"

    @pytest.mark.asyncio
    async def test_send_persistent_notification(self, channel, mock_ha):
        notification = _make_notification()
        config = {"persistent_notification": True}

        result = await channel.send(notification, config)

        assert result.success is True
        mock_ha.create_persistent_notification.assert_called_once()
        call_args = mock_ha.create_persistent_notification.call_args
        assert call_args[1]["title"] == "Water your plants"
        assert call_args[1]["notification_id"] == "kamerplanter_notif_123"

    @pytest.mark.asyncio
    async def test_send_mobile_push(self, channel, mock_ha):
        notification = _make_notification(
            urgency=NotificationUrgency.HIGH,
            actions=[
                NotificationAction(
                    action_id="done", title="Done", uri="/tasks",
                ),
            ],
        )
        config = {"mobile_push": True, "notify_service": "mobile_app_phone"}

        result = await channel.send(notification, config)

        assert result.success is True
        mock_ha.call_service.assert_called_once()
        args = mock_ha.call_service.call_args[0]
        assert args[0] == "notify"
        assert args[1] == "mobile_app_phone"
        service_data = args[2]
        assert service_data["data"]["importance"] == "high"
        assert len(service_data["data"]["actions"]) == 1

    @pytest.mark.asyncio
    async def test_send_tts(self, channel, mock_ha):
        notification = _make_notification()
        config = {
            "tts_enabled": True,
            "tts_entity_id": "media_player.kitchen",
        }

        result = await channel.send(notification, config)

        assert result.success is True
        mock_ha.call_service.assert_called_once()
        args = mock_ha.call_service.call_args[0]
        assert args[0] == "tts"
        assert args[1] == "speak"
        assert args[2]["entity_id"] == "media_player.kitchen"

    @pytest.mark.asyncio
    async def test_send_event_failure_captured(self, channel, mock_ha):
        mock_ha.fire_event.side_effect = ConnectionError("HA unreachable")
        notification = _make_notification()

        result = await channel.send(notification, {})

        assert result.success is False
        assert "fire_event failed" in result.error

    @pytest.mark.asyncio
    async def test_send_batch_merges_care(self, channel, mock_ha):
        notifications = [
            _make_notification(
                title="Water Tomato",
                notification_type="care_watering",
            ),
            _make_notification(
                title="Fertilize Basil",
                notification_type="care_fertilizing",
            ),
        ]
        result = await channel.send_batch(notifications, {})

        assert result.success is True
        # Should merge care notifications into one event fire
        mock_ha.fire_event.assert_called_once()
        event_data = mock_ha.fire_event.call_args[0][1]
        assert event_data["type"] == "care_summary"
        assert event_data["data"]["count"] == 2

    @pytest.mark.asyncio
    async def test_send_batch_non_care_sent_individually(self, channel, mock_ha):
        notifications = [
            _make_notification(
                title="System Alert",
                notification_type="system_alert",
            ),
            _make_notification(
                title="Phase Change",
                notification_type="phase_transition",
            ),
        ]
        result = await channel.send_batch(notifications, {})

        assert result.success is True
        assert mock_ha.fire_event.call_count == 2

    @pytest.mark.asyncio
    async def test_send_batch_empty(self, channel):
        result = await channel.send_batch([], {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_health_check_success(self, channel, mock_ha):
        assert await channel.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, channel, mock_ha):
        mock_ha.fire_event.side_effect = ConnectionError("down")
        assert await channel.health_check() is False


# ── Apprise Channel ─────────────────────────────────────────────────


class TestAppriseNotificationChannel:
    @pytest.fixture
    def channel(self):
        return AppriseNotificationChannel()

    def test_properties(self, channel):
        assert channel.channel_key == "apprise"
        assert channel.supports_actions is False
        assert channel.supports_batching is True

    @pytest.mark.asyncio
    async def test_send_no_urls(self, channel):
        notification = _make_notification()
        result = await channel.send(notification, {"urls": []})
        assert result.success is False
        assert "No Apprise URLs" in result.error

    @pytest.mark.asyncio
    async def test_send_no_urls_key(self, channel):
        notification = _make_notification()
        result = await channel.send(notification, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_send_apprise_not_installed(self, channel):
        notification = _make_notification()
        config = {"urls": ["tgram://bot/chat"]}

        with patch(
            "app.data_access.external.apprise_notification_channel._import_apprise",
            side_effect=ImportError("No module named 'apprise'"),
        ):
            result = await channel.send(notification, config)

        assert result.success is False
        assert "not installed" in result.error

    @pytest.mark.asyncio
    async def test_send_success(self, channel):
        notification = _make_notification(
            urgency=NotificationUrgency.HIGH,
        )
        config = {"urls": ["tgram://bot/chat"]}

        mock_apprise_mod = MagicMock()
        mock_apprise_mod.NotifyType.INFO = "info"
        mock_apprise_mod.NotifyType.WARNING = "warning"
        mock_apprise_mod.NotifyType.FAILURE = "failure"
        mock_ap_instance = MagicMock()
        mock_ap_instance.notify.return_value = True
        mock_apprise_mod.Apprise.return_value = mock_ap_instance

        with patch(
            "app.data_access.external.apprise_notification_channel._import_apprise",
            return_value=mock_apprise_mod,
        ):
            result = await channel.send(notification, config)

        assert result.success is True
        mock_ap_instance.add.assert_called_once_with(
            "tgram://bot/chat", tag=None,
        )
        mock_ap_instance.notify.assert_called_once()
        call_kwargs = mock_ap_instance.notify.call_args[1]
        assert call_kwargs["title"] == "Water your plants"
        assert call_kwargs["notify_type"] == "warning"

    @pytest.mark.asyncio
    async def test_send_failure_from_apprise(self, channel):
        notification = _make_notification()
        config = {"urls": ["tgram://bot/chat"]}

        mock_apprise_mod = MagicMock()
        mock_apprise_mod.NotifyType.INFO = "info"
        mock_apprise_mod.NotifyType.WARNING = "warning"
        mock_apprise_mod.NotifyType.FAILURE = "failure"
        mock_ap_instance = MagicMock()
        mock_ap_instance.notify.return_value = False
        mock_apprise_mod.Apprise.return_value = mock_ap_instance

        with patch(
            "app.data_access.external.apprise_notification_channel._import_apprise",
            return_value=mock_apprise_mod,
        ):
            result = await channel.send(notification, config)

        assert result.success is False
        assert "failure" in result.error.lower()

    @pytest.mark.asyncio
    async def test_send_batch_success(self, channel):
        notifications = [
            _make_notification(title="Task 1"),
            _make_notification(title="Task 2"),
        ]
        config = {"urls": ["slack://token_a/b/c"]}

        mock_apprise_mod = MagicMock()
        mock_apprise_mod.NotifyType.INFO = "info"
        mock_apprise_mod.NotifyType.WARNING = "warning"
        mock_apprise_mod.NotifyType.FAILURE = "failure"
        mock_ap_instance = MagicMock()
        mock_ap_instance.notify.return_value = True
        mock_apprise_mod.Apprise.return_value = mock_ap_instance

        with patch(
            "app.data_access.external.apprise_notification_channel._import_apprise",
            return_value=mock_apprise_mod,
        ):
            result = await channel.send_batch(notifications, config)

        assert result.success is True
        call_kwargs = mock_ap_instance.notify.call_args[1]
        assert "2 Benachrichtigungen" in call_kwargs["title"]

    @pytest.mark.asyncio
    async def test_send_batch_empty(self, channel):
        result = await channel.send_batch([], {"urls": ["x"]})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_health_check_installed(self, channel):
        with patch(
            "app.data_access.external.apprise_notification_channel._import_apprise",
            return_value=MagicMock(),
        ):
            assert await channel.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_not_installed(self, channel):
        with patch(
            "app.data_access.external.apprise_notification_channel._import_apprise",
            side_effect=ImportError,
        ):
            assert await channel.health_check() is False


# ── Channel Registry Integration ─────────────────────────────────────


class TestChannelRegistryIntegration:
    def test_all_channels_register(self):
        from app.domain.engines.notification_channel_registry import (
            NotificationChannelRegistry,
        )

        registry = NotificationChannelRegistry
        registry.clear()

        channels = [
            InAppNotificationChannel(),
            EmailNotificationChannel(MagicMock()),
            HomeAssistantNotificationChannel(MagicMock()),
            AppriseNotificationChannel(),
        ]

        for ch in channels:
            registry.register(ch)

        assert set(registry.all_keys()) == {
            "in_app", "email", "home_assistant", "apprise",
        }
        assert len(registry.get_available()) == 4

        # Cleanup
        registry.clear()
