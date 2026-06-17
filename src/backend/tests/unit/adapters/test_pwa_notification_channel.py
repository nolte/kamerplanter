"""Unit tests for the PWA (Web Push) notification channel adapter."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.data_access.external.pwa_notification_channel import PwaNotificationChannel
from app.domain.models.notification import (
    Notification,
    NotificationAction,
    NotificationUrgency,
)


class _FakeWebPushException(Exception):  # noqa: N818 — mirrors pywebpush.WebPushException
    """Stand-in for pywebpush.WebPushException with a ``response`` carrying status."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.response = MagicMock()
        self.response.status_code = status_code


def _make_notification(**overrides) -> Notification:
    defaults = {
        "_key": "notif_123",
        "tenant_key": "t1",
        "user_key": "u1",
        "notification_type": "care_watering",
        "title": "Water your plants",
        "body": "Tomato needs watering",
        "urgency": NotificationUrgency.NORMAL,
        "group_key": "care:u1:watering",
    }
    defaults.update(overrides)
    return Notification(**defaults)


def _subscription(endpoint: str) -> dict:
    return {"endpoint": endpoint, "p256dh": "pub-key", "auth": "auth-secret"}


@pytest.fixture(autouse=True)
def _allow_test_endpoints():
    """Treat the synthetic ``https://push/...`` test endpoints as safe.

    The SSRF guard performs real DNS resolution, which would (a) require network
    access and (b) reject the non-resolvable hostnames used across these tests.
    Tests that specifically exercise the SSRF skip patch this themselves.
    """
    with patch(
        "app.data_access.external.pwa_notification_channel.is_safe_push_endpoint",
        return_value=True,
    ):
        yield


@pytest.fixture
def channel() -> PwaNotificationChannel:
    return PwaNotificationChannel(
        vapid_private_key="vapid-private",
        vapid_contact_email="ops@kamerplanter.example",
    )


def _patch_pywebpush(channel: PwaNotificationChannel, webpush_mock: MagicMock):
    """Patch the lazy import to return our mock + the fake exception type."""
    return patch(
        "app.data_access.external.pwa_notification_channel._import_pywebpush",
        lambda: (webpush_mock, _FakeWebPushException),
    )


class TestProperties:
    def test_properties(self, channel: PwaNotificationChannel) -> None:
        assert channel.channel_key == "pwa"
        assert channel.supports_actions is True
        assert channel.supports_batching is True


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_true_when_key_set(self, channel: PwaNotificationChannel) -> None:
        assert await channel.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_false_without_key(self) -> None:
        ch = PwaNotificationChannel(vapid_private_key="", vapid_contact_email="x@y.z")
        assert await ch.health_check() is False


