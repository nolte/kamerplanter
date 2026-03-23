"""Notification service — coordinates engine, repositories and channels."""

from collections import defaultdict
from datetime import UTC, datetime

import structlog

from app.domain.engines.notification_engine import NotificationEngine
from app.domain.interfaces.notification_preference_repository import (
    INotificationPreferenceRepository,
)
from app.domain.interfaces.notification_repository import INotificationRepository
from app.domain.models.notification import (
    Notification,
    NotificationPreferences,
    NotificationStatus,
    NotificationUrgency,
)

logger = structlog.get_logger()


class NotificationService:
    """Service layer for notification operations.

    Thin orchestration layer between API endpoints and the
    NotificationEngine. Handles CRUD for notifications and preferences,
    delegates delivery logic to the engine.
    """

    def __init__(
        self,
        engine: NotificationEngine,
        notification_repo: INotificationRepository,
        preference_repo: INotificationPreferenceRepository,
    ) -> None:
        self._engine = engine
        self._notification_repo = notification_repo
        self._preference_repo = preference_repo

    # ── Sending ───────────────────────────────────────────────────────

    async def send_notification(
        self,
        user_key: str,
        tenant_key: str,
        notification_type: str,
        title: str,
        body: str,
        *,
        urgency: NotificationUrgency = NotificationUrgency.NORMAL,
        data: dict | None = None,
        actions: list[dict] | None = None,
        image_url: str | None = None,
        group_key: str | None = None,
        ha_event_type: str | None = None,
    ) -> dict:
        """Create and send a notification to a user."""
        from app.domain.models.notification import NotificationAction

        parsed_actions = []
        if actions:
            parsed_actions = [NotificationAction(**a) for a in actions]

        notification = Notification(
            notification_type=notification_type,
            title=title,
            body=body,
            urgency=urgency,
            data=data or {},
            actions=parsed_actions,
            image_url=image_url,
            group_key=group_key,
            ha_event_type=ha_event_type,
        )

        return await self._engine.notify(user_key, tenant_key, notification)

    async def send_care_notifications(
        self,
        tenant_key: str,
        due_tasks: list[dict],
    ) -> dict:
        """Send notifications for due care tasks (called by Celery).

        Groups tasks by user_key and sends batched notifications.

        due_tasks: list of dicts with keys:
            user_key, plant_key, plant_name, reminder_type, urgency, due_date
        """
        if not due_tasks:
            return {"status": "empty", "users_notified": 0}

        # Group by user
        by_user: dict[str, list[dict]] = defaultdict(list)
        for task in due_tasks:
            by_user[task["user_key"]].append(task)

        users_notified = 0
        total_sent = 0

        for user_key, tasks in by_user.items():
            notifications = []
            for task in tasks:
                urgency_map = {
                    "overdue": NotificationUrgency.HIGH,
                    "due_today": NotificationUrgency.NORMAL,
                    "upcoming": NotificationUrgency.LOW,
                }
                urgency = urgency_map.get(task.get("urgency", "normal"), NotificationUrgency.NORMAL)

                notification = Notification(
                    notification_type=f"care.{task.get('reminder_type', 'watering')}",
                    title=f"{task.get('plant_name', 'Plant')}",
                    body=f"{task.get('reminder_type', 'Care')} due: {task.get('plant_name', '')}",
                    urgency=urgency,
                    data={
                        "plant_key": task.get("plant_key", ""),
                        "reminder_type": task.get("reminder_type", ""),
                        "due_date": task.get("due_date", ""),
                    },
                    group_key=f"care:{user_key}:{task.get('reminder_type', '')}",
                )
                notifications.append(notification)

            if notifications:
                result = await self._engine.notify_batch(
                    user_key=user_key,
                    tenant_key=tenant_key,
                    notifications=notifications,
                )
                users_notified += 1
                total_sent += result.get("sent", 0)

        logger.info(
            "care_notifications_sent",
            tenant_key=tenant_key,
            users_notified=users_notified,
            total_sent=total_sent,
        )

        return {
            "status": "complete",
            "users_notified": users_notified,
            "total_sent": total_sent,
        }

    # ── Read operations ───────────────────────────────────────────────

    def list_notifications(
        self,
        user_key: str,
        tenant_key: str | None = None,
        limit: int = 50,
        offset: int = 0,
        *,
        unread_only: bool = False,
    ) -> list[Notification]:
        """List notifications for a user."""
        status_filter = None
        if unread_only:
            status_filter = NotificationStatus.DELIVERED

        return self._notification_repo.list_for_user(
            user_key=user_key,
            tenant_key=tenant_key,
            status=status_filter,
            limit=limit,
            offset=offset,
        )

    def count_unread(
        self,
        user_key: str,
        tenant_key: str | None = None,
    ) -> int:
        """Count unread notifications for a user."""
        return self._notification_repo.count_unread(user_key, tenant_key)

    def mark_read(self, notification_key: str, tenant_key: str, user_key: str | None = None) -> Notification | None:
        """Mark a notification as read. Returns None if not found or ownership check fails."""
        notif = self._notification_repo.get(notification_key)
        if notif is None:
            return None
        if notif.tenant_key != tenant_key:
            return None
        # Verify the requesting user owns this notification
        if user_key and notif.user_key and notif.user_key != user_key:
            return None
        return self._notification_repo.mark_read(notification_key, datetime.now(UTC))

    def mark_acted(
        self,
        notification_key: str,
        tenant_key: str,
        action_id: str,
        user_key: str | None = None,
    ) -> Notification | None:
        """Mark a notification action as performed. Returns None if not found or ownership check fails."""
        notif = self._notification_repo.get(notification_key)
        if notif is None:
            return None
        if notif.tenant_key != tenant_key:
            return None
        # Verify the requesting user owns this notification
        if user_key and notif.user_key and notif.user_key != user_key:
            return None
        return self._notification_repo.mark_acted(notification_key, datetime.now(UTC))

    # ── Preferences ───────────────────────────────────────────────────

    def get_preferences(self, user_key: str) -> NotificationPreferences:
        """Get user notification preferences (or defaults)."""
        prefs = self._preference_repo.get_by_user(user_key)
        if prefs is not None:
            return prefs
        return NotificationEngine._default_preferences()

    def update_preferences(
        self,
        user_key: str,
        preferences: NotificationPreferences,
    ) -> NotificationPreferences:
        """Create or update user notification preferences."""
        preferences.user_key = user_key
        preferences.updated_at = datetime.now(UTC)
        return self._preference_repo.upsert(preferences)

    # ── Channel status ────────────────────────────────────────────────

    async def get_channel_status(self) -> list[dict]:
        """Health status of all registered channels."""
        channels = self._engine._channel_registry.get_available()
        statuses = []
        for channel in channels:
            try:
                healthy = await channel.health_check()
            except Exception:
                healthy = False
                logger.exception("channel_health_check_failed", channel=channel.channel_key)

            statuses.append(
                {
                    "channel_key": channel.channel_key,
                    "healthy": healthy,
                    "supports_actions": channel.supports_actions,
                    "supports_batching": channel.supports_batching,
                }
            )
        return statuses

    # ── Test notification ─────────────────────────────────────────────

    async def send_test(
        self,
        user_key: str,
        tenant_key: str,
        channel_key: str,
    ) -> dict:
        """Send a test notification through a specific channel."""
        notification = Notification(
            notification_type="system.test",
            title="Test Notification",
            body="This is a test notification from Kamerplanter.",
            urgency=NotificationUrgency.LOW,
            data={"test": True},
            group_key=f"test:{user_key}:{channel_key}",
        )

        # Override channel resolution — force specific channel
        channel = self._engine._channel_registry.get(channel_key)
        if channel is None:
            return {"status": "error", "error": f"Channel '{channel_key}' not found"}

        prefs = self._engine._load_preferences(user_key)
        channel_config = self._engine._get_channel_config(channel_key, prefs)

        try:
            result = await channel.send(notification, channel_config)
            return {
                "status": "delivered" if result.success else "failed",
                "channel_key": channel_key,
                "success": result.success,
                "error": result.error,
            }
        except Exception as exc:
            logger.exception("test_notification_failed", channel=channel_key)
            return {
                "status": "error",
                "channel_key": channel_key,
                "success": False,
                "error": str(exc),
            }

    # ── Availability ──────────────────────────────────────────────────

    async def is_available(self) -> bool:
        """Return True if at least one channel is registered and healthy."""
        channels = self._engine._channel_registry.get_available()
        if not channels:
            return False

        for channel in channels:
            try:
                if await channel.health_check():
                    return True
            except Exception:
                continue
        return False
