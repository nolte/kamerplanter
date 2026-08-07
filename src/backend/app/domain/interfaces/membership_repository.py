from abc import ABC, abstractmethod

from app.domain.models.membership import MemberInfo, Membership


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
    def count_managers(self, tenant_key: str) -> int: ...

    @abstractmethod
    def delete_all_for_tenant(self, tenant_key: str) -> int: ...
