"""Abstract interface for API key persistence."""

from abc import ABC, abstractmethod

from app.common.types import ApiKeyKey, UserKey
from app.domain.models.auth import ApiKey


class IApiKeyRepository(ABC):
    @abstractmethod
    def create(self, api_key: ApiKey) -> ApiKey: ...

    @abstractmethod
    def get_by_key(self, key: ApiKeyKey) -> ApiKey | None: ...

    @abstractmethod
    def get_by_hash(self, key_hash: str) -> ApiKey | None: ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[ApiKey]: ...

    @abstractmethod
    def update_last_used(self, key: ApiKeyKey) -> None: ...

    @abstractmethod
    def revoke(self, key: ApiKeyKey) -> bool: ...

    @abstractmethod
    def delete(self, key: ApiKeyKey) -> bool: ...
