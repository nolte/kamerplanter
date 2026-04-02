"""Home Assistant notification channel adapter.

Delivers notifications via the HA REST API using four mechanisms:
1. Custom event firing (for HA automations)
2. Persistent notifications (HA UI banner)
3. Mobile push via notify service
4. TTS announcements via tts.speak service
"""

from __future__ import annotations

import structlog

from app.data_access.external.ha_client import HomeAssistantClient
from app.domain.interfaces.notification_channel import INotificationChannel
from app.domain.models.notification import (
    ChannelResult,
    Notification,
    NotificationUrgency,
)

logger = structlog.get_logger(__name__)

_URGENCY_TO_IMPORTANCE: dict[NotificationUrgency, str] = {
    NotificationUrgency.LOW: "low",
    NotificationUrgency.NORMAL: "default",
    NotificationUrgency.HIGH: "high",
    NotificationUrgency.CRITICAL: "high",
}


class HomeAssistantNotificationChannel(INotificationChannel):
    """Delivers notifications through Home Assistant services."""

    def __init__(self, ha_client: HomeAssistantClient) -> None:
        self._ha = ha_client

    @property
    def channel_key(self) -> str:
        return "home_assistant"

    @property
    def supports_actions(self) -> bool:
        return True

    @property
    def supports_batching(self) -> bool:
        return True

    # ── Public API ───────────────────────────────────────────────────

    async def send(
        self,
        notification: Notification,
        channel_config: dict,
    ) -> ChannelResult:
        errors: list[str] = []

        # 1. Fire HA event (always — enables automations)
        await self._fire_event(notification, errors)

        # 2. Persistent notification (default: on — matches frontend default)
        if channel_config.get("persistent_notification", True):
            await self._create_persistent(notification, errors)

        # 3. Mobile push (default: on — matches frontend default)
        if channel_config.get("mobile_push", True):
            await self._send_mobile_push(notification, channel_config, errors)

        # 4. TTS (opt-in via config)
        if channel_config.get("tts_enabled", False) and channel_config.get("tts_entity_id"):
            await self._send_tts(notification, channel_config, errors)

        success = len(errors) == 0
        return ChannelResult(
            channel_key=self.channel_key,
            success=success,
            error="; ".join(errors) if errors else None,
        )

    async def send_batch(
        self,
        notifications: list[Notification],
        channel_config: dict,
    ) -> ChannelResult:
        if not notifications:
            return ChannelResult(channel_key=self.channel_key, success=True)

        # Group care notifications into a single summary
        care_notifications = [n for n in notifications if n.notification_type.startswith("care_")]
        other_notifications = [n for n in notifications if not n.notification_type.startswith("care_")]

        errors: list[str] = []

        if care_notifications:
            merged = self._merge_care_notifications(care_notifications)
            result = await self.send(merged, channel_config)
            if not result.success and result.error:
                errors.append(result.error)

        for notification in other_notifications:
            result = await self.send(notification, channel_config)
            if not result.success and result.error:
                errors.append(result.error)

        success = len(errors) == 0
        return ChannelResult(
            channel_key=self.channel_key,
            success=success,
            error="; ".join(errors) if errors else None,
        )

    async def health_check(self) -> bool:
        try:
            await self._ha.fire_event("kamerplanter_health_check", {})
            return True
        except Exception:
            logger.warning("ha_notification_health_check_failed", exc_info=True)
            return False

    # ── Internal helpers ─────────────────────────────────────────────

    async def _fire_event(
        self,
        notification: Notification,
        errors: list[str],
    ) -> None:
        event_type = notification.ha_event_type or "kamerplanter_notification"
        event_data = {
            "notification_key": notification.key or "",
            "type": notification.notification_type,
            "title": notification.title,
            "body": notification.body,
            "urgency": notification.urgency.value,
            "data": notification.data,
        }
        if notification.actions:
            event_data["actions"] = [a.model_dump() for a in notification.actions]

        try:
            await self._ha.fire_event(event_type, event_data)
            logger.debug(
                "ha_event_fired",
                event_type=event_type,
                notification_key=notification.key,
            )
        except Exception as exc:
            msg = f"fire_event failed: {exc}"
            logger.error("ha_fire_event_failed", error=str(exc), exc_info=True)
            errors.append(msg)

    async def _create_persistent(
        self,
        notification: Notification,
        errors: list[str],
    ) -> None:
        notification_id = f"kamerplanter_{notification.key or 'unknown'}"
        try:
            await self._ha.create_persistent_notification(
                title=notification.title,
                message=notification.body,
                notification_id=notification_id,
            )
            logger.debug(
                "ha_persistent_notification_created",
                notification_id=notification_id,
            )
        except Exception as exc:
            msg = f"persistent_notification failed: {exc}"
            logger.error("ha_persistent_notification_failed", error=str(exc), exc_info=True)
            errors.append(msg)

    async def _send_mobile_push(
        self,
        notification: Notification,
        channel_config: dict,
        errors: list[str],
    ) -> None:
        notify_service = channel_config.get("notify_service", "notify")
        importance = _URGENCY_TO_IMPORTANCE.get(notification.urgency, "default")
        service_data: dict = {
            "title": notification.title,
            "message": notification.body,
            "data": {
                "importance": importance,
                "channel": "kamerplanter",
                "group": notification.group_key or notification.notification_type,
                **notification.data,
            },
        }
        if notification.image_url:
            service_data["data"]["image"] = notification.image_url
        if notification.actions:
            service_data["data"]["actions"] = [
                {"action": a.action_id, "title": a.title, **({"uri": a.uri} if a.uri else {})}
                for a in notification.actions
            ]

        try:
            await self._ha.call_service("notify", notify_service, service_data)
            logger.debug(
                "ha_mobile_push_sent",
                notify_service=notify_service,
                notification_key=notification.key,
            )
        except Exception as exc:
            msg = f"mobile_push failed: {exc}"
            logger.error("ha_mobile_push_failed", error=str(exc), exc_info=True)
            errors.append(msg)

    async def _send_tts(
        self,
        notification: Notification,
        channel_config: dict,
        errors: list[str],
    ) -> None:
        entity_id = channel_config["tts_entity_id"]
        tts_service = channel_config.get("tts_service", "speak")
        service_data = {
            "entity_id": entity_id,
            "message": notification.body,
        }
        try:
            await self._ha.call_service("tts", tts_service, service_data)
            logger.debug(
                "ha_tts_sent",
                entity_id=entity_id,
                notification_key=notification.key,
            )
        except Exception as exc:
            msg = f"tts failed: {exc}"
            logger.error("ha_tts_failed", error=str(exc), exc_info=True)
            errors.append(msg)

    @staticmethod
    def _merge_care_notifications(notifications: list[Notification]) -> Notification:
        """Merge multiple care notifications into a single summary."""
        titles = [n.title for n in notifications]
        bodies = [f"- {n.body}" for n in notifications]
        first = notifications[0]

        # Use highest urgency from the batch
        max_urgency = max(notifications, key=lambda n: list(NotificationUrgency).index(n.urgency))

        return Notification(
            tenant_key=first.tenant_key,
            user_key=first.user_key,
            notification_type="care_summary",
            title=f"Pflege-Zusammenfassung ({len(notifications)} Aufgaben)",
            body="\n".join(bodies),
            urgency=max_urgency.urgency,
            data={
                "count": len(notifications),
                "types": list({n.notification_type for n in notifications}),
                "titles": titles,
            },
            group_key="care_summary",
            ha_event_type="kamerplanter_care_summary",
        )
