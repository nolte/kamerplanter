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

    @abstractmethod
    def delete_by_config_slug(self, oidc_config_slug: str, *, only_without_issuer: bool = False) -> int:
        """Delete every link bound to the OIDC configuration *oidc_config_slug*; return how many (#1935).

        A link is matched by (configuration slug, ``sub``), so one left behind by a
        deleted configuration would be inherited by any configuration created later
        under the same slug. Deleting also drops the link's encrypted provider
        tokens, which are useless once the configuration they were issued through
        is gone. Exact slug only: a link bound to no configuration is not touched.
        ``only_without_issuer`` limits it to links that recorded no
        issuer — the ones a repointing of the configuration would hand to the new IdP.
        """
