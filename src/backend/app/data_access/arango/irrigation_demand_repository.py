"""REQ-037 — ArangoDB repository for ``:IrrigationDemand`` records."""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.irrigation_demand_repository import IIrrigationDemandRepository
from app.domain.models.irrigation_demand import IrrigationDemand


class ArangoIrrigationDemandRepository(BaseArangoRepository[IrrigationDemand], IIrrigationDemandRepository):
    """REQ-037 §7 — ``irrigation_demands`` repository (tenant-scoped).

    Upserts are idempotent on ``(site_key, run_key, demand_date)`` within a tenant,
    so re-running ``compute_irrigation_demand`` for the same day overwrites the
    record instead of accumulating duplicates. Edges (``has_irrigation_demand`` and,
    for a run-bound demand, ``demand_for_run``) are created once on first insert.
    """

    _model_cls = IrrigationDemand
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.IRRIGATION_DEMANDS)

    def upsert(self, demand: IrrigationDemand) -> IrrigationDemand:
        existing = self._find_existing(demand)
        if existing is not None and existing.key:
            return super().update(existing.key, demand)

        created = super().create(demand)
        if demand.site_key and created.key:
            self.create_edge(
                col.HAS_IRRIGATION_DEMAND,
                f"{col.SITES}/{demand.site_key}",
                f"{col.IRRIGATION_DEMANDS}/{created.key}",
            )
        if demand.run_key and created.key:
            self.create_edge(
                col.DEMAND_FOR_RUN,
                f"{col.PLANTING_RUNS}/{demand.run_key}",
                f"{col.IRRIGATION_DEMANDS}/{created.key}",
            )
        return created

    def _find_existing(self, demand: IrrigationDemand) -> IrrigationDemand | None:
        query = """
        FOR d IN @@collection
          FILTER d.site_key == @site_key
             AND d.tenant_key == @tenant_key
             AND d.run_key == @run_key
             AND d.demand_date == @demand_date
          LIMIT 1
          RETURN d
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.IRRIGATION_DEMANDS,
                "site_key": demand.site_key,
                "tenant_key": demand.tenant_key,
                "run_key": demand.run_key,
                "demand_date": demand.demand_date.isoformat(),
            },
        )
        docs = [IrrigationDemand(**self._from_doc(doc)) for doc in cursor]
        return docs[0] if docs else None

    def get_latest_for_run(self, run_key: str, tenant_key: str) -> IrrigationDemand | None:
        return self._latest("run_key", run_key, tenant_key)

    def get_latest_for_site(self, site_key: str, tenant_key: str) -> IrrigationDemand | None:
        return self._latest("site_key", site_key, tenant_key)

    def _latest(self, field: str, value: str, tenant_key: str) -> IrrigationDemand | None:
        query = f"""
        FOR d IN @@collection
          FILTER d.{field} == @value AND d.tenant_key == @tenant_key
          SORT d.demand_date DESC
          LIMIT 1
          RETURN d
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.IRRIGATION_DEMANDS,
                "value": value,
                "tenant_key": tenant_key,
            },
        )
        docs = [IrrigationDemand(**self._from_doc(doc)) for doc in cursor]
        return docs[0] if docs else None
