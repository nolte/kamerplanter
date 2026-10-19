from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.common.types import IrrigationZoneKey, LocationKey, SiteKey
from app.domain.models.irrigation_zone import IrrigationZone, ZoneCoverageChange, ZoneWateringFacts


class IIrrigationZoneRepository(ABC):
    """Persistence of the irrigation zones of a site (REQ-053 §14, §20.11).

    A zone carries ``tenant_key`` (E-01): every method takes the tenant keyword-only without a default and
    filters the document on it inside the query, so a foreign zone answers exactly like an absent one
    (``None`` / ``NotFoundError``). The writes that touch more than the zone document — the coverage set,
    the delete — are one stream transaction each, so ``zone_covers`` and ``Location.irrigation_zone_key``
    cannot drift apart.
    """

    @abstractmethod
    def list_zones_by_site(
        self, site_key: SiteKey, *, tenant_key: str, offset: int, limit: int
    ) -> list[IrrigationZone]: ...

    @abstractmethod
    def get_zone_by_key(self, key: IrrigationZoneKey, *, tenant_key: str) -> IrrigationZone | None: ...

    @abstractmethod
    def get_zone_or_raise(self, key: IrrigationZoneKey, *, tenant_key: str) -> IrrigationZone: ...

    @abstractmethod
    def covered_location_keys(
        self, zone_keys: list[IrrigationZoneKey], *, tenant_key: str
    ) -> dict[IrrigationZoneKey, list[LocationKey]]:
        """The beds each zone covers (``zone_covers``), sorted by key; a zone without beds maps to ``[]``."""

    @abstractmethod
    def create_zone(self, zone: IrrigationZone, *, tenant_key: str) -> IrrigationZone:
        """Insert the zone with its ``has_irrigation_zone`` edge and — with a water source — ``zone_supplied_by``."""

    @abstractmethod
    def update_zone(self, key: IrrigationZoneKey, fields: dict[str, Any], *, tenant_key: str) -> IrrigationZone:
        """Write *only* ``fields`` (``None`` removes a value); a changed water source moves its edge with it."""

    @abstractmethod
    def delete_zone(self, key: IrrigationZoneKey, *, tenant_key: str, user_key: str) -> list[LocationKey]:
        """Delete the zone in one transaction and return the beds it released.

        The transaction clears ``irrigation_zone_key`` on every bed of the zone, removes every edge on the
        zone and writes the ``garden_plan_audit`` row (SR-011).
        """

    @abstractmethod
    def replace_zone_locations(
        self, key: IrrigationZoneKey, location_keys: list[LocationKey], *, tenant_key: str
    ) -> ZoneCoverageChange:
        """Make ``location_keys`` the zone's beds in one transaction: edges and ``irrigation_zone_key`` together.

        The caller has resolved every key to a location of the zone's site. A bed that another zone covered
        is taken from it (a bed is in at most one zone).
        """

    @abstractmethod
    def watering_facts(self, location_keys: list[LocationKey], *, tenant_key: str, now: datetime) -> ZoneWateringFacts:
        """Last watering, oldest open ``watering`` task and 30-day litres of ``location_keys`` (GP-API-052).

        The keys are the beds of a zone the caller resolved under the tenant; the read filters on the tenant too.
        """
