from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.types import FertilizerKey, NutrientPlanKey, NutrientPlanPhaseEntryKey
    from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry


class INutrientPlanRepository(ABC):
    # ── Plan CRUD ────────────────────────────────────────────────────

    @abstractmethod
    def get_all(
        self, offset: int = 0, limit: int = 50, filters: dict | None = None,
    ) -> tuple[list[NutrientPlan], int]:
        ...

    @abstractmethod
    def get_by_key(self, key: NutrientPlanKey) -> NutrientPlan | None:
        ...

    @abstractmethod
    def create(self, plan: NutrientPlan) -> NutrientPlan:
        ...

    @abstractmethod
    def update(self, key: NutrientPlanKey, plan: NutrientPlan) -> NutrientPlan:
        ...

    @abstractmethod
    def delete(self, key: NutrientPlanKey) -> bool:
        ...

    # ── Phase entries ────────────────────────────────────────────────

    @abstractmethod
    def create_phase_entry(self, entry: NutrientPlanPhaseEntry) -> NutrientPlanPhaseEntry:
        ...

    @abstractmethod
    def get_phase_entries(self, plan_key: NutrientPlanKey) -> list[NutrientPlanPhaseEntry]:
        ...

    @abstractmethod
    def get_phase_entry_by_key(self, key: NutrientPlanPhaseEntryKey) -> NutrientPlanPhaseEntry | None:
        ...

    @abstractmethod
    def update_phase_entry(
        self, key: NutrientPlanPhaseEntryKey, entry: NutrientPlanPhaseEntry,
    ) -> NutrientPlanPhaseEntry:
        ...

    @abstractmethod
    def delete_phase_entry(self, key: NutrientPlanPhaseEntryKey) -> bool:
        ...

    # ── Plant assignment ─────────────────────────────────────────────

    @abstractmethod
    def assign_to_plant(self, plant_key: str, plan_key: NutrientPlanKey, assigned_by: str = "") -> dict:
        ...

    @abstractmethod
    def get_plant_plan(self, plant_key: str) -> NutrientPlan | None:
        ...

    @abstractmethod
    def remove_plant_plan(self, plant_key: str) -> bool:
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
    ) -> dict:
        ...

    @abstractmethod
    def remove_fertilizer_from_channel(
        self,
        entry_key: NutrientPlanPhaseEntryKey,
        channel_id: str,
        fertilizer_key: FertilizerKey,
    ) -> bool:
        ...

    # ── Clone ────────────────────────────────────────────────────────

    @abstractmethod
    def clone(self, source_key: NutrientPlanKey, new_name: str, author: str = "") -> NutrientPlan:
        ...
