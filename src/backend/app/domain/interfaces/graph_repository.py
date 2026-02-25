from abc import ABC, abstractmethod
from typing import Any

from app.common.types import SpeciesKey


class IGraphRepository(ABC):
    @abstractmethod
    def get_compatible_species(self, species_key: SpeciesKey) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_incompatible_species(self, species_key: SpeciesKey) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def set_compatibility(self, from_key: SpeciesKey, to_key: SpeciesKey, score: float) -> None:
        ...

    @abstractmethod
    def set_incompatibility(self, from_key: SpeciesKey, to_key: SpeciesKey, reason: str) -> None:
        ...

    @abstractmethod
    def remove_compatibility(self, from_key: SpeciesKey, to_key: SpeciesKey) -> bool:
        ...

    @abstractmethod
    def remove_incompatibility(self, from_key: SpeciesKey, to_key: SpeciesKey) -> bool:
        ...

    @abstractmethod
    def get_rotation_successors(self, family_key: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def set_rotation_successor(self, from_family_key: str, to_family_key: str, wait_years: int) -> None:
        ...

    @abstractmethod
    def get_adjacent_slots(self, slot_key: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def set_adjacent_slots(self, slot_a_key: str, slot_b_key: str) -> None:
        ...
