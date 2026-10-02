from abc import ABC, abstractmethod

from app.common.enums import AuthProviderType
from app.common.types import AuthProviderKey, UserKey
from app.domain.models.auth import AuthProvider


class IAuthProviderRepository(ABC):
    @abstractmethod
    def list_by_provider(self, provider: AuthProviderType, provider_user_id: str) -> list[AuthProvider]:
        """Every link of *provider* type with this subject — across all configurations (#1869).

        A subject is unique per issuer only, so this is a candidate list, never an
        identity: the caller picks the link of the configuration the sign-in came
        through (``AuthService._login_link``).
        """

    @abstractmethod
    def create(self, auth_provider: AuthProvider) -> AuthProvider: ...

    @abstractmethod
    def update(self, key: AuthProviderKey, auth_provider: AuthProvider) -> AuthProvider: ...

    @abstractmethod
    def delete(self, key: AuthProviderKey) -> bool: ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[AuthProvider]: ...
