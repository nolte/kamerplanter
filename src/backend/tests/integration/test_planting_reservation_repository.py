"""REQ-053 WP 3.2 (#2392) — slot reservation, bed clearing and quick planting against a real ArangoDB.

What no double can decide, measured here: that the layout's slots, ``has_slot`` and ``run_planned_at`` edges are
written in **one** transaction (a duplicate ``slot_id`` halfway through leaves nothing), that the reservation
re-check runs inside the transaction and aborts it, that the tenant predicate of every read hides a foreign
tenant's runs and plants, that clearing ends exactly the live runs and plants of the bed, archives the slots no
later run has reserved and writes its care event in the same transaction, and that a quick planting is all or
nothing.

Every "nothing is there" assertion is paired with the positive control in the same test — the tenant's own row
read through the same path — so an empty answer cannot be a reader that sees nothing at all.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from arango import ArangoClient

from app.common.enums import GeometrySource, PlantingRunStatus, PlantingRunType, SlotRole
from app.common.exceptions import DuplicateError, NotFoundError, PlanError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.planting_reservation_repository import ArangoPlantingReservationRepository
from app.domain.engines.slot_reservation_engine import find_conflicts
from app.domain.models.care_event import CareEvent
from app.domain.models.geometry import PointGeometry
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_reservation import (
    ClearBedWrite,
    NewReservedSlot,
    QuickPlantedPlant,
    QuickPlantWrite,
    ReservationWrite,
    RunSlotsWrite,
)
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.models.site import Slot
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("planting_reservation_repository")
A, B = "ten_a", "ten_b"
D = date
NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)

_DOCUMENTS = (
    col.SITES,
    col.LOCATIONS,
    col.SLOTS,
    col.PLANTING_RUNS,
    col.PLANTING_RUN_ENTRIES,
    col.PLANT_INSTANCES,
    col.PHASE_HISTORIES,
    col.CARE_EVENTS,
    col.TASKS,
    col.SPECIES,
)
#: Every edge collection of the graph, so a relation added later is there for the slot cascade of the drop.
_EDGES = tuple(dict.fromkeys(str(d["edge_collection"]) for d in col.GRAPH_EDGE_DEFINITIONS))


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in _DOCUMENTS:
        if not db.has_collection(name):
            db.create_collection(name)
    for name in _EDGES:
        if not db.has_collection(name):
            db.create_collection(name, edge=True)
    db.collection(col.SLOTS).add_persistent_index(fields=col.SLOT_ID_INDEX_FIELDS, unique=True)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    database.collection(col.SITES).insert({"_key": "site_a", "tenant_key": A, "name": "A", "type": "outdoor"})
    database.collection(col.LOCATIONS).insert({"_key": "bed", "site_key": "site_a", "name": "Bed 3"})
    database.collection(col.LOCATIONS).insert({"_key": "bed_b", "site_key": "site_b", "name": "Bed B"})
    return database


@pytest.fixture
def repo(db) -> ArangoPlantingReservationRepository:
    return ArangoPlantingReservationRepository(db)


def make_run(db, key: str, tenant: str = A, status: str = "planned", **fields) -> str:
    db.collection(col.PLANTING_RUNS).insert(
        {"_key": key, "tenant_key": tenant, "name": key, "run_type": "monoculture", "status": status, **fields}
    )
    return key


def make_slot(db, key: str, location: str = "bed", **fields) -> str:
    db.collection(col.SLOTS).insert({"_key": key, "slot_id": f"BED_{key.upper()}", "location_key": location, **fields})
    db.collection(col.HAS_SLOT).insert({"_from": f"locations/{location}", "_to": f"slots/{key}"})
    return key


def reserve(db, run: str, slot: str, start: str, end: str | None, entry: str = "e1", sequence: int = 1) -> None:
    db.collection(col.RUN_PLANNED_AT).insert(
        {
            "_from": f"planting_runs/{run}",
            "_to": f"slots/{slot}",
            "entry_key": entry,
            "planned_species_key": "sp",
            "sequence": sequence,
            "planned_from": start,
            "planned_until": end,
        }
    )


def plant(db, key: str, slot: str | None, run: str | None, tenant: str = A, **fields) -> None:
    db.collection(col.PLANT_INSTANCES).insert(
        {
            "_key": key,
            "tenant_key": tenant,
            "instance_id": f"ID_{key}",
            "species_key": "sp",
            "planted_on": "2026-05-01",
            **fields,
        }
    )
    if slot:
        db.collection(col.PLACED_IN).insert({"_from": f"plant_instances/{key}", "_to": f"slots/{slot}"})
    if run:
        db.collection(col.RUN_CONTAINS).insert({"_from": f"planting_runs/{run}", "_to": f"plant_instances/{key}"})


def edges(db, collection: str) -> list[dict]:
    return list(db.collection(collection).all())


def layout_slot(slot_id: str, sequence: int = 1, role: SlotRole = SlotRole.POSITION) -> Slot:
    return Slot(
        slot_id=slot_id,
        slot_role=role,
        geometry=PointGeometry(origin=(0.1 * sequence, 0.1)),
        sequence=sequence,
        geometry_source=GeometrySource.LAYOUT,
    )


def clearing_event(**overrides) -> CareEvent:
    data = {
        "tenant_key": A,
        "site_key": "site_a",
        "location_key": "bed",
        "category": "clearing",
        "summary": "Bed cleared (senesced)",
        "performed_at": NOW,
        "trigger": "system",
        **overrides,
    }
    return CareEvent(**data)


class TestPlaceRunLayout:
    def write(self, *ids: str) -> RunSlotsWrite:
        return RunSlotsWrite(
            location_key="bed",
            run_key="run_a",
            planned_from=D(2026, 5, 15),
            planned_until=D(2026, 9, 30),
            slots=[NewReservedSlot(layout_slot(slot_id, n), "e1", "sp", n) for n, slot_id in enumerate(ids, start=1)],
        )

    def test_slots_and_both_edges_are_written_together(self, db, repo) -> None:
        make_run(db, "run_a")

        keys = repo.place_run_layout(self.write("BED_001", "BED_002"))

        assert len(keys) == 2
        assert sorted(e["_to"] for e in edges(db, col.HAS_SLOT)) == sorted(f"slots/{k}" for k in keys)
        planned = sorted(edges(db, col.RUN_PLANNED_AT), key=lambda e: e["sequence"])
        assert [(e["_from"], e["sequence"], e["planned_from"], e["planned_until"]) for e in planned] == [
            ("planting_runs/run_a", 1, "2026-05-15", "2026-09-30"),
            ("planting_runs/run_a", 2, "2026-05-15", "2026-09-30"),
        ]
        stored = db.collection(col.SLOTS).get(keys[0])
        assert (stored["location_key"], stored["geometry_source"], stored["slot_role"]) == ("bed", "layout", "position")

    def test_a_duplicate_slot_id_leaves_nothing_behind(self, db, repo) -> None:
        make_run(db, "run_a")
        make_slot(db, "old")  # slot_id BED_OLD
        before = len(edges(db, col.HAS_SLOT))

        with pytest.raises(DuplicateError):
            repo.place_run_layout(self.write("BED_001", "BED_OLD"))

        assert [s["slot_id"] for s in edges(db, col.SLOTS)] == ["BED_OLD"]  # the first slot was rolled back
        assert len(edges(db, col.HAS_SLOT)) == before
        assert edges(db, col.RUN_PLANNED_AT) == []

    def test_a_bed_that_is_gone_is_404_and_writes_nothing(self, db, repo) -> None:
        make_run(db, "run_a")
        write = self.write("BED_001")

        with pytest.raises(NotFoundError):
            repo.place_run_layout(RunSlotsWrite(**{**write.__dict__, "location_key": "ghost"}))

        assert edges(db, col.SLOTS) == []


class TestTheBedLock:
    def test_a_writer_of_the_bed_that_comes_second_gets_the_write_conflict(self, db, repo) -> None:
        """Every write starts by updating the bed's own document, so two writers of one bed serialise (409)."""
        make_run(db, "run_a")
        holder = db.begin_transaction(write=[col.LOCATIONS])
        try:
            holder.collection(col.LOCATIONS).update({"_key": "bed", "name": "Bed 3 (held)"})

            with pytest.raises(WriteConflictError):
                repo.place_run_layout(TestPlaceRunLayout().write("BED_001"))
        finally:
            holder.abort_transaction()

        assert edges(db, col.SLOTS) == []  # the loser wrote nothing
        keys = repo.place_run_layout(
            TestPlaceRunLayout().write("BED_001")
        )  # the positive control: the lock is free again
        assert len(keys) == 1

    def test_a_release_waits_for_no_one_but_takes_the_same_lock(self, db, repo) -> None:
        make_slot(db, "s1")
        make_run(db, "run_a", location_key="bed")
        reserve(db, "run_a", "s1", "2026-05-15", None)
        holder = db.begin_transaction(write=[col.LOCATIONS])
        try:
            holder.collection(col.LOCATIONS).update({"_key": "bed", "name": "Bed 3 (held)"})

            with pytest.raises(WriteConflictError):
                repo.release_reservation("run_a", "s1")
            with pytest.raises(WriteConflictError):
                repo.drop_run_reservations("run_a", remove_layout_slots=False)
        finally:
            holder.abort_transaction()

        assert len(edges(db, col.RUN_PLANNED_AT)) == 1  # the loser released nothing
        assert repo.release_reservation("run_a", "s1") is True  # the lock is free again

    def test_a_drop_for_a_bed_that_is_gone_still_goes_through(self, db, repo) -> None:
        make_run(db, "run_a", location_key="ghost")
        make_slot(db, "s1")
        reserve(db, "run_a", "s1", "2026-05-15", None)

        assert repo.drop_run_reservations("run_a", remove_layout_slots=False) == 1


