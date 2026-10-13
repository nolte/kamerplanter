"""Abstract interface for API key persistence."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.common.types import ApiKeyKey, UserKey
from app.domain.models.auth import ApiKey


class IApiKeyRepository(ABC):
    @abstractmethod
    def create(self, api_key: ApiKey) -> ApiKey: ...

    @abstractmethod
    def get_by_key(self, key: ApiKeyKey) -> ApiKey | None: ...

    @abstractmethod
    def get_or_raise(self, key: ApiKeyKey) -> ApiKey: ...

    @abstractmethod
    def get_by_hash(self, key_hash: str) -> ApiKey | None: ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[ApiKey]: ...

    @abstractmethod
    def update_last_used(self, key: ApiKeyKey) -> None: ...

    @abstractmethod
    def revoke(self, key: ApiKeyKey) -> bool: ...

    @abstractmethod
    def expire_no_later_than(self, key: ApiKeyKey, at: datetime) -> bool:
        """Bring the key's ``expires_at`` forward to *at*; never push it later (#2137 rotation overlap).

        ``False`` when the key is unknown or already ends at or before *at*. Both key surfaces refuse
        an expired key on its next use, so the end of an overlap window needs no task to enforce it.
        """

    @abstractmethod
    def delete(self, key: ApiKeyKey) -> bool: ...
