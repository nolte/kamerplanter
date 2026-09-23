from abc import ABC, abstractmethod
from typing import Any

from app.common.types import UserKey
from app.domain.models.privacy import ErasureRequest, ErasureRequestKey


class IErasureRepository(ABC):
    @abstractmethod
    def create(self, erasure: ErasureRequest) -> ErasureRequest: ...

    @abstractmethod
    def get_by_key(self, key: ErasureRequestKey) -> ErasureRequest | None: ...

    @abstractmethod
    def get_or_raise(self, key: ErasureRequestKey) -> ErasureRequest: ...

    @abstractmethod
    def update(self, key: ErasureRequestKey, erasure: ErasureRequest) -> ErasureRequest: ...

    @abstractmethod
    def update_fields(self, key: ErasureRequestKey, fields: dict[str, Any]) -> ErasureRequest:
        """Merge exactly ``fields``, preserving ``None`` (``keep_none=True``).

        The status transitions write through this: the repository merges, so a
        full-model write can never clear ``error_message``, and a record that
        reached ``completed`` would keep saying the erasure did not run (#1662
        SCR-003).
        """
        ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[ErasureRequest]: ...

    @abstractmethod
    def find_active_for_user(self, user_key: UserKey) -> ErasureRequest | None: ...

    @abstractmethod
    def list_due_for_hard_delete(self, now_iso: str, stale_before_iso: str) -> list[ErasureRequest]: ...
