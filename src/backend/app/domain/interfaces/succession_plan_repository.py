from abc import ABC, abstractmethod

from app.common.types import LocationKey, PlantingRunKey
from app.domain.models.succession_plan import SuccessionPlan

type SuccessionPlanKey = str


class ISuccessionPlanRepository(ABC):
    @abstractmethod
    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str | None = None,
        *,
        all_tenants: bool = False,
    ) -> tuple[list[SuccessionPlan], int]: ...

    @abstractmethod
    def get_by_key(self, key: SuccessionPlanKey) -> SuccessionPlan | None: ...

    @abstractmethod
    def get_or_raise(self, key: SuccessionPlanKey) -> SuccessionPlan: ...

    @abstractmethod
    def create(self, plan: SuccessionPlan) -> SuccessionPlan: ...

    @abstractmethod
    def update(self, key: SuccessionPlanKey, plan: SuccessionPlan) -> SuccessionPlan: ...

    @abstractmethod
    def delete(self, key: SuccessionPlanKey) -> bool: ...

    # ── Edge operations ───────────────────────────────────────────────

    @abstractmethod
    def link_plan_to_run(self, plan_key: SuccessionPlanKey, run_key: PlantingRunKey) -> None: ...

    @abstractmethod
    def link_plan_to_location(self, plan_key: SuccessionPlanKey, location_key: LocationKey) -> None: ...

    @abstractmethod
    def get_run_keys_for_plan(self, plan_key: SuccessionPlanKey) -> list[str]: ...
