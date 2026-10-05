from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.models.membership import MemberInfo, Membership, UserMembershipInfo


class IMembershipRepository(ABC):
    @abstractmethod
    def get_by_key(self, key: str) -> Membership | None: ...

    @abstractmethod
    def get_by_user_and_tenant(self, user_key: str, tenant_key: str) -> Membership | None: ...

    @abstractmethod
    def create(self, membership: Membership) -> Membership: ...

    @abstractmethod
    def update_fields(self, key: str, fields: dict) -> Membership | None:
        """Apply a partial field update to one membership (#968 §2).

        Named ``update_fields`` rather than ``update`` because that is what it
        is: ``fields`` is a partial payload, not a full model. Under the old
        name it shadowed the full-model ``update`` of the base repository with
        an arbitrary-``dict`` signature — an "update" that silently accepted
        mass assignment.

        Callers MUST build ``fields`` from named fields or a validated
        schema's ``model_dump()``, never from a raw request body.

        Returns ``None`` when no membership carries ``key``.
        """

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def delete_while_tenant_frozen(self, key: str, tenant_key: str) -> bool:
        """Remove membership *key* only while the tenant's deletion record is open, in one atomic step (#1924).

        The rollback of a join that found the tenant frozen after its insert
        (REQ-025 AK-IE-07). Atomic against the erasure's withdrawal of the
        record, so exactly one of the two decisions stands. ``True`` when the
        membership was removed; ``False`` when no open record exists any more —
        the membership stands then.

        Raises:
            WriteConflictError: a concurrent write on the record kept conflicting.
        """

    @abstractmethod
    def list_by_tenant(self, tenant_key: str) -> list[MemberInfo]: ...

    @abstractmethod
    def list_by_user(self, user_key: str) -> list[Membership]: ...

    @abstractmethod
    def list_by_user_with_tenant(self, user_key: str) -> list[UserMembershipInfo]:
        """A user's memberships, each joined to its tenant's name and slug.

        The user-perspective twin of :meth:`list_by_tenant`. Backs the
        platform-admin user-membership read paths (#1019) so the join is written
        once, in the data-access layer, instead of as raw AQL in three router
        handlers.
        """

    @abstractmethod
    def count_managers(self, tenant_key: str) -> int: ...

    @abstractmethod
    def count_active_members(self, *, tenant_key: str) -> int:
        """Active memberships of the tenant (``is_active != false``) - the seats its member limit counts (#2133)."""

    @abstractmethod
    def count(self) -> int:
        """Total number of membership documents (platform-admin statistics, #1019)."""

    @abstractmethod
    def deactivate_all_for_tenant(self, tenant_key: str) -> int:
        """Deactivate every membership of the tenant (#1769: freezes a tenant being erased)."""

    @abstractmethod
    def active_member_user_keys(self, *, tenant_key: str) -> list[str]:
        """The distinct account keys holding an active membership of the tenant (#1788)."""

    @abstractmethod
    def active_member_joined_at(self, *, tenant_key: str) -> dict[str, datetime | None]:
        """Active member account key → when that membership began (``None`` when not recorded), #1824.

        Same population as :meth:`active_member_user_keys`. Tells a member who
        was there when an account erasure froze the tenant from one who joined
        after it.
        """
