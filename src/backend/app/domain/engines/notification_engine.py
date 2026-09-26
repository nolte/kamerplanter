"""Notification engine — orchestrates delivery across channels."""

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import structlog

from app.common.log_privacy import log_subject, loggable_error, mask_url_paths
from app.domain.engines.notification_channel_registry import NotificationChannelRegistry
from app.domain.interfaces.notification_preference_repository import (
    INotificationPreferenceRepository,
)
from app.domain.interfaces.notification_repository import INotificationRepository
from app.domain.models.notification import (
    ChannelPreference,
    ChannelResult,
    EscalationPreference,
    Notification,
    NotificationPreferences,
    NotificationStatus,
    NotificationUrgency,
    QuietHoursPreference,
)

logger = structlog.get_logger()

# Notification types that bypass quiet hours. ``frost_forecast_warning`` is the
# proactive early-warning (Issue #409, F4): high-urgency, so it is delivered
# immediately rather than held until the quiet-hours flush, consistent with the
# reactive ``weather.frost``.
_QUIET_HOURS_BYPASS_TYPES: frozenset[str] = frozenset({"sensor.alert", "weather.frost", "frost_forecast_warning"})

# Dedup key TTL in seconds (24 hours)
_DEDUP_TTL_SECONDS: int = 86400

# Redis key prefix for dedup
_DEDUP_PREFIX: str = "kp:notif:dedup:"


