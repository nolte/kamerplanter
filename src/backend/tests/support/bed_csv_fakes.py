"""Doubles the CSV bed list import needs beside :mod:`tests.support.garden_plan_fakes` (REQ-053 WP 8.26, #2669).

The location-type catalogue holds the same three types :class:`FakePlanRepo.bed_types` knows (``bed`` and
``raised_bed`` are beds, ``greenhouse`` is not), so the import's type mapping and the batch's bed flags agree.
"""

from __future__ import annotations

from app.domain.models.irrigation_zone import IrrigationZone
from app.domain.models.location_type import LocationType
from tests.support.garden_plan_fakes import SITE, TENANT

LOCATION_TYPES: tuple[LocationType, ...] = (
    LocationType(_key="bed", name="Beet", name_en="Bed", is_bed=True, sort_order=80),
    LocationType(_key="raised_bed", name="Hochbeet", name_en="Raised Bed", is_bed=True, sort_order=82),
    LocationType(_key="greenhouse", name="Gewächshaus", name_en="Greenhouse", is_bed=False, sort_order=20),
)


class FakeLocationTypes:
    def __init__(self, types: tuple[LocationType, ...] = LOCATION_TYPES) -> None:
        self.types = list(types)

    def get_all(self) -> list[LocationType]:
        return list(self.types)


class FakeZones:
    """``list_zones_by_site`` over a list of zones; a zone of another site or tenant is never listed."""

    def __init__(self, *zones: IrrigationZone) -> None:
        self.zones = list(zones)
        self.reads: list[tuple[str, str]] = []

    def list_zones_by_site(self, site_key, *, tenant_key, offset, limit):
        self.reads.append((site_key, tenant_key))
        found = [z for z in self.zones if z.site_key == site_key and z.tenant_key == tenant_key]
        return found[offset : offset + limit]


def zone(key: str, name: str, *, site: str = SITE, tenant: str = TENANT) -> IrrigationZone:
    return IrrigationZone(_key=key, tenant_key=tenant, site_key=site, name=name)