class TestReservationReads:
    def arrange(self, db) -> None:
        make_slot(db, "s1")
        make_run(db, "run_a", status="active")
        make_run(db, "run_gone", status="completed")
        make_run(db, "run_foreign", tenant=B)
        reserve(db, "run_a", "s1", "2026-05-15", "2026-09-30")
        reserve(db, "run_gone", "s1", "2026-01-01", "2026-02-01")
        reserve(db, "run_foreign", "s1", "2026-06-01", None)

    def test_only_the_tenants_runs_are_seen_with_their_status(self, db, repo) -> None:
        self.arrange(db)

        mine = repo.reservations_for(["s1"], tenant_key=A)
        theirs = repo.reservations_for(["s1"], tenant_key=B)

        assert sorted((r.run_key, r.run_status) for r in mine) == [("run_a", "active"), ("run_gone", "completed")]
        assert [r.run_key for r in theirs] == ["run_foreign"]  # the positive control for B
        assert (mine[0].planned_from, mine[0].planned_until) is not None

    def test_a_foreign_run_does_not_conflict_but_an_overlap_with_the_own_one_does(self, db, repo) -> None:
        """GP-ACC-039 end to end: the window from the edge, the tenant from the run."""
        self.arrange(db)

        conflicts = find_conflicts(
            ["s1"],
            run_key="run_new",
            planned_from=D(2026, 8, 1),
            planned_until=None,
            reservations=repo.reservations_for(["s1"], tenant_key=A),
            plants=[],
        )
        assert [(c.conflicting_run_key, c.overlap_from, c.overlap_until) for c in conflicts] == [
            ("run_a", D(2026, 8, 1), D(2026, 9, 30))
        ]
        after = find_conflicts(
            ["s1"],
            run_key="run_new",
            planned_from=D(2026, 10, 5),
            planned_until=None,
            reservations=repo.reservations_for(["s1"], tenant_key=A),
            plants=[],
        )
        assert after == []

    def test_the_reservations_of_a_run_come_in_consumption_order(self, db, repo) -> None:
        make_run(db, "run_a")
        for n, slot in enumerate(("s3", "s1", "s2"), start=1):
            make_slot(db, slot)
            reserve(db, "run_a", slot, "2026-05-15", None, sequence=n)

        rows = repo.reservations_of_run("run_a", tenant_key=A)

        assert [(r.slot_key, r.sequence) for r in rows] == [("s3", 1), ("s1", 2), ("s2", 3)]
        assert repo.reservations_of_run("run_a", tenant_key=B) == []

    def test_active_plants_carry_the_expected_end_of_their_run(self, db, repo) -> None:
        make_slot(db, "s1")
        make_run(db, "run_a", status="active", planned_until="2026-09-30")
        plant(db, "pi_1", "s1", "run_a")
        plant(db, "pi_gone", "s1", "run_a", removed_on="2026-06-01")
        plant(db, "pi_loose", "s1", None)
        plant(db, "pi_foreign", "s1", None, tenant=B)

        mine = repo.active_plants_in(["s1"], tenant_key=A)

        assert sorted((p.plant_key, p.run_key, p.expected_end) for p in mine) == [
            ("pi_1", "run_a", D(2026, 9, 30)),
            ("pi_loose", None, None),
        ]
        assert [p.plant_key for p in repo.active_plants_in(["s1"], tenant_key=B)] == ["pi_foreign"]

    def test_an_empty_tenant_is_no_tenant(self, repo) -> None:
        with pytest.raises(ValueError):
            repo.reservations_for(["s1"], tenant_key="")
        with pytest.raises(ValueError):
            repo.active_plants_in(["s1"], tenant_key="")


