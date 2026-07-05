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
    def find_by_group_key(self, group_key: str, tenant_key: str) -> list[Notification]:
        """Return the tenant's notifications carrying ``group_key`` (any user).

        Backs cross-run idempotency for producers that must emit a group at most
        once (e.g. one frost forecast warning per ``(site_key, forecast_date)``).
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
