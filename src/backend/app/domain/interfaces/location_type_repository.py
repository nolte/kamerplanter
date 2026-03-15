from abc import ABC, abstractmethod

from app.domain.models.location_type import LocationType


class ILocationTypeRepository(ABC):
    @abstractmethod
    def get_all(self) -> list[LocationType]: ...

    @abstractmethod
    def get_by_key(self, key: str) -> LocationType | None: ...

    @abstractmethod
    def create(self, location_type: LocationType) -> LocationType: ...

    @abstractmethod
    def update(self, key: str, location_type: LocationType) -> LocationType: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...
