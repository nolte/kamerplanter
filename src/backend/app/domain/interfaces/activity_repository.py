from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.types import ActivityKey
    from app.domain.models.activity import Activity


class IActivityRepository(ABC):
    @abstractmethod
    def get_all(
        self, offset: int = 0, limit: int = 50, filters: dict | None = None,
    ) -> tuple[list[Activity], int]:
        ...

    @abstractmethod
    def get_by_key(self, key: ActivityKey) -> Activity | None:
        ...

    @abstractmethod
    def get_by_name(self, name: str) -> Activity | None:
        ...

    @abstractmethod
    def create(self, activity: Activity) -> Activity:
        ...

    @abstractmethod
    def update(self, key: ActivityKey, activity: Activity) -> Activity:
        ...

    @abstractmethod
    def delete(self, key: ActivityKey) -> bool:
        ...

    @abstractmethod
    def get_system_activities(self) -> list[Activity]:
        ...

    @abstractmethod
    def get_by_category(self, category: str) -> list[Activity]:
        ...
