from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.tenant import Tenant


class ITenantRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: str) -> Tenant | None: ...

    @abstractmethod
    def get_by_slug(self, slug: str) -> Tenant | None: ...

    @abstractmethod
    def create(self, tenant: Tenant) -> Tenant: ...

    @abstractmethod
    def update(self, key: str, data: dict) -> Tenant | None: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def list_by_owner(self, owner_user_key: str) -> list[Tenant]: ...

    @abstractmethod
    def count_organizations_by_owner(self, owner_user_key: str) -> int: ...
