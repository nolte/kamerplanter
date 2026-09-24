from abc import ABC, abstractmethod

from app.common.types import FertilizerKey, NutrientPlanKey, NutrientPlanPhaseEntryKey
from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry


class INutrientPlanRepository(ABC):
    # ── Plan CRUD ────────────────────────────────────────────────────

    @abstractmethod
    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
    ) -> tuple[list[NutrientPlan], int]: ...

    @abstractmethod
    def get_by_key(self, key: NutrientPlanKey) -> NutrientPlan | None: ...

    @abstractmethod
    def get_or_raise(self, key: NutrientPlanKey) -> NutrientPlan: ...

    @abstractmethod
    def get_readable_or_raise(self, key: NutrientPlanKey, *, tenant_key: str) -> NutrientPlan:
        """Return a plan readable from ``tenant_key`` — own or global — else 404 (#950)."""
        ...

    @abstractmethod
    def create(self, plan: NutrientPlan) -> NutrientPlan: ...

    @abstractmethod
    def update(self, key: NutrientPlanKey, plan: NutrientPlan) -> NutrientPlan: ...

    @abstractmethod
    def delete(self, key: NutrientPlanKey) -> bool: ...

    # ── Phase entries ────────────────────────────────────────────────

    @abstractmethod
    def create_phase_entry(self, entry: NutrientPlanPhaseEntry) -> NutrientPlanPhaseEntry: ...

    @abstractmethod
    def get_phase_entries(self, plan_key: NutrientPlanKey) -> list[NutrientPlanPhaseEntry]: ...

    @abstractmethod
    def get_phase_entry_by_key(self, key: NutrientPlanPhaseEntryKey) -> NutrientPlanPhaseEntry | None: ...

    @abstractmethod
    def get_phase_entry_or_raise(self, key: NutrientPlanPhaseEntryKey) -> NutrientPlanPhaseEntry: ...

    @abstractmethod
    def update_phase_entry(
        self,
        key: NutrientPlanPhaseEntryKey,
        entry: NutrientPlanPhaseEntry,
    ) -> NutrientPlanPhaseEntry: ...

    @abstractmethod
    def delete_phase_entry(self, key: NutrientPlanPhaseEntryKey) -> bool: ...

    # ── Plant assignment ─────────────────────────────────────────────

    @abstractmethod
    def assign_to_plant(self, plant_key: str, plan_key: NutrientPlanKey, assigned_by: str = "") -> dict: ...

    @abstractmethod
    def get_plant_plan(self, plant_key: str, *, tenant_key: str) -> NutrientPlan | None:
        """Return the plan assigned to a plant of ``tenant_key`` (#927)."""
        ...

    @abstractmethod
    def remove_plant_plan(self, plant_key: str) -> bool: ...

    # ── Onboarding / favourites reads (#1638) ───────────────────────

    @abstractmethod
    def list_template_plan_summaries(self, *, tenant_key: str, species_keys: list[str]) -> list[dict]:
        """Template plans visible to ``tenant_key`` (own ∪ global) linked to any of ``species_keys``.

        Every row is ``{plan_key, name, description, substrate_type,
        species_keys, matched_species, fertilizer_count, fertilizers: [{key,
        product_name, brand}]}``, sorted by the number of matched species
        (descending), then by name. The fertilizer set is the union of the
        ``plan_uses_fertilizer`` edges and the dosages embedded in the phase
        entries' delivery channels.

        A plan matches when its ``species_keys`` relation shares at least one key
        with ``species_keys`` (#1618). A plan with an empty or absent relation
        matches **no** species, and an empty ``species_keys`` argument returns
        nothing.

        Both arguments are keyword-only with no default (#948): an omitted
        predicate must not be spellable. An empty ``tenant_key`` is the anonymous
        / light-mode context and collapses the union to global-only.
        """
        ...

    @abstractmethod
    def list_edge_fertilizer_keys(self, plan_key: NutrientPlanKey) -> list[str]:
        """Distinct fertilizer keys a plan reaches through its ``plan_uses_fertilizer`` edges."""
        ...

    # ── Channel fertilizer edges ────────────────────────────────────

    @abstractmethod
    def add_fertilizer_to_channel(
        self,
        entry_key: NutrientPlanPhaseEntryKey,
        channel_id: str,
        fertilizer_key: FertilizerKey,
        ml_per_liter: float,
        optional: bool = False,
    ) -> dict: ...

    @abstractmethod
    def remove_fertilizer_from_channel(
        self,
        entry_key: NutrientPlanPhaseEntryKey,
        channel_id: str,
        fertilizer_key: FertilizerKey,
    ) -> bool: ...

    # ── Clone ────────────────────────────────────────────────────────

    @abstractmethod
    def clone(
        self, source_key: NutrientPlanKey, new_name: str, author: str = "", tenant_key: str = ""
    ) -> NutrientPlan: ...
