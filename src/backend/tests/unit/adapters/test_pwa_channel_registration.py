"""Tests for notification channel registration (PWA + email)."""

from unittest.mock import MagicMock

from app.data_access.external.email_notification_channel import EmailNotificationChannel
from app.data_access.external.pwa_notification_channel import PwaNotificationChannel
from app.domain.engines.notification_channel_registry import NotificationChannelRegistry


def _register_like_lifespan(*, vapid_public: str, vapid_private: str) -> None:
    """Mirror the registration logic in main.py lifespan (email + conditional PWA)."""
    # Email channel — unconditional, best-effort.
    NotificationChannelRegistry.register(EmailNotificationChannel(MagicMock()))

    # Web Push channel — only when both VAPID keys are configured.
    if vapid_public and vapid_private:
        NotificationChannelRegistry.register(PwaNotificationChannel(vapid_private, "ops@kamerplanter.example"))


class TestChannelRegistration:
    def test_pwa_registered_when_vapid_configured(self) -> None:
        NotificationChannelRegistry.clear()
        _register_like_lifespan(vapid_public="pub", vapid_private="priv")

        keys = set(NotificationChannelRegistry.all_keys())
        assert "pwa" in keys
        assert "email" in keys

        pwa = NotificationChannelRegistry.get("pwa")
        assert isinstance(pwa, PwaNotificationChannel)

        NotificationChannelRegistry.clear()

    def test_pwa_not_registered_without_vapid(self) -> None:
        NotificationChannelRegistry.clear()
        _register_like_lifespan(vapid_public="", vapid_private="")

        keys = set(NotificationChannelRegistry.all_keys())
        assert "pwa" not in keys
        # Email is always registered, even without VAPID.
        assert "email" in keys

        NotificationChannelRegistry.clear()
