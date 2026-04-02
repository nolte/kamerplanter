import contextlib
from datetime import UTC, datetime

from app.common.exceptions import NotFoundError
from app.common.types import PhaseKey, PlantID
from app.domain.engines.phase_transition_engine import PhaseTransitionEngine
from app.domain.engines.resource_profile_generator import ResourceProfileGenerator
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase import NutrientProfile, PhaseHistory, PhaseTransitionRule, RequirementProfile
from app.domain.models.plant_instance import PlantInstance


class PhaseService:
    def __init__(self, phase_repo: IPhaseRepository, plant_repo: IPlantInstanceRepository) -> None:
        self._repo = phase_repo
        self._plant_repo = plant_repo
        self._transition_engine = PhaseTransitionEngine(phase_repo, plant_repo)
        self._profile_generator = ResourceProfileGenerator()
        self._on_phase_transition_callbacks: list = []

    def register_on_transition(self, callback) -> None:
        """Register a callback(plant_key: str, phase_name: str) to invoke after phase transitions."""
        self._on_phase_transition_callbacks.append(callback)

    # --- Lifecycle ---

    def get_lifecycle(self, key: str) -> LifecycleConfig:
        lc = self._repo.get_lifecycle_by_key(key)
        if lc is None:
            raise NotFoundError("LifecycleConfig", key)
        return lc

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
        phase = self._repo.get_phase_by_key(key)
        if phase is None:
            raise NotFoundError("GrowthPhase", key)
        return phase

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
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None:
            raise NotFoundError("PlantInstance", plant_key)

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

        phase_name = ""
        lifecycle_key = None
        if phase_key:
            phase = self._repo.get_phase_by_key(phase_key)
            if phase:
                phase_name = phase.name
                lifecycle_key = phase.lifecycle_key

        # Resolve lifecycle metadata
        cycle_type: str | None = None
        has_harvest_phase = False
        if lifecycle_key:
            lifecycle = self._repo.get_lifecycle_by_key(lifecycle_key)
            if lifecycle:
                cycle_type = lifecycle.cycle_type.value
            phases = self._repo.get_phases_by_lifecycle(lifecycle_key)
            has_harvest_phase = any(p.allows_harvest for p in phases)

        return {
            "phase": phase_name,
            "phase_key": phase_key,
            "days_in_phase": days_in_phase,
            "next_phase": next_phase,
            "cycle_type": cycle_type,
            "cycle_number": cycle_number,
            "has_harvest_phase": has_harvest_phase,
        }

    def transition_phase(
        self,
        plant_key: PlantID,
        target_phase_key: PhaseKey,
        reason: str = "manual",
        *,
        force: bool = False,
    ) -> PlantInstance:
        plant = self._transition_engine.execute_transition(plant_key, target_phase_key, reason, force=force)

        # Resolve phase name for callbacks
        phase_name = ""
        if plant.current_phase_key:
            phase = self._repo.get_phase_by_key(plant.current_phase_key)
            if phase:
                phase_name = phase.name

        # Notify registered callbacks (e.g. activate dormant tasks)
        for callback in self._on_phase_transition_callbacks:
            with contextlib.suppress(Exception):
                callback(plant_key, phase_name)

        return plant

    def get_phase_history(self, plant_key: PlantID) -> list[PhaseHistory]:
        return self._repo.get_phase_history(plant_key)

    def delete_phase_history(self, plant_key: PlantID, history_key: str) -> None:
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None:
            raise NotFoundError("PlantInstance", plant_key)

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
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None:
            raise NotFoundError("PlantInstance", plant_key)

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
