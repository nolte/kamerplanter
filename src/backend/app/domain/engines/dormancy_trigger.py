from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.interfaces.species_repository import ISpeciesRepository


class DormancyTrigger:
    """Checks if dormancy conditions are met for perennial plants."""

    def __init__(
        self,
        phase_repo: IPhaseRepository,
        species_repo: ISpeciesRepository,
        phase_seq_repo: IPhaseSequenceRepository | None = None,
    ) -> None:
        self._phase_repo = phase_repo
        self._species_repo = species_repo
        self._phase_seq_repo = phase_seq_repo

    def _resolve_dormancy_config(self, species_key: str) -> tuple[bool, float | None]:
        """Resolve dormancy_required and critical_day_length_hours.

        Tries PhaseSequence first, falls back to LifecycleConfig.
        Returns (dormancy_required, critical_day_length_hours).
        """
        if self._phase_seq_repo:
            seq = self._phase_seq_repo.get_sequence_by_species(species_key)
            if seq:
                return seq.dormancy_required, seq.critical_day_length_hours

        lifecycle = self._phase_repo.get_lifecycle_by_species(species_key)
        if lifecycle is None:
            return False, None
        return lifecycle.dormancy_required, lifecycle.critical_day_length_hours

    def should_trigger_dormancy(self, species_key: str, current_temp_c: float, day_length_hours: float) -> bool:
        """Determine if dormancy should be triggered based on environmental conditions."""
        dormancy_required, critical_day_length = self._resolve_dormancy_config(species_key)
        if not dormancy_required:
            return False

        # Dormancy triggers: temperature drops below base temp or short photoperiod
        species = self._species_repo.get_by_key(species_key)
        if species is None:
            return False

        temp_trigger = current_temp_c < species.base_temp
        photoperiod_trigger = False
        if critical_day_length is not None:
            photoperiod_trigger = day_length_hours < critical_day_length

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
        dormancy_required, critical_day_length = self._resolve_dormancy_config(species_key)
        if not dormancy_required:
            # Distinguish "no config found" from "dormancy not required"
            has_config = False
            if self._phase_seq_repo:
                seq = self._phase_seq_repo.get_sequence_by_species(species_key)
                has_config = seq is not None
            if not has_config:
                lifecycle = self._phase_repo.get_lifecycle_by_species(species_key)
                has_config = lifecycle is not None
            if not has_config:
                return False, "No lifecycle found"
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
            if critical_day_length is not None:
                photoperiod_trigger = day_length < critical_day_length

            if not (temp_trigger or photoperiod_trigger):
                all_cold = False
                break

        if all_cold:
            return True, f"Dormancy conditions met for {consecutive_days_required} consecutive days"
        return False, "Not enough consecutive days meeting dormancy conditions"

    def get_dormancy_phase_key(self, species_key: str) -> str | None:
        """Find the dormancy phase key for a species.

        Tries PhaseSequence first, falls back to LifecycleConfig.
        """
        # Try PhaseSequence first
        if self._phase_seq_repo:
            seq = self._phase_seq_repo.get_sequence_by_species(species_key)
            if seq:
                entries = self._phase_seq_repo.get_entries_for_sequence(seq.key or "")
                for entry in entries:
                    defn = self._phase_seq_repo.get_definition_by_key(entry.phase_definition_key)
                    if defn and defn.name == "dormancy":
                        return entry.key
                # PhaseSequence exists but has no dormancy phase
                return None

        # Fallback to LifecycleConfig
        lifecycle = self._phase_repo.get_lifecycle_by_species(species_key)
        if lifecycle is None:
            return None
        phases = self._phase_repo.get_phases_by_lifecycle(lifecycle.key or "")
        for phase in phases:
            if phase.name == "dormancy":
                return phase.key
        return None
