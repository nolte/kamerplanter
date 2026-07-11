"""REQ-041 — ArangoDB repository for ``:ClimateNormal`` records (NASA POWER)."""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.climate_normal_repository import IClimateNormalRepository
from app.domain.models.weather import ClimateNormal


class ArangoClimateNormalRepository(BaseArangoRepository[ClimateNormal], IClimateNormalRepository):
    """REQ-041 §2.2 — ``climate_normals`` repository (tenant-scoped).

    Upserts are idempotent on ``(site_key, source)`` within a tenant so the
    monthly ``fetch_climate_normals`` beat never accumulates duplicate records for
    the same site/source; the ``has_climate_normal`` edge is created once on first
    insert only.
    """

    _model_cls = ClimateNormal
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.CLIMATE_NORMALS)

    def upsert(self, normal: ClimateNormal) -> ClimateNormal:
        existing = self.find_one(normal.site_key, normal.tenant_key, normal.source)
        if existing is not None and existing.key:
            return super().update(existing.key, normal)

        created = super().create(normal)
        if normal.site_key and created.key:
            from_id = f"{col.SITES}/{normal.site_key}"
            to_id = f"{col.CLIMATE_NORMALS}/{created.key}"
            self.create_edge(col.HAS_CLIMATE_NORMAL, from_id, to_id)
        return created

    def find_one(self, site_key: str, tenant_key: str, source: str) -> ClimateNormal | None:
        query = """
        FOR c IN @@collection
          FILTER c.site_key == @site_key
             AND c.tenant_key == @tenant_key
             AND c.source == @source
          LIMIT 1
          RETURN c
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.CLIMATE_NORMALS,
                "site_key": site_key,
                "tenant_key": tenant_key,
                "source": source,
            },
        )
        docs = [ClimateNormal(**self._from_doc(doc)) for doc in cursor]
        return docs[0] if docs else None

    def get_by_site(self, site_key: str, tenant_key: str) -> list[ClimateNormal]:
        query = """
        FOR c IN @@collection
          FILTER c.site_key == @site_key AND c.tenant_key == @tenant_key
          SORT c.source ASC
          RETURN c
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.CLIMATE_NORMALS,
                "site_key": site_key,
                "tenant_key": tenant_key,
            },
        )
        return [ClimateNormal(**self._from_doc(doc)) for doc in cursor]
