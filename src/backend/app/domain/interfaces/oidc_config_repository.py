from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.types import OidcProviderConfigKey
    from app.domain.models.oidc_config import OidcProviderConfig


class IOidcConfigRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: OidcProviderConfigKey) -> OidcProviderConfig | None: ...

    @abstractmethod
    def get_by_slug(self, slug: str) -> OidcProviderConfig | None: ...

    @abstractmethod
    def create(self, config: OidcProviderConfig) -> OidcProviderConfig: ...

    @abstractmethod
    def update(self, key: OidcProviderConfigKey, config: OidcProviderConfig) -> OidcProviderConfig: ...

    @abstractmethod
    def delete(self, key: OidcProviderConfigKey) -> bool: ...

    @abstractmethod
    def list_all(self) -> list[OidcProviderConfig]: ...

    @abstractmethod
    def list_enabled(self) -> list[OidcProviderConfig]: ...
