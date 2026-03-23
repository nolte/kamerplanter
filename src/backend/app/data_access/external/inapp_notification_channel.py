"""In-app notification channel adapter.

This is the fallback channel. Notifications are already persisted in ArangoDB
and served via the REST API. The channel itself is a no-op — it simply confirms
delivery since the notification is already stored and retrievable.
"""

from __future__ import annotations

from app.domain.interfaces.notification_channel import INotificationChannel
from app.domain.models.notification import ChannelResult, Notification


class InAppNotificationChannel(INotificationChannel):
    """No-op channel: notifications are already in DB, loaded via API."""

    @property
    def channel_key(self) -> str:
        return "in_app"

    @property
    def supports_actions(self) -> bool:
        return False

    @property
    def supports_batching(self) -> bool:
        return False

    async def send(
        self,
        notification: Notification,
        channel_config: dict,
    ) -> ChannelResult:
        # Notification is already persisted — nothing to deliver externally.
        return ChannelResult(channel_key=self.channel_key, success=True)
