"""The calendar reads #1638 moved out of ``CalendarAggregationEngine``, against ArangoDB.

The engine used to run these queries against a database handle it held. They now
live in :class:`ArangoCalendarSourceRepository`, moved verbatim, and the question
this module answers is whether every arm survived the move — which only a real
server can answer, because the arms are AQL text.

**Tenant scoping.** Tasks and the watering forecast are measured here with a row
of another tenant that must not come back. The other three sources (phase
timeline, maintenance logs, watering logs) had no tenant predicate until #1704;
their two-tenant isolation is measured in ``test_calendar_tenant_isolation.py``,
and this module keeps measuring their window and join behaviour.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.calendar_source_repository import ArangoCalendarSourceRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("calendar_source_repository")
CALLER_TENANT = "tenant-alice"
FOREIGN_TENANT = "tenant-bob"
START = "2026-03-01T00:00:00+00:00"
END = "2026-03-31T23:59:59+00:00"

_DOCUMENT_COLLECTIONS = (
    col.TASKS,
    col.PLANT_INSTANCES,
    col.PHASE_HISTORIES,
    col.GROWTH_PHASES,
    col.LIFECYCLE_CONFIGS,
    col.PLANTING_RUNS,
    col.SPECIES,
    col.TANKS,
    col.MAINTENANCE_LOGS,
    col.WATERING_LOGS,
    col.CARE_PROFILES,
    col.CARE_CONFIRMATIONS,
    col.CULTIVARS,
    col.NUTRIENT_PLANS,
    col.NUTRIENT_PLAN_PHASE_ENTRIES,
    col.FERTILIZERS,
)
_EDGE_COLLECTIONS = (col.RUN_CONTAINS, col.HAS_LIFECYCLE, col.CONSISTS_OF, col.FOLLOWS_PLAN)


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in _DOCUMENT_COLLECTIONS:
        db.create_collection(name)
    for name in _EDGE_COLLECTIONS:
        db.create_collection(name, edge=True)

    yield db

    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    for name in database.collections():
        if not name["system"]:
            database.collection(name["name"]).truncate()
    return database


def _plant_with_lifecycle(db, key: str, tenant_key: str) -> None:
    """A live plant whose species reaches one growth phase via the legacy lifecycle path."""
    db.collection(col.SPECIES).insert({"_key": f"sp-{key}"})
    db.collection(col.LIFECYCLE_CONFIGS).insert({"_key": f"lc-{key}"})
    db.collection(col.GROWTH_PHASES).insert({"_key": f"gp-{key}", "name": "vegetative", "sequence_order": 1})
    db.collection(col.HAS_LIFECYCLE).insert(
        {"_from": f"{col.SPECIES}/sp-{key}", "_to": f"{col.LIFECYCLE_CONFIGS}/lc-{key}"}
    )
    db.collection(col.CONSISTS_OF).insert(
        {"_from": f"{col.LIFECYCLE_CONFIGS}/lc-{key}", "_to": f"{col.GROWTH_PHASES}/gp-{key}"}
    )
    db.collection(col.PLANT_INSTANCES).insert(
        {
            "_key": key,
            "instance_id": key,
            "species_key": f"sp-{key}",
            "tenant_key": tenant_key,
            "current_phase_key": f"gp-{key}",
            "removed_on": None,
        }
    )


class TestTasksDue:
    def test_another_tenants_task_is_not_returned(self, db) -> None:
        tasks = db.collection(col.TASKS)
        tasks.insert({"_key": "t-own", "tenant_key": CALLER_TENANT, "due_date": "2026-03-10T00:00:00+00:00"})
        tasks.insert({"_key": "t-foreign", "tenant_key": FOREIGN_TENANT, "due_date": "2026-03-10T00:00:00+00:00"})
        tasks.insert({"_key": "t-outside", "tenant_key": CALLER_TENANT, "due_date": "2026-04-10T00:00:00+00:00"})
        tasks.insert({"_key": "t-undated", "tenant_key": CALLER_TENANT, "due_date": None})

        rows = ArangoCalendarSourceRepository(db).list_tasks_due(START, END, tenant_key=CALLER_TENANT)

        assert [row["_key"] for row in rows] == ["t-own"]


class TestWateringForecastRows:
    def test_another_tenants_plant_is_not_returned(self, db) -> None:
        for key, tenant in (("p-own", CALLER_TENANT), ("p-foreign", FOREIGN_TENANT)):
            _plant_with_lifecycle(db, key, tenant)
            db.collection(col.CARE_PROFILES).insert({"plant_key": key, "watering_interval_days": 3})

        rows = ArangoCalendarSourceRepository(db).list_watering_forecast_rows(tenant_key=CALLER_TENANT)

        assert [row["plant_key"] for row in rows] == ["p-own"]
        assert [gp["name"] for gp in rows[0]["growth_phases"]] == ["vegetative"]
        assert rows[0]["care_profile"]["watering_interval_days"] == 3

    def test_a_plant_without_a_care_profile_is_not_returned(self, db) -> None:
        _plant_with_lifecycle(db, "p-bare", CALLER_TENANT)

        assert ArangoCalendarSourceRepository(db).list_watering_forecast_rows(tenant_key=CALLER_TENANT) == []


class TestWindowAndJoinBehaviour:
    """Window and join behaviour of the three sources #1704 scoped — isolation lives elsewhere."""

    def test_phase_timeline_reaches_the_lifecycle_phases_and_skips_removed_plants(self, db) -> None:
        _plant_with_lifecycle(db, "p-live", CALLER_TENANT)
        _plant_with_lifecycle(db, "p-gone", CALLER_TENANT)
        db.collection(col.PLANT_INSTANCES).update({"_key": "p-gone", "removed_on": "2026-02-01"})
        db.collection(col.PHASE_HISTORIES).insert({"plant_instance_key": "p-live", "phase_name": "vegetative"})

        rows = ArangoCalendarSourceRepository(db).list_phase_timeline_rows(tenant_key=CALLER_TENANT)

        assert [row["plant_key"] for row in rows] == ["p-live"]
        assert rows[0]["current_phase"] == "vegetative"
        assert len(rows[0]["phase_histories"]) == 1

    def test_maintenance_logs_are_windowed(self, db) -> None:
        db.collection(col.TANKS).insert({"_key": "tank-1", "tenant_key": CALLER_TENANT})
        logs = db.collection(col.MAINTENANCE_LOGS)
        logs.insert({"_key": "m-in", "tank_key": "tank-1", "performed_at": "2026-03-15T10:00:00+00:00"})
        logs.insert({"_key": "m-out", "tank_key": "tank-1", "performed_at": "2026-02-15T10:00:00+00:00"})

        rows = ArangoCalendarSourceRepository(db).list_maintenance_logs(START, END, tenant_key=CALLER_TENANT)

        assert [row["_key"] for row in rows] == ["m-in"]

    def test_watering_logs_are_windowed_and_resolve_plant_names(self, db) -> None:
        db.collection(col.PLANT_INSTANCES).insert({"_key": "p1", "plant_name": "Tomate", "tenant_key": CALLER_TENANT})
        logs = db.collection(col.WATERING_LOGS)
        logs.insert(
            {
                "_key": "w-in",
                "tenant_key": CALLER_TENANT,
                "logged_at": "2026-03-05T09:00:00+00:00",
                "plant_keys": ["p1", "p-missing"],
            }
        )
        logs.insert(
            {
                "_key": "w-out",
                "tenant_key": CALLER_TENANT,
                "logged_at": "2026-04-05T09:00:00+00:00",
                "plant_keys": ["p1"],
            }
        )

        rows = ArangoCalendarSourceRepository(db).list_watering_logs(START, END, tenant_key=CALLER_TENANT)

        assert [row["_key"] for row in rows] == ["w-in"]
        assert rows[0]["resolved_plant_names"] == ["Tomate"]


