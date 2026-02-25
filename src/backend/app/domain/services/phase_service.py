from datetime import UTC

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

        days_in_phase = 0
        if plant.current_phase_started_at:
            from datetime import datetime

            delta = datetime.now(UTC) - plant.current_phase_started_at
            days_in_phase = delta.days

        next_phase = None
        if plant.current_phase_key:
            rules = self._repo.get_transition_rules(plant.current_phase_key)
            if rules:
                target = self._repo.get_phase_by_key(rules[0].to_phase_key)
                if target:
                    next_phase = target.name

        return {
            "phase": plant.current_phase,
            "phase_key": plant.current_phase_key,
            "days_in_phase": days_in_phase,
            "next_phase": next_phase,
        }

    def transition_phase(self, plant_key: PlantID, target_phase_key: PhaseKey, reason: str = "manual") -> PlantInstance:
        return self._transition_engine.execute_transition(plant_key, target_phase_key, reason)

    def get_phase_history(self, plant_key: PlantID) -> list[PhaseHistory]:
        return self._repo.get_phase_history(plant_key)
