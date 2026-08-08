from abc import ABC, abstractmethod

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
    def count(self) -> int:
        """Total number of membership documents (platform-admin statistics, #1019)."""

    @abstractmethod
    def delete_all_for_tenant(self, tenant_key: str) -> int: ...

    @abstractmethod
    def delete_all_for_user(self, user_key: str) -> int:
        """Delete every membership of one user, with its graph edges (#1019).

        The user-perspective twin of :meth:`delete_all_for_tenant`; the
        platform-admin ``delete_user`` cascade routes its membership removal
        through here instead of hand-writing the ``REMOVE`` + edge cleanup in the
        router. Returns the number of memberships removed.
        """