class TestFertilizerProductNames:
    def test_missing_keys_are_omitted_and_a_nameless_row_falls_back_to_its_key(self, db) -> None:
        fertilizers = db.collection(col.FERTILIZERS)
        fertilizers.insert({"_key": "f-named", "product_name": "Grow A"})
        fertilizers.insert({"_key": "f-nameless"})

        names = ArangoCalendarSourceRepository(db).get_fertilizer_product_names(
            ["f-named", "f-nameless", "f-ghost"], tenant_key="t1"
        )

        assert names == {"f-named": "Grow A", "f-nameless": "f-nameless"}

    def test_a_foreign_private_fertilizer_is_omitted_and_an_own_one_kept(self, db) -> None:
        """#1708: the name lookup follows the catalogue's own ∪ global union."""
        fertilizers = db.collection(col.FERTILIZERS)
        fertilizers.insert({"_key": "f-own", "tenant_key": "t1", "product_name": "Own Blend"})
        fertilizers.insert({"_key": "f-global", "tenant_key": "", "product_name": "Global Grow"})
        fertilizers.insert({"_key": "f-foreign", "tenant_key": "t2", "product_name": "Secret Blend"})

        names = ArangoCalendarSourceRepository(db).get_fertilizer_product_names(
            ["f-own", "f-global", "f-foreign"], tenant_key="t1"
        )

        assert names == {"f-own": "Own Blend", "f-global": "Global Grow"}
