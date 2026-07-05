"""REQ-046 — ArangoDB repository for ``:WeatherSourceConfig`` (tenant-scoped)."""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.weather_source_config_repository import IWeatherSourceConfigRepository
from app.domain.models.weather import WeatherSourceConfig


class ArangoWeatherSourceConfigRepository(BaseArangoRepository[WeatherSourceConfig], IWeatherSourceConfigRepository):
    """REQ-046 §2.1 — ``weather_source_configs`` repository (1:1 per site).

    All reads and writes are strictly tenant-scoped (REQ-024): callers pass the
    site's ``tenant_key``, and :meth:`upsert` requires the config to carry it.
    """

    _model_cls = WeatherSourceConfig
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.WEATHER_SOURCE_CONFIGS)

    def get_by_site(self, site_key: str, tenant_key: str) -> WeatherSourceConfig | None:
        query = """
        FOR c IN @@collection
          FILTER c.site_key == @site_key AND c.tenant_key == @tenant_key
          LIMIT 1
          RETURN c
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.WEATHER_SOURCE_CONFIGS,
                "site_key": site_key,
                "tenant_key": tenant_key,
            },
        )
        docs = [WeatherSourceConfig(**self._from_doc(doc)) for doc in cursor]
        return docs[0] if docs else None

    def upsert(self, config: WeatherSourceConfig) -> WeatherSourceConfig:
        if not config.tenant_key:
            raise ValueError(
                "WeatherSourceConfig.tenant_key must be set before upsert "
                "(REQ-024 tenant isolation — inherit it from the owning site)."
            )
        existing = self.get_by_site(config.site_key, config.tenant_key)
        if existing is not None and existing.key:
            return super().update(existing.key, config)

        created = super().create(config)
        if config.site_key and created.key:
            from_id = f"{col.SITES}/{config.site_key}"
            to_id = f"{col.WEATHER_SOURCE_CONFIGS}/{created.key}"
            self.create_edge(col.HAS_WEATHER_SOURCE_CONFIG, from_id, to_id)
        return created

    def delete_by_site(self, site_key: str, tenant_key: str) -> bool:
        existing = self.get_by_site(site_key, tenant_key)
        if existing is None or not existing.key:
            return False
        config_id = f"{col.WEATHER_SOURCE_CONFIGS}/{existing.key}"
        self.delete_edges(col.HAS_WEATHER_SOURCE_CONFIG, vertex_id=config_id, direction="inbound")
        return super().delete(existing.key)
