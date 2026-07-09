"""Tests for notification channel registration (PWA + email + Home Assistant)."""

from collections.abc import Callable
from unittest.mock import MagicMock

from app.common.exceptions import ValidationError
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


def _register_ha_like_lifespan(get_ha_client: Callable[[], object]) -> None:
    """Mirror the HA channel registration in main.py lifespan.

    Home Assistant is an optional integration (REQ-018): a missing,
    unreachable or unresolvable HA_URL must never abort startup, so any
    failure only skips the HA channel.
    """
    try:
        ha_client = get_ha_client()
        if ha_client is not None:
            from app.data_access.external.ha_notification_channel import HomeAssistantNotificationChannel

            NotificationChannelRegistry.register(HomeAssistantNotificationChannel(ha_client))
    except Exception:
        pass
    # Email is registered afterwards and must survive an HA failure.
    NotificationChannelRegistry.register(EmailNotificationChannel(MagicMock()))


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


class TestHomeAssistantChannelRegistration:
    def test_unresolvable_ha_url_does_not_abort_startup(self) -> None:
        # get_ha_client raises when the configured HA_URL is unresolvable
        # (validate_ha_url in the client constructor). Startup must survive.
        def _raising_get_ha_client() -> object:
            raise ValidationError("Home Assistant URL host could not be resolved.")

        NotificationChannelRegistry.clear()
        _register_ha_like_lifespan(_raising_get_ha_client)

        keys = set(NotificationChannelRegistry.all_keys())
        assert "home_assistant" not in keys
        # The HA failure must not prevent later channels from registering.
        assert "email" in keys

        NotificationChannelRegistry.clear()

    def test_ha_not_registered_when_client_is_none(self) -> None:
        # No HA_URL configured → get_ha_client returns None → channel skipped.
        NotificationChannelRegistry.clear()
        _register_ha_like_lifespan(lambda: None)

        keys = set(NotificationChannelRegistry.all_keys())
        assert "home_assistant" not in keys
        assert "email" in keys

        NotificationChannelRegistry.clear()

    def test_ha_registered_when_client_available(self) -> None:
        NotificationChannelRegistry.clear()
        _register_ha_like_lifespan(lambda: MagicMock())

        keys = set(NotificationChannelRegistry.all_keys())
        assert "home_assistant" in keys
        assert "email" in keys

        NotificationChannelRegistry.clear()
