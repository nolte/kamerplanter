from abc import ABC, abstractmethod
from collections.abc import Callable

from app.domain.models.membership import Membership
from app.domain.models.security_audit import SecurityAuditEntry
from app.domain.models.tenant import Tenant


class ITenantRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: str) -> Tenant | None: ...

    @abstractmethod
    def get_by_slug(self, slug: str) -> Tenant | None: ...

    @abstractmethod
    def create(self, tenant: Tenant) -> Tenant: ...

    @abstractmethod
    def create_with_lead_membership(
        self,
        tenant: Tenant,
        membership: Membership,
        *,
        audit: Callable[[Tenant, Membership], SecurityAuditEntry] | None = None,
    ) -> tuple[Tenant, Membership]:
        """Found a tenant: tenant, founder membership, both edges and the audit row, atomically (#2118).

        The tenant document, the membership (its ``tenant_key`` is set to the new tenant's key), the
        ``has_membership`` and ``membership_in`` edges and, when ``audit`` is given, the security-audit row
        it builds from the stored tenant and membership are written in **one** transaction: either all of
        them exist or none does. Written one by one, a failure between two of them left a tenant nobody could
        reach or delete (its slug taken, no member), or a membership without edges.

        Raises the same domain conflicts :meth:`create` does (``DuplicateError`` for a taken slug).
        """

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
    def list_all(self, *, offset: int | None = None, limit: int | None = None) -> list[Tenant]:
        """Tenants, newest first (platform-admin listing, #1019); a window when ``limit`` is set (MT-035).

        Not tenant-scoped by design: this is the platform-admin cross-tenant
        catalogue, the same system-context read the router hand-wrote as raw AQL.
        """

    @abstractmethod
    def count(self, *, active_only: bool = False) -> int:
        """Number of tenant documents; ``active_only`` counts those in state ``active`` (#1019, #2123)."""

    @abstractmethod
    def count_organizations_by_owner(self, owner_user_key: str) -> int: ...

    @abstractmethod
    def personal_tenant_keys_by_owner(self, owner_user_key: str) -> list[str]:
        """The keys of every ``personal`` tenant *owner_user_key* owns, oldest first (#1788).

        Keys only, filtered in the query: the account erasure must reach a
        personal tenant even when a document of it would not pass model
        validation, and never loads the owner's organisations to find it.
        """
