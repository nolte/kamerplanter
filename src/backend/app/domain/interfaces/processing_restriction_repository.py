from abc import ABC, abstractmethod

from app.common.types import UserKey
from app.domain.models.privacy import (
    ProcessingRestriction,
    ProcessingRestrictionKey,
)


class IProcessingRestrictionRepository(ABC):
    @abstractmethod
    def create(self, restriction: ProcessingRestriction) -> ProcessingRestriction: ...

    @abstractmethod
    def get_by_key(self, key: ProcessingRestrictionKey) -> ProcessingRestriction | None: ...

    @abstractmethod
    def get_or_raise(self, key: ProcessingRestrictionKey) -> ProcessingRestriction: ...

    @abstractmethod
    def get_by_user_and_scope(
        self,
        user_key: UserKey,
        scope: str,
    ) -> ProcessingRestriction | None: ...

    @abstractmethod
    def update(
        self,
        key: ProcessingRestrictionKey,
        restriction: ProcessingRestriction,
    ) -> ProcessingRestriction: ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[ProcessingRestriction]: ...

    @abstractmethod
    def list_active_by_user(self, user_key: UserKey) -> list[ProcessingRestriction]: ...

    @abstractmethod
    def delete(self, key: ProcessingRestrictionKey) -> bool: ...
