from datetime import UTC, datetime

from app.common.exceptions import NotFoundError
from app.domain.interfaces.plant_diary_repository import IPlantDiaryRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.models.plant_diary_entry import PlantDiaryEntry


class PlantDiaryService:
    """Service for managing plant diary entries."""

    def __init__(
        self,
        diary_repo: IPlantDiaryRepository,
        run_repo: IPlantingRunRepository | None = None,
        plant_repo: IPlantInstanceRepository | None = None,
    ) -> None:
        self._repo = diary_repo
        self._run_repo = run_repo
        self._plant_repo = plant_repo

    def create_entry(
        self,
        plant_key: str,
        entry: PlantDiaryEntry,
        run_key: str | None = None,
    ) -> PlantDiaryEntry:
        """Create a diary entry for a plant.

        If run_key is provided, validates that the plant belongs to the run.
        """
        if run_key and self._run_repo:
            plants = self._run_repo.get_run_plants(run_key, include_detached=False)
            plant_keys = {p.get("_key", "") for p in plants}
            if plant_key not in plant_keys:
                raise NotFoundError("PlantInstance in Run", plant_key)

        entry.plant_key = plant_key
        now = datetime.now(UTC)
        entry.created_at = now
        entry.updated_at = now
        return self._repo.create(entry)

    def get_entry(self, key: str) -> PlantDiaryEntry:
        """Get a single diary entry by key."""
        entry = self._repo.get_by_key(key)
        if entry is None:
            raise NotFoundError("PlantDiaryEntry", key)
        return entry

    def update_entry(self, key: str, data: dict) -> PlantDiaryEntry:
        """Update a diary entry. Protects immutable fields."""
        existing = self.get_entry(key)
        protected_fields = {"key", "plant_key", "created_by", "created_at"}
        for field, value in data.items():
            if hasattr(existing, field) and field not in protected_fields:
                setattr(existing, field, value)
        existing.updated_at = datetime.now(UTC)
        return self._repo.update(key, existing)

    def delete_entry(self, key: str) -> bool:
        """Delete a diary entry. Raises NotFoundError if missing."""
        self.get_entry(key)
        return self._repo.delete(key)

    def list_entries_for_plant(
        self, plant_key: str, offset: int = 0, limit: int = 50
    ) -> tuple[list[PlantDiaryEntry], int]:
        """List diary entries for a specific plant with pagination."""
        return self._repo.get_by_plant(plant_key, offset, limit)

    def list_entries_for_run(self, run_key: str, offset: int = 0, limit: int = 50) -> tuple[list[dict], int]:
        """List diary entries for all plants in a run with pagination."""
        return self._repo.get_by_run(run_key, offset, limit)
