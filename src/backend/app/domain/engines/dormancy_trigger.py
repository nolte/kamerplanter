from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.species_repository import ISpeciesRepository


class DormancyTrigger:
    """Checks if dormancy conditions are met for perennial plants."""

    def __init__(self, phase_repo: IPhaseRepository, species_repo: ISpeciesRepository) -> None:
        self._phase_repo = phase_repo
        self._species_repo = species_repo

    def should_trigger_dormancy(self, species_key: str, current_temp_c: float, day_length_hours: float) -> bool:
        """Determine if dormancy should be triggered based on environmental conditions."""
        lifecycle = self._phase_repo.get_lifecycle_by_species(species_key)
        if lifecycle is None:
            return False
        if not lifecycle.dormancy_required:
            return False

        # Dormancy triggers: temperature drops below base temp or short photoperiod
        species = self._species_repo.get_by_key(species_key)
        if species is None:
            return False

        temp_trigger = current_temp_c < species.base_temp
        photoperiod_trigger = False
        if lifecycle.critical_day_length_hours is not None:
            photoperiod_trigger = day_length_hours < lifecycle.critical_day_length_hours

        return temp_trigger or photoperiod_trigger

    def should_trigger_dormancy_consecutive(
        self,
        species_key: str,
        observations: list[dict],
        consecutive_days_required: int = 7,
    ) -> tuple[bool, str]:
        """Check if dormancy should trigger based on N consecutive observations.

        Each observation: {"temperature_c": float, "day_length_hours": float}
        Returns (should_trigger, reason).
        """
        lifecycle = self._phase_repo.get_lifecycle_by_species(species_key)
        if lifecycle is None:
            return False, "No lifecycle found"
        if not lifecycle.dormancy_required:
            return False, "Dormancy not required for this species"

        species = self._species_repo.get_by_key(species_key)
        if species is None:
            return False, "Species not found"

        if len(observations) < consecutive_days_required:
            return False, f"Not enough observations ({len(observations)}/{consecutive_days_required})"

        # Check last N observations
        recent = observations[-consecutive_days_required:]

        all_cold = True
        for obs in recent:
            temp = obs.get("temperature_c", 999.0)
            day_length = obs.get("day_length_hours", 24.0)

            temp_trigger = temp < species.base_temp
            photoperiod_trigger = False
            if lifecycle.critical_day_length_hours is not None:
                photoperiod_trigger = day_length < lifecycle.critical_day_length_hours

            if not (temp_trigger or photoperiod_trigger):
                all_cold = False
                break

        if all_cold:
            return True, f"Dormancy conditions met for {consecutive_days_required} consecutive days"
        return False, "Not enough consecutive days meeting dormancy conditions"

    def get_dormancy_phase_key(self, species_key: str) -> str | None:
        """Find the dormancy phase key for a species."""
        lifecycle = self._phase_repo.get_lifecycle_by_species(species_key)
        if lifecycle is None:
            return None
        phases = self._phase_repo.get_phases_by_lifecycle(lifecycle.key or "")
        for phase in phases:
            if phase.name == "dormancy":
                return phase.key
        return None
