from abc import ABC, abstractmethod

from app.common.types import LocationKey, PlantID, PlantingRunEntryKey, PlantingRunKey
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry


class IPlantingRunRepository(ABC):
    # ── Run CRUD ──────────────────────────────────────────────────────

    @abstractmethod
    def get_all(
        self, offset: int = 0, limit: int = 50, filters: dict | None = None,
    ) -> tuple[list[PlantingRun], int]:
        ...

    @abstractmethod
    def get_by_key(self, key: PlantingRunKey) -> PlantingRun | None:
        ...

    @abstractmethod
    def create(self, run: PlantingRun) -> PlantingRun:
        ...

    @abstractmethod
    def update(self, key: PlantingRunKey, run: PlantingRun) -> PlantingRun:
        ...

    @abstractmethod
    def delete(self, key: PlantingRunKey) -> bool:
        ...

    # ── Entry CRUD ────────────────────────────────────────────────────

    @abstractmethod
    def create_entry(self, entry: PlantingRunEntry) -> PlantingRunEntry:
        ...

    @abstractmethod
    def get_entries(self, run_key: PlantingRunKey) -> list[PlantingRunEntry]:
        ...

    @abstractmethod
    def get_entry_by_key(self, entry_key: PlantingRunEntryKey) -> PlantingRunEntry | None:
        ...

    @abstractmethod
    def update_entry(self, entry_key: PlantingRunEntryKey, entry: PlantingRunEntry) -> PlantingRunEntry:
        ...

    @abstractmethod
    def delete_entry(self, entry_key: PlantingRunEntryKey) -> bool:
        ...

    # ── Edge operations ───────────────────────────────────────────────

    @abstractmethod
    def link_run_to_location(self, run_key: PlantingRunKey, location_key: str) -> None:
        ...

    @abstractmethod
    def link_run_to_substrate(self, run_key: PlantingRunKey, batch_key: str) -> None:
        ...

    @abstractmethod
    def link_run_to_plant(self, run_key: PlantingRunKey, plant_key: PlantID) -> None:
        ...

    @abstractmethod
    def link_run_to_entry(self, run_key: PlantingRunKey, entry_key: PlantingRunEntryKey) -> None:
        ...

    @abstractmethod
    def link_entry_to_species(self, entry_key: PlantingRunEntryKey, species_key: str) -> None:
        ...

    # ── Queries ───────────────────────────────────────────────────────

    @abstractmethod
    def get_run_plants(self, run_key: PlantingRunKey, include_detached: bool = False) -> list[dict]:
        ...

    @abstractmethod
    def detach_plant(self, run_key: PlantingRunKey, plant_key: PlantID, reason: str) -> None:
        ...

    @abstractmethod
    def get_existing_ids_at_location(self, location_key: LocationKey) -> set[str]:
        ...

    # ── Nutrient plan assignment ───────────────────────────────────────

    @abstractmethod
    def assign_nutrient_plan(self, run_key: PlantingRunKey, plan_key: str, assigned_by: str) -> dict:
        ...

    @abstractmethod
    def get_run_nutrient_plan_key(self, run_key: PlantingRunKey) -> str | None:
        ...

    @abstractmethod
    def remove_nutrient_plan(self, run_key: PlantingRunKey) -> bool:
        ...

    @abstractmethod
    def get_batch_phase_summaries(self, run_keys: list[str]) -> dict[str, list[dict]]:
        ...

    @abstractmethod
    def get_active_runs_with_schedule(self) -> list[dict]:
        ...

    @abstractmethod
    def get_plant_keys_with_active_schedule(self) -> set[str]:
        ...
