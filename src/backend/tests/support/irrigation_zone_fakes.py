"""In-memory double of the irrigation-zone repository (REQ-053 WP 7.1), over a :class:`FakePlanRepo`'s beds.

``FakeZones`` keeps the coverage the way ``ArangoIrrigationZoneRepository`` does — an edge set (zone → bed,
one zone per bed) **and** ``Location.irrigation_zone_key`` on the fake repository's beds — so a test can assert
that both moved together. Shared by the unit tier and the API tier.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.common.exceptions import NotFoundError
from app.domain.interfaces.irrigation_zone_repository import IIrrigationZoneRepository
from app.domain.models.irrigation_zone import IrrigationZone, ZoneCoverageChange, ZoneWateringFacts
from tests.support.garden_plan_fakes import FakePlanRepo


class FakeZones(IIrrigationZoneRepository):
    def __init__(self, repo: FakePlanRepo) -> None:
        self._repo = repo
        self.zones: dict[str, IrrigationZone] = {}
        #: location key → zone key (the ``zone_covers`` edges; unique on the bed like the v0099 index).
        self.covers: dict[str, str] = {}
        self.audit: list[dict[str, Any]] = []
        self.updates: list[tuple[str, dict[str, Any]]] = []
        self._next = 0
        #: What ``watering_facts`` answers, and the bed keys it was last asked about.
        self.facts = ZoneWateringFacts(last_watering=None, next_planned=None, consumption_liters=0.0)
        self.facts_asked: list[list[str]] = []

    def add(self, zone: IrrigationZone) -> IrrigationZone:
        self.zones[zone.key or ""] = zone
        return zone

    def _owned(self, zone: IrrigationZone | None, tenant_key: str) -> IrrigationZone | None:
        return zone if zone is not None and tenant_key and zone.tenant_key == tenant_key else None

    def list_zones_by_site(self, site_key, *, tenant_key, offset, limit):
        found = sorted(
            (z for z in self.zones.values() if z.site_key == site_key and self._owned(z, tenant_key)),
            key=lambda z: (z.name, z.key or ""),
        )
        return found[offset : offset + limit]

    def get_zone_by_key(self, key, *, tenant_key):
        return self._owned(self.zones.get(key), tenant_key)

    def get_zone_or_raise(self, key, *, tenant_key):
        zone = self.get_zone_by_key(key, tenant_key=tenant_key)
        if zone is None:
            raise NotFoundError("IrrigationZone", key)
        return zone

    def covered_location_keys(self, zone_keys, *, tenant_key):
        owned = {key for key in zone_keys if self.get_zone_by_key(key, tenant_key=tenant_key) is not None}
        return {
            key: sorted(loc for loc, zone in self.covers.items() if zone == key) if key in owned else []
            for key in zone_keys
        }

    def create_zone(self, zone, *, tenant_key):
        assert zone.tenant_key == tenant_key
        self._next += 1
        stored = zone.model_copy(update={"key": f"zone_new_{self._next}", "created_at": datetime.now(UTC)})
        self.zones[stored.key or ""] = stored
        return stored

    def update_zone(self, key, fields, *, tenant_key):
        zone = self.get_zone_or_raise(key, tenant_key=tenant_key)
        self.updates.append((key, dict(fields)))
        merged = {**zone.model_dump(by_alias=True), **fields}
        self.zones[key] = IrrigationZone.model_validate(merged)
        return self.zones[key]

    def _set_bed_zone(self, location_key: str, zone_key: str | None) -> None:
        location = self._repo.locations[location_key]
        self._repo.locations[location_key] = location.model_copy(update={"irrigation_zone_key": zone_key})

    def delete_zone(self, key, *, tenant_key, user_key):
        zone = self.get_zone_or_raise(key, tenant_key=tenant_key)
        released = sorted(
            loc
            for loc, location in self._repo.locations.items()
            if location.irrigation_zone_key == key or self.covers.get(loc) == key
        )
        for loc in released:
            self.covers.pop(loc, None)
            self._set_bed_zone(loc, None)
        del self.zones[key]
        self.audit.append({"op": "delete", "entity": "irrigation_zone", "key": key, "user_key": user_key})
        assert zone.site_key
        return released

    def replace_zone_locations(self, key, location_keys, *, tenant_key):
        self.get_zone_or_raise(key, tenant_key=tenant_key)
        wanted = sorted(dict.fromkeys(location_keys))
        current = {loc for loc, zone in self.covers.items() if zone == key}
        added = [loc for loc in wanted if loc not in current]
        removed = sorted(current - set(wanted))
        moved = {loc: self.covers[loc] for loc in added if loc in self.covers}
        for loc in removed:
            self.covers.pop(loc, None)
            self._set_bed_zone(loc, None)
        for loc in wanted:
            self.covers[loc] = key
            self._set_bed_zone(loc, key)
        return ZoneCoverageChange(added=tuple(added), removed=tuple(removed), moved_from=moved)

    def watering_facts(self, location_keys, *, tenant_key, now):
        assert tenant_key
        self.facts_asked.append(list(location_keys))
        return self.facts
