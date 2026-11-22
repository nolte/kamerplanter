"""REQ-053 WP 4.5 (#2423) — the combined history of a bed, read from a real store (GP-FR-102, GP-API-038).

The AQL of ``ArangoBedHistoryRepository`` merges stored care events with planting events derived from plants and runs
and cuts one page from the merged order; a double that returns what the service expects certifies nothing about the
statement. Pinned: the merge order across both sources, the page boundary (50 newest of both together), every filter,
the corrections default, the tenant filter on events, plants and runs, and that a person filter leaves the derived
events out. Needs a real ArangoDB (see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.bed_history_repository import ArangoBedHistoryRepository
from app.domain.interfaces.bed_history_repository import BedHistoryFilter, BedHistoryRow
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("bed_history")
pytestmark = pytest.mark.usefixtures("arango_db")

_DOCUMENTS = [col.SLOTS, col.PLANT_INSTANCES, col.PLANTING_RUNS, col.CARE_EVENTS, col.USERS]
_EDGES = [col.RUN_CONTAINS]
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
    _database.collection(col.USERS).insert({"_key": "u_sabine", "display_name": "Sabine"})
    return _database


@pytest.fixture
def repo(db):
    return ArangoBedHistoryRepository(db)


def _event(db, key, *, performed, category="watering", location="bed", tenant=TENANT, **extra):
    db.collection(col.CARE_EVENTS).insert(
        {
            "_key": key,
            "tenant_key": tenant,
            "site_key": "site_1",
            "location_key": location,
            "category": category,
            "summary": f"event {key}",
            "trigger": "manual",
            "performed_at": performed,
            "performed_by_user_key": "u_sabine",
            "plant_keys": [],
            "superseded_by_key": None,
            **extra,
        }
    )


def _plant(db, key, *, slot="s1", location=None, planted="2025-04-01", removed=None, tenant=TENANT, **extra):
    db.collection(col.PLANT_INSTANCES).insert(
        {
            "_key": key,
            "tenant_key": tenant,
            "instance_id": f"id-{key}",
            "species_key": "sp",
            "planted_on": planted,
            "removed_on": removed,
            "slot_key": slot,
            "location_key": location,
            **extra,
        }
    )


def _page(repo, criteria: BedHistoryFilter | None = None, *, tenant=TENANT, offset=0, limit=50) -> list[BedHistoryRow]:
    return repo.list_history("bed", criteria or BedHistoryFilter(), tenant_key=tenant, offset=offset, limit=limit)


def _ids(rows: list[BedHistoryRow]) -> list[str]:
    return [
        f"care:{r.care.event.key}"
        if r.care is not None
        else f"{r.planting.kind}:{r.planting.plant_key or r.planting.run_key}"  # type: ignore[union-attr]
        for r in rows
    ]


@pytest.fixture
def bed(db):
    db.collection(col.SLOTS).insert_many(
        [{"_key": "s1", "location_key": "bed"}, {"_key": "other", "location_key": "bed2"}]
    )


class TestTheMerge:
    def test_care_events_and_planting_events_share_one_newest_first_order(self, db, repo, bed) -> None:
        _plant(db, "p1", planted="2025-04-01", removed="2025-09-30", termination_type="harvested")
        _event(db, "w1", performed="2025-06-01T08:00:00Z")
        _event(db, "w2", performed="2025-10-05T08:00:00Z")
        db.collection(col.PLANTING_RUNS).insert(
            {
                "_key": "r1",
                "tenant_key": TENANT,
                "name": "Spring tomatoes",
                "status": "completed",
                "started_at": "2025-03-20T09:00:00Z",
                "completed_at": "2025-09-30T17:00:00Z",
                "location_key": "bed",
            }
        )

        rows = _page(repo)

        assert _ids(rows) == [
            "care:w2",
            "run_completed:r1",
            "plant_removed:p1",
            "care:w1",
            "plant_planted:p1",
            "run_started:r1",
        ]
        removed = rows[2].planting
        assert removed is not None and removed.termination_type == "harvested" and removed.category == "removal"
        assert removed.at == datetime(2025, 9, 30, tzinfo=UTC)
        run = rows[1].planting
        assert run is not None and run.run_name == "Spring tomatoes" and run.run_status == "completed"
        assert rows[0].care is not None and rows[0].care.performed_by_name == "Sabine"

    def test_a_page_is_cut_from_the_merged_order_not_per_source(self, db, repo, bed) -> None:
        for day in range(1, 61):
            _event(
                db,
                f"e{day:02d}",
                performed=f"2025-06-{day:02d}T08:00:00Z" if day <= 30 else f"2025-07-{day - 30:02d}T08:00:00Z",
            )
        _plant(db, "p1", planted="2025-05-01")

        first = _page(repo, limit=50)
        second = _page(repo, offset=50, limit=50)

        assert len(first) == 50 and len(second) == 11
        assert _ids(second)[-1] == "plant_planted:p1"
        assert _ids(first)[0] == "care:e60"
        assert not set(_ids(first)) & set(_ids(second))

    def test_the_run_of_a_plant_of_the_bed_is_history_a_run_elsewhere_is_not(self, db, repo, bed) -> None:
        _plant(db, "p1")
        db.collection(col.PLANTING_RUNS).insert_many(
            [
                {
                    "_key": "mine",
                    "tenant_key": TENANT,
                    "name": "A",
                    "status": "active",
                    "started_at": "2025-04-01T00:00:00Z",
                },
                {
                    "_key": "far",
                    "tenant_key": TENANT,
                    "name": "B",
                    "status": "active",
                    "started_at": "2025-04-02T00:00:00Z",
                },
            ]
        )
        db.collection(col.RUN_CONTAINS).insert({"_from": "planting_runs/mine", "_to": "plant_instances/p1"})

        assert "run_started:mine" in _ids(_page(repo))
        assert "run_started:far" not in _ids(_page(repo))


class TestTheFilters:
    def test_category_planting_keeps_planted_and_started_not_removed(self, db, repo, bed) -> None:
        _plant(db, "p1", removed="2025-09-01")
        _event(db, "w1", performed="2025-06-01T08:00:00Z")
        _event(db, "b1", category="planting", performed="2024-07-01T12:00:00Z")

        ids = _ids(_page(repo, BedHistoryFilter(category="planting")))

        assert sorted(ids) == ["care:b1", "plant_planted:p1"]

    def test_a_care_category_leaves_the_derived_events_out(self, db, repo, bed) -> None:
        _plant(db, "p1", removed="2025-09-01")
        _event(db, "w1", performed="2025-06-01T08:00:00Z")
        _event(db, "f1", category="feeding", performed="2025-06-02T08:00:00Z")

        assert _ids(_page(repo, BedHistoryFilter(category="watering"))) == ["care:w1"]

    def test_the_period_applies_to_both_sources(self, db, repo, bed) -> None:
        _plant(db, "old", planted="2023-04-01", removed="2023-09-01")
        _plant(db, "new", planted="2025-04-01")
        _event(db, "w_old", performed="2023-06-01T08:00:00Z")
        _event(db, "w_new", performed="2025-06-01T08:00:00Z")

        rows = _page(
            repo,
            BedHistoryFilter(
                performed_from=datetime(2025, 1, 1, tzinfo=UTC), performed_to=datetime(2025, 12, 31, tzinfo=UTC)
            ),
        )

        assert sorted(_ids(rows)) == ["care:w_new", "plant_planted:new"]

    def test_a_lower_bound_inside_the_day_still_shows_a_plant_put_in_that_day(self, db, repo, bed) -> None:
        """Plants carry a date, not an instant: ``from = 12 May 05:00Z`` (a viewer at UTC-5) keeps 12 May."""
        _plant(db, "same_day", planted="2025-05-12", removed="2025-05-12")
        _plant(db, "day_before", planted="2025-05-11")

        rows = _page(repo, BedHistoryFilter(performed_from=datetime(2025, 5, 12, 5, tzinfo=UTC)))

        assert sorted(_ids(rows)) == ["plant_planted:same_day", "plant_removed:same_day"]

    def test_the_plant_filter_keeps_that_plants_events_and_drops_runs(self, db, repo, bed) -> None:
        _plant(db, "p1")
        _plant(db, "p2")
        _event(db, "w1", performed="2025-06-01T08:00:00Z", plant_keys=["p1"])
        _event(db, "w2", performed="2025-06-02T08:00:00Z", plant_keys=["p2"])
        db.collection(col.PLANTING_RUNS).insert(
            {
                "_key": "r1",
                "tenant_key": TENANT,
                "name": "A",
                "status": "active",
                "started_at": "2025-04-01T00:00:00Z",
                "location_key": "bed",
            }
        )

        assert sorted(_ids(_page(repo, BedHistoryFilter(plant_key="p1")))) == ["care:w1", "plant_planted:p1"]

    def test_a_person_filter_leaves_the_derived_events_out(self, db, repo, bed) -> None:
        _plant(db, "p1")
        _event(db, "mine", performed="2025-06-01T08:00:00Z")
        _event(db, "theirs", performed="2025-06-02T08:00:00Z", performed_by_user_key="u_other")

        assert _ids(_page(repo, BedHistoryFilter(performed_by="u_sabine"))) == ["care:mine"]

    def test_corrections_are_hidden_by_default_and_shown_on_request(self, db, repo, bed) -> None:
        _event(db, "old", performed="2025-06-01T08:00:00Z", superseded_by_key="new")
        _event(db, "new", performed="2025-06-01T08:00:00Z", supersedes_key="old")
        _event(db, "moved", category="position_corrected", performed="2025-06-02T08:00:00Z")

        assert _ids(_page(repo)) == ["care:new"]
        assert sorted(_ids(_page(repo, BedHistoryFilter(include_corrections=True)))) == [
            "care:moved",
            "care:new",
            "care:old",
        ]


class TestPlantNames:
    def test_a_care_event_names_its_plants_in_order_and_skips_gone_and_foreign_ones(self, db, repo, bed) -> None:
        """#2514: the history line names the plant from the same read - ``plant_name``, else ``instance_id``."""
        _plant(db, "named", plant_name="Tomato 'Black Krim' #3")
        _plant(db, "plain")
        _plant(db, "theirs", tenant=OTHER)
        _event(
            db,
            "moved",
            performed="2025-06-01T08:00:00Z",
            category="position_corrected",
            plant_keys=["plain", "gone", "theirs", "named"],
        )
        _event(db, "watered", performed="2025-06-02T08:00:00Z")

        # A position correction is a correction: shown on request only (GP-FR-102).
        page = _page(repo, BedHistoryFilter(include_corrections=True))
        rows = {r.care.event.key: r.care for r in page if r.care is not None}

        assert rows["moved"].plant_names == ("id-plain", "Tomato 'Black Krim' #3")
        assert rows["watered"].plant_names == ()

    def test_a_later_page_names_its_own_plants_and_performers(self, db, repo, bed) -> None:
        """The names are resolved after ``LIMIT``: page 2 must still carry the names of *its* lines, not page 1's."""
        _plant(db, "p_old", plant_name="Old bean")
        _plant(db, "p_new", plant_name="New bean")
        _event(db, "w_old", performed="2025-06-01T08:00:00Z", plant_keys=["p_old"], performed_for_user_key="u_sabine")
        _event(db, "w_new", performed="2025-06-02T08:00:00Z", plant_keys=["p_new"], performed_by_user_key="u_gone")

        first = _page(repo, offset=0, limit=1)
        second = _page(repo, offset=1, limit=1)

        assert _ids(first) == ["care:w_new"] and _ids(second) == ["care:w_old"]
        assert first[0].care is not None and second[0].care is not None
        assert first[0].care.plant_names == ("New bean",) and first[0].care.performed_by_name is None
        assert second[0].care.plant_names == ("Old bean",)
        assert second[0].care.performed_by_name == "Sabine" and second[0].care.performed_for_name == "Sabine"

    def test_the_name_lookups_are_bounded_by_the_page_not_by_the_history(self, db, bed) -> None:
        """SEC-001 (#2514): one page must not resolve the names of every care event of the bed.

        The production statement runs unchanged with ``profile=2``; the server counts the rows every calculation node
        evaluated. Summed over the nodes that call ``DOCUMENT`` (performer, recipient, plant names) a page of 2 lines
        over 40 events naming 10 plants each stays near ``2 x (10 + 2)``; resolved before the ``LIMIT`` it is ~520.
        """
        plants, events, limit = 10, 40, 2
        keys = [f"p{i}" for i in range(plants)]
        for key in keys:
            _plant(db, key)
        for i in range(events):
            _event(
                db,
                f"e{i:02d}",
                performed=f"2025-06-01T{i // 60:02d}:{i % 60:02d}:00Z",
                plant_keys=keys,
                performed_for_user_key="u_sabine",
            )
        cursors: list[Any] = []

        def profiled(query: str, bind_vars: dict[str, Any] | None = None, **options: Any) -> Any:
            cursor = db.aql.execute(query, bind_vars=bind_vars, profile=2, **options)
            cursors.append(cursor)
            return cursor

        spy = SimpleNamespace(aql=SimpleNamespace(execute=profiled))
        rows = ArangoBedHistoryRepository(spy).list_history(  # type: ignore[arg-type]
            "bed", BedHistoryFilter(), tenant_key=TENANT, offset=0, limit=limit
        )

        assert len(rows) == limit and all(r.care is not None and len(r.care.plant_names) == plants for r in rows)
        (cursor,) = cursors
        plan, stats = cursor.plan(), cursor.statistics()
        lookups = {
            node["id"]
            for node in plan["nodes"]
            if node["type"] == "CalculationNode" and "DOCUMENT" in str(node.get("expression"))
        }
        evaluated = sum(node["items"] for node in stats["nodes"] if node["id"] in lookups)
        assert lookups, "the plan resolves no name with DOCUMENT - the probe no longer sees the lookups"
        assert evaluated <= 2 * limit * (plants + 2), evaluated


class TestTheTenant:
    def test_another_tenants_rows_naming_this_bed_are_not_history(self, db, repo, bed) -> None:
        _plant(db, "mine")
        _plant(db, "theirs", tenant=OTHER)
        _event(db, "e_mine", performed="2025-06-01T08:00:00Z")
        _event(db, "e_theirs", performed="2025-06-02T08:00:00Z", tenant=OTHER)
        db.collection(col.PLANTING_RUNS).insert(
            {
                "_key": "r_theirs",
                "tenant_key": OTHER,
                "name": "X",
                "status": "active",
                "started_at": "2025-04-01T00:00:00Z",
                "location_key": "bed",
            }
        )

        assert sorted(_ids(_page(repo))) == ["care:e_mine", "plant_planted:mine"]
        assert sorted(_ids(_page(repo, tenant=OTHER))) == [
            "care:e_theirs",
            "plant_planted:theirs",
            "run_started:r_theirs",
        ]

    def test_an_empty_tenant_is_refused(self, repo) -> None:
        with pytest.raises(ValueError, match="tenant_key"):
            repo.list_history("bed", BedHistoryFilter(), tenant_key="", offset=0, limit=50)
