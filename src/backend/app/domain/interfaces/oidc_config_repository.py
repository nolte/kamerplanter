from abc import ABC, abstractmethod
from typing import Any

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
    def update_fields(self, key: OidcProviderConfigKey, fields: dict[str, Any]) -> OidcProviderConfig:
        """Merge only ``fields`` into the stored configuration (#1883 security review SEC-002/003).

        A write of the whole model from a snapshot read earlier reverts whatever
        changed meanwhile — including a step-up'd change of the issuer, the secret
        or ``enabled``. Callers build ``fields`` from a validated model.
        """

    @abstractmethod
    def delete(self, key: OidcProviderConfigKey) -> bool: ...

    @abstractmethod
    def list_all(self) -> list[OidcProviderConfig]: ...

    @abstractmethod
    def list_enabled(self) -> list[OidcProviderConfig]: ...
