"""In-memory doubles of the slot-reservation collaborators (REQ-053 WP 3.2).

``FakeReservationRepo`` keeps the reservations and the plants of a small world and applies the write sets the
way ``ArangoPlantingReservationRepository`` does: the reservation write runs the service's ``verify`` against
itself first (the re-check inside the transaction), a layout write inserts the slots into the shared
:class:`FakePlanRepo`. It records what it was handed so a test can assert what the service decided.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

from app.common.exceptions import DuplicateError, NotFoundError
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.engines.slot_reservation_engine import (
    LIVE_RUN_STATUSES,
    ActivePlant,
    Reservation,
    intersects_year,
)
from app.domain.interfaces.planting_reservation_repository import IPlantingReservationRepository
from app.domain.models.planting_reservation import (
    ClearBedOutcome,
    ClearBedWrite,
    MixedRunsOutcome,
    MixedRunsWrite,
    PlantingRow,
    QuickPlantOutcome,
    QuickPlantWrite,
    ReservationReads,
    ReservationWrite,
    RunSlotsWrite,
)
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.services.care_event_service import CareEventService
from app.domain.services.planting_reservation_service import PlantingReservationService
from app.domain.services.planting_run_service import PlantingRunService
from tests.support.care_event_fakes import (
    FakeAttachmentRepo,
    FakeAttachmentService,
    FakeCareEventRepo,
    FakeFertilizers,
    FakeMemberships,
)
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)


class FakeRuns:
    """The two run reads ``PlantingReservationService`` needs; a run of any tenant, the service decides."""

    def __init__(self, *runs: PlantingRun) -> None:
        self.runs = {run.key: run for run in runs}
        self.entries: dict[str, PlantingRunEntry] = {}

    def get_or_raise(self, key):
        run = self.runs.get(key)
        if run is None:
            raise NotFoundError("PlantingRun", key)
        return run

    def get_entry_or_raise(self, key):
        entry = self.entries.get(key)
        if entry is None:
            raise NotFoundError("PlantingRunEntry", key)
        return entry


class FakeReservationRepo(IPlantingReservationRepository):
    def __init__(self, plan: FakePlanRepo, runs: FakeRuns | None = None) -> None:
        self._plan = plan
        self._runs = runs
        self.reservations: list[Reservation] = []
        self.plants: list[ActivePlant] = []
        self.rows: list[PlantingRow] = []
        self.layout_writes: list[RunSlotsWrite] = []
        self.reservation_writes: list[ReservationWrite] = []
        self.released: list[tuple[str, str]] = []
        self.dropped: list[tuple[str, bool]] = []
        self.clear_writes: list[ClearBedWrite] = []
        self.quick_writes: list[QuickPlantWrite] = []
        self.mixed_writes: list[MixedRunsWrite] = []
        #: Where ``create_mixed_runs`` stores the runs it was handed (the world's run double), if wired.
        self.run_sink = None
        self.clear_outcome = ClearBedOutcome(
            plants_removed=0, runs_completed=0, slots_archived=0, slots_released=0, care_event_key="ce_1"
        )
        self._next = 500

    # reads ---------------------------------------------------------------
    def reservations_for(self, slot_keys, *, tenant_key):
        return [r for r in self.reservations if r.slot_key in slot_keys and r.run_status in LIVE_RUN_STATUSES]

    def active_plants_in(self, slot_keys, *, tenant_key):
        return [p for p in self.plants if p.slot_key in slot_keys]

    def reservations_of_run(self, run_key, *, tenant_key):
        return sorted((r for r in self.reservations if r.run_key == run_key), key=lambda r: (r.entry_key, r.sequence))

    def list_plantings(self, location_key, *, tenant_key, state, year):
        rows = [r for r in self.rows if state is None or r.state == state]
        if year is not None:
            rows = [
                r
                for r in rows
                if intersects_year(r.planted_on or r.planned_from, r.removed_on or r.planned_until, year)
            ]
        return rows

    # writes --------------------------------------------------------------
    def place_run_layout(self, write: RunSlotsWrite) -> list[str]:
        self.layout_writes.append(write)
        taken = {s.slot_id for s in self._plan.slots if s.location_key == write.location_key}
        keys: list[str] = []
        for item in write.slots:
            if item.slot.slot_id in taken:
                raise DuplicateError("Slot", "slot_id", item.slot.slot_id)
            self._next += 1
            key = f"slot_{self._next}"
            keys.append(key)
            self._plan.slots.append(item.slot.model_copy(update={"key": key, "location_key": write.location_key}))
            self.reservations.append(
                Reservation(
                    slot_key=key,
                    run_key=write.run_key,
                    entry_key=item.entry_key,
                    planned_species_key=item.planned_species_key,
                    sequence=item.sequence,
                    planned_from=write.planned_from,
                    planned_until=write.planned_until,
                )
            )
        return keys

    def set_reservation(self, write: ReservationWrite, verify: Callable[[ReservationReads], None]) -> None:
        verify(self)
        self.reservation_writes.append(write)
        self.reservations = [
            r for r in self.reservations if not (r.run_key == write.run_key and r.entry_key == write.entry_key)
        ]
        for sequence, slot_key in enumerate(write.ordered_slot_keys, start=1):
            self.reservations.append(
                Reservation(
                    slot_key=slot_key,
                    run_key=write.run_key,
                    entry_key=write.entry_key,
                    planned_species_key=write.planned_species_key,
                    sequence=sequence,
                    planned_from=write.planned_from,
                    planned_until=write.planned_until,
                )
            )

    def release_reservation(self, run_key, slot_key):
        before = len(self.reservations)
        self.reservations = [r for r in self.reservations if not (r.run_key == run_key and r.slot_key == slot_key)]
        self.released.append((run_key, slot_key))
        return len(self.reservations) < before

    def drop_run_reservations(self, run_key, *, remove_layout_slots):
        self.dropped.append((run_key, remove_layout_slots))
        before = len(self.reservations)
        self.reservations = [r for r in self.reservations if r.run_key != run_key]
        return before - len(self.reservations)

    def clear_bed(self, write: ClearBedWrite) -> ClearBedOutcome:
        self.clear_writes.append(write)
        self._plan.care_events.append(write.event)
        return self.clear_outcome

    def create_mixed_runs(self, write: MixedRunsWrite) -> MixedRunsOutcome:
        self.mixed_writes.append(write)
        run_keys: list[str] = []
        slot_keys: list[str] = []
        for item in write.runs:
            self._next += 1
            run_key = f"run_{self._next}"
            run_keys.append(run_key)
            if self.run_sink is not None:
                self.run_sink.runs[run_key] = item.run.model_copy(update={"key": run_key})
                self.run_sink.entries[f"entry_{self._next}"] = item.entry.model_copy(
                    update={"key": f"entry_{self._next}", "run_key": run_key}
                )
            for reserved in item.slots:
                self._next += 1
                key = f"slot_{self._next}"
                slot_keys.append(key)
                self._plan.slots.append(
                    reserved.slot.model_copy(update={"key": key, "location_key": write.location_key})
                )
                self.reservations.append(
                    Reservation(
                        slot_key=key,
                        run_key=run_key,
                        entry_key=f"entry_{self._next}",
                        planned_species_key=item.entry.species_key,
                        sequence=reserved.sequence,
                        planned_from=item.planned_from,
                        planned_until=item.planned_until,
                    )
                )
        return MixedRunsOutcome(run_keys=run_keys, created_slot_keys=slot_keys)

    def quick_plant(self, write: QuickPlantWrite) -> QuickPlantOutcome:
        self.quick_writes.append(write)
        slot_keys = []
        for _slot in write.slots:
            self._next += 1
            slot_keys.append(f"slot_{self._next}")
        self._next += 1
        return QuickPlantOutcome(
            run_key=f"run_{self._next}",
            entry_key=f"entry_{self._next}",
            created_slot_keys=slot_keys,
            plant_keys=[f"pi_{self._next}_{i}" for i in range(len(write.plants))],
            created_at=datetime.now(UTC),
        )


def with_status(reservation: Reservation, status: str) -> Reservation:
    return replace(reservation, run_status=status)


class FakeRunRepo:
    """The run repository calls the flow makes, over dicts."""

    def __init__(self) -> None:
        self.runs: dict[str, PlantingRun] = {}
        self.entries: dict[str, PlantingRunEntry] = {}
        self.plant_links: list[tuple[str, str]] = []
        self.deleted: list[str] = []
        self._next = 0

    def verify_entry_references(self, entry) -> None:
        return None

    def create(self, run: PlantingRun) -> PlantingRun:
        self._next += 1
        stored = run.model_copy(update={"key": f"run_{self._next}"})
        self.runs[stored.key] = stored
        return stored

    def create_entry(self, entry: PlantingRunEntry) -> PlantingRunEntry:
        self._next += 1
        stored = entry.model_copy(update={"key": f"entry_{self._next}"})
        self.entries[stored.key] = stored
        return stored

    def get_by_key(self, key):
        return self.runs.get(key)

    def get_or_raise(self, key):
        if key not in self.runs:
            raise NotFoundError("PlantingRun", key)
        return self.runs[key]

    def get_entries(self, run_key):
        return [e for e in self.entries.values() if e.run_key == run_key]

    def get_entry_or_raise(self, key):
        if key not in self.entries:
            raise NotFoundError("PlantingRunEntry", key)
        return self.entries[key]

    def update(self, key, run):
        self.runs[key] = run
        return run

    def delete(self, key) -> bool:
        self.deleted.append(key)
        self.runs.pop(key, None)
        return True

    def get_existing_ids_at_location(self, location_key):
        return set()

    def link_run_to_plant(self, run_key, plant_key) -> None:
        self.plant_links.append((run_key, plant_key))

    def get_run_plants(self, run_key, include_detached=False):
        """The plants ``create_plants`` linked to the run (``run_contains``), as key rows."""
        return [{"_key": plant_key} for linked_run, plant_key in self.plant_links if linked_run == run_key]


class FakePlants:
    def __init__(self) -> None:
        self.created: list = []

    def create(self, plant):
        stored = plant.model_copy(update={"key": plant.instance_id})
        self.created.append(stored)
        return stored

    def get_by_key(self, key):
        return next((p for p in self.created if p.key == key), None)

    def update(self, key, plant):
        return plant


def build_world() -> SimpleNamespace:
    """The world of the slot-flow tests: a site with beds, the in-memory repositories and the real services."""
    sites = FakeSites(make_site(), make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed 3", geometry=rect(0, 0, 4, 2))
    plan.locations["bed_nogeo"] = make_location("bed_nogeo", name="Pot row")
    plan.locations["loc_foreign"] = make_location("loc_foreign", name="Foreign").model_copy(
        update={"site_key": "site_foreign"}
    )
    runs = FakeRunRepo()
    reservation_repo = FakeReservationRepo(plan, FakeRuns())
    reservation_repo.run_sink = runs
    care_repo = FakeCareEventRepo()
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    reservations = PlantingReservationService(reservation_repo, runs, sites, plan, care)
    plants = FakePlants()
    species = {
        "sp_tomato": SimpleNamespace(scientific_name="Solanum lycopersicum", green_manure_suitable=False),
        "sp_phacelia": SimpleNamespace(scientific_name="Phacelia tanacetifolia", green_manure_suitable=True),
    }

    def resolver(key, *, tenant_key):
        if key not in species:
            raise NotFoundError("Species", key)
        return species[key]

    service = PlantingRunService(
        runs,
        plants,
        PlantingRunEngine(),
        site_repo=sites,
        species_resolver=resolver,
        reservations=reservations,
        reservation_repo=reservation_repo,
    )
    # create_plants marks slots occupied through the site repository; keep what it was told
    updates: list = []
    sites.update_slot = lambda key, slot: updates.append((key, slot.currently_occupied)) or slot
    return SimpleNamespace(
        service=service,
        runs=runs,
        plan=plan,
        sites=sites,
        repo=reservation_repo,
        plants=plants,
        slot_updates=updates,
        reservations=reservations,
        care_repo=care_repo,
    )
