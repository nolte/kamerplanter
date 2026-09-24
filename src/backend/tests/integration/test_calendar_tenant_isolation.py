"""#1704 — the aggregated calendar shows the requesting tenant's rows and nobody else's.

Three of the five calendar sources carried no tenant predicate: the phase
timeline (every active plant instance), tank maintenance logs and watering logs.
Their rows went straight into ``CalendarAggregationEngine.aggregate``, so a
member of one tenant read another tenant's plant names, phases, tank maintenance
and watering events in ``/t/{slug}/calendar/events`` and in the tokenised iCal
export.

The ownership each predicate hangs on was measured, not assumed:

* **Phase timeline** — ``plant_instances.tenant_key``, stamped on every create.
* **Maintenance logs** — ``MaintenanceLog`` has *no* ``tenant_key``. The log
  belongs to its tank (``maintenance_logs.tank_key``), and ``Tank`` carries
  ``tenant_key`` itself, stamped by the tank router from the request context.
  The tank's location is not needed and would be the wrong anchor: ``Location``
  carries no ``tenant_key``.
* **Watering logs** — ``WateringLog.tenant_key``, stamped by all three creators
  (router, watering-log service, care-reminder confirmation) and backfilled by
  migration ``v0020``.

Each check runs the production path — the real repository against a real server,
behind the real service, and for the API check behind the real route — and each
is paired with the tenant's **own** row so a calendar that returns nothing at all
cannot pass.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from arango import ArangoClient

from app.common.datetimes import today_utc
from app.data_access.arango import collections as col
from app.data_access.arango.calendar_feed_repository import ArangoCalendarFeedRepository
from app.data_access.arango.calendar_source_repository import ArangoCalendarSourceRepository
from app.domain.engines.calendar_aggregation_engine import CalendarAggregationEngine
from app.domain.models.calendar import CalendarEventsQuery, CalendarFeed
from app.domain.services.calendar_service import CalendarService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("calendar_tenant_isolation")
TENANT_A = "tenant-alice"
TENANT_B = "tenant-bob"
SLUG_A = "alice"

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
    col.CALENDAR_FEEDS,
)
_EDGE_COLLECTIONS = (col.RUN_CONTAINS, col.HAS_LIFECYCLE, col.CONSISTS_OF, col.FOLLOWS_PLAN)

#: Per tenant, the id each source's event carries and a name only that tenant owns.
_SEED = {
    TENANT_A: {"suffix": "a", "plant_name": "Alice Tomato", "tank_action": "Alice reservoir flush"},
    TENANT_B: {"suffix": "b", "plant_name": "Bob Hemp", "tank_action": "Bob reservoir flush"},
}


def _event_ids(tenant: str) -> dict[str, str]:
    s = _SEED[tenant]["suffix"]
    return {
        "phase_timeline": f"phase:plant-{s}:gp-{s}",
        "maintenance_log": f"maint:maint-{s}",
        "watering_log": f"water:water-{s}",
    }


def _iso(day_offset: int) -> str:
    return f"{(today_utc() + timedelta(days=day_offset)).isoformat()}T12:00:00+00:00"


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


def _seed_tenant(db, tenant: str) -> None:
    """One row per unscoped source: a plant in its current phase, a tank log, a watering log."""
    s = _SEED[tenant]["suffix"]
    db.collection(col.SPECIES).insert({"_key": f"sp-{s}"})
    db.collection(col.LIFECYCLE_CONFIGS).insert({"_key": f"lc-{s}"})
    db.collection(col.GROWTH_PHASES).insert(
        {"_key": f"gp-{s}", "name": "vegetative", "sequence_order": 1, "typical_duration_days": 14}
    )
    db.collection(col.HAS_LIFECYCLE).insert(
        {"_from": f"{col.SPECIES}/sp-{s}", "_to": f"{col.LIFECYCLE_CONFIGS}/lc-{s}"}
    )
    db.collection(col.CONSISTS_OF).insert(
        {"_from": f"{col.LIFECYCLE_CONFIGS}/lc-{s}", "_to": f"{col.GROWTH_PHASES}/gp-{s}"}
    )
    db.collection(col.PLANT_INSTANCES).insert(
        {
            "_key": f"plant-{s}",
            "instance_id": f"PI-{s}",
            "plant_name": _SEED[tenant]["plant_name"],
            "species_key": f"sp-{s}",
            "tenant_key": tenant,
            "current_phase_key": f"gp-{s}",
            "removed_on": None,
        }
    )
    db.collection(col.PHASE_HISTORIES).insert(
        {"plant_instance_key": f"plant-{s}", "phase_name": "vegetative", "entered_at": _iso(-2), "exited_at": None}
    )
    # The tank carries the tenant; the maintenance log only names its tank —
    # exactly the shape the tank router writes.
    db.collection(col.TANKS).insert({"_key": f"tank-{s}", "tenant_key": tenant, "name": f"Tank {s}"})
    db.collection(col.MAINTENANCE_LOGS).insert(
        {"_key": f"maint-{s}", "tank_key": f"tank-{s}", "action": _SEED[tenant]["tank_action"], "performed_at": _iso(0)}
    )
    db.collection(col.WATERING_LOGS).insert(
        {"_key": f"water-{s}", "tenant_key": tenant, "logged_at": _iso(0), "plant_keys": [f"plant-{s}"]}
    )


@pytest.fixture
def db(database):
    for name in database.collections():
        if not name["system"]:
            database.collection(name["name"]).truncate()
    _seed_tenant(database, TENANT_A)
    _seed_tenant(database, TENANT_B)
    return database


def _service(db) -> CalendarService:
    return CalendarService(
        ArangoCalendarFeedRepository(db),
        CalendarAggregationEngine(),
        ArangoCalendarSourceRepository(db),
    )


def _query(tenant: str) -> CalendarEventsQuery:
    today = today_utc()
    return CalendarEventsQuery(
        start_date=today - timedelta(days=5), end_date=today + timedelta(days=5), tenant_key=tenant
    )


SOURCES = ("phase_timeline", "maintenance_log", "watering_log")


class TestTheServiceScopesEverySource:
    @pytest.mark.parametrize("source", SOURCES)
    @pytest.mark.parametrize(("caller", "other"), [(TENANT_A, TENANT_B), (TENANT_B, TENANT_A)])
    def test_the_other_tenants_row_is_absent_and_the_own_row_present(self, db, source, caller, other) -> None:
        ids = {event.id for event in _service(db).get_events(_query(caller))}

        assert _event_ids(caller)[source] in ids, f"own {source} row missing: {sorted(ids)}"
        assert _event_ids(other)[source] not in ids, f"foreign {source} row leaked: {sorted(ids)}"

    def test_no_foreign_name_reaches_any_event(self, db) -> None:
        events = _service(db).get_events(_query(TENANT_A))
        text = " ".join(f"{e.title} {e.metadata}" for e in events)

        assert _SEED[TENANT_A]["plant_name"] in text
        assert _SEED[TENANT_A]["tank_action"] in text
        assert _SEED[TENANT_B]["plant_name"] not in text
        assert _SEED[TENANT_B]["tank_action"] not in text


class TestTheIcalFeedIsScopedToTheFeedsTenant:
    """The token-authenticated export builds its query from ``feed.tenant_key``."""

    def test_the_feed_exports_its_tenants_events_only(self, db) -> None:
        repo = ArangoCalendarFeedRepository(db)
        feed = repo.save(CalendarFeed(name="Alice feed", tenant_key=TENANT_A, user_key="user-a", token="tok-alice"))

        ics = _service(db).generate_ical_for_feed(feed.key, "tok-alice")

        assert _SEED[TENANT_A]["plant_name"] in ics
        assert _SEED[TENANT_A]["tank_action"] in ics
        assert _SEED[TENANT_B]["plant_name"] not in ics
        assert _SEED[TENANT_B]["tank_action"] not in ics


class TestTheRouteIsScopedToTheCallersTenant:
    """``GET /t/{slug}/calendar/events`` end to end, with only auth and the service factory bound."""

    @pytest.fixture
    def client(self, db):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from app.api.v1.tenant_scoped.router import tenant_scoped_router
        from app.common.auth import get_current_tenant
        from app.common.enums import TenantRole
        from app.domain.models.tenant_context import TenantContext

        app = FastAPI()
        app.include_router(tenant_scoped_router, prefix="/api/v1")
        app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
            tenant_key=TENANT_A, tenant_slug=SLUG_A, user_key="user-a", role=TenantRole.VIEWER
        )
        with patch("app.api.v1.calendar.tenant_router.get_calendar_service", lambda: _service(db)):
            yield TestClient(app, raise_server_exceptions=False)

    def test_the_response_carries_no_foreign_row(self, client) -> None:
        query = _query(TENANT_A)
        response = client.get(
            f"/api/v1/t/{SLUG_A}/calendar/events",
            params={"start": query.start_date.isoformat(), "end": query.end_date.isoformat()},
        )

        assert response.status_code == 200, response.text
        ids = {event["id"] for event in response.json()["events"]}
        for source in SOURCES:
            assert _event_ids(TENANT_A)[source] in ids, f"own {source} row missing: {sorted(ids)}"
            assert _event_ids(TENANT_B)[source] not in ids, f"foreign {source} row leaked: {sorted(ids)}"


class TestTheRepositoryPredicates:
    """The anchors themselves, one level below the service."""

    def _window(self) -> tuple[str, str]:
        return _iso(-5), _iso(5)

    def test_a_maintenance_log_of_an_unknown_tank_belongs_to_nobody(self, db) -> None:
        db.collection(col.MAINTENANCE_LOGS).insert(
            {"_key": "maint-orphan", "tank_key": "tank-gone", "performed_at": _iso(0)}
        )

        rows = ArangoCalendarSourceRepository(db).list_maintenance_logs(*self._window(), tenant_key=TENANT_A)

        assert [row["_key"] for row in rows] == ["maint-a"]

    def test_a_watering_log_resolves_only_its_own_tenants_plant_names(self, db) -> None:
        db.collection(col.WATERING_LOGS).insert(
            {"_key": "water-mixed", "tenant_key": TENANT_A, "logged_at": _iso(1), "plant_keys": ["plant-a", "plant-b"]}
        )

        rows = ArangoCalendarSourceRepository(db).list_watering_logs(*self._window(), tenant_key=TENANT_A)

        by_key = {row["_key"]: row for row in rows}
        assert set(by_key) == {"water-a", "water-mixed"}
        assert by_key["water-mixed"]["resolved_plant_names"] == [_SEED[TENANT_A]["plant_name"]]

    def test_the_phase_timeline_returns_the_tenants_plants_only(self, db) -> None:
        rows = ArangoCalendarSourceRepository(db).list_phase_timeline_rows(tenant_key=TENANT_A)

        assert [row["plant_key"] for row in rows] == ["plant-a"]
