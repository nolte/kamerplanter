"""REQ-041 — ``:ClimateNormal`` repository interface."""

from abc import ABC, abstractmethod

from app.domain.models.weather import ClimateNormal


class IClimateNormalRepository(ABC):
    @abstractmethod
    def upsert(self, normal: ClimateNormal) -> ClimateNormal:
        """Idempotently persist one climate-normal record on ``(site_key, source)``
        within a tenant — updates the existing record or inserts a new one and its
        ``has_climate_normal`` edge."""

    @abstractmethod
    def get_by_site(self, site_key: str, tenant_key: str) -> list[ClimateNormal]:
        """All climate normals of a site (one per source), tenant-scoped."""

    @abstractmethod
    def find_one(self, site_key: str, tenant_key: str, source: str) -> ClimateNormal | None:
        """The single ``(site_key, source)`` record within a tenant, or ``None``."""
