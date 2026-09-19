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


class _PhaseHistoryRepository(BaseArangoRepository[PhaseHistory]):
    """The ``phase_histories`` collection, with full-replace null semantics (#1516).

    A dedicated class rather than a bare ``BaseArangoRepository`` instance because
    :attr:`BaseArangoRepository._update_is_full_replace` is a ``ClassVar`` — the
    null semantics belong to the collection, not to one call site.

    **What it repairs.** In the inherited merge mode a ``None`` never reached the
    store, so:

    * ``PhaseService.delete_phase_history`` reopens the previous phase by nulling
      ``exited_at`` and ``actual_duration_days`` — the reopened phase stayed
      closed, while its sibling clears on the ``PlantInstance``
      (``current_phase_key`` / ``current_phase_started_at``) *did* land because
      ``ArangoPlantInstanceRepository`` is already full-replace. That is why the
      function looked half-correct.
    * ``PhaseService.update_phase_history_dates`` and
      ``PlantingRunService.batch_update_phase_dates`` null
      ``actual_duration_days`` when the exit date is removed — the duration
      computed from the deleted exit date stayed.

    **Every writer starts from the stored entry**, so none can lose a field it
    never mentioned (measured 2026-09-18 over all five ``update_phase_history``
    call sites): the three above load through ``get_phase_history`` and mutate
    attributes, and the two in ``PhaseTransitionEngine`` (``transition`` and
    ``terminate``) derive their model with ``model_copy(update=...)`` off the
    stored one — which is what #1516 changed them to. They used to re-list ten
    fields into a fresh :class:`PhaseHistory`, and that list had already drifted:
    ``performance_score`` was missing from it, so under full-replace closing a
    phase would have erased it — measured per field, against the engine's own call,
    in ``tests/unit/domain/engines/test_phase_history_close_carries_the_whole_entry.py``.

    Shaped like every other repository in this package (#1525 SCR-013): bound model on
    the class, collection name in ``__init__``, so a caller cannot construct it
    against the wrong collection.
    """

    _model_cls = PhaseHistory
    _update_is_full_replace = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.PHASE_HISTORIES)


