"""Notification service — coordinates engine, repositories and channels."""

from collections import defaultdict
from datetime import UTC, date, datetime

import structlog

from app.common.url_safety import validate_push_endpoint
from app.domain.engines.notification_engine import NotificationEngine
from app.domain.interfaces.notification_preference_repository import (
    INotificationPreferenceRepository,
)
from app.domain.interfaces.notification_repository import INotificationRepository
from app.domain.models.notification import (
    ChannelPreference,
    Notification,
    NotificationPreferences,
    NotificationStatus,
    NotificationUrgency,
)

logger = structlog.get_logger()

# SEC-003 — per-user cap on stored Web Push subscriptions. When exceeded by a
# new endpoint, the oldest subscription is evicted (FIFO) so the newest device
# always works.
MAX_PWA_SUBSCRIPTIONS_PER_USER = 20


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

    async def send_frost_forecast_notifications(
        self,
        tenant_key: str,
        user_keys: list[str],
        *,
        site_key: str,
        site_name: str,
        expected_date: date,
        min_temp: float | None,
        source: str | None,
    ) -> dict:
        """Emit a proactive frost early-warning to a tenant's users (Issue #392).

        Idempotent per ``(site_key, expected frost date)`` via ``group_key``. Rather
        than a group-wide once-only guard, recipients are tracked per event
        (Issue #409, F3): the set of members already announced for this
        ``(group_key, tenant_key)`` is derived from persisted notification rows and
        only *newly-eligible* members are topped up on later runs — so a member who
        joins after the first daily run but before the frost date still receives the
        already-announced warning, and prior recipients are never re-notified. A new
        or earlier frost date yields a new ``group_key`` and therefore a fresh
        announcement. User notification preferences are honoured by the underlying
        ``send_notification`` path.

        Args:
            tenant_key: Owning tenant of the site (R10 tenant isolation).
            user_keys: Recipient user keys (the tenant's active members).
            site_key: Site the frost is expected for (idempotency key part).
            site_name: Human-readable site name for the message body.
            expected_date: Earliest in-horizon frost date (idempotency key part).
            min_temp: Expected minimum temperature in °C for that night.
            source: Provenance of the forecast (e.g. ``open-meteo``).

        Returns:
            ``{"status": "deduplicated"|"empty"|"complete", "users_notified": int}``.
            ``users_notified`` counts only genuinely delivered sends (Issue #409, F5).
        """
        group_key = f"frost-forecast:{site_key}:{expected_date.isoformat()}"

        # F3 (Issue #409) — per-recipient top-up: the members already announced for
        # this (site_key, forecast_date) event are derived from persisted rows via
        # the index-backed projected read, so only newly-eligible members are sent
        # to (mid-event joiners included) without re-notifying prior recipients.
        already_notified = self._notification_repo.find_notified_user_keys(group_key, tenant_key)
        pending = [user_key for user_key in user_keys if user_key not in already_notified]

        if not pending:
            if already_notified:
                logger.info(
                    "frost_forecast_notification_deduplicated",
                    tenant_key=tenant_key,
                    site_key=site_key,
                    group_key=group_key,
                    already_notified=len(already_notified),
                )
                return {"status": "deduplicated", "users_notified": 0}
            return {"status": "empty", "users_notified": 0}

        temp_text = f"{min_temp} °C" if min_temp is not None else "unknown"
        title = "Frost warning"
        body = f"Frost is expected for {site_name} on the night of {expected_date.isoformat()} (min. {temp_text})."
        data = {
            "site_key": site_key,
            "expected_date": expected_date.isoformat(),
            "min_temp": min_temp,
            "source": source,
        }

        users_notified = 0
        for user_key in pending:
            result = await self.send_notification(
                user_key=user_key,
                tenant_key=tenant_key,
                notification_type="frost_forecast_warning",
                title=title,
                body=body,
                urgency=NotificationUrgency.HIGH,
                data=data,
                group_key=group_key,
            )
            # F5 (Issue #409) — only a genuine delivery counts as reach; deduplicated,
            # queued_quiet_hours, no_channels and failed sends must not inflate the metric.
            if result.get("status") == "delivered":
                users_notified += 1

        logger.info(
            "frost_forecast_notifications_sent",
            tenant_key=tenant_key,
            site_key=site_key,
            expected_date=expected_date.isoformat(),
            recipients=len(pending),
            users_notified=users_notified,
        )
        return {"status": "complete", "users_notified": users_notified}

    async def send_email_digest(
        self,
        user_key: str,
        to_email: str,
        since: datetime,
    ) -> dict:
        """Send one digest email summarising the user's notifications since ``since``.

        Collects all notifications created in the window and delivers them as a
        single batch email through the registered ``email`` channel, reusing its
        batch HTML rendering (REQ-030).

        Returns a dict ``{"status": "sent"|"empty"|"failed", "count": int}``.
        An empty window sends no mail; a missing/unhealthy channel or a failed
        send returns ``"failed"`` without raising.
        """
        notifications = self._notification_repo.list_for_user_since(user_key, since)
        if not notifications:
            return {"status": "empty", "count": 0}

        channel = self._engine._channel_registry.get("email")
        if channel is None:
            logger.warning("email_digest_channel_unavailable", user_key=user_key)
            return {"status": "failed", "count": 0}

        result = await channel.send_batch(notifications, {"email": to_email})
        if not result.success:
            logger.warning(
                "email_digest_send_failed",
                user_key=user_key,
                error=result.error,
            )
            return {"status": "failed", "count": len(notifications)}

        logger.info("email_digest_sent", user_key=user_key, count=len(notifications))
        return {"status": "sent", "count": len(notifications)}

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

    # ── Web Push (PWA) subscriptions ──────────────────────────────────

    def subscribe_pwa(
        self,
        user_key: str,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: str | None = None,
    ) -> str:
        """Register a Web Push subscription for the user's ``pwa`` channel.

        Creates the ``pwa`` channel preference if missing, enables it and
        deduplicates subscriptions by ``endpoint``. Persists via the existing
        preferences update path.

        The endpoint is validated against SSRF before being stored (SEC-001):
        it must be https and must not resolve to an internal/non-routable
        address. The number of stored subscriptions is capped per user
        (SEC-003): when a new endpoint exceeds the cap, the oldest subscription
        is evicted (FIFO) so the newest device always works.

        Args:
            user_key: Owning user.
            endpoint: Push service endpoint URL (the subscription identity).
            p256dh: Client public key (base64url).
            auth: Client auth secret (base64url).
            user_agent: Optional originating user agent (stored for display).

        Returns:
            The stored subscription endpoint.

        Raises:
            ValidationError: if the endpoint fails SSRF validation (HTTP 422).
        """
        # SEC-001 — reject SSRF-unsafe endpoints before they are ever dialed.
        validate_push_endpoint(endpoint)

        prefs = self.get_preferences(user_key)
        channel_pref = prefs.channels.get("pwa")
        if channel_pref is None:
            channel_pref = ChannelPreference()
            prefs.channels["pwa"] = channel_pref

        subscriptions = channel_pref.config.setdefault("subscriptions", [])
        # Dedupe by endpoint — replace any existing entry for the same endpoint.
        subscriptions = [s for s in subscriptions if s.get("endpoint") != endpoint]
        subscription: dict = {"endpoint": endpoint, "p256dh": p256dh, "auth": auth}
        if user_agent:
            subscription["user_agent"] = user_agent
        subscriptions.append(subscription)

        # SEC-003 — enforce the per-user cap, evicting oldest first (FIFO).
        if len(subscriptions) > MAX_PWA_SUBSCRIPTIONS_PER_USER:
            evicted = subscriptions[:-MAX_PWA_SUBSCRIPTIONS_PER_USER]
            subscriptions = subscriptions[-MAX_PWA_SUBSCRIPTIONS_PER_USER:]
            logger.info(
                "pwa_subscriptions_evicted",
                user_key=user_key,
                evicted=len(evicted),
                cap=MAX_PWA_SUBSCRIPTIONS_PER_USER,
            )

        channel_pref.config["subscriptions"] = subscriptions
        channel_pref.enabled = True

        self.update_preferences(user_key, prefs)
        logger.info("pwa_subscription_added", user_key=user_key, endpoint=endpoint)
        return endpoint

    def unsubscribe_pwa(self, user_key: str, endpoint: str) -> bool:
        """Remove a Web Push subscription identified by ``endpoint``.

        Args:
            user_key: Owning user.
            endpoint: Push service endpoint URL to remove.

        Returns:
            True if a matching subscription was removed, else False.
        """
        prefs = self.get_preferences(user_key)
        channel_pref = prefs.channels.get("pwa")
        if channel_pref is None:
            return False

        subscriptions = channel_pref.config.get("subscriptions", [])
        remaining = [s for s in subscriptions if s.get("endpoint") != endpoint]
        if len(remaining) == len(subscriptions):
            return False

        channel_pref.config["subscriptions"] = remaining
        self.update_preferences(user_key, prefs)
        logger.info("pwa_subscription_removed", user_key=user_key, endpoint=endpoint)
        return True

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
