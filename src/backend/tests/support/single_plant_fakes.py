"""In-memory doubles for a single plant on a planting position (REQ-053 GP-UX-071, V-25, #2913).

They store whole domain models and answer like the real reads: ``get_active_by_slot`` like the ``placed_in``
traversal (live plants of one tenant), ``reservations_for`` with the reservations of the slots asked for.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock

from app.common.datetimes import today_utc
from app.common.enums import SiteType, SlotRole
from app.domain.engines.slot_reservation_engine import Reservation
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Location, Site, Slot
from app.domain.services.plant_instance_service import PlantInstanceService

TENANT = "tenant-anna"
OTHER = "tenant-bob"
SITE = "site-1"
BED = "bed-1"


class FakeSiteRepo:
    def __init__(self, slots: dict[str, Slot]) -> None:
        site = Site(key=SITE, tenant_key=TENANT, name="Garten", type=SiteType.OUTDOOR, climate_zone="")
        self.sites = {SITE: site}
        self.locations = {BED: Location(key=BED, name="Beet 1", site_key=SITE, area_m2=2.0)}
        self.slots = slots
        self.occupied: list[str] = []

    def get_site_by_key(self, key: str) -> Site | None:
        return self.sites.get(key)

    def get_location_by_key(self, key: str) -> Location | None:
        return self.locations.get(key)

    def get_slot_by_key(self, key: str) -> Slot | None:
        return self.slots.get(key)

    def set_slot_occupied(self, key: str, occupied: bool) -> None:
        self.occupied.append(key)


class FakePlantRepo:
    def __init__(self, standing: list[PlantInstance] | None = None) -> None:
        self.plants = list(standing or [])
        self.created: list[PlantInstance] = []

    def get_active_by_slot(self, slot_key: str, *, tenant_key: str) -> list[PlantInstance]:
        return [
            plant
            for plant in self.plants
            if plant.removed_on is None and plant.tenant_key == tenant_key and plant.slot_key == slot_key
        ]

    def create(self, plant: PlantInstance) -> PlantInstance:
        stored = plant.model_copy(update={"key": f"p{len(self.created) + 1}"})
        self.created.append(stored)
        self.plants.append(stored)
        return stored


class FakeReservations:
    def __init__(self, reservations: list[Reservation] | None = None) -> None:
        self.reservations = reservations or []
        self.asked: list[tuple[list[str], str]] = []

    def reservations_for(self, slot_keys: list[str], *, tenant_key: str) -> list[Reservation]:
        self.asked.append((slot_keys, tenant_key))
        return [reservation for reservation in self.reservations if reservation.slot_key in slot_keys]


def make_slot(key: str, role: SlotRole = SlotRole.POSITION, capacity: int = 1) -> Slot:
    return Slot(key=key, slot_id=f"B1_{key.upper()}", location_key=BED, slot_role=role, capacity_plants=capacity)


def make_plant(**fields: Any) -> PlantInstance:
    return PlantInstance(
        tenant_key=fields.pop("tenant_key", TENANT),
        instance_id=fields.pop("instance_id", "LACTU-1"),
        species_key="sp-lettuce",
        planted_on=date(2026, 11, 13),
        site_key=SITE,
        location_key=BED,
        **fields,
    )


def make_reservation(slot_key: str, *, status: str = "planned", until: date | None = None) -> Reservation:
    start = today_utc() + timedelta(days=10)
    return Reservation(
        slot_key=slot_key,
        run_key="run-7",
        entry_key="e1",
        planned_species_key="sp-carrot",
        sequence=1,
        planned_from=start,
        planned_until=until if until is not None else start + timedelta(days=60),
        run_status=status,
    )


def build_service(
    slots: dict[str, Slot],
    *,
    standing: list[PlantInstance] | None = None,
    reservations: list[Reservation] | None = None,
) -> tuple[PlantInstanceService, FakePlantRepo, FakeSiteRepo, FakeReservations]:
    """The real service over the doubles; rotation and neighbours always pass (they are not the subject)."""
    plants = FakePlantRepo(standing)
    sites = FakeSiteRepo(slots)
    reservation_repo = FakeReservations(reservations)
    rotation = MagicMock()
    rotation.validate_or_raise.return_value = None
    companion = MagicMock()
    companion.check_or_raise.return_value = []
    service = PlantInstanceService(
        plants,  # type: ignore[arg-type]
        sites,  # type: ignore[arg-type]
        rotation,
        companion,
        reservation_repo=reservation_repo,  # type: ignore[arg-type]
    )
    return service, plants, sites, reservation_repo
