from abc import ABC, abstractmethod

from app.common.types import UserKey
from app.domain.models.privacy import ErasureRequest, ErasureRequestKey


class IErasureRepository(ABC):
    @abstractmethod
    def create(self, erasure: ErasureRequest) -> ErasureRequest: ...

    @abstractmethod
    def get_by_key(self, key: ErasureRequestKey) -> ErasureRequest | None: ...

    @abstractmethod
    def update(self, key: ErasureRequestKey, erasure: ErasureRequest) -> ErasureRequest: ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[ErasureRequest]: ...

    @abstractmethod
    def find_active_for_user(self, user_key: UserKey) -> ErasureRequest | None: ...

    @abstractmethod
    def list_due_for_hard_delete(self, now_iso: str) -> list[ErasureRequest]: ...
