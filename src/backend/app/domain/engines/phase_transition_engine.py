from datetime import UTC, date, datetime

from app.common.enums import CycleType, TerminationCause, TerminationType
from app.common.exceptions import PhaseTransitionError
from app.domain.engines.cycle_resolver import resolve_effective_cycle
from app.domain.engines.phase_key_resolver import PhaseKeyResolver
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance


class PhaseTransitionEngine:
    """Manages plant phase transitions with validation.

    Phase keys are resolved through :class:`PhaseKeyResolver` across both the
    PhaseSequenceEntry and legacy GrowthPhase key-spaces (#579): before this the
    engine looked keys up only in ``growth_phases``, so every transition of a
    PhaseSequence-driven species failed with ``Target phase '…' not found``.
    """

    def __init__(
        self,
        phase_repo: IPhaseRepository,
        plant_repo: IPlantInstanceRepository,
        phase_seq_repo: IPhaseSequenceRepository | None = None,
    ) -> None:
        self._phase_repo = phase_repo
        self._plant_repo = plant_repo
        self._phase_seq_repo = phase_seq_repo
        self._resolver = PhaseKeyResolver(phase_repo, phase_seq_repo)

    def _is_perennial_cycle_restart(
        self,
        plant: PlantInstance,
        current_phase_key: str,
        target_sequence_order: int,
    ) -> bool:
        """Check if transition is a valid perennial cycle restart.

        A cycle restart is allowed when the current phase is terminal, the plant is
        effectively perennial, and the target phase matches the configured
        cycle-restart order. The annual-vs-perennial gate runs through the single
        :func:`resolve_effective_cycle` cascade (ADR-006 E1) — the same one used by
        the auto-transition restart gate (``app/tasks/phase_transitions.py``) and the
        REQ-047 season coupler — instead of the raw botanical ``cycle_type``. That
        makes the engine honour BOTH the per-instance ``cultivation_cycle_type``
        override AND the species-level ``cultivation_cycle_type`` (a botanically
        perennial species grown as an annual, e.g. the tomato cohort after #735, must
        not restart even if it later gains a repeating sequence or a
        ``cycle_restart`` anchor). ``resolve_effective_cycle`` already consults the
        instance tier first, so the override precedence is applied exactly once.

        Resolves the current phase across both key-spaces (#579): a PhaseSequence
        entry carries its owning sequence directly (``sequence_key``); a legacy
        GrowthPhase reaches its sequence via ``lifecycle_key -> species_key ->
        PhaseSequence`` and finally falls back to the LifecycleConfig itself.
        """
        current_phase = self._resolver.resolve(current_phase_key)
        if current_phase is None or not current_phase.is_terminal:
            return False

        # PhaseSequence-driven phase: the entry owns its sequence directly, so the
        # restart decision reads the sequence's cycle metadata without a detour
        # through LifecycleConfig (#579). The species LifecycleConfig is still resolved
        # so the effective-cycle gate can see a species-level ``cultivation_cycle_type``
        # (a botanically perennial species grown annually); ``None`` for a pure Weg-B
        # species without a LifecycleConfig, where the sequence's cycle_type governs.
        if current_phase.source == "phase_sequence" and self._phase_seq_repo and current_phase.sequence_key:
            seq = self._phase_seq_repo.get_sequence_by_key(current_phase.sequence_key)
            if seq:
                lifecycle = self._phase_repo.get_lifecycle_by_species(plant.species_key) if plant.species_key else None
                if resolve_effective_cycle(plant, lifecycle, seq) != CycleType.PERENNIAL:
                    return False
                if seq.cycle_restart_entry_order is not None:
                    return target_sequence_order == seq.cycle_restart_entry_order
                return False

        # Legacy GrowthPhase: try PhaseSequence via lifecycle_key -> species_key.
        if self._phase_seq_repo and current_phase.lifecycle_key:
            lifecycle = self._phase_repo.get_lifecycle_by_key(current_phase.lifecycle_key)
            if lifecycle and lifecycle.species_key:
                seq = self._phase_seq_repo.get_sequence_by_species(lifecycle.species_key)
                if seq:
                    if resolve_effective_cycle(plant, lifecycle, seq) != CycleType.PERENNIAL:
                        return False
                    if seq.cycle_restart_entry_order is not None:
                        return target_sequence_order == seq.cycle_restart_entry_order
                    return False

        # Fallback to LifecycleConfig.
        lifecycle = self._phase_repo.get_lifecycle_by_key(current_phase.lifecycle_key or "")
        if lifecycle is None:
            return False

        if resolve_effective_cycle(plant, lifecycle, None) != CycleType.PERENNIAL:
            return False

        if lifecycle.cycle_restart_phase_order is None:
            return False

        return target_sequence_order == lifecycle.cycle_restart_phase_order

    def _is_reversion(self, current_phase_key: str | None, target_phase_key: str) -> bool:
        """E3: a controlled backward transition explicitly allowed by a transition
        rule with ``is_reversion=True`` (e.g. re-vegging, mother-plant upkeep) — no
        cycle-restart semantics."""
        if not current_phase_key:
            return False
        rules = self._phase_repo.get_transition_rules(current_phase_key)
        return any(r.to_phase_key == target_phase_key and r.is_reversion for r in rules)

    def _is_premature(self, current_phase_key: str | None, target_phase_key: str) -> bool:
        """E6: a stress-induced premature transition (e.g. vegetative → bolting under
        heat/long-day stress), flagged on the transition rule with ``is_premature=True``.
        Recorded on the resulting phase history so analytics can tell it apart from a
        planned bolting."""
        if not current_phase_key:
            return False
        rules = self._phase_repo.get_transition_rules(current_phase_key)
        return any(r.to_phase_key == target_phase_key and r.is_premature for r in rules)

    def validate_transition(self, plant_key: str, target_phase_key: str, *, force: bool = False) -> list[str]:
        """Validate if transition is allowed. Returns list of warnings (empty = OK)."""
        warnings: list[str] = []
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None:
            raise PhaseTransitionError(f"Plant '{plant_key}' not found")

        target_phase = self._resolver.resolve(target_phase_key)
        if target_phase is None:
            raise PhaseTransitionError(f"Target phase '{target_phase_key}' not found")

        # If current_phase_key is not set (legacy plants), allow any transition
        current_phase = None
        if plant.current_phase_key:
            current_phase = self._resolver.resolve(plant.current_phase_key)

        if current_phase is not None:
            if target_phase.sequence_order < current_phase.sequence_order:
                # Allow perennial cycle restarts without force
                if self._is_perennial_cycle_restart(
                    plant,
                    plant.current_phase_key or "",
                    target_phase.sequence_order,
                ):
                    warnings.append(f"Perennial cycle restart: {current_phase.name} → {target_phase.name}")
                elif self._is_reversion(plant.current_phase_key, target_phase_key):
                    warnings.append(f"Controlled reversion: {current_phase.name} → {target_phase.name}")
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

        target_phase = self._resolver.resolve(target_phase_key)
        if target_phase is None:
            raise PhaseTransitionError(f"Target phase '{target_phase_key}' not found")

        now = datetime.now(UTC)

        # Determine cycle_number for the new phase history entry
        history = self._phase_repo.get_phase_history(plant_key)
        current_cycle_number = max((h.cycle_number for h in history), default=1)

        is_cycle_restart = plant.current_phase_key and self._is_perennial_cycle_restart(
            plant,
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
                    is_premature=h.is_premature,
                )
                self._phase_repo.update_phase_history(h.key or "", updated)

        # Create new history entry — flag a stress-induced premature transition (E6)
        # so it is distinguishable from a planned bolting in the history/analytics.
        new_history = PhaseHistory(
            plant_instance_key=plant_key,
            phase_key=target_phase_key,
            phase_name=target_phase.name,
            entered_at=now,
            transition_reason=reason,
            cycle_number=new_cycle_number,
            is_premature=self._is_premature(plant.current_phase_key, target_phase_key),
        )
        self._phase_repo.create_phase_history(new_history)

        # Count controlled reversions (E3) — re-vegging etc.
        if self._is_reversion(plant.current_phase_key, target_phase_key):
            plant.reversion_count += 1

        # Update plant
        plant.current_phase_key = target_phase_key
        plant.current_phase_started_at = now
        return self._plant_repo.update(plant_key, plant)

    def terminate(
        self,
        plant_key: str,
        termination_type: TerminationType,
        *,
        termination_cause: TerminationCause | None = None,
        on_date: date | None = None,
    ) -> PlantInstance:
        """E5: end a plant's lifecycle, distinguishing planned end from unplanned loss.

        ``died`` (unplanned) freezes the current growth phase — the open phase-history
        entry is closed at the time of death and NO transition to ``senescence`` happens,
        so failure analytics can attribute the loss to the phase it occurred in.
        ``harvested``/``senesced`` are the planned ends; ``cancelled`` is a user abort.
        ``termination_cause`` is only meaningful for ``died``.
        """
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None:
            raise PhaseTransitionError(f"Plant '{plant_key}' not found")
        if termination_cause is not None and termination_type != TerminationType.DIED:
            raise PhaseTransitionError("termination_cause is only valid for termination_type='died'")

        now = datetime.now(UTC)
        # Freeze the current phase: close the open phase-history entry, no new transition.
        for h in self._phase_repo.get_phase_history(plant_key):
            if h.exited_at is None:
                duration = None
                if plant.current_phase_started_at:
                    duration = (now - plant.current_phase_started_at).days
                self._phase_repo.update_phase_history(
                    h.key or "",
                    PhaseHistory(
                        key=h.key,
                        plant_instance_key=h.plant_instance_key,
                        phase_key=h.phase_key,
                        phase_name=h.phase_name,
                        entered_at=h.entered_at,
                        exited_at=now,
                        actual_duration_days=duration,
                        transition_reason=termination_type.value,
                        cycle_number=h.cycle_number,
                        is_premature=h.is_premature,
                    ),
                )

        plant.termination_type = termination_type
        plant.termination_cause = termination_cause
        plant.removed_on = on_date or now.date()
        return self._plant_repo.update(plant_key, plant)
