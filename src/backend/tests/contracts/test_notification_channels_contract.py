"""Consumer-driven contract: the backend (provider) must register a channel for
every user-facing notification channel the frontend (consumer) offers.

The shared contract is owned by the consumer (the frontend) and lives at
``src/frontend/src/contracts/notification-channels.json``; it is also asserted
from the frontend
(``src/frontend/src/test/contracts/notificationChannels.contract.test.ts``).

This guards the exact bug class that motivated it: the frontend offered a
``pwa`` (Browser Push) channel that the backend never registered, so
``POST /notifications/test`` returned ``Channel 'pwa' not found``. A drift on
either side — a key added to the frontend without a backend channel, or a
backend channel renamed — now fails a test before merge.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from app.data_access.external.apprise_notification_channel import AppriseNotificationChannel
from app.data_access.external.email_notification_channel import EmailNotificationChannel
from app.data_access.external.ha_notification_channel import HomeAssistantNotificationChannel
from app.data_access.external.pwa_notification_channel import PwaNotificationChannel
from app.domain.engines.notification_channel_registry import NotificationChannelRegistry

_CONTRACT_PATH = (
    Path(__file__).resolve().parents[4] / "src" / "frontend" / "src" / "contracts" / "notification-channels.json"
)


def _load_contract_channels() -> set[str]:
    data = json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))
    return set(data["user_facing_channels"])


def _register_all_user_facing_channels() -> None:
    """Register every user-facing channel with stub dependencies.

    The contract is about the channel-key vocabulary, not runtime configuration,
    so channels that are conditional at startup (Home Assistant, PWA) are
    force-registered here with stubs.
    """
    NotificationChannelRegistry.clear()
    NotificationChannelRegistry.register(HomeAssistantNotificationChannel(MagicMock()))
    NotificationChannelRegistry.register(EmailNotificationChannel(MagicMock()))
    NotificationChannelRegistry.register(AppriseNotificationChannel())
    NotificationChannelRegistry.register(PwaNotificationChannel("vapid-private-key", "ops@kamerplanter.example"))


class TestNotificationChannelContract:
    def test_contract_file_is_present_and_nonempty(self) -> None:
        channels = _load_contract_channels()
        assert channels, "contract must list at least one user-facing channel"

    def test_every_contract_channel_is_registrable(self) -> None:
        _register_all_user_facing_channels()
        registered = set(NotificationChannelRegistry.all_keys())
        contract = _load_contract_channels()

        missing = contract - registered
        assert not missing, (
            f"frontend offers channel(s) {sorted(missing)} with no backend channel "
            f"registered — POST /notifications/test would return 'Channel ... not found'. "
            f"Registered: {sorted(registered)}"
        )

    def test_every_contract_channel_resolves_in_registry(self) -> None:
        # Mirrors NotificationService.send_test: get(channel_key) must not be None.
        _register_all_user_facing_channels()
        for channel_key in sorted(_load_contract_channels()):
            channel = NotificationChannelRegistry.get(channel_key)
            assert channel is not None, f"Channel '{channel_key}' not found in registry"
            assert channel.channel_key == channel_key
