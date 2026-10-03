"""Apprise notification channel adapter.

Supports 100+ notification services (Telegram, Slack, Pushover, Gotify, ntfy,
email, etc.) via the Apprise library. Apprise is an optional dependency —
imported lazily to avoid hard failures when not installed.

Only a fixed allow-list of chat/push schemes is delivered to (#1947): the URL
list comes from a user-editable preference, and Apprise would otherwise mail or
POST to any third party the user names. Checked on save and again here; host
targets are also resolved and refused when they land in loopback/link-local/
reserved space (#1986). Redirects and Matrix discovery happen inside Apprise
and are not controllable here: that is the operator's egress policy.

Channel config expects:
  {
    "urls": ["tgram://bottoken/ChatID", "slack://token_a/token_b/..."],
    "tag": "optional-tag"
  }
"""

from __future__ import annotations

import asyncio
from functools import partial

import structlog

from app.common.log_privacy import loggable_error
from app.common.url_safety import partition_apprise_urls
from app.domain.interfaces.notification_channel import INotificationChannel
from app.domain.models.notification import (
    ChannelResult,
    Notification,
    NotificationUrgency,
)

logger = structlog.get_logger(__name__)


class AppriseNotificationChannel(INotificationChannel):
    """Delivers notifications via the Apprise multi-service library."""

    @property
    def channel_key(self) -> str:
        return "apprise"

    @property
    def supports_actions(self) -> bool:
        return False

    @property
    def supports_batching(self) -> bool:
        return True

    async def send(
        self,
        notification: Notification,
        channel_config: dict,
    ) -> ChannelResult:
        urls, refused = await _partition(channel_config.get("urls", []), _owner_key(notification))
        if refused:
            logger.warning("apprise_urls_refused_at_send", refused_count=refused)
        if not urls:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="No allowed Apprise URLs configured in channel_config"
                if refused
                else "No Apprise URLs configured in channel_config",
            )

        try:
            apprise_mod = _import_apprise()
        except ImportError:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="apprise package is not installed",
            )

        notify_type = _map_urgency(notification.urgency, apprise_mod)
        tag = channel_config.get("tag")

        ap = apprise_mod.Apprise()
        for url in urls:
            ap.add(url, tag=tag)

        # Apprise.notify() is synchronous — run in executor to avoid blocking
        loop = asyncio.get_running_loop()
        try:
            success = await loop.run_in_executor(
                None,
                partial(
                    ap.notify,
                    title=notification.title,
                    body=notification.body,
                    notify_type=notify_type,
                ),
            )
            if success:
                logger.debug(
                    "apprise_notification_sent",
                    notification_key=notification.key,
                    url_count=len(urls),
                )
                return ChannelResult(channel_key=self.channel_key, success=True)

            logger.warning(
                "apprise_notification_partial_failure",
                notification_key=notification.key,
            )
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="Apprise notify returned failure for one or more targets",
            )

        except Exception as exc:
            logger.error(
                "apprise_notification_failed",
                error=loggable_error(exc),
                exc_info=True,
            )
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error=f"Apprise send failed: {loggable_error(exc)}",
            )

    async def send_batch(
        self,
        notifications: list[Notification],
        channel_config: dict,
    ) -> ChannelResult:
        if not notifications:
            return ChannelResult(channel_key=self.channel_key, success=True)

        urls, refused = await _partition(channel_config.get("urls", []), _owner_key(notifications[0]))
        if refused:
            logger.warning("apprise_urls_refused_at_send", refused_count=refused)
        if not urls:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="No allowed Apprise URLs configured in channel_config"
                if refused
                else "No Apprise URLs configured in channel_config",
            )

        try:
            apprise_mod = _import_apprise()
        except ImportError:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="apprise package is not installed",
            )

        # Build a summary message
        max_urgency = max(
            notifications,
            key=lambda n: list(NotificationUrgency).index(n.urgency),
        )
        notify_type = _map_urgency(max_urgency.urgency, apprise_mod)

        title = f"Kamerplanter: {len(notifications)} Benachrichtigungen"
        body_lines = [f"- {n.title}: {n.body}" for n in notifications]
        body = "\n".join(body_lines)

        tag = channel_config.get("tag")
        ap = apprise_mod.Apprise()
        for url in urls:
            ap.add(url, tag=tag)

        loop = asyncio.get_running_loop()
        try:
            success = await loop.run_in_executor(
                None,
                partial(ap.notify, title=title, body=body, notify_type=notify_type),
            )
            if success:
                logger.debug(
                    "apprise_batch_sent",
                    count=len(notifications),
                )
                return ChannelResult(channel_key=self.channel_key, success=True)

            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="Apprise batch notify returned failure",
            )
        except Exception as exc:
            logger.error("apprise_batch_failed", error=loggable_error(exc), exc_info=True)
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error=f"Apprise batch send failed: {loggable_error(exc)}",
            )

    async def health_check(self) -> bool:
        try:
            _import_apprise()
            return True
        except ImportError:
            return False


# ── Module-level helpers ─────────────────────────────────────────────


#: Owner of a delivery whose notification names neither user nor tenant: such
#: deliveries share one resolver share (#1995).
_UNATTRIBUTED_OWNER = "unattributed"


def _owner_key(notification: Notification) -> str:
    """Whose share of the send resolver lane a delivery uses: recipient, else tenant (#1995)."""
    return notification.user_key or notification.tenant_key or _UNATTRIBUTED_OWNER


async def _partition(urls: object, owner_key: str) -> tuple[list[str], int]:
    """``partition_apprise_urls`` off the event loop: it resolves host targets (#1986)."""
    return await asyncio.get_running_loop().run_in_executor(
        None, partial(partition_apprise_urls, urls, owner_key=owner_key)
    )


def _import_apprise():  # noqa: ANN202
    """Lazy import of apprise to keep it an optional dependency."""
    import apprise  # noqa: PLC0415

    return apprise


def _map_urgency(urgency: NotificationUrgency, apprise_mod) -> str:  # noqa: ANN001
    """Map notification urgency to Apprise NotifyType."""
    mapping = {
        NotificationUrgency.LOW: apprise_mod.NotifyType.INFO,
        NotificationUrgency.NORMAL: apprise_mod.NotifyType.INFO,
        NotificationUrgency.HIGH: apprise_mod.NotifyType.WARNING,
        NotificationUrgency.CRITICAL: apprise_mod.NotifyType.FAILURE,
    }
    return mapping.get(urgency, apprise_mod.NotifyType.INFO)
