from abc import ABC, abstractmethod

from app.domain.models.plant_diary_entry import PlantDiaryEntry


class IPlantDiaryRepository(ABC):
    """Interface for plant diary entry persistence."""

    @abstractmethod
    def create(self, entry: PlantDiaryEntry) -> PlantDiaryEntry: ...

    @abstractmethod
    def get_by_key(self, key: str) -> PlantDiaryEntry | None: ...

    @abstractmethod
    def update(self, key: str, entry: PlantDiaryEntry) -> PlantDiaryEntry: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def get_by_plant(self, plant_key: str, offset: int = 0, limit: int = 50) -> tuple[list[PlantDiaryEntry], int]: ...

    @abstractmethod
    def get_by_run(self, run_key: str, offset: int = 0, limit: int = 50) -> tuple[list[dict], int]: ...
