"""REQ-046 — ArangoDB repository for ``:WeatherForecast`` records."""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.weather_forecast_repository import IWeatherForecastRepository
from app.domain.models.weather import WeatherForecast


class ArangoWeatherForecastRepository(BaseArangoRepository[WeatherForecast], IWeatherForecastRepository):
    """REQ-046 §2 — ``weather_forecasts`` repository (tenant-scoped)."""

    _model_cls = WeatherForecast
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.WEATHER_FORECASTS)

    def upsert_daily(self, forecast: WeatherForecast) -> WeatherForecast:
        """Idempotent on ``(site_key, forecast_date, source)`` within a tenant.

        On the first insert the ``has_forecast`` edge (site → forecast) is
        persisted; subsequent updates of the same record do not duplicate it.
        """
        existing = self._find_existing(forecast)
        if existing is not None and existing.key:
            return super().update(existing.key, forecast)

        created = super().create(forecast)
        if forecast.site_key and created.key:
            from_id = f"{col.SITES}/{forecast.site_key}"
            to_id = f"{col.WEATHER_FORECASTS}/{created.key}"
            self.create_edge(col.HAS_FORECAST, from_id, to_id)
        return created

    def _find_existing(self, forecast: WeatherForecast) -> WeatherForecast | None:
        query = """
        FOR f IN @@collection
          FILTER f.site_key == @site_key
             AND f.forecast_date == @forecast_date
             AND f.source == @source
             AND f.tenant_key == @tenant_key
          LIMIT 1
          RETURN f
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.WEATHER_FORECASTS,
                "site_key": forecast.site_key,
                "forecast_date": forecast.forecast_date.isoformat(),
                "source": forecast.source,
                "tenant_key": forecast.tenant_key,
            },
        )
        docs = [WeatherForecast(**self._from_doc(doc)) for doc in cursor]
        return docs[0] if docs else None

    def find_by_site(self, site_key: str, tenant_key: str) -> list[WeatherForecast]:
        query = """
        FOR f IN @@collection
          FILTER f.site_key == @site_key AND f.tenant_key == @tenant_key
          SORT f.forecast_date ASC
          RETURN f
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.WEATHER_FORECASTS,
                "site_key": site_key,
                "tenant_key": tenant_key,
            },
        )
        return [WeatherForecast(**self._from_doc(doc)) for doc in cursor]

    def get(self, key: str) -> WeatherForecast | None:
        return self.get_by_key(key)
