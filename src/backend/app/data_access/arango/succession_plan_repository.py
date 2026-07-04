from arango.database import StandardDatabase

from app.common.types import LocationKey, PlantingRunKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.succession_plan_repository import ISuccessionPlanRepository, SuccessionPlanKey
from app.domain.models.succession_plan import SuccessionPlan


class ArangoSuccessionPlanRepository(BaseArangoRepository[SuccessionPlan], ISuccessionPlanRepository):
    is_tenant_scoped = True
    _model_cls = SuccessionPlan

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.SUCCESSION_PLANS)

    def delete(self, key: SuccessionPlanKey) -> bool:
        plan_id = f"{col.SUCCESSION_PLANS}/{key}"
        self.delete_edges(col.HAS_SUCCESSION_PLAN, from_id=plan_id)
        self.delete_edges(col.SUCCESSION_AT, from_id=plan_id)
        return super().delete(key)

    # ── Edge operations ───────────────────────────────────────────────

    def link_plan_to_run(self, plan_key: SuccessionPlanKey, run_key: PlantingRunKey) -> None:
        from_id = f"{col.SUCCESSION_PLANS}/{plan_key}"
        to_id = f"{col.PLANTING_RUNS}/{run_key}"
        self.create_edge(col.HAS_SUCCESSION_PLAN, from_id, to_id)

    def link_plan_to_location(self, plan_key: SuccessionPlanKey, location_key: LocationKey) -> None:
        from_id = f"{col.SUCCESSION_PLANS}/{plan_key}"
        # N:1 — a plan sows at exactly one location; replace any prior edge.
        self.delete_edges(col.SUCCESSION_AT, from_id=from_id)
        to_id = f"{col.LOCATIONS}/{location_key}"
        self.create_edge(col.SUCCESSION_AT, from_id, to_id)

    def get_run_keys_for_plan(self, plan_key: SuccessionPlanKey) -> list[str]:
        query = f"""
        FOR e IN {col.HAS_SUCCESSION_PLAN}
          FILTER e._from == @plan_id
          RETURN PARSE_IDENTIFIER(e._to).key
        """
        cursor = self._db.aql.execute(query, bind_vars={"plan_id": f"{col.SUCCESSION_PLANS}/{plan_key}"})
        return [key for key in cursor if key]
