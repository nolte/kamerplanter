"""REQ-053 WP 3.4 (#2394) — what stood in a bed, read from a real store (GP-FR-131, GP-API-039).

The AQL of ``ArangoRotationHistoryRepository`` is only proven by a server: a double that returns what the validator
expects certifies nothing about the statement. Pinned: plants of every slot of the bed (archived slots included) and
those that name the bed directly, the role of the run a plant belongs to, the tenant filter on plants and events,
and that a voided or superseded backfill is not history. Needs a real ArangoDB (see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.rotation_history_repository import ArangoRotationHistoryRepository
from app.domain.models.care_event import CareEvent, RotationEntry
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("rotation_history")
pytestmark = pytest.mark.usefixtures("arango_db")

_DOCUMENTS = [col.SLOTS, col.PLANT_INSTANCES, col.PLANTING_RUNS, col.CARE_EVENTS]
_EDGES = [col.RUN_CONTAINS, col.CARE_EVENT_AT, col.CARE_EVENT_FOR, col.TASK_LOGGED_AS]
TENANT = "ten_own"
OTHER = "ten_other"


@pytest.fixture(scope="module")
def _database():
    client = ArangoClient(hosts=ARANGO_URL)
    try:
        system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        if system.has_database(TEST_DATABASE):
            system.delete_database(TEST_DATABASE)
        system.create_database(TEST_DATABASE)
        database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        for name in _DOCUMENTS:
            database.create_collection(name)
        for name in _EDGES:
            database.create_collection(name, edge=True)
        yield database
        system.delete_database(TEST_DATABASE)
    finally:
        client.close()


@pytest.fixture
def db(_database):
    for name in (*_DOCUMENTS, *_EDGES):
        _database.collection(name).truncate()
    return _database


@pytest.fixture
def repo(db):
    return ArangoRotationHistoryRepository(db)


def _plant(db, key, *, slot=None, location=None, species="sp", planted="2025-04-01", removed=None, tenant=TENANT):
    doc = {
        "_key": key,
        "tenant_key": tenant,
        "species_key": species,
        "planted_on": planted,
        "removed_on": removed,
        "slot_key": slot,
        "location_key": location,
    }
    db.collection(col.PLANT_INSTANCES).insert(doc)


def _event(db, key, *, location="bed", tenant=TENANT, performed="2024-07-01T12:00:00Z", **extra):
    db.collection(col.CARE_EVENTS).insert(
        {
            "_key": key,
            "tenant_key": tenant,
            "location_key": location,
            "category": "planting",
            "trigger": "backfill",
            "performed_at": performed,
            "created_by": "u_sabine",
            "rotation_entry": {"year": 2024, "season": None, "family_key": "solanum", "plan_role": "main_crop"},
            **extra,
        }
    )


class TestPlantings:
    def test_reads_the_plants_of_every_slot_of_the_bed_archived_slots_included(self, db, repo) -> None:
        db.collection(col.SLOTS).insert_many(
            [
                {"_key": "s1", "location_key": "bed"},
                {"_key": "s2", "location_key": "bed", "archived_at": "2025-10-01T00:00:00Z"},
                {"_key": "other", "location_key": "bed2"},
            ]
        )
        _plant(db, "p1", slot="s1")
        _plant(db, "p2", slot="s2", removed="2025-09-01")
        _plant(db, "p3", slot="other")
        _plant(db, "p4", location="bed")  # names the bed, sits on no slot

        rows = repo.list_plantings("bed", since=date(2020, 1, 1), tenant_key=TENANT)

        assert sorted(r.plant_key for r in rows) == ["p1", "p2", "p4"]

    def test_another_tenants_plant_in_a_slot_of_this_bed_is_not_history(self, db, repo) -> None:
        db.collection(col.SLOTS).insert({"_key": "s1", "location_key": "bed"})
        _plant(db, "mine", slot="s1")
        _plant(db, "theirs", slot="s1", tenant=OTHER)

        assert [r.plant_key for r in repo.list_plantings("bed", since=date(2020, 1, 1), tenant_key=TENANT)] == ["mine"]
        assert [r.plant_key for r in repo.list_plantings("bed", since=date(2020, 1, 1), tenant_key=OTHER)] == ["theirs"]

    def test_a_plant_removed_before_the_window_is_left_out_a_standing_one_stays(self, db, repo) -> None:
        db.collection(col.SLOTS).insert({"_key": "s1", "location_key": "bed"})
        _plant(db, "old", slot="s1", planted="2018-04-01", removed="2018-09-01")
        _plant(db, "standing", slot="s1", planted="2018-04-01")

        rows = repo.list_plantings("bed", since=date(2024, 1, 1), tenant_key=TENANT)

        assert [r.plant_key for r in rows] == ["standing"]
        assert rows[0].removed_on is None

    def test_the_role_comes_from_the_run_the_plant_belongs_to(self, db, repo) -> None:
        db.collection(col.SLOTS).insert({"_key": "s1", "location_key": "bed"})
        db.collection(col.PLANTING_RUNS).insert({"_key": "r1", "plan_role": "green_manure"})
        _plant(db, "green", slot="s1")
        _plant(db, "plain", slot="s1")
        db.collection(col.RUN_CONTAINS).insert({"_from": "planting_runs/r1", "_to": "plant_instances/green"})

        roles = {
            r.plant_key: r.plan_role for r in repo.list_plantings("bed", since=date(2020, 1, 1), tenant_key=TENANT)
        }

        assert roles == {"green": "green_manure", "plain": "main_crop"}

    def test_a_detached_run_does_not_decide_the_role(self, db, repo) -> None:
        db.collection(col.SLOTS).insert({"_key": "s1", "location_key": "bed"})
        db.collection(col.PLANTING_RUNS).insert_many(
            [{"_key": "r_a_detached", "plan_role": "green_manure"}, {"_key": "r_b_attached", "plan_role": "main_crop"}]
        )
        _plant(db, "moved", slot="s1")
        db.collection(col.RUN_CONTAINS).insert_many(
            [
                {
                    "_from": "planting_runs/r_a_detached",
                    "_to": "plant_instances/moved",
                    "detached_at": "2025-06-01T00:00:00Z",
                },
                {"_from": "planting_runs/r_b_attached", "_to": "plant_instances/moved"},
            ]
        )

        (row,) = repo.list_plantings("bed", since=date(2020, 1, 1), tenant_key=TENANT)

        assert row.plan_role == "main_crop"

    def test_an_empty_tenant_is_refused(self, repo) -> None:
        with pytest.raises(ValueError, match="tenant_key"):
            repo.list_plantings("bed", since=date(2020, 1, 1), tenant_key="")


class TestBackfills:
    SINCE = datetime(2020, 1, 1, tzinfo=UTC)

    def test_reads_live_backfills_of_the_bed_newest_first(self, db, repo) -> None:
        _event(db, "older", performed="2023-07-01T12:00:00Z")
        _event(db, "newer", performed="2024-07-01T12:00:00Z")
        _event(db, "elsewhere", location="bed2")

        rows = repo.list_backfills("bed", since=self.SINCE, tenant_key=TENANT)

        assert [r.event_key for r in rows] == ["newer", "older"]
        assert rows[0].entry.family_key == "solanum"
        assert rows[0].created_by == "u_sabine"

    def test_a_voided_or_superseded_backfill_is_not_history(self, db, repo) -> None:
        _event(db, "live")
        _event(db, "voided", voided_at="2025-01-01T00:00:00Z", void_reason="backfill_error")
        _event(db, "superseded", superseded_by_key="live")

        assert [r.event_key for r in repo.list_backfills("bed", since=self.SINCE, tenant_key=TENANT)] == ["live"]

    def test_only_planting_backfills_with_an_entry_count(self, db, repo) -> None:
        _event(db, "ok")
        _event(db, "note", category="note")
        _event(db, "manual", trigger="manual")
        db.collection(col.CARE_EVENTS).insert(
            {
                "_key": "bare",
                "tenant_key": TENANT,
                "location_key": "bed",
                "category": "planting",
                "trigger": "backfill",
                "performed_at": "2024-07-01T12:00:00Z",
            }
        )

        assert [r.event_key for r in repo.list_backfills("bed", since=self.SINCE, tenant_key=TENANT)] == ["ok"]

    def test_another_tenants_event_naming_this_bed_is_not_history(self, db, repo) -> None:
        _event(db, "mine")
        _event(db, "theirs", tenant=OTHER)

        assert [r.event_key for r in repo.list_backfills("bed", since=self.SINCE, tenant_key=TENANT)] == ["mine"]

    def test_the_window_compares_instants_not_spellings(self, db, repo) -> None:
        _event(db, "before", performed="2019-12-31T23:59:59Z")
        _event(db, "after", performed="2020-01-01T00:00:00+00:00")

        assert [r.event_key for r in repo.list_backfills("bed", since=self.SINCE, tenant_key=TENANT)] == ["after"]


class TestTheRowTheServiceWrites:
    """A backfill written through the care-event repository reads back as the same family-year (round trip)."""

    def test_the_stored_rotation_entry_reads_back_and_a_void_removes_it(self, db, repo) -> None:
        events = ArangoCareEventRepository(db)
        entry = RotationEntry(
            year=2024, season="spring", family_key="brassica", species_key="cabbage", plan_role="green_manure"
        )
        stored = events.insert(
            CareEvent(
                tenant_key=TENANT,
                site_key="site_1",
                location_key="bed",
                category="planting",
                summary="Backfill 2024",
                performed_at=datetime(2024, 4, 15, 12, tzinfo=UTC),
                trigger="backfill",
                created_by="u_sabine",
                rotation_entry=entry,
            ),
            tenant_key=TENANT,
        )

        (row,) = repo.list_backfills("bed", since=datetime(2020, 1, 1, tzinfo=UTC), tenant_key=TENANT)
        assert row.event_key == stored.key
        assert row.entry == entry
        assert row.performed_at == datetime(2024, 4, 15, 12, tzinfo=UTC)

        events.void(stored.key, tenant_key=TENANT, voided_by="u_sabine", reason="backfill_error", at=datetime.now(UTC))
        assert repo.list_backfills("bed", since=datetime(2020, 1, 1, tzinfo=UTC), tenant_key=TENANT) == []
