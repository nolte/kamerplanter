from abc import ABC, abstractmethod
from typing import Any

from app.common.types import CultivarKey, FamilyKey, SpeciesKey
from app.domain.models.species import Cultivar, Species


class ISpeciesRepository(ABC):
    @abstractmethod
    def get_all(self, offset: int = 0, limit: int = 50) -> tuple[list[Species], int]:
        ...

    @abstractmethod
    def get_by_key(self, key: SpeciesKey) -> Species | None:
        ...

    @abstractmethod
    def get_by_scientific_name(self, name: str) -> Species | None:
        ...

    @abstractmethod
    def create(self, species: Species) -> Species:
        ...

    @abstractmethod
    def update(self, key: SpeciesKey, species: Species) -> Species:
        ...

    @abstractmethod
    def delete(self, key: SpeciesKey) -> bool:
        ...

    @abstractmethod
    def search(self, name: str | None = None, family_key: FamilyKey | None = None) -> list[Species]:
        ...

    @abstractmethod
    def get_cultivars(self, species_key: SpeciesKey) -> list[Cultivar]:
        ...

    @abstractmethod
    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        ...

    @abstractmethod
    def get_cultivar_by_key(self, key: CultivarKey) -> Cultivar | None:
        ...

    @abstractmethod
    def update_cultivar(self, key: CultivarKey, cultivar: Cultivar) -> Cultivar:
        ...

    @abstractmethod
    def delete_cultivar(self, key: CultivarKey) -> bool:
        ...

    @abstractmethod
    def update_field(self, key: SpeciesKey, field: str, value: Any) -> None:
        ...
