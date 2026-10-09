from abc import ABC, abstractmethod

from app.common.types import ActivityKey
from app.domain.models.activity import Activity


class IActivityRepository(ABC):
    @abstractmethod
    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
        *,
        tenant_key: str,
    ) -> tuple[list[Activity], int]: ...

    @abstractmethod
    def get_readable_or_raise(self, key: ActivityKey, *, tenant_key: str) -> Activity: ...

    @abstractmethod
    def get_by_key(self, key: ActivityKey) -> Activity | None: ...

    @abstractmethod
    def get_or_raise(self, key: ActivityKey) -> Activity: ...

    @abstractmethod
    def create(self, activity: Activity) -> Activity: ...

    @abstractmethod
    def update(self, key: ActivityKey, activity: Activity) -> Activity: ...

    @abstractmethod
    def delete(self, key: ActivityKey) -> bool: ...

    @abstractmethod
    def get_system_activities(self, *, tenant_key: str) -> list[Activity]: ...

    @abstractmethod
    def get_by_category(self, category: str, *, tenant_key: str) -> list[Activity]: ...
