"""REQ-037 — ``:IrrigationDemand`` repository interface."""

from abc import ABC, abstractmethod

from app.domain.models.irrigation_demand import IrrigationDemand


class IIrrigationDemandRepository(ABC):
    @abstractmethod
    def upsert(self, demand: IrrigationDemand) -> IrrigationDemand:
        """Idempotently persist one demand on ``(site_key, run_key, demand_date)``
        within a tenant — updates the existing record or inserts a new one plus its
        ``has_irrigation_demand`` (and, for a run-bound demand, ``demand_for_run``)
        edges."""

    @abstractmethod
    def get_latest_for_run(self, run_key: str, tenant_key: str) -> IrrigationDemand | None:
        """The most recent demand computed for a planting run, or ``None``."""

    @abstractmethod
    def get_latest_for_site(self, site_key: str, tenant_key: str) -> IrrigationDemand | None:
        """The most recent demand computed for a site, or ``None``."""
