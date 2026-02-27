from abc import ABC, abstractmethod

from app.domain.models.membership import MemberInfo, Membership


class IMembershipRepository(ABC):

    @abstractmethod
    def get_by_key(self, key: str) -> Membership | None: ...

    @abstractmethod
    def get_by_user_and_tenant(
        self, user_key: str, tenant_key: str
    ) -> Membership | None: ...

    @abstractmethod
    def create(self, membership: Membership) -> Membership: ...

    @abstractmethod
    def update(self, key: str, data: dict) -> Membership | None: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def list_by_tenant(self, tenant_key: str) -> list[MemberInfo]: ...

    @abstractmethod
    def list_by_user(self, user_key: str) -> list[Membership]: ...

    @abstractmethod
    def count_admins(self, tenant_key: str) -> int: ...

    @abstractmethod
    def delete_all_for_tenant(self, tenant_key: str) -> int: ...
