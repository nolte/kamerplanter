"""#2774 — a plant that moved to another slot stands only on its new one, for every "currently on the slot" reader.

``ArangoPlantInstanceRepository.update`` adds the ``placed_in`` edge to a moved plant's new slot and keeps the edge to
the slot it left - that edge is the old slot's crop-rotation history (#2948). Measured here against a real ArangoDB,
with the moved state produced the way production produces it (``create`` on slot A, then ``update`` with slot B, so
both edges exist): sowing and thinning the old slot are not refused, the old slot has no occupant, the bed listing and
the bed clearing see the plant only in its new bed, the sown-slot read lists the old slot, and the slot of a plant is
its new one. A run relocation through ``PlantingRunService.update_run`` leaves the old bed's readers empty.

Every "not there" assertion is paired with the control through the same reader: the plant on its new slot, or a
plant that never moved.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from arango import ArangoClient

from app.common.datetimes import today_utc
from app.common.enums import PlantingRunStatus, PlantingRunType
from app.common.exceptions import WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.plant_state_repository import ArangoPlantStateRepository
from app.data_access.arango.planting_reservation_repository import ArangoPlantingReservationRepository
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.models.care_event import CareEvent
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_reservation import ClearBedWrite, SlotThinningWrite
from app.domain.models.planting_run import PlantingRun
from app.domain.services.planting_run_service import PlantingRunService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("moved_plant_slot_readers")
A = "ten_a"
NOW = datetime(2026, 11, 13, 12, 0, tzinfo=UTC)
SOWN_AT = date(2026, 10, 1)


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    # The production schema and graph: ``get_active_by_slot`` traverses ``kamerplanter_graph``.
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)
    client.close()


def _location(key: str, name: str) -> dict[str, Any]:
    return {"_key": key, "site_key": "site_a", "name": name, "location_type_key": "bed", "area_m2": 2.0}


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    database.collection(col.SITES).insert(
        {"_key": "site_a", "tenant_key": A, "name": "A", "type": "outdoor", "total_area_m2": 0.0, "timezone": "UTC"}
    )
    database.collection(col.LOCATIONS).insert(_location("bed", "Bed 1"))
    database.collection(col.LOCATIONS).insert(_location("bed2", "Bed 2"))
    return database


@pytest.fixture
def plants(db) -> ArangoPlantInstanceRepository:
    return ArangoPlantInstanceRepository(db)


@pytest.fixture
def repo(db) -> ArangoPlantingReservationRepository:
    return ArangoPlantingReservationRepository(db)


def make_slot(db, key: str, location: str = "bed", role: str = "position", **fields: Any) -> str:
    db.collection(col.SLOTS).insert(
        {
            "_key": key,
            "slot_id": f"{location.upper()}_{key.upper()}",
            "location_key": location,
            "slot_role": role,
            "capacity_plants": 1,
            "currently_occupied": False,
            "archived_at": None,
            **fields,
        }
    )
    db.collection(col.HAS_SLOT).insert({"_from": f"locations/{location}", "_to": f"slots/{key}"})
    return key


def make_run(db, key: str, status: str = "active", location: str = "bed") -> str:
    db.collection(col.PLANTING_RUNS).insert(
        {
            "_key": key,
            "tenant_key": A,
            "name": key,
            "run_type": "monoculture",
            "status": status,
            "location_key": location,
        }
    )
    return key


def reserve(db, run: str, slot: str, entry: str = "e1") -> None:
    db.collection(col.RUN_PLANNED_AT).insert(
        {
            "_from": f"planting_runs/{run}",
            "_to": f"slots/{slot}",
            "entry_key": entry,
            "planned_species_key": "sp",
            "sequence": 1,
            "planned_from": (today_utc() - timedelta(days=30)).isoformat(),
            "planned_until": None,
        }
    )


def place(plants: ArangoPlantInstanceRepository, name: str, slot: str, location: str = "bed") -> str:
    """A plant created on ``slot`` the way the plant router creates it: ``create`` writes the ``placed_in`` edge."""
    created = plants.create(
        PlantInstance(
            tenant_key=A,
            instance_id=f"ID_{name}",
            species_key="sp",
            planted_on=date(2026, 5, 1),
            site_key="site_a",
            location_key=location,
            slot_key=slot,
        )
    )
    assert created.key is not None
    return created.key


def move(plants: ArangoPlantInstanceRepository, key: str, slot: str | None, location: str | None = None) -> None:
    """Move a plant the way ``PUT``/``PATCH`` and the run relocation do: ``update`` keeps the old edge (#2948)."""
    plant = plants.get_by_key(key)
    assert plant is not None
    plant.slot_key = slot
    if location is not None:
        plant.location_key = location
    plants.update(key, plant)


def edge_targets(db, plant_key: str) -> list[str]:
    return sorted(e["_to"] for e in db.collection(col.PLACED_IN).find({"_from": f"plant_instances/{plant_key}"}))


def event(category: str, location: str = "bed") -> CareEvent:
    return CareEvent(
        tenant_key=A,
        site_key="site_a",
        location_key=location,
        category=category,
        summary=category,
        performed_at=NOW,
        trigger="system",
    )


def test_the_moved_state_keeps_both_edges(db, plants) -> None:
    """The precondition every test below relies on: production leaves the edge to the slot the plant left."""
    make_slot(db, "s1")
    make_slot(db, "t1", location="bed2")
    pi = place(plants, "pi", "s1")

    move(plants, pi, "t1", "bed2")

    assert edge_targets(db, pi) == ["slots/s1", "slots/t1"]
    moved = plants.get_by_key(pi)
    assert moved is not None and moved.slot_key == "t1"


class TestSowing:
    def test_the_slot_a_plant_left_can_be_sown(self, db, plants, repo) -> None:
        make_slot(db, "row1", role="row")
        make_slot(db, "row2", role="row")
        pi = place(plants, "pi", "row1")
        move(plants, pi, "row2")

        assert repo.mark_slot_sown("bed", "row1", sown_at=SOWN_AT, tenant_key=A)
        assert db.collection(col.SLOTS).get("row1")["sown_at"] == SOWN_AT.isoformat()
        # control: the slot the plant stands in now is still refused
        assert not repo.mark_slot_sown("bed", "row2", sown_at=SOWN_AT, tenant_key=A)
        assert db.collection(col.SLOTS).get("row2").get("sown_at") is None


class TestThinning:
    def arrange(self, db, plants) -> str:
        make_slot(db, "row1", role="row", sown_at=SOWN_AT.isoformat())
        make_slot(db, "row2", role="row")
        make_run(db, "run_a", status="planned")
        reserve(db, "run_a", "row1")
        return place(plants, "pi", "row1")

    def write(self) -> SlotThinningWrite:
        return SlotThinningWrite(
            location_key="bed",
            slot_key="row1",
            sown_at=SOWN_AT,
            run_key="run_a",
            entry_key="e1",
            tenant_key=A,
            plants=[],
            event=event("thinning"),
            phase_started_at=NOW,
            activate_run=False,
        )

    def test_the_slot_a_plant_left_is_thinned(self, db, plants, repo) -> None:
        pi = self.arrange(db, plants)
        move(plants, pi, "row2")

        repo.thin_sown_slot(self.write())

        stored = db.collection(col.SLOTS).get("row1")
        assert (stored.get("sown_at"), stored["currently_occupied"]) == (None, True)

    def test_a_plant_still_standing_in_the_slot_refuses_the_thinning(self, db, plants, repo) -> None:
        self.arrange(db, plants)

        with pytest.raises(WriteConflictError):
            repo.thin_sown_slot(self.write())

        assert db.collection(col.SLOTS).get("row1")["sown_at"] == SOWN_AT.isoformat()


class TestActivePlantsIn:
    def test_a_moved_plant_occupies_only_its_new_slot(self, db, plants, repo) -> None:
        make_slot(db, "s1")
        make_slot(db, "t1", location="bed2")
        pi = place(plants, "pi", "s1")
        move(plants, pi, "t1", "bed2")

        assert repo.active_plants_in(["s1"], tenant_key=A) == []
        (occupant,) = repo.active_plants_in(["s1", "t1"], tenant_key=A)
        assert (occupant.slot_key, occupant.plant_key) == ("t1", pi)


class TestListPlantings:
    def test_the_old_bed_does_not_list_a_moved_plant_and_the_new_one_lists_it_once(self, db, plants, repo) -> None:
        make_slot(db, "s1")
        make_slot(db, "s2")
        make_slot(db, "t1", location="bed2")
        pi = place(plants, "pi", "s1")
        stay = place(plants, "pi_stay", "s2")
        move(plants, pi, "t1", "bed2")

        old_bed = repo.list_plantings("bed", tenant_key=A, state=None, year=None)
        new_bed = repo.list_plantings("bed2", tenant_key=A, state=None, year=None)

        assert [(r.plant_key, r.slot_key) for r in old_bed] == [(stay, "s2")]
        assert [(r.plant_key, r.slot_key) for r in new_bed] == [(pi, "t1")]


class TestClearBed:
    def arrange(self, db, plants) -> tuple[str, str]:
        make_slot(db, "s1")
        make_slot(db, "s2")
        make_slot(db, "t1", location="bed2")
        moved = place(plants, "pi_moved", "s1")
        stay = place(plants, "pi_stay", "s2")
        move(plants, moved, "t1", "bed2")
        return moved, stay

    def write(self, location: str) -> ClearBedWrite:
        return ClearBedWrite(
            location_key=location,
            tenant_key=A,
            termination_type="senesced",
            removed_on=date(2026, 11, 13),
            event=event("clearing", location),
        )

    def test_clearing_the_old_bed_does_not_remove_a_plant_that_moved_away(self, db, plants, repo) -> None:
        moved, stay = self.arrange(db, plants)

        outcome = repo.clear_bed(self.write("bed"))

        assert outcome.removed_plant_keys == [stay]
        assert db.collection(col.PLANT_INSTANCES).get(moved).get("removed_on") is None
        assert db.collection(col.PLANT_INSTANCES).get(stay)["removed_on"] == "2026-11-13"

    def test_clearing_the_new_bed_removes_it(self, db, plants, repo) -> None:
        moved, stay = self.arrange(db, plants)

        outcome = repo.clear_bed(self.write("bed2"))

        assert outcome.removed_plant_keys == [moved]
        assert db.collection(col.PLANT_INSTANCES).get(moved)["removed_on"] == "2026-11-13"
        assert db.collection(col.PLANT_INSTANCES).get(stay).get("removed_on") is None


class TestSownSlots:
    def test_the_sown_slot_a_plant_left_is_listed_and_its_new_one_is_not(self, db, plants) -> None:
        make_slot(db, "row1", role="row", sown_at=SOWN_AT.isoformat())
        make_slot(db, "row2", role="row", sown_at=SOWN_AT.isoformat())
        make_run(db, "run_a", status="planned")
        reserve(db, "run_a", "row1")
        reserve(db, "run_a", "row2")
        pi = place(plants, "pi", "row1")
        move(plants, pi, "row2")

        sown = ArangoPlantStateRepository(db).list_sown_slots("bed", tenant_key=A)

        assert [s.slot_key for s in sown] == ["row1"]


class TestSlotForPlant:
    def test_the_slot_of_a_moved_plant_is_its_new_one(self, db, plants) -> None:
        make_slot(db, "s1")
        make_slot(db, "t1", location="bed2")
        pi = place(plants, "pi", "s1")
        move(plants, pi, "t1", "bed2")

        slot = ArangoSiteRepository(db).get_slot_for_plant(pi, tenant_key=A)

        assert slot is not None and slot.key == "t1"

    def test_a_plant_that_never_moved_keeps_its_slot(self, db, plants) -> None:
        make_slot(db, "s1")
        pi = place(plants, "pi", "s1")

        slot = ArangoSiteRepository(db).get_slot_for_plant(pi, tenant_key=A)

        assert slot is not None and slot.key == "s1"

    def test_a_plant_taken_off_every_slot_has_none(self, db, plants) -> None:
        make_slot(db, "s1")
        pi = place(plants, "pi", "s1")
        move(plants, pi, None)

        assert ArangoSiteRepository(db).get_slot_for_plant(pi, tenant_key=A) is None


class TestRunRelocation:
    """A run moved to another bed (``update_run`` → ``_reassign_plant_slots``) leaves nothing in the old bed."""

    def arrange(self, db, plants) -> tuple[PlantingRunService, str, list[str]]:
        for slot in ("s1", "s2"):
            make_slot(db, slot, currently_occupied=True)
        for slot in ("t1", "t2"):
            make_slot(db, slot, location="bed2")
        run_repo = ArangoPlantingRunRepository(db)
        run = run_repo.create(
            PlantingRun(
                tenant_key=A,
                name="Lettuce",
                run_type=PlantingRunType.MONOCULTURE,
                status=PlantingRunStatus.ACTIVE,
                location_key="bed",
            )
        )
        run_key = run.key or ""
        keys = []
        for name, slot in (("pi_1", "s1"), ("pi_2", "s2")):
            key = place(plants, name, slot)
            keys.append(key)
            db.collection(col.RUN_CONTAINS).insert(
                {"_from": f"planting_runs/{run_key}", "_to": f"plant_instances/{key}"}
            )
        service = PlantingRunService(run_repo, plants, PlantingRunEngine(), site_repo=ArangoSiteRepository(db))
        return service, run_key, keys

    def test_the_old_beds_readers_no_longer_see_the_plants(self, db, plants, repo) -> None:
        service, run_key, keys = self.arrange(db, plants)

        service.update_run(run_key, {"location_key": "bed2"}, tenant_key=A)

        slot_of = {}
        for key in keys:
            plant = plants.get_by_key(key)
            assert plant is not None
            slot_of[key] = plant.slot_key
        assert sorted(slot_of.values()) == ["t1", "t2"]
        # the old slot keeps the edge: it is its crop-rotation history
        assert all(f"slots/{old}" in edge_targets(db, key) for key, old in zip(keys, ("s1", "s2"), strict=True))
        # the old bed: no occupant, no listed plant, the slots free, nothing for a clearing to remove
        assert repo.active_plants_in(["s1", "s2"], tenant_key=A) == []
        assert plants.get_active_by_slot("s1", tenant_key=A) == []
        assert [r.plant_key for r in repo.list_plantings("bed", tenant_key=A, state=None, year=None)] == []
        assert all(not db.collection(col.SLOTS).get(k)["currently_occupied"] for k in ("s1", "s2"))
        cleared = repo.clear_bed(
            ClearBedWrite(
                location_key="bed",
                tenant_key=A,
                termination_type="senesced",
                removed_on=date(2026, 11, 13),
                event=event("clearing"),
            )
        )
        assert cleared.removed_plant_keys == []
        assert all(db.collection(col.PLANT_INSTANCES).get(k).get("removed_on") is None for k in keys)
        # control: the new bed sees both, each on the slot it names
        occupants = repo.active_plants_in(["t1", "t2"], tenant_key=A)
        assert sorted((a.slot_key, a.plant_key) for a in occupants) == sorted((s, k) for k, s in slot_of.items())
        listed = repo.list_plantings("bed2", tenant_key=A, state=None, year=None)
        assert sorted(r.plant_key for r in listed) == sorted(keys)
