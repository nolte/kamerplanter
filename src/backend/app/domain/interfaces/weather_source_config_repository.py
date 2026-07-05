"""REQ-046 — ``:WeatherSourceConfig`` repository interface."""

from abc import ABC, abstractmethod

from app.domain.models.weather import WeatherSourceConfig


class IWeatherSourceConfigRepository(ABC):
    @abstractmethod
    def get_by_site(self, site_key: str, tenant_key: str) -> WeatherSourceConfig | None: ...

    @abstractmethod
    def upsert(self, config: WeatherSourceConfig) -> WeatherSourceConfig:
        """Idempotently persist the per-site config (1:1 per site). ``config``
        MUST carry a ``tenant_key`` (REQ-024 tenant isolation)."""

    @abstractmethod
    def delete_by_site(self, site_key: str, tenant_key: str) -> bool: ...
