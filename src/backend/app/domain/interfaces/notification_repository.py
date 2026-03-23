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
    def count_unread(self, user_key: str, tenant_key: str | None = None) -> int: ...

    @abstractmethod
    def create_edges(
        self,
        notification_key: str,
        task_keys: list[str],
        plant_keys: list[str],
    ) -> None: ...
