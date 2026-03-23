"""Email notification channel adapter.

Delivers notifications via the existing IEmailService (SMTP or console).
"""

from __future__ import annotations

from html import escape

import structlog

from app.domain.interfaces.email_service import IEmailService
from app.domain.interfaces.notification_channel import INotificationChannel
from app.domain.models.notification import (
    ChannelResult,
    Notification,
    NotificationUrgency,
)

logger = structlog.get_logger(__name__)

_URGENCY_EMOJI: dict[NotificationUrgency, str] = {
    NotificationUrgency.LOW: "&#8505;&#65039;",      # info
    NotificationUrgency.NORMAL: "&#9989;",            # check
    NotificationUrgency.HIGH: "&#9888;&#65039;",      # warning
    NotificationUrgency.CRITICAL: "&#128680;",        # rotating light
}

_URGENCY_COLOR: dict[NotificationUrgency, str] = {
    NotificationUrgency.LOW: "#2196F3",
    NotificationUrgency.NORMAL: "#4CAF50",
    NotificationUrgency.HIGH: "#FF9800",
    NotificationUrgency.CRITICAL: "#F44336",
}


class EmailNotificationChannel(INotificationChannel):
    """Delivers notifications as emails via IEmailService."""

    def __init__(self, email_service: IEmailService) -> None:
        self._email = email_service

    @property
    def channel_key(self) -> str:
        return "email"

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
        to_email = channel_config.get("email")
        if not to_email:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="No email address configured in channel_config",
            )

        subject = f"Kamerplanter: {notification.title}"
        html_body = self._render_single(notification)

        try:
            self._email.send_notification_email(to_email, subject, html_body)
            logger.debug(
                "email_notification_sent",
                to=to_email,
                notification_key=notification.key,
            )
            return ChannelResult(channel_key=self.channel_key, success=True)
        except Exception as exc:
            logger.error(
                "email_notification_failed",
                to=to_email,
                error=str(exc),
                exc_info=True,
            )
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error=f"Email send failed: {exc}",
            )

    async def send_batch(
        self,
        notifications: list[Notification],
        channel_config: dict,
    ) -> ChannelResult:
        if not notifications:
            return ChannelResult(channel_key=self.channel_key, success=True)

        to_email = channel_config.get("email")
        if not to_email:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="No email address configured in channel_config",
            )

        subject = f"Kamerplanter: {len(notifications)} Benachrichtigungen"
        html_body = self._render_batch(notifications)

        try:
            self._email.send_notification_email(to_email, subject, html_body)
            logger.debug(
                "email_notification_batch_sent",
                to=to_email,
                count=len(notifications),
            )
            return ChannelResult(channel_key=self.channel_key, success=True)
        except Exception as exc:
            logger.error(
                "email_notification_batch_failed",
                to=to_email,
                error=str(exc),
                exc_info=True,
            )
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error=f"Email batch send failed: {exc}",
            )

    # ── HTML rendering ───────────────────────────────────────────────

    @staticmethod
    def _render_single(notification: Notification) -> str:
        color = _URGENCY_COLOR.get(notification.urgency, "#4CAF50")
        emoji = _URGENCY_EMOJI.get(notification.urgency, "")
        title = escape(notification.title)
        body = escape(notification.body).replace("\n", "<br>")

        font = (
            "-apple-system, BlinkMacSystemFont, "
            "'Segoe UI', Roboto, sans-serif"
        )
        wrapper = f"font-family: {font}; max-width: 600px; margin: 0 auto"
        header = (
            f"background-color: {color}; color: white; "
            f"padding: 16px 24px; border-radius: 8px 8px 0 0"
        )
        content = (
            "padding: 24px; background-color: #f9f9f9; "
            "border: 1px solid #e0e0e0; border-top: none; "
            "border-radius: 0 0 8px 8px"
        )
        return (
            f'<div style="{wrapper}">'
            f'<div style="{header}">'
            f'<h2 style="margin: 0; font-size: 1.25rem;">'
            f"{emoji} {title}</h2></div>"
            f'<div style="{content}">'
            f'<p style="margin: 0; line-height: 1.6; color: #333;">'
            f"{body}</p></div>"
            f'<p style="text-align: center; color: #999; '
            f'font-size: 0.75rem; margin-top: 16px;">'
            f"Kamerplanter &mdash; Plant Lifecycle Management</p>"
            f"</div>"
        )

    @staticmethod
    def _render_batch(notifications: list[Notification]) -> str:
        items_html = ""
        for n in notifications:
            color = _URGENCY_COLOR.get(n.urgency, "#4CAF50")
            emoji = _URGENCY_EMOJI.get(n.urgency, "")
            title = escape(n.title)
            body = escape(n.body).replace("\n", "<br>")
            item_style = (
                f"border-left: 4px solid {color}; "
                "padding: 12px 16px; margin-bottom: 12px; "
                "background: white; border-radius: 0 4px 4px 0"
            )
            items_html += (
                f'<div style="{item_style}">'
                f"<strong>{emoji} {title}</strong>"
                f'<p style="margin: 4px 0 0; color: #555;">'
                f"{body}</p></div>"
            )

        font = (
            "-apple-system, BlinkMacSystemFont, "
            "'Segoe UI', Roboto, sans-serif"
        )
        wrapper = f"font-family: {font}; max-width: 600px; margin: 0 auto"
        header = (
            "background-color: #4CAF50; color: white; "
            "padding: 16px 24px; border-radius: 8px 8px 0 0"
        )
        content = (
            "padding: 16px; background-color: #f9f9f9; "
            "border: 1px solid #e0e0e0; border-top: none; "
            "border-radius: 0 0 8px 8px"
        )
        count = len(notifications)
        return (
            f'<div style="{wrapper}">'
            f'<div style="{header}">'
            f'<h2 style="margin: 0; font-size: 1.25rem;">'
            f"{count} Benachrichtigungen</h2></div>"
            f'<div style="{content}">{items_html}</div>'
            f'<p style="text-align: center; color: #999; '
            f'font-size: 0.75rem; margin-top: 16px;">'
            f"Kamerplanter &mdash; Plant Lifecycle Management</p>"
            f"</div>"
        )
