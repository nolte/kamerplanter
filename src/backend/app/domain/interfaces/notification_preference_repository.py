from abc import ABC, abstractmethod

from app.domain.models.notification import NotificationPreferences


class INotificationPreferenceRepository(ABC):
    @abstractmethod
    def get_by_user(self, user_key: str) -> NotificationPreferences | None: ...

    @abstractmethod
    def upsert(self, preferences: NotificationPreferences) -> NotificationPreferences: ...
