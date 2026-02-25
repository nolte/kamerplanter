from app.common.exceptions import RotationViolationError
from app.config.constants import DEFAULT_ROTATION_WINDOW_YEARS
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.species_repository import ISpeciesRepository


class CropRotationValidator:
    """Validates crop rotation rules for a slot."""

    def __init__(self, plant_repo: IPlantInstanceRepository, species_repo: ISpeciesRepository) -> None:
        self._plant_repo = plant_repo
        self._species_repo = species_repo

    def validate_planting(
        self,
        slot_key: str,
        species_key: str,
        rotation_window_years: int = DEFAULT_ROTATION_WINDOW_YEARS,
    ) -> tuple[bool, list[str]]:
        """Check if planting this species in the slot violates rotation rules.
        Returns (valid, warnings).
        """
        warnings: list[str] = []
        species = self._species_repo.get_by_key(species_key)
        if species is None:
            return False, ["Species not found"]

        history = self._plant_repo.get_history_by_slot(slot_key, years=rotation_window_years)

        for past_plant in history:
            past_species = self._species_repo.get_by_key(past_plant.species_key)
            if past_species is None:
                continue
            # Same family check
            if (
                past_species.family_key and species.family_key
                and past_species.family_key == species.family_key
            ):
                warnings.append(
                    f"Same family '{species.family_key}' was planted in this slot"
                    f" within the last {rotation_window_years} years"
                )

        return len(warnings) == 0, warnings

    def validate_or_raise(
        self, slot_key: str, species_key: str, rotation_window_years: int = DEFAULT_ROTATION_WINDOW_YEARS,
    ) -> None:
        valid, warnings = self.validate_planting(slot_key, species_key, rotation_window_years)
        if not valid:
            species = self._species_repo.get_by_key(species_key)
            family = species.family_key if species else "unknown"
            raise RotationViolationError(family, slot_key, rotation_window_years)
