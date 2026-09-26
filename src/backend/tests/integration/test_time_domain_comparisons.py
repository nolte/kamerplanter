"""#1798 #1799 #1801 #1802 #1809 — time values compared and sorted in their own domain, against ArangoDB.

The companion of ``test_window_instant_comparisons.py`` and
``test_retention_instant_comparisons.py`` (#1784), for the neighbours that
bundle left out. Each case is built so the old query answers differently:

* **Karenz (#1798)** — ``DATE_ADD(…)`` returns a string, ``DATE_NOW()`` a number,
  and AQL orders every string above every number: an ended waiting period was
  listed as active.
* **Crop-rotation history (#1799)** — ``planted_on`` is a ``date``; compared with
  a datetime string (``…T00:00:00+00:00``) a planting *on* the cutoff day
  collated before it and fell out. The cutoff computation also raised on
  29 February.
* **Latest pick (#1801)** — ``SORT s.recorded_at DESC LIMIT 1`` over the same
  second spelled twice (``…:00.5Z`` vs ``…:00+00:00``) picked the earlier one.
* **Inclusive end date (#1802)** — a date-only ``end_date`` read as midnight
  and excluded every fill on that day.
* **Index reach (#1809)** — the retention sweeps compare instants *and* still
  reach the persistent index on the swept field.

No personal data: every value is synthetic.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from arango import ArangoClient
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango import plant_instance_repository as plant_instance_module
from app.data_access.arango.ipm_repository import ArangoIpmRepository
from app.data_access.arango.mcp_repository import ArangoMcpAuditRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.query_builder import AQLBuilder
from app.data_access.arango.tank_repository import ArangoTankRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("time_domain")
TENANT = "tenant-time"

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database: StandardDatabase) -> StandardDatabase:
    for collection in database.collections():
        if not collection["system"]:
            database.collection(collection["name"]).truncate()
    return database


# ── #1798 Karenz ──────────────────────────────────────────────────────────────


def test_only_a_running_karenz_period_is_listed_as_active(db: StandardDatabase) -> None:
    now = datetime.now(UTC)
    db.collection(col.TREATMENTS).insert_many(
        [
            {"_key": "t7", "name": "Seven", "active_ingredient": "A", "safety_interval_days": 7},
        ]
    )
    db.collection(col.TREATMENT_APPLICATIONS).insert_many(
        [
            {
                "_key": "ended",
                "plant_key": "p1",
                "treatment_key": "t7",
                "applied_at": (now - timedelta(days=30)).isoformat(),
            },
            {
                "_key": "running",
                "plant_key": "p1",
                "treatment_key": "t7",
                "applied_at": (now - timedelta(days=1)).isoformat(),
            },
        ]
    )

    periods = ArangoIpmRepository(db).get_active_karenz_periods("p1")

    assert [p["applied_at"] for p in periods] == [(now - timedelta(days=1)).isoformat()]


# ── #1799 crop-rotation history ───────────────────────────────────────────────


def _plant(db: StandardDatabase, key: str, planted_on: date) -> None:
    db.collection(col.PLANT_INSTANCES).insert(
        {
            "_key": key,
            "tenant_key": TENANT,
            "instance_id": key,
            "species_key": "s1",
            "slot_key": "slot1",
            "planted_on": planted_on.isoformat(),
        }
    )
    db.collection(col.PLACED_IN).insert({"_from": f"{col.PLANT_INSTANCES}/{key}", "_to": f"{col.SLOTS}/slot1"})


@pytest.fixture
def slot(db: StandardDatabase) -> StandardDatabase:
    db.collection(col.SLOTS).insert({"_key": "slot1", "tenant_key": TENANT})
    return db


def test_a_planting_on_the_cutoff_day_is_part_of_the_rotation_history(
    slot: StandardDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(plant_instance_module, "today_utc", lambda: date(2026, 9, 26))
    _plant(slot, "on-cutoff", date(2023, 9, 26))
    _plant(slot, "day-before", date(2023, 9, 25))

    history = ArangoPlantInstanceRepository(slot).get_history_by_slot("slot1", years=3, tenant_key=TENANT)

    assert [p.key for p in history] == ["on-cutoff"]


def test_the_rotation_history_on_29_february_counts_back_to_28_february(
    slot: StandardDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(plant_instance_module, "today_utc", lambda: date(2028, 2, 29))
    _plant(slot, "feb-28", date(2025, 2, 28))
    _plant(slot, "feb-27", date(2025, 2, 27))

    history = ArangoPlantInstanceRepository(slot).get_history_by_slot("slot1", years=3, tenant_key=TENANT)

    assert [p.key for p in history] == ["feb-28"]


# ── #1801 latest pick ─────────────────────────────────────────────────────────


def test_the_latest_tank_state_is_the_later_instant_not_the_later_spelling(db: StandardDatabase) -> None:
    db.collection(col.TANKS).insert({"_key": "tank1", "tenant_key": TENANT, "low_threshold_percent": 20})
    db.collection(col.TANK_STATES).insert_many(
        [
            # Half a second earlier, spelled with an offset: collates *after* the fraction.
            {"tank_key": "tank1", "recorded_at": "2025-09-25T10:00:00+00:00", "fill_level_percent": 5},
            {"tank_key": "tank1", "recorded_at": "2025-09-25T10:00:00.5Z", "fill_level_percent": 90},
        ]
    )

    assert ArangoTankRepository(db).count_below_threshold(TENANT) == 0


def test_a_builder_sort_on_a_timestamp_orders_instants(db: StandardDatabase) -> None:
    db.collection(col.TANK_STATES).insert_many(
        [
            {"_key": "earlier", "recorded_at": "2025-09-25T10:00:00+00:00"},
            {"_key": "later", "recorded_at": "2025-09-25T10:00:00.5Z"},
        ]
    )
    query, bind_vars = AQLBuilder(col.TANK_STATES).sort("recorded_at", "DESC").build_list()

    assert [d["_key"] for d in db.aql.execute(query, bind_vars=bind_vars)] == ["later", "earlier"]


# ── #1802 inclusive end date ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("end_date", "expected"),
    [
        pytest.param("2025-09-25", 2, id="a-date-includes-the-whole-day"),
        pytest.param("2025-09-25T12:00:00+00:00", 1, id="an-instant-is-an-inclusive-instant"),
        pytest.param("2025-09-24", 0, id="the-day-before-includes-none"),
    ],
)
def test_the_fill_stats_end_date_is_inclusive(db: StandardDatabase, end_date: str, expected: int) -> None:
    db.collection(col.TANK_FILL_EVENTS).insert_many(
        [
            {"tank_key": "tank1", "filled_at": "2025-09-25T08:00:00Z", "fill_type": "full_change", "volume_liters": 10},
            {"tank_key": "tank1", "filled_at": "2025-09-25T23:30:00.5Z", "fill_type": "top_up", "volume_liters": 2},
            {"tank_key": "tank1", "filled_at": "2025-09-26T00:00:00Z", "fill_type": "top_up", "volume_liters": 3},
        ]
    )

    stats = ArangoTankRepository(db).get_fill_event_stats("tank1", "2025-09-25", end_date)

    assert stats["total_count"] == expected


# ── #1809 index reach ─────────────────────────────────────────────────────────


def test_the_audit_sweep_reaches_the_created_at_index_and_still_compares_instants(
    db: StandardDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime(2025, 9, 25, 4, 30, tzinfo=UTC)
    cutoff = now - timedelta(days=90)
    audit = db.collection(col.MCP_AUDIT_LOG)
    # 0.5 s after the cutoff with a fraction (collates *before* the ``+00:00`` cutoff), and
    # 0.5 s before it spelled with an offset — the instant decides, not the text.
    audit.insert_many(
        [
            {"_key": "young", "created_at": (cutoff + timedelta(milliseconds=500)).isoformat().replace("+00:00", "Z")},
            {"_key": "old", "created_at": (cutoff - timedelta(milliseconds=500)).isoformat()},
            {"_key": "undated", "created_at": None},
        ]
    )
    seen: list[tuple[str, dict]] = []
    aql_class = type(db.aql)  # ``db.aql`` is a fresh wrapper per access: spy on the class
    execute = aql_class.execute

    def spy(self, query: str, bind_vars: dict | None = None, **kwargs):
        seen.append((query, bind_vars or {}))
        return execute(self, query, bind_vars=bind_vars, **kwargs)

    monkeypatch.setattr(aql_class, "execute", spy)

    removed = ArangoMcpAuditRepository(db).delete_expired(retention_days=90, now=now)

    assert removed == 1
    assert sorted(d["_key"] for d in audit.all()) == ["undated", "young"]
    ((query, bind_vars),) = seen
    plan = db.aql.explain(query, bind_vars=bind_vars)
    index_fields = [i["fields"] for n in plan["nodes"] if n["type"] == "IndexNode" for i in n["indexes"]]
    assert ["created_at"] in index_fields, plan["nodes"]
