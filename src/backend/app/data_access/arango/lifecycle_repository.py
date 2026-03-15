from arango.database import StandardDatabase

from app.common.types import PhaseKey, PlantID, ProfileKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase import (
    NutrientProfile,
    PhaseHistory,
    PhaseTransitionRule,
    RequirementProfile,
)


class ArangoLifecycleRepository(IPhaseRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.LIFECYCLE_CONFIGS)

    # ── Lifecycle CRUD ────────────────────────────────────────────────

    def get_lifecycle_by_key(self, key: str) -> LifecycleConfig | None:
        doc = super().get_by_key(key)
        return LifecycleConfig(**doc) if doc else None

    def get_lifecycle_by_species(self, species_key: str) -> LifecycleConfig | None:
        results = self.get_edges(col.HAS_LIFECYCLE, f"{col.SPECIES}/{species_key}", direction="outbound")
        if not results:
            return None
        return LifecycleConfig(**self._from_doc(results[0]["vertex"]))

    def create_lifecycle(self, config: LifecycleConfig) -> LifecycleConfig:
        doc = super().create(config)
        lifecycle = LifecycleConfig(**doc)
        if config.species_key:
            species_id = f"{col.SPECIES}/{config.species_key}"
            lifecycle_id = f"{col.LIFECYCLE_CONFIGS}/{doc['_key']}"
            self.create_edge(col.HAS_LIFECYCLE, species_id, lifecycle_id)
        return lifecycle

    def update_lifecycle(self, key: str, config: LifecycleConfig) -> LifecycleConfig:
        doc = super().update(key, config)
        return LifecycleConfig(**doc)

    # ── Growth Phase CRUD ─────────────────────────────────────────────

    def get_phases_by_lifecycle(self, lifecycle_key: str) -> list[GrowthPhase]:
        lifecycle_id = f"{col.LIFECYCLE_CONFIGS}/{lifecycle_key}"
        results = self.get_edges(col.CONSISTS_OF, lifecycle_id, direction="outbound")
        phases = [GrowthPhase(**self._from_doc(r["vertex"])) for r in results if r["vertex"] is not None]
        return sorted(phases, key=lambda p: p.sequence_order)

    def get_phase_by_key(self, key: PhaseKey) -> GrowthPhase | None:
        repo = BaseArangoRepository(self._db, col.GROWTH_PHASES)
        doc = repo.get_by_key(key)
        return GrowthPhase(**doc) if doc else None

    def create_phase(self, phase: GrowthPhase) -> GrowthPhase:
        repo = BaseArangoRepository(self._db, col.GROWTH_PHASES)
        doc = repo.create(phase)
        created_phase = GrowthPhase(**doc)
        if phase.lifecycle_key:
            lifecycle_id = f"{col.LIFECYCLE_CONFIGS}/{phase.lifecycle_key}"
            phase_id = f"{col.GROWTH_PHASES}/{doc['_key']}"
            self.create_edge(col.CONSISTS_OF, lifecycle_id, phase_id)
        return created_phase

    def update_phase(self, key: PhaseKey, phase: GrowthPhase) -> GrowthPhase:
        repo = BaseArangoRepository(self._db, col.GROWTH_PHASES)
        doc = repo.update(key, phase)
        return GrowthPhase(**doc)

    def delete_phase(self, key: PhaseKey) -> bool:
        phase_id = f"{col.GROWTH_PHASES}/{key}"
        self._db.aql.execute(
            f"FOR e IN {col.CONSISTS_OF} FILTER e._to == @to REMOVE e IN {col.CONSISTS_OF}",
            bind_vars={"to": phase_id},
        )
        self.delete_edges(col.NEXT_PHASE, from_id=phase_id)
        self.delete_edges(col.REQUIRES_PROFILE, from_id=phase_id)
        self.delete_edges(col.USES_NUTRIENTS, from_id=phase_id)
        self.delete_edges(col.GOVERNED_BY, from_id=phase_id)
        return BaseArangoRepository(self._db, col.GROWTH_PHASES).delete(key)

    # ── Requirement Profile ───────────────────────────────────────────

    def get_requirement_profile(self, phase_key: PhaseKey) -> RequirementProfile | None:
        phase_id = f"{col.GROWTH_PHASES}/{phase_key}"
        results = self.get_edges(col.REQUIRES_PROFILE, phase_id, direction="outbound")
        if not results:
            return None
        return RequirementProfile(**self._from_doc(results[0]["vertex"]))

    def create_requirement_profile(self, profile: RequirementProfile) -> RequirementProfile:
        repo = BaseArangoRepository(self._db, col.REQUIREMENT_PROFILES)
        doc = repo.create(profile)
        if profile.phase_key:
            phase_id = f"{col.GROWTH_PHASES}/{profile.phase_key}"
            profile_id = f"{col.REQUIREMENT_PROFILES}/{doc['_key']}"
            self.create_edge(col.REQUIRES_PROFILE, phase_id, profile_id)
        return RequirementProfile(**doc)

    def update_requirement_profile(self, key: ProfileKey, profile: RequirementProfile) -> RequirementProfile:
        repo = BaseArangoRepository(self._db, col.REQUIREMENT_PROFILES)
        doc = repo.update(key, profile)
        return RequirementProfile(**doc)

    # ── Nutrient Profile ──────────────────────────────────────────────

    def get_nutrient_profile(self, phase_key: PhaseKey) -> NutrientProfile | None:
        phase_id = f"{col.GROWTH_PHASES}/{phase_key}"
        results = self.get_edges(col.USES_NUTRIENTS, phase_id, direction="outbound")
        if not results:
            return None
        return NutrientProfile(**self._from_doc(results[0]["vertex"]))

    def create_nutrient_profile(self, profile: NutrientProfile) -> NutrientProfile:
        repo = BaseArangoRepository(self._db, col.NUTRIENT_PROFILES)
        doc = repo.create(profile)
        if profile.phase_key:
            phase_id = f"{col.GROWTH_PHASES}/{profile.phase_key}"
            profile_id = f"{col.NUTRIENT_PROFILES}/{doc['_key']}"
            self.create_edge(col.USES_NUTRIENTS, phase_id, profile_id)
        return NutrientProfile(**doc)

    def update_nutrient_profile(self, key: ProfileKey, profile: NutrientProfile) -> NutrientProfile:
        repo = BaseArangoRepository(self._db, col.NUTRIENT_PROFILES)
        doc = repo.update(key, profile)
        return NutrientProfile(**doc)

    # ── Transition Rules ──────────────────────────────────────────────

    def get_transition_rules(self, from_phase_key: PhaseKey) -> list[PhaseTransitionRule]:
        phase_id = f"{col.GROWTH_PHASES}/{from_phase_key}"
        results = self.get_edges(col.GOVERNED_BY, phase_id, direction="outbound")
        return [PhaseTransitionRule(**self._from_doc(r["vertex"])) for r in results]

    def create_transition_rule(self, rule: PhaseTransitionRule) -> PhaseTransitionRule:
        repo = BaseArangoRepository(self._db, col.PHASE_TRANSITION_RULES)
        doc = repo.create(rule)
        created_rule = PhaseTransitionRule(**doc)

        if rule.from_phase_key:
            from_id = f"{col.GROWTH_PHASES}/{rule.from_phase_key}"
            rule_id = f"{col.PHASE_TRANSITION_RULES}/{doc['_key']}"
            self.create_edge(col.GOVERNED_BY, from_id, rule_id)

        if rule.from_phase_key and rule.to_phase_key:
            from_phase_id = f"{col.GROWTH_PHASES}/{rule.from_phase_key}"
            to_phase_id = f"{col.GROWTH_PHASES}/{rule.to_phase_key}"
            self.create_edge(
                col.NEXT_PHASE,
                from_phase_id,
                to_phase_id,
                data={
                    "transition_rule_key": doc["_key"],
                },
            )

        return created_rule

    # ── Phase History ─────────────────────────────────────────────────

    def get_phase_history(self, plant_key: PlantID) -> list[PhaseHistory]:
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        results = self.get_edges(col.PHASE_HISTORY_EDGE, plant_id, direction="outbound")
        histories = [PhaseHistory(**self._from_doc(r["vertex"])) for r in results]
        return sorted(histories, key=lambda h: h.entered_at)

    def create_phase_history(self, history: PhaseHistory) -> PhaseHistory:
        repo = BaseArangoRepository(self._db, col.PHASE_HISTORIES)
        doc = repo.create(history)
        if history.plant_instance_key:
            plant_id = f"{col.PLANT_INSTANCES}/{history.plant_instance_key}"
            history_id = f"{col.PHASE_HISTORIES}/{doc['_key']}"
            self.create_edge(col.PHASE_HISTORY_EDGE, plant_id, history_id)
        return PhaseHistory(**doc)

    def update_phase_history(self, key: str, history: PhaseHistory) -> PhaseHistory:
        repo = BaseArangoRepository(self._db, col.PHASE_HISTORIES)
        doc = repo.update(key, history)
        return PhaseHistory(**doc)

    def delete_phase_history(self, key: str) -> bool:
        history_id = f"{col.PHASE_HISTORIES}/{key}"
        self.delete_edges(col.PHASE_HISTORY_EDGE, to_id=history_id)
        repo = BaseArangoRepository(self._db, col.PHASE_HISTORIES)
        return repo.delete(key)
