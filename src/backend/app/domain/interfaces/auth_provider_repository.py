from abc import ABC, abstractmethod

from app.common.enums import AuthProviderType
from app.common.types import AuthProviderKey, UserKey
from app.domain.models.auth import AuthProvider


class IAuthProviderRepository(ABC):
    @abstractmethod
    def get_by_provider(self, provider: AuthProviderType, provider_user_id: str) -> AuthProvider | None: ...

    @abstractmethod
    def create(self, auth_provider: AuthProvider) -> AuthProvider: ...

    @abstractmethod
    def update(self, key: AuthProviderKey, auth_provider: AuthProvider) -> AuthProvider: ...

    @abstractmethod
    def delete(self, key: AuthProviderKey) -> bool: ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[AuthProvider]: ...
