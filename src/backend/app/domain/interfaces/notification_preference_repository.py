from abc import ABC, abstractmethod

from app.domain.models.notification import NotificationPreferences


class INotificationPreferenceRepository(ABC):
    @abstractmethod
    def get_by_user(self, user_key: str) -> NotificationPreferences | None: ...

    @abstractmethod
    def upsert(self, preferences: NotificationPreferences) -> NotificationPreferences: ...

    @abstractmethod
    def remove_subscriptions(self, user_key: str, channel_key: str, endpoints: list[str]) -> int:
        """Remove the subscriptions with these endpoints from one channel's config, atomically (#1827).

        One write that only changes an **existing** preferences document and never
        creates one: pruning must neither overwrite a concurrent change of the
        rest of the document nor resurrect a document an erasure removed.

        Returns:
            How many subscriptions were removed (0 when the document is gone).
        """
        ...

    @abstractmethod
    def list_users_with_digest_enabled(self) -> list[NotificationPreferences]:
        """Return preferences of all users with the email digest opted in.

        Opt-in requires both ``channels.email.enabled`` and
        ``channels.email.config.digest`` to be true (REQ-030).
        """
        ...
