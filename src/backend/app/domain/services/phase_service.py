from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from app.common.enums import TransitionTrigger
from app.common.exceptions import NotFoundError
from app.common.types import PhaseKey, PlantID
from app.domain.engines.phase_key_resolver import PhaseKeyResolver
from app.domain.engines.phase_role_map import core_phase
from app.domain.engines.phase_transition_engine import PhaseTransitionEngine
from app.domain.engines.resource_profile_generator import ResourceProfileGenerator
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase import NutrientProfile, PhaseHistory, PhaseTransitionRule, RequirementProfile
from app.domain.models.plant_instance import PlantInstance

logger = structlog.get_logger()


@dataclass(frozen=True)
class SequenceAutoTarget:
    """The next automatic-transition target for a PhaseSequence-driven plant (WP-2).

    Derived directly from the plant's PhaseSequence entries — the sequence *is* the
    transition definition (ADR-006 E2, one model / Weg B), so no second GrowthPhase
    rule set is needed. ``is_restart`` marks the terminal→restart edge that fires the
    perennial cycle restart at ``cycle_restart_entry_order``.
    """

    target_phase_key: str
    duration_days: int
    is_restart: bool
    current_is_terminal: bool


class PhaseService:
    def __init__(
        self,
        phase_repo: IPhaseRepository,
        plant_repo: IPlantInstanceRepository,
        phase_seq_repo: IPhaseSequenceRepository | None = None,
    ) -> None:
        self._repo = phase_repo
        self._plant_repo = plant_repo
        self._phase_seq_repo = phase_seq_repo
        self._transition_engine = PhaseTransitionEngine(phase_repo, plant_repo, phase_seq_repo=phase_seq_repo)
        self._resolver = PhaseKeyResolver(phase_repo, phase_seq_repo)
        self._profile_generator = ResourceProfileGenerator()
        self._on_phase_transition_callbacks: list = []

    def register_on_transition(self, callback) -> None:
        """Register a post-transition callback to invoke after phase transitions.

        The callback is invoked as ``callback(plant_key, phase_name, trigger=...)``
        where ``trigger`` is a :class:`TransitionTrigger` distinguishing an
        automatic (Celery) advance from a manual (API) one. Callbacks that do not
        care about the trigger accept it as a keyword-only argument and ignore it.
        """
        self._on_phase_transition_callbacks.append(callback)

    def _resolve_phases_for_species(self, species_key: str) -> tuple[list[dict], str, dict]:
        """Resolve phases for a species, preferring PhaseSequence over LifecycleConfig.

        Returns:
            Tuple of (phases_list, cycle_type, sequence_metadata).
            phases_list contains GrowthPhase-compatible dicts.
        """
        # Try PhaseSequence first
        if self._phase_seq_repo:
            seq = self._phase_seq_repo.get_sequence_by_species(species_key)
            if seq:
                entries = self._phase_seq_repo.get_entries_for_sequence(seq.key or "")
                phases: list[dict] = []
                for entry in entries:
                    defn = self._phase_seq_repo.get_definition_by_key(entry.phase_definition_key)
                    phases.append(
                        {
                            "key": entry.key,
                            "name": defn.name if defn else "",
                            "display_name": defn.display_name if defn else "",
                            "typical_duration_days": (
                                entry.override_duration_days or (defn.typical_duration_days if defn else 1)
                            ),
                            "sequence_order": entry.sequence_order,
                            "is_terminal": entry.is_terminal,
                            "allows_harvest": entry.allows_harvest,
                            "is_recurring": entry.is_recurring,
                            "stress_tolerance": defn.stress_tolerance.value if defn else "medium",
                            "watering_interval_days": defn.watering_interval_days if defn else None,
                        }
                    )
                cycle_type_val = seq.cycle_type.value if hasattr(seq.cycle_type, "value") else seq.cycle_type
                meta = {
                    "cycle_type": cycle_type_val,
                    "is_repeating": seq.is_repeating,
                    "cycle_restart_entry_order": seq.cycle_restart_entry_order,
                    "dormancy_required": seq.dormancy_required,
                    "source": "phase_sequence",
                    "sequence_key": seq.key,
                }
                return phases, str(cycle_type_val), meta

        # Fallback to LifecycleConfig
        lc = self._repo.get_lifecycle_by_species(species_key)
        if not lc:
            return [], "annual", {}
        growth_phases = self._repo.get_phases_by_lifecycle(lc.key or "")
        phases = [
            {
                "key": gp.key,
                "name": gp.name,
                "display_name": gp.display_name,
                "typical_duration_days": gp.typical_duration_days,
                "sequence_order": gp.sequence_order,
                "is_terminal": gp.is_terminal,
                "allows_harvest": gp.allows_harvest,
                "is_recurring": gp.is_recurring,
                "stress_tolerance": (
                    gp.stress_tolerance.value if hasattr(gp.stress_tolerance, "value") else gp.stress_tolerance
                ),
                "watering_interval_days": gp.watering_interval_days,
            }
            for gp in growth_phases
        ]
        cycle_type_val = lc.cycle_type.value if hasattr(lc.cycle_type, "value") else lc.cycle_type
        meta = {
            "cycle_type": cycle_type_val,
            "is_repeating": str(cycle_type_val) == "perennial",
            "cycle_restart_entry_order": lc.cycle_restart_phase_order,
            "dormancy_required": lc.dormancy_required,
            "source": "lifecycle_config",
            "lifecycle_key": lc.key,
        }
        return phases, str(cycle_type_val), meta

    # --- Lifecycle ---

    def get_lifecycle(self, key: str) -> LifecycleConfig:
        return self._repo.get_lifecycle_or_raise(key)

    def get_lifecycle_by_species(self, species_key: str) -> LifecycleConfig:
        lc = self._repo.get_lifecycle_by_species(species_key)
        if lc is None:
            raise NotFoundError("LifecycleConfig for species", species_key)
        return lc

    def create_lifecycle(self, config: LifecycleConfig) -> LifecycleConfig:
        return self._repo.create_lifecycle(config)

    def update_lifecycle(self, key: str, config: LifecycleConfig) -> LifecycleConfig:
        self.get_lifecycle(key)
        return self._repo.update_lifecycle(key, config)

    # --- Phases ---

    def get_phases(self, lifecycle_key: str) -> list[GrowthPhase]:
        return self._repo.get_phases_by_lifecycle(lifecycle_key)

    def get_phase(self, key: PhaseKey) -> GrowthPhase:
        return self._repo.get_phase_or_raise(key)

    def create_phase(self, phase: GrowthPhase) -> GrowthPhase:
        return self._repo.create_phase(phase)

    def update_phase(self, key: PhaseKey, phase: GrowthPhase) -> GrowthPhase:
        self.get_phase(key)
        return self._repo.update_phase(key, phase)

    def delete_phase(self, key: PhaseKey) -> bool:
        self.get_phase(key)
        return self._repo.delete_phase(key)

    # --- Profiles ---

    def get_requirement_profile(self, phase_key: PhaseKey) -> RequirementProfile:
        profile = self._repo.get_requirement_profile(phase_key)
        if profile is None:
            raise NotFoundError("RequirementProfile for phase", phase_key)
        return profile

    def create_requirement_profile(self, profile: RequirementProfile) -> RequirementProfile:
        return self._repo.create_requirement_profile(profile)

    def update_requirement_profile(self, key: str, profile: RequirementProfile) -> RequirementProfile:
        return self._repo.update_requirement_profile(key, profile)

    def get_nutrient_profile(self, phase_key: PhaseKey) -> NutrientProfile:
        profile = self._repo.get_nutrient_profile(phase_key)
        if profile is None:
            raise NotFoundError("NutrientProfile for phase", phase_key)
        return profile

    def create_nutrient_profile(self, profile: NutrientProfile) -> NutrientProfile:
        return self._repo.create_nutrient_profile(profile)

    def update_nutrient_profile(self, key: str, profile: NutrientProfile) -> NutrientProfile:
        return self._repo.update_nutrient_profile(key, profile)

    def generate_default_profiles(self, phase_key: PhaseKey) -> tuple[RequirementProfile, NutrientProfile]:
        phase = self.get_phase(phase_key)
        req = self._profile_generator.generate_requirement_profile(phase.name, phase_key)
        nut = self._profile_generator.generate_nutrient_profile(phase.name, phase_key)
        req = self._repo.create_requirement_profile(req)
        nut = self._repo.create_nutrient_profile(nut)
        return req, nut

    # --- Transition Rules ---

    def get_transition_rules(self, from_phase_key: PhaseKey) -> list[PhaseTransitionRule]:
        return self._repo.get_transition_rules(from_phase_key)

    def create_transition_rule(self, rule: PhaseTransitionRule) -> PhaseTransitionRule:
        return self._repo.create_transition_rule(rule)

    # --- Phase Transitions ---

    def get_current_phase(self, plant_key: PlantID) -> dict:
        plant = self._plant_repo.get_or_raise(plant_key)

        # Phase history is the source of truth for phase key and start time
        history = self._repo.get_phase_history(plant_key)
        active = next((h for h in history if h.exited_at is None), None)

        phase_key = active.phase_key if active else plant.current_phase_key
        phase_started_at = active.entered_at if active else plant.current_phase_started_at
        cycle_number = active.cycle_number if active else 1

        days_in_phase = 0
        if phase_started_at:
            delta = datetime.now(UTC) - phase_started_at
            days_in_phase = delta.days

        next_phase = None
        if phase_key:
            rules = self._repo.get_transition_rules(phase_key)
            if rules:
                target = self._repo.get_phase_by_key(rules[0].to_phase_key)
                if target:
                    next_phase = target.name

        # Resolve the phase name across both key-spaces (#579): a sequence-driven
        # plant carries a PhaseSequenceEntry key that the legacy GrowthPhase lookup
        # never finds. ``lifecycle_key`` only exists for a legacy GrowthPhase and
        # gates the LifecycleConfig fallback below.
        phase_name = ""
        lifecycle_key = None
        current_source: str | None = None
        current_is_terminal = False
        if phase_key:
            resolved = self._resolver.resolve(phase_key)
            if resolved:
                phase_name = resolved.name
                lifecycle_key = resolved.lifecycle_key
                current_source = resolved.source
                current_is_terminal = resolved.is_terminal

        # Resolve lifecycle metadata — prefer PhaseSequence, fallback to LifecycleConfig
        cycle_type: str | None = None
        has_harvest_phase = False

        # Try PhaseSequence first via species_key on the plant
        resolved_from_seq = False
        if plant.species_key and self._phase_seq_repo:
            seq_phases, seq_cycle_type, seq_meta = self._resolve_phases_for_species(plant.species_key)
            if seq_phases:
                cycle_type = seq_cycle_type
                has_harvest_phase = any(p.get("allows_harvest", False) for p in seq_phases)
                resolved_from_seq = True

        # Fallback to LifecycleConfig
        if not resolved_from_seq and lifecycle_key:
            lifecycle = self._repo.get_lifecycle_by_key(lifecycle_key)
            if lifecycle:
                cycle_type = lifecycle.cycle_type.value
            phases = self._repo.get_phases_by_lifecycle(lifecycle_key)
            has_harvest_phase = any(p.allows_harvest for p in phases)

        # ADR-006 E1 — reflect the per-instance cultivation override in the reported
        # cycle_type so the dashboard / phase detail / timeline show the EFFECTIVE
        # cycle the plant is actually grown on (the single-source-of-truth cascade;
        # the species tiers already produced ``cycle_type`` above).
        if plant.cultivation_cycle_type is not None:
            cycle_type = plant.cultivation_cycle_type.value

        return {
            "phase": phase_name,
            "phase_key": phase_key,
            "days_in_phase": days_in_phase,
            "next_phase": next_phase,
            "cycle_type": cycle_type,
            "cycle_number": cycle_number,
            "has_harvest_phase": has_harvest_phase,
            # ── #579 key-space + WP-2 auto-advance ──
            # ``source`` selects the auto-advance path (phase_sequence → sequence-driven
            # cyclic advance; growth_phase → legacy rule-based). ``is_terminal`` gates the
            # perennial cycle restart out of the terminal phase.
            "source": current_source,
            "is_terminal": current_is_terminal,
        }

    def resolve_sequence_auto_target(
        self,
        species_key: str | None,
        current_phase_key: str | None,
    ) -> SequenceAutoTarget | None:
        """WP-2 — the next automatic-transition target for a PhaseSequence-driven plant.

        Reads the species' PhaseSequence and its entries and returns the forward next
        entry (by ``sequence_order``) or, when the current entry is terminal, the
        ``cycle_restart_entry_order`` entry (a perennial cycle restart). Returns
        ``None`` when the species is not PhaseSequence-driven, the current key is not
        an entry of that sequence, there is no forward step, or a terminal phase has
        no restart anchor (a bounded/monocarpic sequence terminates instead of
        looping). The sequence is the single transition model (ADR-006 E2); no second
        GrowthPhase rule set is consulted.
        """
        if not self._phase_seq_repo or not species_key or not current_phase_key:
            return None
        seq = self._phase_seq_repo.get_sequence_by_species(species_key)
        if seq is None:
            return None
        entries = self._phase_seq_repo.get_entries_for_sequence(seq.key or "")
        if not entries:
            return None
        entries_sorted = sorted(entries, key=lambda e: e.sequence_order)
        current = next((e for e in entries_sorted if e.key == current_phase_key), None)
        if current is None:
            return None
        duration = current.override_duration_days or self._entry_duration_days(current)

        if current.is_terminal:
            # Seasonal cycle restart out of the terminal phase (perennial loop). A
            # non-repeating sequence (annual/biennial/monocarpic) has no restart
            # anchor → the lifecycle terminates rather than looping.
            if not seq.is_repeating or seq.cycle_restart_entry_order is None:
                return None
            target = next((e for e in entries_sorted if e.sequence_order == seq.cycle_restart_entry_order), None)
            if target is None or not target.key:
                return None
            return SequenceAutoTarget(target.key, duration, is_restart=True, current_is_terminal=True)

        forward = [e for e in entries_sorted if e.sequence_order > current.sequence_order and e.key]
        if not forward:
            return None
        return SequenceAutoTarget(forward[0].key or "", duration, is_restart=False, current_is_terminal=False)

    def _entry_duration_days(self, entry) -> int:  # noqa: ANN001 — PhaseSequenceEntry (avoid import churn)
        """Duration of a sequence entry: its override, else the definition default."""
        if not self._phase_seq_repo:
            return 1
        defn = self._phase_seq_repo.get_definition_by_key(entry.phase_definition_key)
        return (defn.typical_duration_days if defn else 1) or 1

    def find_phase_key_by_name(self, species_key: str, phase_name: str) -> str | None:
        """Resolve a species' phase key (entry or GrowthPhase key) by phase name.

        Used by the REQ-047↔REQ-003 coupling (ADR-006 E3) to find the ``dormancy``
        target for the season-driven dormancy transition. Returns ``None`` when the
        species has no phase of that name (e.g. an evergreen without a dormancy phase).
        """
        phases, _cycle, _meta = self._resolve_phases_for_species(species_key)
        for phase in phases:
            if phase.get("name") == phase_name and phase.get("key"):
                return phase["key"]
        return None

    def find_phase_key_by_role(self, species_key: str, core_role: str) -> str | None:
        """Resolve a species' phase key by its REQ-003 §D8 engine ROLE, not its literal name.

        Unlike :meth:`find_phase_key_by_name`, this matches any archetype-specific phase
        that *behaves* like ``core_role`` via ``phase_role_map.core_phase`` — e.g. the #616
        fine-typed rest phases ``winter_rest`` / ``rest_phase`` / ``dry_storage`` all resolve
        to the ``dormancy`` role. Used by the REQ-047 ↔ REQ-003 season coupling (ADR-006 E3)
        so the site winter signal reaches a plant's real, botanically-named rest phase and
        not only a literal ``dormancy``. Returns the first matching phase in sequence order,
        or ``None`` when the species has no phase in that role.
        """
        phases, _cycle, _meta = self._resolve_phases_for_species(species_key)
        for phase in sorted(phases, key=lambda p: p.get("sequence_order") or 0):
            name = phase.get("name")
            if name and core_phase(name) == core_role and phase.get("key"):
                return phase["key"]
        return None

    def resolve_cycle_restart_phase_key(self, species_key: str) -> str | None:
        """Resolve the phase key of a species' cycle-restart anchor (ADR-006 E3/E4).

        The anchor is the phase whose ``sequence_order`` equals the sequence's
        ``cycle_restart_entry_order`` (Weg B) / the LifecycleConfig's
        ``cycle_restart_phase_order`` (legacy). Returns ``None`` when the species
        defines no restart anchor.
        """
        phases, _cycle, meta = self._resolve_phases_for_species(species_key)
        restart_order = meta.get("cycle_restart_entry_order")
        if restart_order is None:
            return None
        for phase in phases:
            if phase.get("sequence_order") == restart_order and phase.get("key"):
                return phase["key"]
        return None

    def transition_phase(
        self,
        plant_key: PlantID,
        target_phase_key: PhaseKey,
        reason: str = "manual",
        *,
        force: bool = False,
        trigger: TransitionTrigger = TransitionTrigger.MANUAL,
    ) -> PlantInstance:
        """Move a plant into ``target_phase_key`` and fire post-transition callbacks.

        ``trigger`` records whether the change was driven automatically (the Celery
        ``check_auto_transitions`` scan) or manually (a user via the API). It is
        forwarded to every registered callback so trigger-sensitive effects — the
        REQ-003 D10 clonal-pup spawn only reacts to ``AUTO`` — can gate on it. The
        default is ``MANUAL`` so the interactive API path stays unchanged.
        """
        plant = self._transition_engine.execute_transition(plant_key, target_phase_key, reason, force=force)

        # Resolve phase name for callbacks across both key-spaces (#579).
        phase_name = ""
        if plant.current_phase_key:
            phase_name = self._resolver.resolve_name(plant.current_phase_key)

        # Notify registered callbacks (e.g. activate dormant tasks, D10 pup spawn).
        # A failing callback must neither break the transition nor take siblings
        # down with it — but it must NOT fail silently either (observability): each
        # failure is logged. Callbacks that touch side effects are additionally
        # expected to log their own success/failure with domain context.
        for callback in self._on_phase_transition_callbacks:
            try:
                callback(plant_key, phase_name, trigger=trigger)
            except Exception:
                logger.warning(
                    "phase_transition_callback_failed",
                    plant_key=plant_key,
                    phase_name=phase_name,
                    trigger=trigger.value,
                    callback=getattr(callback, "__name__", repr(callback)),
                    exc_info=True,
                )

        return plant

    def get_phase_history(self, plant_key: PlantID) -> list[PhaseHistory]:
        return self._repo.get_phase_history(plant_key)

    def delete_phase_history(self, plant_key: PlantID, history_key: str) -> None:
        plant = self._plant_repo.get_or_raise(plant_key)

        all_history = self._repo.get_phase_history(plant_key)
        history = None
        for h in all_history:
            if h.key == history_key:
                history = h
                break
        if history is None:
            raise NotFoundError("PhaseHistory", history_key)

        is_current = history.exited_at is None

        self._repo.delete_phase_history(history_key)

        # If deleted entry was the current (open) phase, revert to previous phase
        if is_current:
            remaining = [h for h in all_history if h.key != history_key]
            if remaining:
                prev = remaining[-1]
                # Reopen previous phase
                prev.exited_at = None
                prev.actual_duration_days = None
                self._repo.update_phase_history(prev.key or "", prev)
                plant.current_phase_key = prev.phase_key
                plant.current_phase_started_at = prev.entered_at
            else:
                plant.current_phase_key = None
                plant.current_phase_started_at = None
            self._plant_repo.update(plant_key, plant)

    def update_phase_history_dates(
        self,
        plant_key: PlantID,
        history_key: str,
        entered_at: datetime | None = None,
        exited_at: datetime | None = None,
    ) -> PhaseHistory:
        plant = self._plant_repo.get_or_raise(plant_key)

        # Find the history entry
        all_history = self._repo.get_phase_history(plant_key)
        history = None
        for h in all_history:
            if h.key == history_key:
                history = h
                break
        if history is None:
            raise NotFoundError("PhaseHistory", history_key)

        if entered_at is not None:
            history.entered_at = entered_at
        if exited_at is not None:
            history.exited_at = exited_at

        # Validate: entered_at < exited_at
        if history.exited_at is not None and history.entered_at >= history.exited_at:
            raise ValueError("entered_at must be before exited_at")

        # Recalculate actual_duration_days
        if history.exited_at is not None:
            delta = history.exited_at - history.entered_at
            history.actual_duration_days = delta.days
        else:
            history.actual_duration_days = None

        updated = self._repo.update_phase_history(history_key, history)

        # If this is the current (open) phase entry, update plant's current_phase_started_at
        if history.exited_at is None and entered_at is not None:
            plant.current_phase_started_at = entered_at
            self._plant_repo.update(plant_key, plant)

        return updated
