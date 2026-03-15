from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.common.exceptions import PhaseTransitionError
from app.domain.models.phase import PhaseHistory

if TYPE_CHECKING:
    from app.domain.interfaces.phase_repository import IPhaseRepository
    from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
    from app.domain.models.plant_instance import PlantInstance


class PhaseTransitionEngine:
    """Manages plant phase transitions with validation."""

    def __init__(self, phase_repo: IPhaseRepository, plant_repo: IPlantInstanceRepository) -> None:
        self._phase_repo = phase_repo
        self._plant_repo = plant_repo

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
                if force:
                    warnings.append(
                        f"Forced backward transition: {current_phase.name} → {target_phase.name}"
                    )
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
        self, plant_key: str, target_phase_key: str, reason: str = "manual", *, force: bool = False,
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

        # Close current phase history
        history = self._phase_repo.get_phase_history(plant_key)
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
                )
                self._phase_repo.update_phase_history(h.key or "", updated)

        # Create new history entry
        new_history = PhaseHistory(
            plant_instance_key=plant_key,
            phase_key=target_phase_key,
            phase_name=target_phase.name,
            entered_at=now,
            transition_reason=reason,
        )
        self._phase_repo.create_phase_history(new_history)

        # Update plant
        plant.current_phase_key = target_phase_key
        plant.current_phase_started_at = now
        return self._plant_repo.update(plant_key, plant)
