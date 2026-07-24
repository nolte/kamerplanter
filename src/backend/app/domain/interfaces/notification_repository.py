from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.models.notification import Notification, NotificationStatus


class INotificationRepository(ABC):
    @abstractmethod
    def create(self, notification: Notification) -> Notification: ...

    @abstractmethod
    def get(self, key: str) -> Notification | None: ...

    @abstractmethod
    def update(self, key: str, notification: Notification) -> Notification: ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Hard-delete one notification by key. Returns True when a row was removed.

        Backs orphan removal (Issue #742): when a source task/care reminder is
        deleted, its in-app notification must not linger with a dead ``action_url``.
        """
        ...

    @abstractmethod
    def list_by_group_key(self, group_key: str, tenant_key: str) -> list[Notification]:
        """Return every notification carrying ``(group_key, tenant_key)`` (newest first).

        Index-backed by the ``(group_key, tenant_key)`` persistent index. Backs the
        synchronous source→notification feedback loop (Issue #742): a task/care
        mutation locates the single per-source notification via its stable
        ``group_key`` to update, mark done or remove it. Strictly tenant-scoped so a
        mutation can never touch another tenant's notifications (SEC-B4).
        """
        ...

    @abstractmethod
    def list_for_user(
        self,
        user_key: str,
        tenant_key: str | None = None,
        status: NotificationStatus | None = None,
        notification_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]: ...

    @abstractmethod
    def list_for_user_since(
        self,
        user_key: str,
        since: datetime,
        limit: int = 100,
    ) -> list[Notification]:
        """Return the user's notifications created at/after ``since`` (newest first)."""
        ...

    @abstractmethod
    def mark_read(self, key: str, read_at: datetime) -> Notification | None: ...

    @abstractmethod
    def mark_acted(self, key: str, acted_at: datetime) -> Notification | None: ...

    @abstractmethod
    def find_overdue_watering(
        self,
        overdue_since: datetime,
        escalation_level: int,
    ) -> list[Notification]: ...

    @abstractmethod
    def exists_by_group_key(self, group_key: str, tenant_key: str) -> bool:
        """Return whether the tenant has any notification carrying ``group_key``.

        Existence-only primitive (no document materialisation) backing cross-run
        idempotency for producers that must emit a group at most once. Index-backed
        (Issue #409, F2) by the ``(group_key, tenant_key)`` persistent index.
        """
        ...

    @abstractmethod
    def find_notified_user_keys(self, group_key: str, tenant_key: str) -> set[str]:
        """Return the ``user_key`` set already notified for ``(group_key, tenant_key)``.

        Projected read (``RETURN DISTINCT doc.user_key``) — never materialises full
        documents. Backs the per-recipient top-up (Issue #409, F3): a later run
        sends only to members NOT already in this set, so mid-event joiners receive
        the already-announced warning without duplicating it for prior recipients.
        """
        ...

    @abstractmethod
    def count_unread(self, user_key: str, tenant_key: str | None = None) -> int: ...

    @abstractmethod
    def create_edges(
        self,
        notification_key: str,
        task_keys: list[str],
        plant_keys: list[str],
    ) -> None: ...
