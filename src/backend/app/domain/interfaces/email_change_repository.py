from abc import ABC, abstractmethod

from app.common.types import UserKey
from app.domain.models.privacy import EmailChangeRequest, EmailChangeRequestKey


class IEmailChangeRepository(ABC):
    @abstractmethod
    def create(self, change_request: EmailChangeRequest) -> EmailChangeRequest: ...

    @abstractmethod
    def get_by_key(self, key: EmailChangeRequestKey) -> EmailChangeRequest | None: ...

    @abstractmethod
    def get_by_token_hash(self, token_hash: str) -> EmailChangeRequest | None: ...

    @abstractmethod
    def update(
        self,
        key: EmailChangeRequestKey,
        change_request: EmailChangeRequest,
    ) -> EmailChangeRequest: ...

    @abstractmethod
    def list_pending_for_user(self, user_key: UserKey) -> list[EmailChangeRequest]: ...

    @abstractmethod
    def expire_old(self, now_iso: str) -> int: ...

    @abstractmethod
    def delete(self, key: EmailChangeRequestKey) -> bool: ...
