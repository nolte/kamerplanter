from datetime import UTC, datetime

from app.common.enums import CycleType
from app.common.exceptions import PhaseTransitionError
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance


class PhaseTransitionEngine:
    """Manages plant phase transitions with validation."""

    def __init__(
        self,
        phase_repo: IPhaseRepository,
        plant_repo: IPlantInstanceRepository,
        phase_seq_repo: IPhaseSequenceRepository | None = None,
    ) -> None:
        self._phase_repo = phase_repo
        self._plant_repo = plant_repo
        self._phase_seq_repo = phase_seq_repo

    def _is_perennial_cycle_restart(
        self,
        current_phase_key: str,
        target_sequence_order: int,
    ) -> bool:
        """Check if transition is a valid perennial cycle restart.

        A cycle restart is allowed when the current phase is terminal,
        the lifecycle is perennial, and the target phase matches the
        configured cycle_restart_phase_order.

        Tries PhaseSequence first, falls back to LifecycleConfig.
        """
        current_phase = self._phase_repo.get_phase_by_key(current_phase_key)
        if current_phase is None or not current_phase.is_terminal:
            return False

        # Try PhaseSequence first (via lifecycle_key -> species_key -> PhaseSequence)
        if self._phase_seq_repo:
            lifecycle = self._phase_repo.get_lifecycle_by_key(current_phase.lifecycle_key)
            if lifecycle and lifecycle.species_key:
                seq = self._phase_seq_repo.get_sequence_by_species(lifecycle.species_key)
                if seq:
                    if seq.cycle_type != CycleType.PERENNIAL:
                        return False
                    if seq.cycle_restart_entry_order is not None:
                        return target_sequence_order == seq.cycle_restart_entry_order
                    return False

        # Fallback to LifecycleConfig
        lifecycle = self._phase_repo.get_lifecycle_by_key(current_phase.lifecycle_key)
        if lifecycle is None:
            return False

        if lifecycle.cycle_type != CycleType.PERENNIAL:
            return False

        if lifecycle.cycle_restart_phase_order is None:
            return False

        return target_sequence_order == lifecycle.cycle_restart_phase_order

    def validate_transition(self, plant_key: str, target_phase_key: str, *, force: bool = False) -> list[str]:
        """Validate if transition is allowed. Returns list of warnings (empty = OK)."""
        warnings: list[str] = []
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None:
            raise PhaseTransitionError(f"Plant '{plant_key}' not found")

        target_phase = self._phase_repo.get_phase_by_key(target_phase_key)
        if target_phase is None:
            raise PhaseTransitionError(f"Target phase '{target_phase_key}' not found")

        # If current_phase_key is not set (legacy plants), allow any transition
        current_phase = None
        if plant.current_phase_key:
            current_phase = self._phase_repo.get_phase_by_key(plant.current_phase_key)

        if current_phase is not None:
            if target_phase.sequence_order < current_phase.sequence_order:
                # Allow perennial cycle restarts without force
                if self._is_perennial_cycle_restart(
                    plant.current_phase_key or "",
                    target_phase.sequence_order,
                ):
                    warnings.append(f"Perennial cycle restart: {current_phase.name} → {target_phase.name}")
                elif force:
                    warnings.append(f"Forced backward transition: {current_phase.name} → {target_phase.name}")
                else:
                    raise PhaseTransitionError(
                        f"Backward transition not allowed: {current_phase.name} (order {current_phase.sequence_order}) "
                        f"→ {target_phase.name} (order {target_phase.sequence_order})"
                    )

            if target_phase.sequence_order == current_phase.sequence_order:
                raise PhaseTransitionError(f"Already in phase '{current_phase.name}'")

            # Check transition rules
            rules = self._phase_repo.get_transition_rules(current_phase.key or "")
            valid_targets = [r.to_phase_key for r in rules]
            if valid_targets and target_phase_key not in valid_targets:
                warnings.append(f"No explicit transition rule from '{current_phase.name}' to '{target_phase.name}'")

        return warnings

    def execute_transition(
        self,
        plant_key: str,
        target_phase_key: str,
        reason: str = "manual",
        *,
        force: bool = False,
    ) -> PlantInstance:
        """Execute a phase transition."""

        self.validate_transition(plant_key, target_phase_key, force=force)

        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None:
            raise PhaseTransitionError(f"Plant '{plant_key}' not found")

        target_phase = self._phase_repo.get_phase_by_key(target_phase_key)
        if target_phase is None:
            raise PhaseTransitionError(f"Target phase '{target_phase_key}' not found")

        now = datetime.now(UTC)

        # Determine cycle_number for the new phase history entry
        history = self._phase_repo.get_phase_history(plant_key)
        current_cycle_number = max((h.cycle_number for h in history), default=1)

        is_cycle_restart = plant.current_phase_key and self._is_perennial_cycle_restart(
            plant.current_phase_key,
            target_phase.sequence_order,
        )
        new_cycle_number = current_cycle_number + 1 if is_cycle_restart else current_cycle_number

        # Close current phase history
        for h in history:
            if h.exited_at is None:
                duration = None
                if plant.current_phase_started_at:
                    delta = now - plant.current_phase_started_at
                    duration = delta.days
                updated = PhaseHistory(
                    key=h.key,
                    plant_instance_key=h.plant_instance_key,
                    phase_key=h.phase_key,
                    phase_name=h.phase_name,
                    entered_at=h.entered_at,
                    exited_at=now,
                    actual_duration_days=duration,
                    transition_reason=reason,
                    cycle_number=h.cycle_number,
                )
                self._phase_repo.update_phase_history(h.key or "", updated)

        # Create new history entry
        new_history = PhaseHistory(
            plant_instance_key=plant_key,
            phase_key=target_phase_key,
            phase_name=target_phase.name,
            entered_at=now,
            transition_reason=reason,
            cycle_number=new_cycle_number,
        )
        self._phase_repo.create_phase_history(new_history)

        # Update plant
        plant.current_phase_key = target_phase_key
        plant.current_phase_started_at = now
        return self._plant_repo.update(plant_key, plant)
