"""ArangoDB repository for notifications."""

from datetime import datetime

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.notification_repository import INotificationRepository
from app.domain.models.notification import Notification, NotificationStatus

# Collection constants
NOTIFICATIONS = "notifications"


class ArangoNotificationRepository(INotificationRepository, BaseArangoRepository):
    """ArangoDB-backed notification repository."""

    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, NOTIFICATIONS)

    def _to_notification(self, doc: dict) -> Notification:
        """Convert ArangoDB document to Notification model."""
        return Notification(**self._from_doc(doc))

    # ── CRUD ──────────────────────────────────────────────────────────

    def create(self, notification: Notification) -> Notification:
        doc = BaseArangoRepository.create(self, notification)
        return Notification(**doc)

    def get(self, key: str) -> Notification | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        if doc is None:
            return None
        return Notification(**doc)

    def update(self, key: str, notification: Notification) -> Notification:
        doc = BaseArangoRepository.update(self, key, notification)
        return Notification(**doc)

    # ── Queries ───────────────────────────────────────────────────────

    def list_for_user(
        self,
        user_key: str,
        tenant_key: str | None = None,
        status: NotificationStatus | None = None,
        notification_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        """List notifications for a user, sorted by created_at DESC.

        Supports optional filtering by tenant, status (for unread_only),
        and notification type.
        """
        filters = ["doc.user_key == @user_key"]
        bind_vars: dict = {
            "user_key": user_key,
            "limit": limit,
            "offset": offset,
        }

        if tenant_key is not None:
            filters.append("doc.tenant_key == @tenant_key")
            bind_vars["tenant_key"] = tenant_key

        if status is not None:
            # For unread_only: status=DELIVERED means read_at IS NULL
            filters.append("doc.read_at == null")

        if notification_type is not None:
            filters.append("doc.notification_type == @notification_type")
            bind_vars["notification_type"] = notification_type

        filter_clause = " AND ".join(filters)

        query = (
            f"FOR doc IN {NOTIFICATIONS} "
            f"FILTER {filter_clause} "
            f"SORT doc.created_at DESC "
            f"LIMIT @offset, @limit "
            f"RETURN doc"
        )

        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [self._to_notification(doc) for doc in cursor]

    def mark_read(self, key: str, read_at: datetime) -> Notification | None:
        """Mark a notification as read."""
        query = f"UPDATE @key WITH {{ read_at: @read_at, updated_at: @read_at }} IN {NOTIFICATIONS} RETURN NEW"
        cursor = self._db.aql.execute(
            query,
            bind_vars={"key": key, "read_at": read_at.isoformat()},
        )
        doc = next(cursor, None)
        if doc is None:
            return None
        return self._to_notification(doc)

    def mark_acted(self, key: str, acted_at: datetime) -> Notification | None:
        """Mark a notification action as performed."""
        query = f"UPDATE @key WITH {{ acted_at: @acted_at, updated_at: @acted_at }} IN {NOTIFICATIONS} RETURN NEW"
        cursor = self._db.aql.execute(
            query,
            bind_vars={"key": key, "acted_at": acted_at.isoformat()},
        )
        doc = next(cursor, None)
        if doc is None:
            return None
        return self._to_notification(doc)

    def find_overdue_watering(
        self,
        overdue_since: datetime,
        escalation_level: int,
    ) -> list[Notification]:
        """Find overdue watering notifications that have not been acted upon.

        Matches:
        - notification_type starts with 'care.watering'
        - acted_at IS NULL
        - created_at < cutoff
        - escalation_level == given level (to avoid re-escalating)
        """
        query = (
            f"FOR doc IN {NOTIFICATIONS} "
            f"FILTER STARTS_WITH(doc.notification_type, 'care.watering') "
            f"AND doc.acted_at == null "
            f"AND doc.created_at < @cutoff "
            f"AND doc.escalation_level == @level "
            f"RETURN doc"
        )
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "cutoff": overdue_since.isoformat(),
                "level": escalation_level,
            },
        )
        return [self._to_notification(doc) for doc in cursor]

    def count_unread(self, user_key: str, tenant_key: str | None = None) -> int:
        """Count unread notifications for a user."""
        filters = ["doc.user_key == @user_key", "doc.read_at == null"]
        bind_vars: dict = {"user_key": user_key}

        if tenant_key is not None:
            filters.append("doc.tenant_key == @tenant_key")
            bind_vars["tenant_key"] = tenant_key

        filter_clause = " AND ".join(filters)

        query = f"RETURN LENGTH(FOR doc IN {NOTIFICATIONS} FILTER {filter_clause} RETURN 1)"
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return next(cursor, 0)

    def create_edges(
        self,
        notification_key: str,
        task_keys: list[str],
        plant_keys: list[str],
    ) -> None:
        """Create edges from notification to related tasks and plants."""
        notif_id = f"{NOTIFICATIONS}/{notification_key}"

        for task_key in task_keys:
            task_id = f"{col.TASKS}/{task_key}"
            self.create_edge("notified_about_task", notif_id, task_id)

        for plant_key in plant_keys:
            plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
            self.create_edge("notified_about_plant", notif_id, plant_id)
