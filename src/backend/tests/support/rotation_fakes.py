"""In-memory doubles for the bed-level crop-rotation check (REQ-053 WP 3.4, #2394).

``FakeRotationHistory`` honours the same contract as ``ArangoRotationHistoryRepository``: every read names the
tenant, a plant or an event of another tenant is not part of the answer, a voided or superseded backfill is gone.
It reads backfills from the :class:`~tests.support.care_event_fakes.FakeCareEventRepo` it is handed, so a test of
the whole path (``backfill`` then ``rotation``) goes through the real care-event service.
"""

from __future__ import annotations

from datetime import date, datetime

from app.domain.interfaces.rotation_history_repository import (
    BackfillRow,
    IRotationHistoryRepository,
    PlantedRow,
)
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.species import Species
from tests.support.care_event_fakes import FakeCareEventRepo


def make_species(key: str, family_key: str | None, *, tenant: str = "", **kwargs) -> Species:
    return Species(
        _key=key, scientific_name=f"Test {key}", genus="Test", family_key=family_key, tenant_key=tenant, **kwargs
    )


def make_family(key: str, *, pause: int | None, **kwargs) -> BotanicalFamily:
    return BotanicalFamily(_key=key, name=f"{key.capitalize()}aceae", rotation_pause_years=pause, **kwargs)


class FakeSpecies:
    def __init__(self, *species: Species) -> None:
        self.by_key = {s.key: s for s in species}
        self.grants: set[tuple[str, str]] = set()

    def get_by_key(self, key):
        return self.by_key.get(key)

    def is_granted_to(self, species_key, tenant_key):
        return (species_key, tenant_key) in self.grants


class FakeFamilies:
    def __init__(self, *families: BotanicalFamily) -> None:
        self.by_key = {f.key: f for f in families}

    def get_by_key(self, key):
        return self.by_key.get(key)


class FakeRotationHistory(IRotationHistoryRepository):
    def __init__(self, care_events: FakeCareEventRepo | None = None) -> None:
        #: (tenant, location_key, row)
        self.plants: list[tuple[str, str, PlantedRow]] = []
        self._events = care_events

    def add_plant(
        self,
        location_key: str,
        species_key: str,
        planted_on: date,
        *,
        removed_on: date | None = None,
        plan_role: str = "main_crop",
        tenant: str = "ten_own",
    ) -> None:
        row = PlantedRow(f"pi_{len(self.plants)}", species_key, planted_on, removed_on, plan_role)
        self.plants.append((tenant, location_key, row))

    def list_plantings(self, location_key, *, since, tenant_key):
        if not tenant_key:
            raise ValueError("tenant_key required")
        return [
            row
            for tenant, location, row in self.plants
            if tenant == tenant_key and location == location_key and (row.removed_on is None or row.removed_on >= since)
        ]

    def list_backfills(self, location_key, *, since: datetime, tenant_key):
        if not tenant_key:
            raise ValueError("tenant_key required")
        if self._events is None:
            return []
        rows = [
            BackfillRow(e.key or "", e.performed_at, e.rotation_entry, e.created_by)
            for e in self._events.events.values()
            if e.tenant_key == tenant_key
            and e.location_key == location_key
            and e.category == "planting"
            and e.trigger == "backfill"
            and e.voided_at is None
            and e.superseded_by_key is None
            and e.rotation_entry is not None
            and e.performed_at >= since
        ]
        return sorted(rows, key=lambda r: r.performed_at, reverse=True)


class FakeRotationGraph:
    """The graph reads the bed-level check makes: pest risk, adjacency and the companion edges."""

    def __init__(self) -> None:
        self.pest_risks: dict[str, list[dict]] = {}
        self.adjacent: dict[str, list[str]] = {}
        self.incompatible: dict[str, list[str]] = {}
        self.compatible: dict[str, dict[str, float]] = {}

    def get_pest_risks(self, family_key):
        return self.pest_risks.get(family_key, [])

    def get_adjacent_slots(self, slot_key):
        return [{"slot": {"_key": key}} for key in self.adjacent.get(slot_key, [])]

    def get_incompatible_species(self, species_key, *, tenant_key):
        return [{"species": {"_key": key}} for key in self.incompatible.get(species_key, [])]

    def get_compatible_species(self, species_key, *, tenant_key):
        return [
            {"species": {"_key": key}, "score": score} for key, score in self.compatible.get(species_key, {}).items()
        ]