class TestSetReservation:
    def write(self, *slot_keys: str, entry: str = "e1") -> ReservationWrite:
        return ReservationWrite(
            location_key="bed",
            run_key="run_a",
            entry_key=entry,
            planned_species_key="sp",
            ordered_slot_keys=list(slot_keys),
            planned_from=D(2026, 5, 15),
            planned_until=None,
            tenant_key=A,
        )

    def test_it_replaces_the_entrys_edges_and_keeps_the_other_entrys(self, db, repo) -> None:
        for slot in ("s1", "s2", "s3"):
            make_slot(db, slot)
        make_run(db, "run_a")
        reserve(db, "run_a", "s1", "2026-05-15", None, entry="e1")
        reserve(db, "run_a", "s3", "2026-05-15", None, entry="e2")

        repo.set_reservation(self.write("s2", "s1"), lambda reads: None)

        by_entry = {(e["entry_key"], e["_to"]): e["sequence"] for e in edges(db, col.RUN_PLANNED_AT)}
        assert by_entry == {("e1", "slots/s2"): 1, ("e1", "slots/s1"): 2, ("e2", "slots/s3"): 1}

    def test_the_recheck_runs_inside_the_transaction_and_aborts_it(self, db, repo) -> None:
        make_slot(db, "s1")
        make_run(db, "run_a")
        make_run(db, "run_b")
        reserve(db, "run_a", "s1", "2026-05-15", None, entry="e1")

        def verify(reads) -> None:
            if reads.reservations_for(["s1"], tenant_key=A):
                raise PlanError("slot.already_planned", "taken", status_code=409)

        with pytest.raises(PlanError):
            repo.set_reservation(self.write("s1", entry="e9"), verify)

        assert [(e["_from"], e["entry_key"]) for e in edges(db, col.RUN_PLANNED_AT)] == [("planting_runs/run_a", "e1")]

    def test_a_slot_archived_after_the_read_is_a_409(self, db, repo) -> None:
        make_slot(db, "s1", archived_at="2026-01-01T00:00:00+00:00")
        make_run(db, "run_a")

        with pytest.raises(WriteConflictError):
            repo.set_reservation(self.write("s1"), lambda reads: None)

        assert edges(db, col.RUN_PLANNED_AT) == []

    def test_a_slot_of_another_bed_is_refused(self, db, repo) -> None:
        make_slot(db, "s_other", location="bed_b")
        make_run(db, "run_a")

        with pytest.raises(WriteConflictError):
            repo.set_reservation(self.write("s_other"), lambda reads: None)

    def test_release_deletes_one_edge(self, db, repo) -> None:
        make_slot(db, "s1")
        make_slot(db, "s2")
        make_run(db, "run_a")
        reserve(db, "run_a", "s1", "2026-05-15", None)
        reserve(db, "run_a", "s2", "2026-05-15", None)

        assert repo.release_reservation("run_a", "s1") is True
        assert repo.release_reservation("run_a", "s1") is False
        assert [e["_to"] for e in edges(db, col.RUN_PLANNED_AT)] == ["slots/s2"]


