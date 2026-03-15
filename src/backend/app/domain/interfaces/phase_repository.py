from abc import ABC, abstractmethod

from app.common.types import PhaseKey, PlantID, ProfileKey
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase import NutrientProfile, PhaseHistory, PhaseTransitionRule, RequirementProfile


class IPhaseRepository(ABC):
    @abstractmethod
    def get_lifecycle_by_key(self, key: str) -> LifecycleConfig | None:
        ...

    @abstractmethod
    def get_lifecycle_by_species(self, species_key: str) -> LifecycleConfig | None:
        ...

    @abstractmethod
    def create_lifecycle(self, config: LifecycleConfig) -> LifecycleConfig:
        ...

    @abstractmethod
    def update_lifecycle(self, key: str, config: LifecycleConfig) -> LifecycleConfig:
        ...

    @abstractmethod
    def get_phases_by_lifecycle(self, lifecycle_key: str) -> list[GrowthPhase]:
        ...

    @abstractmethod
    def get_phase_by_key(self, key: PhaseKey) -> GrowthPhase | None:
        ...

    @abstractmethod
    def create_phase(self, phase: GrowthPhase) -> GrowthPhase:
        ...

    @abstractmethod
    def update_phase(self, key: PhaseKey, phase: GrowthPhase) -> GrowthPhase:
        ...

    @abstractmethod
    def delete_phase(self, key: PhaseKey) -> bool:
        ...

    @abstractmethod
    def get_requirement_profile(self, phase_key: PhaseKey) -> RequirementProfile | None:
        ...

    @abstractmethod
    def create_requirement_profile(self, profile: RequirementProfile) -> RequirementProfile:
        ...

    @abstractmethod
    def update_requirement_profile(self, key: ProfileKey, profile: RequirementProfile) -> RequirementProfile:
        ...

    @abstractmethod
    def get_nutrient_profile(self, phase_key: PhaseKey) -> NutrientProfile | None:
        ...

    @abstractmethod
    def create_nutrient_profile(self, profile: NutrientProfile) -> NutrientProfile:
        ...

    @abstractmethod
    def update_nutrient_profile(self, key: ProfileKey, profile: NutrientProfile) -> NutrientProfile:
        ...

    @abstractmethod
    def get_transition_rules(self, from_phase_key: PhaseKey) -> list[PhaseTransitionRule]:
        ...

    @abstractmethod
    def create_transition_rule(self, rule: PhaseTransitionRule) -> PhaseTransitionRule:
        ...

    @abstractmethod
    def get_phase_history(self, plant_key: PlantID) -> list[PhaseHistory]:
        ...

    @abstractmethod
    def create_phase_history(self, history: PhaseHistory) -> PhaseHistory:
        ...

    @abstractmethod
    def update_phase_history(self, key: str, history: PhaseHistory) -> PhaseHistory:
        ...

    @abstractmethod
    def delete_phase_history(self, key: str) -> bool:
        ...
