from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.sensor import Sensor


class ISensorRepository(ABC):
    @abstractmethod
    def create(self, sensor: Sensor) -> Sensor: ...

    @abstractmethod
    def get(self, key: str) -> Sensor | None: ...

    @abstractmethod
    def find_by_tank(self, tank_key: str) -> list[Sensor]: ...

    @abstractmethod
    def find_by_site(self, site_key: str) -> list[Sensor]: ...

    @abstractmethod
    def find_by_location(self, location_key: str) -> list[Sensor]: ...

    @abstractmethod
    def update(self, key: str, sensor: Sensor) -> Sensor: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...