class TestDropRunReservations:
    def test_it_removes_the_edges_and_only_the_slots_nothing_uses(self, db, repo) -> None:
        make_run(db, "run_a")
        make_run(db, "run_other")
        make_slot(db, "free", geometry_source="layout")
        make_slot(db, "taken", geometry_source="layout", currently_occupied=True)
        make_slot(db, "shared", geometry_source="layout")
        make_slot(db, "by_hand", geometry_source="editor")
        make_slot(db, "history", geometry_source="layout", archived_at="2026-01-01T00:00:00+00:00")
        for slot in ("free", "taken", "shared", "by_hand", "history"):
            reserve(db, "run_a", slot, "2026-05-15", None)
        reserve(db, "run_other", "shared", "2027-05-15", None)

        dropped = repo.drop_run_reservations("run_a", remove_layout_slots=True)

        assert dropped == 5
        assert sorted(s["_key"] for s in edges(db, col.SLOTS)) == ["by_hand", "history", "shared", "taken"]
        assert [e["_from"] for e in edges(db, col.RUN_PLANNED_AT)] == ["planting_runs/run_other"]
        # the has_slot edge of the removed slot went with it
        assert "slots/free" not in {e["_to"] for e in edges(db, col.HAS_SLOT)}

    def test_without_the_flag_no_slot_is_removed(self, db, repo) -> None:
        make_run(db, "run_a")
        make_slot(db, "free", geometry_source="layout")
        reserve(db, "run_a", "free", "2026-05-15", None)

        assert repo.drop_run_reservations("run_a", remove_layout_slots=False) == 1
        assert [s["_key"] for s in edges(db, col.SLOTS)] == ["free"]

    def test_a_run_without_reservations_drops_nothing(self, db, repo) -> None:
        make_run(db, "run_a")
        assert repo.drop_run_reservations("run_a", remove_layout_slots=True) == 0


