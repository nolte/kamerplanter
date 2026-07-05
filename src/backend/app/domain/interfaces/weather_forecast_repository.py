"""REQ-046 — ``:WeatherForecast`` repository interface."""

from abc import ABC, abstractmethod

from app.domain.models.weather import WeatherForecast


class IWeatherForecastRepository(ABC):
    @abstractmethod
    def upsert_daily(self, forecast: WeatherForecast) -> WeatherForecast:
        """Idempotently persist one daily record on ``(site_key, forecast_date,
        source)`` — updates the existing record or inserts a new one."""

    @abstractmethod
    def find_by_site(self, site_key: str, tenant_key: str) -> list[WeatherForecast]: ...

    @abstractmethod
    def get(self, key: str) -> WeatherForecast | None: ...
