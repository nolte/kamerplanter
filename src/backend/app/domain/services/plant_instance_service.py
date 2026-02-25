from datetime import UTC, datetime

from app.common.exceptions import NotFoundError
from app.common.types import PlantID, SlotKey, SpeciesKey
from app.domain.engines.companion_planting_engine import CompanionPlantingEngine
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.plant_instance import PlantInstance


class PlantInstanceService:
    def __init__(
        self,
        plant_repo: IPlantInstanceRepository,
        site_repo: ISiteRepository,
        rotation_validator: CropRotationValidator,
        companion_engine: CompanionPlantingEngine,
    ) -> None:
        self._repo = plant_repo
        self._site_repo = site_repo
        self._rotation = rotation_validator
        self._companion = companion_engine

    def list_plants(self, offset: int = 0, limit: int = 50) -> tuple[list[PlantInstance], int]:
        return self._repo.get_all(offset, limit)

    def get_plant(self, key: PlantID) -> PlantInstance:
        plant = self._repo.get_by_key(key)
        if plant is None:
            raise NotFoundError("PlantInstance", key)
        return plant

    def create_plant(self, plant: PlantInstance, skip_validation: bool = False) -> PlantInstance:
        if not skip_validation and plant.slot_key:
            # Validate rotation
            self._rotation.validate_or_raise(plant.slot_key, plant.species_key)
            # Validate companion planting
            self._companion.check_or_raise(plant.species_key, plant.slot_key)

        if plant.current_phase_started_at is None:
            plant.current_phase_started_at = datetime.now(UTC)

        created = self._repo.create(plant)

        # Mark slot as occupied
        if plant.slot_key:
            slot = self._site_repo.get_slot_by_key(plant.slot_key)
            if slot:
                slot.currently_occupied = True
                self._site_repo.update_slot(plant.slot_key, slot)

        return created

    def update_plant(self, key: PlantID, plant: PlantInstance) -> PlantInstance:
        self.get_plant(key)
        return self._repo.update(key, plant)

    def remove_plant(self, key: PlantID) -> PlantInstance:
        plant = self.get_plant(key)
        from datetime import date

        plant.removed_on = date.today()
        updated = self._repo.update(key, plant)

        if plant.slot_key:
            slot = self._site_repo.get_slot_by_key(plant.slot_key)
            if slot:
                active = self._repo.get_active_by_slot(plant.slot_key)
                if len(active) <= 1:
                    slot.currently_occupied = False
                    self._site_repo.update_slot(plant.slot_key, slot)

        return updated

    def get_plants_in_slot(self, slot_key: SlotKey) -> list[PlantInstance]:
        return self._repo.get_active_by_slot(slot_key)

    def get_slot_history(self, slot_key: SlotKey, years: int = 3) -> list[PlantInstance]:
        return self._repo.get_history_by_slot(slot_key, years)

    def validate_planting(self, slot_key: SlotKey, species_key: SpeciesKey) -> dict:
        rotation_valid, rotation_warnings = self._rotation.validate_planting(slot_key, species_key)
        companion_ok, companion_warnings, companion_benefits = self._companion.check_compatibility(
            species_key, slot_key
        )
        return {
            "valid": rotation_valid and companion_ok,
            "warnings": rotation_warnings + companion_warnings,
            "benefits": companion_benefits,
        }