class ArangoLifecycleRepository(BaseArangoRepository[LifecycleConfig], IPhaseRepository):
    _model_cls = LifecycleConfig

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.LIFECYCLE_CONFIGS)
        self._phases = BaseArangoRepository[GrowthPhase](db, col.GROWTH_PHASES, GrowthPhase)
        self._requirement_profiles = BaseArangoRepository[RequirementProfile](
            db, col.REQUIREMENT_PROFILES, RequirementProfile
        )
        self._nutrient_profiles = BaseArangoRepository[NutrientProfile](db, col.NUTRIENT_PROFILES, NutrientProfile)
        self._transition_rules = BaseArangoRepository[PhaseTransitionRule](
            db, col.PHASE_TRANSITION_RULES, PhaseTransitionRule
        )
        self._phase_histories = _PhaseHistoryRepository(db)

    # ── Lifecycle CRUD ────────────────────────────────────────────────

    def get_lifecycle_by_key(self, key: str) -> LifecycleConfig | None:
        return super().get_by_key(key)

    def get_lifecycle_or_raise(self, key: str) -> LifecycleConfig:
        return super().get_or_raise(key)

    def get_lifecycle_by_species(self, species_key: str) -> LifecycleConfig | None:
        results = self.get_edges(col.HAS_LIFECYCLE, f"{col.SPECIES}/{species_key}", direction="outbound")
        if not results:
            return None
        return LifecycleConfig(**self._from_doc(results[0]["vertex"]))

    def create_lifecycle(self, config: LifecycleConfig) -> LifecycleConfig:
        created = super().create(config)
        if config.species_key:
            species_id = f"{col.SPECIES}/{config.species_key}"
            lifecycle_id = f"{col.LIFECYCLE_CONFIGS}/{created.key}"
            self.create_edge(col.HAS_LIFECYCLE, species_id, lifecycle_id)
        return created

    def update_lifecycle(self, key: str, config: LifecycleConfig) -> LifecycleConfig:
        return super().update(key, config)

    # ── Growth Phase CRUD ─────────────────────────────────────────────

    def get_phases_by_lifecycle(self, lifecycle_key: str) -> list[GrowthPhase]:
        lifecycle_id = f"{col.LIFECYCLE_CONFIGS}/{lifecycle_key}"
        results = self.get_edges(col.CONSISTS_OF, lifecycle_id, direction="outbound")
        phases = [GrowthPhase(**self._from_doc(r["vertex"])) for r in results if r["vertex"] is not None]
        return sorted(phases, key=lambda p: p.sequence_order)

    def get_phase_by_key(self, key: PhaseKey) -> GrowthPhase | None:
        return self._phases.get_by_key(key)

    def get_phase_or_raise(self, key: PhaseKey) -> GrowthPhase:
        return self._phases.get_or_raise(key)

    def create_phase(self, phase: GrowthPhase) -> GrowthPhase:
        created_phase = self._phases.create(phase)
        if phase.lifecycle_key:
            lifecycle_id = f"{col.LIFECYCLE_CONFIGS}/{phase.lifecycle_key}"
            phase_id = f"{col.GROWTH_PHASES}/{created_phase.key}"
            self.create_edge(col.CONSISTS_OF, lifecycle_id, phase_id)
        return created_phase

    def update_phase(self, key: PhaseKey, phase: GrowthPhase) -> GrowthPhase:
        return self._phases.update(key, phase)

    def delete_phase(self, key: PhaseKey) -> bool:
        phase_id = f"{col.GROWTH_PHASES}/{key}"
        self.delete_edges(col.CONSISTS_OF, phase_id, direction="inbound")
        # `next_phase` is a chain (`create_transition_rule` writes
        # from_phase → to_phase), so a phase in the middle carries one edge on each
        # end. Detaching only the outbound half left the predecessor's edge pointing
        # at a deleted document — the #1535 defect, found here by the R5 rule of
        # `tests/unit/guards/test_arango_call_surface_scoping.py` (#1573 review
        # SCR-001).
        self.delete_edges(col.NEXT_PHASE, vertex_id=phase_id, direction="any")
        self.delete_edges(col.REQUIRES_PROFILE, from_id=phase_id)
        self.delete_edges(col.USES_NUTRIENTS, from_id=phase_id)
        self.delete_edges(col.GOVERNED_BY, from_id=phase_id)
        return self._phases.delete(key)

    # ── Requirement Profile ───────────────────────────────────────────

    def get_requirement_profile(self, phase_key: PhaseKey) -> RequirementProfile | None:
        phase_id = f"{col.GROWTH_PHASES}/{phase_key}"
        results = self.get_edges(col.REQUIRES_PROFILE, phase_id, direction="outbound")
        if not results:
            return None
        return RequirementProfile(**self._from_doc(results[0]["vertex"]))

    def create_requirement_profile(self, profile: RequirementProfile) -> RequirementProfile:
        created = self._requirement_profiles.create(profile)
        if profile.phase_key:
            phase_id = f"{col.GROWTH_PHASES}/{profile.phase_key}"
            profile_id = f"{col.REQUIREMENT_PROFILES}/{created.key}"
            self.create_edge(col.REQUIRES_PROFILE, phase_id, profile_id)
        return created

    def update_requirement_profile(self, key: ProfileKey, profile: RequirementProfile) -> RequirementProfile:
        return self._requirement_profiles.update(key, profile)

    # ── Nutrient Profile ──────────────────────────────────────────────

    def get_nutrient_profile(self, phase_key: PhaseKey) -> NutrientProfile | None:
        phase_id = f"{col.GROWTH_PHASES}/{phase_key}"
        results = self.get_edges(col.USES_NUTRIENTS, phase_id, direction="outbound")
        if not results:
            return None
        return NutrientProfile(**self._from_doc(results[0]["vertex"]))

    def create_nutrient_profile(self, profile: NutrientProfile) -> NutrientProfile:
        created = self._nutrient_profiles.create(profile)
        if profile.phase_key:
            phase_id = f"{col.GROWTH_PHASES}/{profile.phase_key}"
            profile_id = f"{col.NUTRIENT_PROFILES}/{created.key}"
            self.create_edge(col.USES_NUTRIENTS, phase_id, profile_id)
        return created

    def update_nutrient_profile(self, key: ProfileKey, profile: NutrientProfile) -> NutrientProfile:
        return self._nutrient_profiles.update(key, profile)

    # ── Transition Rules ──────────────────────────────────────────────

    def get_transition_rules(self, from_phase_key: PhaseKey) -> list[PhaseTransitionRule]:
        phase_id = f"{col.GROWTH_PHASES}/{from_phase_key}"
        results = self.get_edges(col.GOVERNED_BY, phase_id, direction="outbound")
        return [PhaseTransitionRule(**self._from_doc(r["vertex"])) for r in results]

    def create_transition_rule(self, rule: PhaseTransitionRule) -> PhaseTransitionRule:
        created_rule = self._transition_rules.create(rule)

        if rule.from_phase_key:
            from_id = f"{col.GROWTH_PHASES}/{rule.from_phase_key}"
            rule_id = f"{col.PHASE_TRANSITION_RULES}/{created_rule.key}"
            self.create_edge(col.GOVERNED_BY, from_id, rule_id)

        if rule.from_phase_key and rule.to_phase_key:
            from_phase_id = f"{col.GROWTH_PHASES}/{rule.from_phase_key}"
            to_phase_id = f"{col.GROWTH_PHASES}/{rule.to_phase_key}"
            self.create_edge(
                col.NEXT_PHASE,
                from_phase_id,
                to_phase_id,
                data={
                    "transition_rule_key": created_rule.key,
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
        created = self._phase_histories.create(history)
        if history.plant_instance_key:
            plant_id = f"{col.PLANT_INSTANCES}/{history.plant_instance_key}"
            history_id = f"{col.PHASE_HISTORIES}/{created.key}"
            self.create_edge(col.PHASE_HISTORY_EDGE, plant_id, history_id)
        return created

    def update_phase_history(self, key: str, history: PhaseHistory) -> PhaseHistory:
        return self._phase_histories.update(key, history)

    def delete_phase_history(self, key: str) -> bool:
        history_id = f"{col.PHASE_HISTORIES}/{key}"
        # The edge points *at* the history entry (plant → history), so the vertex to
        # detach is the inbound end. Spelled `to_id=` alone since #346, which is the
        # one combination `delete_edges` rejects outright ("requires from_id or
        # vertex_id") — so this method raised `ValueError` before it ever deleted
        # anything, and with it every `DELETE .../phase-history/{key}`. Measured
        # 2026-09-18 against a real ArangoDB: it is the write path #1516's
        # `phase_service.delete_phase_history` entry names, and it could not run.
        self.delete_edges(col.PHASE_HISTORY_EDGE, vertex_id=history_id, direction="inbound")
        return self._phase_histories.delete(key)