class NotificationEngine:
    """Orchestrates notification delivery across channels.

    Responsibilities:
    - Deduplication via Redis
    - Quiet hours enforcement (timezone-aware)
    - Channel resolution from user preferences
    - Fault-tolerant delivery (channel failures are isolated)
    - Escalation of overdue watering reminders
    """

    def __init__(
        self,
        notification_repo: INotificationRepository,
        preference_repo: INotificationPreferenceRepository,
        channel_registry: NotificationChannelRegistry,
        redis_client: object,
    ) -> None:
        self._notification_repo = notification_repo
        self._preference_repo = preference_repo
        self._channel_registry = channel_registry
        self._redis = redis_client

    # ── Public API ────────────────────────────────────────────────────

    async def notify(
        self,
        user_key: str,
        tenant_key: str,
        notification: Notification,
    ) -> dict:
        """Send a notification to a user.

        Steps:
        1. Dedup check (Redis, 24h TTL)
        2. Load preferences (or defaults)
        3. Quiet hours check — queue for morning if active
        4. Resolve channels (type overrides or default active channels)
        5. Send via each channel (errors caught, not propagated)
        6. Persist notification in DB
        7. Set dedup key in Redis
        """
        log = logger.bind(
            subject=log_subject(user_key),
            tenant_key=tenant_key,
            notification_type=notification.notification_type,
        )

        # 1. Dedup check
        dedup_key = self._build_dedup_key(
            user_key,
            notification.notification_type,
            notification.group_key,
        )
        if await self._is_duplicate(dedup_key):
            # Not the dedup key: it embeds the account key (#1830, NFR-011 §3.4 L-1).
            # ``subject`` and ``notification_type`` are bound on ``log`` already.
            log.info("notification_deduplicated")
            return {"status": "deduplicated", "channels_sent": [], "channels_failed": []}

        # 2. Preferences
        prefs = self._load_preferences(user_key)

        # 3. Quiet hours
        if self._is_quiet_hours(prefs) and not self._ignores_quiet_hours(notification, prefs):
            log.info("notification_queued_quiet_hours")
            notification.status = NotificationStatus.PENDING
            notification.user_key = user_key
            notification.tenant_key = tenant_key
            notification.data = {**notification.data, "_queued_reason": "quiet_hours"}
            # notification-write-ok: event: quiet hours park this inbound event as PENDING
            # for later channel delivery. The row is BORN here; it follows no change at a
            # source, so it is not the propagation service's to write.
            saved = self._notification_repo.create(notification)
            return {
                "status": "queued_quiet_hours",
                "notification_key": saved.key,
                "channels_sent": [],
                "channels_failed": [],
            }

        # 4. Resolve channels
        channel_keys = self._resolve_channels(notification, prefs)
        if not channel_keys:
            log.warning("no_channels_available")
            notification.status = NotificationStatus.FAILED
            notification.user_key = user_key
            notification.tenant_key = tenant_key
            # notification-write-ok: event: the event reached no deliverable channel. The row
            # is still born here so the in-app centre shows it — again a first
            # materialisation, not a source change being followed.
            saved = self._notification_repo.create(notification)
            return {
                "status": "no_channels",
                "notification_key": saved.key,
                "channels_sent": [],
                "channels_failed": [],
            }

        # 5. Send through each channel
        channels_sent: list[str] = []
        channels_failed: list[str] = []
        results: list[ChannelResult] = []

        for channel_key in channel_keys:
            result = await self._send_to_channel(user_key, channel_key, notification, prefs)
            results.append(result)
            if result.success:
                channels_sent.append(channel_key)
            else:
                channels_failed.append(channel_key)

        # 6. Persist
        notification.user_key = user_key
        notification.tenant_key = tenant_key
        notification.channels_sent = channels_sent
        notification.channels_failed = channels_failed
        notification.status = NotificationStatus.DELIVERED if channels_sent else NotificationStatus.FAILED
        # notification-write-ok: event: the first materialisation of an inbound event
        # after channel dispatch (REQ-030 §4.1). NotificationPropagationService owns the
        # reverse direction — an existing row following its source — not this one.
        saved = self._notification_repo.create(notification)

        # 7. Dedup key
        await self._set_dedup_key(dedup_key)

        log.info(
            "notification_sent",
            notification_key=saved.key,
            channels_sent=channels_sent,
            channels_failed=channels_failed,
        )

        return {
            "status": "delivered" if channels_sent else "failed",
            "notification_key": saved.key,
            "channels_sent": channels_sent,
            "channels_failed": channels_failed,
            "results": [r.model_dump() for r in results],
        }

    async def notify_batch(
        self,
        user_key: str,
        tenant_key: str,
        notifications: list[Notification],
    ) -> dict:
        """Send batch notifications to a user.

        If a channel supports batching, notifications are grouped.
        Otherwise, each notification is sent individually.
        """
        if not notifications:
            return {"status": "empty", "sent": 0, "failed": 0}

        prefs = self._load_preferences(user_key)
        channel_keys = self._resolve_channels(notifications[0], prefs)

        total_sent = 0
        total_failed = 0

        for channel_key in channel_keys:
            channel = self._channel_registry.get(channel_key)
            if channel is None:
                total_failed += len(notifications)
                continue

            channel_config = self._get_channel_config(channel_key, prefs)

            if channel.supports_batching:
                try:
                    result = await channel.send_batch(notifications, channel_config)
                    self.prune_expired_subscriptions(user_key, result)
                    if result.success:
                        total_sent += len(notifications)
                    else:
                        total_failed += len(notifications)
                        logger.warning(
                            "batch_channel_failed",
                            channel=channel_key,
                            # A channel's detail can carry a push endpoint, whose
                            # path is the device token (#1796): host only.
                            error=loggable_error(mask_url_paths(result.error or "")),
                        )
                except Exception:
                    total_failed += len(notifications)
                    logger.exception("batch_channel_exception", channel=channel_key)
            else:
                for notif in notifications:
                    result = await self._send_to_channel(user_key, channel_key, notif, prefs)
                    if result.success:
                        total_sent += 1
                    else:
                        total_failed += 1

        # Persist each notification
        for notif in notifications:
            notif.user_key = user_key
            notif.tenant_key = tenant_key
            notif.status = NotificationStatus.DELIVERED if total_sent > 0 else NotificationStatus.FAILED
            # notification-write-ok: event: batch materialisation, one row per inbound event
            # of the digest. Same class as the single-event path above.
            self._notification_repo.create(notif)

        return {"status": "batch_complete", "sent": total_sent, "failed": total_failed}

    async def escalate_overdue(self, tenant_key: str) -> dict:
        """Escalate overdue watering reminders.

        Escalation levels:
        - Day +2: urgency -> HIGH
        - Day +4: urgency -> CRITICAL
        - Day +7: final warning
        """
        escalation_config = EscalationPreference()
        escalation_days = escalation_config.escalation_days  # [2, 4, 7]

        escalated_count = 0
        now = datetime.now(UTC)

        for level, days in enumerate(escalation_days):
            cutoff = now - timedelta(days=days)
            overdue = self._notification_repo.find_overdue_watering(
                overdue_since=cutoff,
                escalation_level=level,
            )

            for notif in overdue:
                # Check user preferences for watering escalation
                prefs = self._load_preferences(notif.user_key)
                if not prefs.escalation.watering_enabled:
                    continue

                # Determine new urgency based on level
                if level == 0:
                    new_urgency = NotificationUrgency.HIGH
                elif level == 1:
                    new_urgency = NotificationUrgency.CRITICAL
                else:
                    new_urgency = NotificationUrgency.CRITICAL

                escalation_notif = Notification(
                    tenant_key=notif.tenant_key,
                    user_key=notif.user_key,
                    notification_type="care.watering.escalation",
                    title=notif.title,
                    body=f"Overdue: {notif.body}",
                    urgency=new_urgency,
                    data={
                        **notif.data,
                        "escalation_level": level + 1,
                        "original_notification_key": notif.key,
                    },
                    group_key=notif.group_key,
                    escalation_level=level + 1,
                    parent_notification_key=notif.key,
                )

                await self.notify(
                    user_key=notif.user_key,
                    tenant_key=notif.tenant_key,
                    notification=escalation_notif,
                )

                # Update original notification escalation level
                notif.escalation_level = level + 1
                if notif.key:
                    self._notification_repo.update(notif.key, notif)

                escalated_count += 1

        logger.info(
            "escalation_complete",
            tenant_key=tenant_key,
            escalated_count=escalated_count,
        )

        return {"escalated": escalated_count}

    # ── Channel resolution ────────────────────────────────────────────

    def _resolve_channels(
        self,
        notification: Notification,
        prefs: NotificationPreferences,
    ) -> list[str]:
        """Resolve channel keys from type overrides or default preferences.

        Type overrides take precedence. Otherwise, enabled channels are
        returned sorted by priority (highest first).
        """
        # Check type-specific overrides
        override = prefs.type_overrides.get(notification.notification_type)
        if override and override.channels:
            available = self._channel_registry.all_keys()
            return [ch for ch in override.channels if ch in available]

        # Fall back to enabled channels sorted by priority
        enabled: list[tuple[str, int]] = []
        for channel_key, channel_pref in prefs.channels.items():
            if channel_pref.enabled and self._channel_registry.get(channel_key) is not None:
                enabled.append((channel_key, channel_pref.priority))

        # Sort by priority descending (higher priority first)
        enabled.sort(key=lambda x: x[1], reverse=True)
        return [ch for ch, _ in enabled]

    # ── Quiet hours ───────────────────────────────────────────────────

    def _is_quiet_hours(self, prefs: NotificationPreferences) -> bool:
        """Check if current time falls within quiet hours (timezone-aware)."""
        if not prefs.quiet_hours.enabled:
            return False

        try:
            tz = ZoneInfo(prefs.quiet_hours.timezone)
        except (KeyError, ValueError):  # fmt: skip
            tz = ZoneInfo("Europe/Berlin")

        now_local = datetime.now(tz).time()
        start = self._parse_time(prefs.quiet_hours.start)
        end = self._parse_time(prefs.quiet_hours.end)

        # Handle overnight ranges (e.g. 22:00 - 07:00)
        if start <= end:
            return start <= now_local <= end
        return now_local >= start or now_local <= end

    def _ignores_quiet_hours(
        self,
        notification: Notification,
        prefs: NotificationPreferences,
    ) -> bool:
        """Check if notification type bypasses quiet hours."""
        # Global bypass types
        if notification.notification_type in _QUIET_HOURS_BYPASS_TYPES:
            return True

        # Type-specific override with ignore_quiet_hours flag
        override = prefs.type_overrides.get(notification.notification_type)
        return bool(override and override.ignore_quiet_hours)

    # ── Default preferences ───────────────────────────────────────────

    @staticmethod
    def _default_preferences() -> NotificationPreferences:
        """Build default preferences for users without configuration."""
        return NotificationPreferences(
            channels={
                "home_assistant": ChannelPreference(enabled=True, priority=10),
            },
            quiet_hours=QuietHoursPreference(
                enabled=True,
                start="22:00",
                end="07:00",
                timezone="Europe/Berlin",
            ),
        )

    # ── Private helpers ───────────────────────────────────────────────

    def _load_preferences(self, user_key: str) -> NotificationPreferences:
        """Load user preferences or return defaults."""
        prefs = self._preference_repo.get_by_user(user_key)
        if prefs is not None:
            return prefs
        return self._default_preferences()

    async def _send_to_channel(
        self,
        user_key: str,
        channel_key: str,
        notification: Notification,
        prefs: NotificationPreferences,
    ) -> ChannelResult:
        """Send a notification through a single channel with error isolation; prune what expired."""
        channel = self._channel_registry.get(channel_key)
        if channel is None:
            return ChannelResult(
                channel_key=channel_key,
                success=False,
                error=f"Channel '{channel_key}' not registered",
            )

        channel_config = self._get_channel_config(channel_key, prefs)

        try:
            result = await channel.send(notification, channel_config)
        except Exception as exc:
            logger.exception(
                "channel_send_failed",
                channel=channel_key,
                notification_type=notification.notification_type,
            )
            return ChannelResult(
                channel_key=channel_key,
                success=False,
                error=str(exc),
            )
        self.prune_expired_subscriptions(user_key, result)
        return result

    def prune_expired_subscriptions(self, user_key: str, result: ChannelResult) -> int:
        """Remove the push subscriptions *result* reports as gone from *user_key*'s preferences (#1827).

        A push service answers 404/410 for a subscription that no longer
        exists; until #1827 the endpoint was reported and kept, and dialled again
        on every notification. Every sender of a channel result calls this — the
        engine's single and batch paths and the test notification. The
        preferences are re-read right before the write to keep the window
        against a concurrent subscribe short. A failed write is logged and not
        raised: the notification was delivered or not independently of it.
        Logs a count, never an endpoint (its path is the device's push token).

        Returns:
            How many subscriptions were removed.
        """
        if not result.expired_endpoints:
            return 0
        gone = set(result.expired_endpoints)
        try:
            prefs = self._preference_repo.get_by_user(user_key)
            channel_pref = prefs.channels.get(result.channel_key) if prefs is not None else None
            if channel_pref is None:
                return 0
            subscriptions = channel_pref.config.get("subscriptions", [])
            remaining = [s for s in subscriptions if s.get("endpoint") not in gone]
            pruned = len(subscriptions) - len(remaining)
            if not pruned:
                return 0
            channel_pref.config["subscriptions"] = remaining
            self._preference_repo.upsert(prefs)
        except Exception as exc:
            logger.warning(
                "push_subscription_prune_failed",
                subject=log_subject(user_key),
                channel=result.channel_key,
                error_type=type(exc).__name__,
            )
            return 0
        logger.info(
            "push_subscriptions_pruned",
            subject=log_subject(user_key),
            channel=result.channel_key,
            pruned=pruned,
            remaining=len(remaining),
        )
        return pruned

    def _get_channel_config(
        self,
        channel_key: str,
        prefs: NotificationPreferences,
    ) -> dict:
        """Extract per-channel config from user preferences."""
        channel_pref = prefs.channels.get(channel_key)
        if channel_pref is not None:
            return channel_pref.config
        return {}

    def _build_dedup_key(
        self,
        user_key: str,
        notification_type: str,
        group_key: str | None,
    ) -> str:
        """Build a Redis dedup key."""
        effective_group = group_key or "default"
        return f"{_DEDUP_PREFIX}{user_key}:{notification_type}:{effective_group}"

    async def _is_duplicate(self, dedup_key: str) -> bool:
        """Check if a dedup key exists in Redis."""
        try:
            result = self._redis.get(dedup_key)
            return result is not None
        except Exception:
            # The key embeds the account key (#1830); the failure is the Redis outage, not the key.
            logger.warning("redis_dedup_check_failed")
            # Redis failure: allow the notification through (graceful degradation)
            return False

    async def _set_dedup_key(self, dedup_key: str) -> None:
        """Set a dedup key in Redis with TTL."""
        try:
            self._redis.set(dedup_key, "1", ex=_DEDUP_TTL_SECONDS)
        except Exception:
            logger.warning("redis_dedup_set_failed")
            # Redis failure: non-blocking (graceful degradation)

    @staticmethod
    def _parse_time(time_str: str) -> time:
        """Parse HH:MM string to time object."""
        parts = time_str.split(":")
        return time(int(parts[0]), int(parts[1]))
