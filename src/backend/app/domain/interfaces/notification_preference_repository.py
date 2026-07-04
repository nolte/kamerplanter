from abc import ABC, abstractmethod

from app.domain.models.notification import NotificationPreferences


class INotificationPreferenceRepository(ABC):
    @abstractmethod
    def get_by_user(self, user_key: str) -> NotificationPreferences | None: ...

    @abstractmethod
    def upsert(self, preferences: NotificationPreferences) -> NotificationPreferences: ...

    @abstractmethod
    def list_users_with_digest_enabled(self) -> list[NotificationPreferences]:
        """Return preferences of all users with the email digest opted in.

        Opt-in requires both ``channels.email.enabled`` and
        ``channels.email.config.digest`` to be true (REQ-030).
        """
        ...
