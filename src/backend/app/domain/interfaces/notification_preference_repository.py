from abc import ABC, abstractmethod

from app.domain.models.notification import NotificationPreferences


class INotificationPreferenceRepository(ABC):
    @abstractmethod
    def get_by_user(self, user_key: str) -> NotificationPreferences | None: ...

    @abstractmethod
    def upsert(self, preferences: NotificationPreferences) -> NotificationPreferences: ...

    @abstractmethod
    def remove_endpoint_from_other_users(self, channel_key: str, endpoint: str, holder_user_key: str) -> int:
        """Remove ``endpoint`` from every account's ``channel_key`` subscriptions except the holder's (#2117).

        A push endpoint names one browser profile on one device; when an account
        subscribes it, no other account may still receive pushes through it.
        Same write shape as :meth:`remove_subscriptions`: an existing document only,
        one atomic update per document.

        Returns:
            How many subscriptions were removed across all other accounts.
        """

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