class TestSend:
    @pytest.mark.asyncio
    async def test_empty_subscriptions(self, channel: PwaNotificationChannel) -> None:
        result = await channel.send(_make_notification(), {"subscriptions": []})
        assert result.success is False
        assert result.channel_key == "pwa"
        assert "No Web Push subscriptions" in (result.error or "")

    @pytest.mark.asyncio
    async def test_missing_subscriptions_key(self, channel: PwaNotificationChannel) -> None:
        result = await channel.send(_make_notification(), {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_success_path(self, channel: PwaNotificationChannel) -> None:
        webpush_mock = MagicMock(return_value=None)
        config = {"subscriptions": [_subscription("https://push/a"), _subscription("https://push/b")]}

        with _patch_pywebpush(channel, webpush_mock):
            result = await channel.send(_make_notification(), config)

        assert result.success is True
        assert result.error is None
        assert webpush_mock.call_count == 2

        # Payload + VAPID claims are wired correctly.
        _, kwargs = webpush_mock.call_args
        payload = json.loads(kwargs["data"])
        assert payload["title"] == "Water your plants"
        assert payload["tag"] == "care:u1:watering"
        assert payload["urgency"] == "normal"
        assert kwargs["vapid_private_key"] == "vapid-private"
        assert kwargs["vapid_claims"] == {"sub": "mailto:ops@kamerplanter.example"}
        assert kwargs["subscription_info"]["keys"]["p256dh"] == "pub-key"

    @pytest.mark.asyncio
    async def test_actions_in_payload(self, channel: PwaNotificationChannel) -> None:
        webpush_mock = MagicMock(return_value=None)
        notification = _make_notification(actions=[NotificationAction(action_id="done", title="Mark done", uri="/x")])
        config = {"subscriptions": [_subscription("https://push/a")]}

        with _patch_pywebpush(channel, webpush_mock):
            await channel.send(notification, config)

        _, kwargs = webpush_mock.call_args
        payload = json.loads(kwargs["data"])
        assert payload["actions"] == [{"action_id": "done", "title": "Mark done", "uri": "/x"}]

    @pytest.mark.asyncio
    async def test_partial_failure_still_succeeds(self, channel: PwaNotificationChannel) -> None:
        # First subscription fails with a generic 500, second succeeds.
        def side_effect(*, subscription_info, **_kwargs):
            if subscription_info["endpoint"] == "https://push/fail":
                raise _FakeWebPushException("boom", status_code=500)
            return None

        webpush_mock = MagicMock(side_effect=side_effect)
        config = {"subscriptions": [_subscription("https://push/fail"), _subscription("https://push/ok")]}

        with _patch_pywebpush(channel, webpush_mock):
            result = await channel.send(_make_notification(), config)

        # At least one delivered → success, but the error is reported.
        assert result.success is True
        assert "https://push/fail" in (result.error or "")
        assert "expired:" not in (result.error or "")

    @pytest.mark.asyncio
    async def test_all_fail_returns_failure(self, channel: PwaNotificationChannel) -> None:
        webpush_mock = MagicMock(side_effect=_FakeWebPushException("boom", status_code=500))
        config = {"subscriptions": [_subscription("https://push/a")]}

        with _patch_pywebpush(channel, webpush_mock):
            result = await channel.send(_make_notification(), config)

        assert result.success is False

    @pytest.mark.asyncio
    async def test_expired_410_collected(self, channel: PwaNotificationChannel) -> None:
        def side_effect(*, subscription_info, **_kwargs):
            if subscription_info["endpoint"] == "https://push/gone":
                raise _FakeWebPushException("gone", status_code=410)
            return None

        webpush_mock = MagicMock(side_effect=side_effect)
        config = {"subscriptions": [_subscription("https://push/gone"), _subscription("https://push/ok")]}

        with _patch_pywebpush(channel, webpush_mock):
            result = await channel.send(_make_notification(), config)

        # One delivered → success; expired endpoint surfaced for pruning.
        assert result.success is True
        assert "expired:https://push/gone" in (result.error or "")

    @pytest.mark.asyncio
    async def test_expired_404_collected(self, channel: PwaNotificationChannel) -> None:
        webpush_mock = MagicMock(side_effect=_FakeWebPushException("nope", status_code=404))
        config = {"subscriptions": [_subscription("https://push/missing")]}

        with _patch_pywebpush(channel, webpush_mock):
            result = await channel.send(_make_notification(), config)

        # The only subscription expired → nothing delivered → failure,
        # but the expired endpoint is still reported.
        assert result.success is False
        assert "expired:https://push/missing" in (result.error or "")

    @pytest.mark.asyncio
    async def test_unexpected_exception_does_not_abort_batch(self, channel: PwaNotificationChannel) -> None:
        def side_effect(*, subscription_info, **_kwargs):
            if subscription_info["endpoint"] == "https://push/crash":
                raise RuntimeError("unexpected")
            return None

        webpush_mock = MagicMock(side_effect=side_effect)
        config = {
            "subscriptions": [
                _subscription("https://push/crash"),
                _subscription("https://push/ok"),
            ]
        }

        with _patch_pywebpush(channel, webpush_mock):
            result = await channel.send(_make_notification(), config)

        assert result.success is True
        assert "https://push/crash" in (result.error or "")

    @pytest.mark.asyncio
    async def test_missing_vapid_private_key(self) -> None:
        ch = PwaNotificationChannel(vapid_private_key="", vapid_contact_email="x@y.z")
        result = await ch.send(_make_notification(), {"subscriptions": [_subscription("https://p/a")]})
        assert result.success is False
        assert "VAPID private key" in (result.error or "")


class TestSendSsrfDefense:
    """SEC-001 — the send loop must skip SSRF-unsafe stored endpoints."""

    @pytest.mark.asyncio
    async def test_unsafe_endpoint_is_skipped_not_dialed(self, channel: PwaNotificationChannel) -> None:
        webpush_mock = MagicMock(return_value=None)
        config = {
            "subscriptions": [
                _subscription("https://169.254.169.254/x"),  # cloud metadata — unsafe
                _subscription("https://push/ok"),  # treated as safe (autouse patch)
            ]
        }

        # Only the metadata endpoint is unsafe; the synthetic one is allowed.
        def is_safe(endpoint: str) -> bool:
            return "169.254.169.254" not in endpoint

        with (
            _patch_pywebpush(channel, webpush_mock),
            patch(
                "app.data_access.external.pwa_notification_channel.is_safe_push_endpoint",
                side_effect=is_safe,
            ),
        ):
            result = await channel.send(_make_notification(), config)

        # webpush was called exactly once — never for the unsafe endpoint.
        assert webpush_mock.call_count == 1
        _, kwargs = webpush_mock.call_args
        assert kwargs["subscription_info"]["endpoint"] == "https://push/ok"
        # The safe one delivered → overall success, unsafe one reported as error.
        assert result.success is True
        assert "169.254.169.254" in (result.error or "")

    @pytest.mark.asyncio
    async def test_all_unsafe_endpoints_yields_failure_without_dialing(self, channel: PwaNotificationChannel) -> None:
        webpush_mock = MagicMock(return_value=None)
        config = {"subscriptions": [_subscription("https://127.0.0.1/x")]}

        with (
            _patch_pywebpush(channel, webpush_mock),
            patch(
                "app.data_access.external.pwa_notification_channel.is_safe_push_endpoint",
                return_value=False,
            ),
        ):
            result = await channel.send(_make_notification(), config)

        webpush_mock.assert_not_called()
        assert result.success is False