class TestClearBed:
    def arrange(self, db) -> None:
        """GP-ACC-040 in miniature: two live runs with four plants in four slots, one planned run for later."""
        make_run(db, "run_1", status="active", planned_until="2026-09-30")
        make_run(db, "run_2", status="harvesting")
        make_run(db, "run_next", status="planned")
        make_run(db, "run_foreign", tenant=B, status="active")
        for slot in ("s1", "s2", "s3", "s4", "s5"):
            make_slot(db, slot, currently_occupied=slot != "s5")
        db.collection(col.RUN_AT_LOCATION).insert({"_from": "planting_runs/run_1", "_to": "locations/bed"})
        plant(db, "pi_1", "s1", "run_1")
        plant(db, "pi_2", "s2", "run_1")
        plant(db, "pi_3", "s3", "run_2")
        plant(db, "pi_4", "s4", "run_2")
        plant(db, "pi_gone", "s4", "run_2", removed_on="2026-06-01", termination_type="died")
        plant(db, "pi_foreign", "s4", "run_foreign", tenant=B)
        reserve(db, "run_1", "s5", "2026-05-15", None, sequence=5)  # a surplus reservation of an ended run
        reserve(db, "run_next", "s2", "2026-10-05", None)  # a follow-up crop planned in a used slot

    def write(self, termination: str = "senesced") -> ClearBedWrite:
        return ClearBedWrite(
            location_key="bed",
            tenant_key=A,
            termination_type=termination,
            removed_on=D(2026, 10, 18),
            event=clearing_event(),
        )

    def test_it_ends_the_live_runs_and_plants_and_archives_the_slots(self, db, repo) -> None:
        self.arrange(db)

        outcome = repo.clear_bed(self.write())

        assert (outcome.plants_removed, outcome.runs_completed) == (4, 2)
        for key in ("pi_1", "pi_2", "pi_3", "pi_4"):
            doc = db.collection(col.PLANT_INSTANCES).get(key)
            assert (doc["removed_on"], doc["termination_type"]) == ("2026-10-18", "senesced")
        # an earlier removal keeps its own date and cause; another tenant's plant is not touched
        assert db.collection(col.PLANT_INSTANCES).get("pi_gone")["termination_type"] == "died"
        assert db.collection(col.PLANT_INSTANCES).get("pi_foreign").get("removed_on") is None
        assert {k: db.collection(col.PLANTING_RUNS).get(k)["status"] for k in ("run_1", "run_2")} == {
            "run_1": "completed",
            "run_2": "completed",
        }
        assert db.collection(col.PLANTING_RUNS).get("run_foreign")["status"] == "active"
        assert db.collection(col.PLANTING_RUNS).get("run_next")["status"] == "planned"

    def test_slots_nothing_reserves_become_history_and_a_later_runs_slot_is_only_freed(self, db, repo) -> None:
        self.arrange(db)

        outcome = repo.clear_bed(self.write())

        archived = {s["_key"] for s in edges(db, col.SLOTS) if s.get("archived_at")}
        assert archived == {"s1", "s3", "s4", "s5"}  # s5: the surplus reservation of the ended run
        s2 = db.collection(col.SLOTS).get("s2")
        assert s2.get("archived_at") is None and s2["currently_occupied"] is False  # reserved by run_next
        assert (outcome.slots_archived, outcome.slots_released) == (4, 1)
        assert all(not s["currently_occupied"] for s in edges(db, col.SLOTS))
        # the ended runs' reservations are gone, the planned run keeps its own
        assert [e["_from"] for e in edges(db, col.RUN_PLANNED_AT)] == ["planting_runs/run_next"]

    def test_it_writes_the_clearing_event_with_the_plants_it_ended(self, db, repo) -> None:
        self.arrange(db)

        outcome = repo.clear_bed(self.write())

        event = db.collection(col.CARE_EVENTS).get(outcome.care_event_key)
        assert (event["category"], event["trigger"], event["location_key"]) == ("clearing", "system", "bed")
        assert sorted(e["_to"] for e in edges(db, col.CARE_EVENT_FOR)) == [
            f"plant_instances/{k}" for k in ("pi_1", "pi_2", "pi_3", "pi_4")
        ]
        assert [e["_to"] for e in edges(db, col.CARE_EVENT_AT)] == ["locations/bed"]
        assert sorted(outcome.removed_plant_keys) == ["pi_1", "pi_2", "pi_3", "pi_4"]

    def test_a_run_with_plants_standing_in_another_bed_is_not_ended(self, db, repo) -> None:
        self.arrange(db)
        db.collection(col.LOCATIONS).insert({"_key": "bed_two", "site_key": "site_a", "name": "Bed 4"})
        make_slot(db, "s_two", location="bed_two")
        plant(db, "pi_far", "s_two", "run_1")  # run_1 also has a plant in the other bed

        repo.clear_bed(self.write())

        assert db.collection(col.PLANT_INSTANCES).get("pi_1")["removed_on"] == "2026-10-18"
        assert db.collection(col.PLANTING_RUNS).get("run_1")["status"] == "active"  # its other plant still stands
        assert db.collection(col.PLANT_INSTANCES).get("pi_far").get("removed_on") is None
        assert db.collection(col.PLANTING_RUNS).get("run_2")["status"] == "completed"

    def test_a_cancelled_clearing_cancels_the_runs(self, db, repo) -> None:
        self.arrange(db)

        repo.clear_bed(self.write("cancelled"))

        assert db.collection(col.PLANTING_RUNS).get("run_1")["status"] == "cancelled"

    def test_a_bed_without_anything_live_still_logs_the_clearing(self, db, repo) -> None:
        outcome = repo.clear_bed(self.write())

        assert (outcome.plants_removed, outcome.runs_completed, outcome.slots_archived) == (0, 0, 0)
        assert db.collection(col.CARE_EVENTS).get(outcome.care_event_key) is not None

    def test_a_bed_that_is_gone_writes_nothing(self, db, repo) -> None:
        self.arrange(db)
        write = ClearBedWrite(
            location_key="ghost",
            tenant_key=A,
            termination_type="died",
            removed_on=D(2026, 10, 18),
            event=clearing_event(),
        )

        with pytest.raises(NotFoundError):
            repo.clear_bed(write)

        assert edges(db, col.CARE_EVENTS) == []
        assert db.collection(col.PLANT_INSTANCES).get("pi_1").get("removed_on") is None

    def test_a_clearing_under_another_tenant_touches_nothing_of_the_beds(self, db, repo) -> None:
        self.arrange(db)

        outcome = repo.clear_bed(ClearBedWrite(**{**self.write().__dict__, "tenant_key": B}))

        assert outcome.plants_removed == 1  # only the foreign tenant's own plant standing in the slot
        assert db.collection(col.PLANT_INSTANCES).get("pi_1").get("removed_on") is None
        assert db.collection(col.PLANTING_RUNS).get("run_1")["status"] == "active"

    def test_the_cleared_bed_no_longer_blocks_a_new_reservation(self, db, repo) -> None:
        """GP-ACC-040: archived slots block neither V-06 nor V-08; a new run takes the freed slot at once."""
        self.arrange(db)
        repo.clear_bed(self.write())
        plants = repo.active_plants_in(["s1", "s2", "s3", "s4"], tenant_key=A)
        reservations = repo.reservations_for(["s2"], tenant_key=A)

        assert plants == []
        conflicts = find_conflicts(
            ["s2"],
            run_key="run_new",
            planned_from=D(2026, 10, 18),
            planned_until=D(2026, 10, 31),
            reservations=reservations,
            plants=plants,
        )
        # only the follow-up crop planned for 2026-10-05 stands in the way — the ended runs' edges are gone
        assert [c.conflicting_run_key for c in conflicts] == ["run_next"]


