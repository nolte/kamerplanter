from abc import ABC, abstractmethod

from app.domain.models.tenant import Tenant


class ITenantRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: str) -> Tenant | None: ...

    @abstractmethod
    def get_by_slug(self, slug: str) -> Tenant | None: ...

    @abstractmethod
    def create(self, tenant: Tenant) -> Tenant: ...

    @abstractmethod
    def update_fields(self, key: str, fields: dict) -> Tenant | None:
        """Apply a partial field update to one tenant (#968 §2).

        Named ``update_fields`` rather than ``update`` because that is what it
        is: ``fields`` is a partial payload, not a full model. Under the old
        name it shadowed the full-model ``update`` of the base repository with
        an arbitrary-``dict`` signature — an "update" that silently accepted
        mass assignment.

        Callers MUST build ``fields`` from named fields or a validated
        schema's ``model_dump()``, never from a raw request body.

        Returns ``None`` when no tenant carries ``key``.
        """

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def list_by_owner(self, owner_user_key: str) -> list[Tenant]: ...

    @abstractmethod
    def list_all(self) -> list[Tenant]:
        """Every tenant, newest first (platform-admin listing, #1019).

        Not tenant-scoped by design: this is the platform-admin cross-tenant
        catalogue, the same system-context read the router hand-wrote as raw AQL.
        """

    @abstractmethod
    def count(self, *, active_only: bool = False) -> int:
        """Number of tenant documents; ``active_only`` counts ``is_active`` ones (#1019)."""

    @abstractmethod
    def count_organizations_by_owner(self, owner_user_key: str) -> int: ...
