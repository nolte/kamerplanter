from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.types import PlantID, SlotKey, SpeciesKey
    from app.domain.models.plant_instance import PlantInstance


class IPlantInstanceRepository(ABC):
    @abstractmethod
    def get_all(self, offset: int = 0, limit: int = 50) -> tuple[list[PlantInstance], int]:
        ...

    @abstractmethod
    def get_by_key(self, key: PlantID) -> PlantInstance | None:
        ...

    @abstractmethod
    def get_by_instance_id(self, instance_id: str) -> PlantInstance | None:
        ...

    @abstractmethod
    def create(self, plant: PlantInstance) -> PlantInstance:
        ...

    @abstractmethod
    def update(self, key: PlantID, plant: PlantInstance) -> PlantInstance:
        ...

    @abstractmethod
    def delete(self, key: PlantID) -> bool:
        ...

    @abstractmethod
    def get_by_slot(self, slot_key: SlotKey) -> list[PlantInstance]:
        ...

    @abstractmethod
    def get_active_by_slot(self, slot_key: SlotKey) -> list[PlantInstance]:
        ...

    @abstractmethod
    def get_history_by_slot(self, slot_key: SlotKey, years: int = 3) -> list[PlantInstance]:
        ...

    @abstractmethod
    def get_by_species(self, species_key: SpeciesKey) -> list[PlantInstance]:
        ...

    @abstractmethod
    def resolve_phase_name(self, phase_key: str) -> str:
        """Resolve a GrowthPhase key to its name. Returns empty string if not found."""
        ...