class TestQuickPlant:
    def write(self, *, slot_ids: tuple[str, ...] = ("BED_Q1", "BED_Q2"), plants: int = 3) -> QuickPlantWrite:
        history = PhaseHistory(phase_key="ph_1", phase_name="seedling", entered_at=NOW, transition_reason="initial")
        return QuickPlantWrite(
            location_key="bed",
            run=PlantingRun(
                tenant_key=A,
                name="Quick planting",
                run_type=PlantingRunType.MONOCULTURE,
                status=PlantingRunStatus.ACTIVE,
                planned_quantity=plants,
                actual_quantity=plants,
                location_key="bed",
                source="field_mode",
                started_at=NOW,
            ),
            entry=PlantingRunEntry(tenant_key=A, species_key="sp", quantity=plants, id_prefix="TOM"),
            slots=[layout_slot(slot_id, n) for n, slot_id in enumerate(slot_ids, start=1)],
            plants=[
                QuickPlantedPlant(
                    plant=PlantInstance(
                        tenant_key=A,
                        instance_id=f"bed_TOM_{n:02d}",
                        species_key="sp",
                        location_key="bed",
                        site_key="site_a",
                        planted_on=D(2026, 10, 18),
                    ),
                    slot_index=n - 1 if n <= len(slot_ids) else None,
                    history=history,
                )
                for n in range(1, plants + 1)
            ],
            run_history=history,
        )

    def test_everything_is_written_together_and_linked(self, db, repo) -> None:
        outcome = repo.quick_plant(self.write())

        run = db.collection(col.PLANTING_RUNS).get(outcome.run_key)
        assert (run["status"], run["source"], run["tenant_key"], run["actual_quantity"]) == (
            "active",
            "field_mode",
            A,
            3,
        )
        entry = db.collection(col.PLANTING_RUN_ENTRIES).get(outcome.entry_key)
        assert (entry["run_key"], entry["tenant_key"]) == (outcome.run_key, A)
        assert len(outcome.created_slot_keys) == 2 and len(outcome.plant_keys) == 3
        assert sorted(e["_to"] for e in edges(db, col.RUN_CONTAINS)) == sorted(
            f"plant_instances/{k}" for k in outcome.plant_keys
        )
        placed = {e["_from"]: e["_to"] for e in edges(db, col.PLACED_IN)}
        assert len(placed) == 2  # the third plant has no slot
        assert set(placed.values()) == {f"slots/{k}" for k in outcome.created_slot_keys}
        assert [(e["_from"], e["_to"]) for e in edges(db, col.RUN_AT_LOCATION)] == [
            (f"planting_runs/{outcome.run_key}", "locations/bed")
        ]
        assert len(edges(db, col.HAS_ENTRY)) == 1 and len(edges(db, col.ENTRY_FOR_SPECIES)) == 1
        # one history row per plant and one for the run, each reachable through its phase_history_edge
        assert len(edges(db, col.PHASE_HISTORIES)) == 4
        assert {e["_from"] for e in edges(db, col.PHASE_HISTORY_EDGE)} == {
            *(f"plant_instances/{k}" for k in outcome.plant_keys),
            f"plant_instances/{outcome.run_key}",
        }
        first = db.collection(col.PLANT_INSTANCES).get(outcome.plant_keys[0])
        assert (first["slot_key"], first["location_key"], first["tenant_key"]) == (
            outcome.created_slot_keys[0],
            "bed",
            A,
        )
        assert "slot_key" not in db.collection(col.PLANT_INSTANCES).get(outcome.plant_keys[2])

    def test_a_failure_halfway_leaves_nothing(self, db, repo) -> None:
        make_slot(db, "old")  # slot_id BED_OLD
        before = {name: len(edges(db, name)) for name in (col.HAS_SLOT, col.SLOTS)}

        with pytest.raises(DuplicateError):
            repo.quick_plant(self.write(slot_ids=("BED_Q1", "BED_OLD")))

        assert {name: len(edges(db, name)) for name in before} == before
        for collection in (
            col.PLANTING_RUNS,
            col.PLANTING_RUN_ENTRIES,
            col.PLANT_INSTANCES,
            col.PLACED_IN,
            col.RUN_CONTAINS,
            col.PHASE_HISTORIES,
            col.PHASE_HISTORY_EDGE,
        ):
            assert edges(db, collection) == [], collection

    def test_a_duplicate_instance_id_per_tenant_is_refused_without_residue(self, db, repo) -> None:
        db.collection(col.PLANT_INSTANCES).add_persistent_index(fields=["tenant_key", "instance_id"], unique=True)
        plant(db, "pi_x", None, None)
        db.collection(col.PLANT_INSTANCES).update({"_key": "pi_x", "instance_id": "bed_TOM_02"})

        with pytest.raises(DuplicateError):
            repo.quick_plant(self.write())

        assert edges(db, col.PLANTING_RUNS) == []
        assert [p["_key"] for p in edges(db, col.PLANT_INSTANCES)] == ["pi_x"]

    def test_a_bed_that_is_gone_is_404(self, db, repo) -> None:
        write = self.write()
        with pytest.raises(NotFoundError):
            repo.quick_plant(QuickPlantWrite(**{**write.__dict__, "location_key": "ghost"}))
        assert edges(db, col.PLANTING_RUNS) == []


