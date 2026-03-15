from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.invitation import Invitation


class IInvitationRepository(ABC):

    @abstractmethod
    def get_by_key(self, key: str) -> Invitation | None: ...

    @abstractmethod
    def get_by_token_hash(self, token_hash: str) -> Invitation | None: ...

    @abstractmethod
    def create(self, invitation: Invitation) -> Invitation: ...

    @abstractmethod
    def update(self, key: str, data: dict) -> Invitation | None: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def list_by_tenant(self, tenant_key: str) -> list[Invitation]: ...

    @abstractmethod
    def cleanup_expired(self) -> int: ...

    @abstractmethod
    def delete_all_for_tenant(self, tenant_key: str) -> int: ...