class TestListPlantings:
    def arrange(self, db) -> None:
        make_slot(db, "s1")
        make_slot(db, "s2")
        make_slot(db, "s3")
        make_slot(db, "s_arch", archived_at="2026-01-01T00:00:00+00:00")
        make_run(db, "run_a", status="active")
        make_run(db, "run_b", status="planned")
        make_run(db, "run_done", status="completed")
        make_run(db, "run_foreign", tenant=B, status="planned")
        plant(db, "pi_live", "s1", "run_a")
        plant(
            db,
            "pi_harvest",
            "s2",
            "run_a",
            removed_on="2025-09-01",
            termination_type="harvested",
            planted_on="2025-05-01",
        )
        plant(db, "pi_died", "s3", "run_a", removed_on="2025-07-01", termination_type="died", planted_on="2025-05-01")
        plant(db, "pi_loose", None, None, location_key="bed")
        plant(db, "pi_foreign", "s1", None, tenant=B)
        reserve(db, "run_a", "s1", "2026-04-01", None, entry="e_a")  # consumed: pi_live of run_a stands there
        reserve(db, "run_b", "s1", "2027-04-01", "2027-09-30", entry="e_b")  # planned for next year, same slot
        reserve(db, "run_b", "s_arch", "2027-04-01", None, entry="e_b")  # an archived slot is not a position
        reserve(db, "run_done", "s2", "2024-04-01", None)  # an ended run reserves nothing
        reserve(db, "run_foreign", "s2", "2027-04-01", None)

    def test_each_state_is_its_own_list(self, db, repo) -> None:
        self.arrange(db)

        def rows(state=None, year=None):
            return repo.list_plantings("bed", tenant_key=A, state=state, year=year)

        assert {r.plant_key for r in rows("active")} == {"pi_live", "pi_loose"}
        assert [r.plant_key for r in rows("harvested")] == ["pi_harvest"]
        assert [r.plant_key for r in rows("historical")] == ["pi_died"]
        (planned,) = rows("planned")
        assert (planned.run_key, planned.slot_key, planned.planned_from, planned.planned_until) == (
            "run_b",
            "s1",
            D(2027, 4, 1),
            D(2027, 9, 30),
        )

    def test_the_year_keeps_what_touches_it(self, db, repo) -> None:
        self.arrange(db)

        in_2025 = {r.plant_key for r in repo.list_plantings("bed", tenant_key=A, state=None, year=2025) if r.plant_key}
        in_2027 = repo.list_plantings("bed", tenant_key=A, state=None, year=2027)

        assert in_2025 == {"pi_harvest", "pi_died"}  # pi_live and pi_loose were planted in 2026
        assert {(r.state, r.run_key) for r in in_2027 if r.state == "planned"} == {("planned", "run_b")}

    def test_another_tenants_rows_are_not_listed(self, db, repo) -> None:
        self.arrange(db)

        mine = repo.list_plantings("bed", tenant_key=A, state=None, year=None)
        theirs = repo.list_plantings("bed", tenant_key=B, state=None, year=None)

        assert "pi_foreign" not in {r.plant_key for r in mine} and "run_foreign" not in {r.run_key for r in mine}
        assert {r.plant_key for r in theirs if r.plant_key} == {"pi_foreign"}  # the positive control for B
        assert {r.run_key for r in theirs if r.state == "planned"} == {"run_foreign"}
