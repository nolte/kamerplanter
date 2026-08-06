"""Cross-tenant reads on key-anchored endpoints (#927).

The defect shape #927 catalogues: the endpoint resolves its *anchor* — a run, a
location — against the tenant, but the key that actually selects the rows
(``plant_key``, ``location_key``, ``entity_key``) is passed through unchecked,
**and** the repository query behind it carries no ``tenant_key`` filter either.
Neither layer holds, so a member of tenant A supplies a key belonging to tenant B
and reads tenant B's records.

Every test below is an **end-to-end API test**: the real router, the real
service and the real ArangoDB repository, on a database double that replays
whichever predicates the emitted query actually spells out
(:mod:`tests.support.tenant_replay`). Delete the ``tenant_key`` predicate from a
repository and the corresponding "…is not readable…" test goes red, because the
fake then hands the foreign row back the way ArangoDB would. That is the point:
a cross-tenant test that only exercises the happy path proves nothing.

Each endpoint gets **both** directions:

* the negative case — a foreign key must return nothing (and, where the endpoint
  aggregates, must not report the foreign count/volume either);
* the positive case — the caller's own data still comes back. A strict tenant
  filter that also hides legitimate rows is the #324 regression class, and the
  two together are what pin the boundary.

**404 vs 403.** These are list/aggregate endpoints: a foreign key yields an empty
list or a zeroed aggregate, which is indistinguishable from "no such thing" and
therefore discloses nothing. Where a single record *is* addressed by key
(``…/tasks/{key}/comments``) the answer is 404 with the generic
``ENTITY_NOT_FOUND`` envelope — never 403, which would confirm that the record
exists in someone else's tenant.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.feeding_events.tenant_router import router as feeding_router
from app.api.v1.harvest.tenant_router import router as harvest_router
from app.api.v1.tasks.tenant_router import router as tasks_router
from app.api.v1.watering_events.tenant_router import router as watering_events_router
from app.api.v1.watering_logs.tenant_router import router as watering_logs_router
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_feeding_service,
    get_harvest_service,
    get_task_service,
    get_watering_log_service,
    get_watering_service,
)
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.feeding_repository import ArangoFeedingRepository
from app.data_access.arango.harvest_repository import ArangoHarvestRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.data_access.arango.watering_log_repository import ArangoWateringLogRepository
from app.data_access.arango.watering_repository import ArangoWateringRepository
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.watering_engine import WateringEngine
from app.domain.models.tenant_context import TenantContext
from app.domain.services.feeding_service import FeedingService
from app.domain.services.harvest_service import HarvestService
from app.domain.services.task_service import TaskService
from app.domain.services.watering_log_service import WateringLogService
from app.domain.services.watering_service import WateringService
from tests.support.tenant_replay import (
    ReplayingAql,
    ReplayingDatabase,
    apply_predicates,
    paginate,
    rows_and_count,
)

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_PLANT = "plant-a1"
FOREIGN_PLANT = "plant-b1"
OWN_LOCATION = "loc-a1"
FOREIGN_LOCATION = "loc-b1"
OWN_SLOT = "slot-a1"
FOREIGN_SLOT = "slot-b1"

#: Text that must never reach a caller of the other tenant. Asserting on the raw
#: response body catches a leak that slips past a field-by-field comparison.
FOREIGN_MARKER = "geheime-fremde-notiz"


# ── Harness ──────────────────────────────────────────────────────────────────


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _client(router, dependency, service) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user-1",
        role=TenantRole.GROWER,
    )
    app.dependency_overrides[dependency] = lambda: service
    return TestClient(app)


def _url(path: str) -> str:
    return f"/api/v1/t/{TENANT_SLUG}{path}"


# ── 1–3: watering events (plant / location / location stats) ─────────────────


def _watering_events() -> list[dict[str, Any]]:
    """One event per tenant, both reachable from their own plant/slot/location."""
    return [
        {
            "_key": "we-a",
            "_id": f"{col.WATERING_EVENTS}/we-a",
            "tenant_key": TENANT_KEY,
            "plant_keys": [OWN_PLANT],
            "watered_at": "2026-08-01T08:00:00+00:00",
            "volume_liters": 2.0,
            "application_method": "drench",
        },
        {
            "_key": "we-b",
            "_id": f"{col.WATERING_EVENTS}/we-b",
            "tenant_key": FOREIGN_TENANT_KEY,
            "plant_keys": [FOREIGN_PLANT],
            "watered_at": "2026-08-02T08:00:00+00:00",
            "volume_liters": 99.0,
            "application_method": "drench",
            "notes": FOREIGN_MARKER,
        },
    ]


def _watering_client() -> TestClient:
    """Real router → real service → real repository, on a replaying database.

    The graph is modelled by the plant/slot/location keys embedded in the
    fixtures: the ``watered_plant`` traversal selects the events whose
    ``plant_keys`` contain the plant named in the URL, the location traversal the
    events of that location's plants. Both then get exactly the predicates the
    repository query spells out — so a repository without a ``tenant_key``
    predicate returns both tenants' events here, as it did in production.
    """
    events = _watering_events()
    plant_of = {OWN_PLANT: (OWN_SLOT, OWN_LOCATION), FOREIGN_PLANT: (FOREIGN_SLOT, FOREIGN_LOCATION)}

    def by_plant(query: str, bind_vars: dict[str, Any]) -> Any:
        plant_key = str(bind_vars["plant_id"]).split("/")[-1]
        rows = [e for e in events if plant_key in e["plant_keys"]]
        return paginate(apply_predicates(rows, query, bind_vars), query, bind_vars)

    def by_location(query: str, bind_vars: dict[str, Any]) -> Any:
        location_key = str(bind_vars["location_id"]).split("/")[-1]
        rows = [e for e in events if plant_of[e["plant_keys"][0]][1] == location_key]
        return paginate(apply_predicates(rows, query, bind_vars), query, bind_vars)

    def stats_by_location(query: str, bind_vars: dict[str, Any]) -> Any:
        rows = apply_predicates(by_location_rows(bind_vars), query, bind_vars)
        # ``COLLECT … AGGREGATE`` produces no group for an empty input, which is
        # exactly what the aggregate must report for a foreign location.
        by_method = (
            [{"method": "drench", "count": len(rows), "total_volume": sum(r["volume_liters"] for r in rows)}]
            if rows
            else []
        )
        return {
            "total_events": len(rows),
            "total_volume": sum(r["volume_liters"] for r in rows),
            "by_method": by_method,
        }

    def by_location_rows(bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
        location_key = str(bind_vars["location_id"]).split("/")[-1]
        return [e for e in events if plant_of[e["plant_keys"][0]][1] == location_key]

    aql = ReplayingAql()
    # Most specific marker first: the stats query also contains ``@@has_slot``.
    aql.route("LET events = (", stats_by_location)
    aql.route("@@has_slot", by_location)
    aql.route("@@edge_col", by_plant)

    repo = ArangoWateringRepository(ReplayingDatabase(aql))
    service = WateringService(repo, WateringEngine(), MagicMock())
    return _client(watering_events_router, get_watering_service, service)


class TestWateringEventsOfAPlant:
    """``GET /t/{slug}/plant-instances/{plant_key}/watering-events`` (#927)."""

    def test_a_foreign_plant_key_returns_nothing(self):
        client = _watering_client()

        resp = client.get(_url(f"/plant-instances/{FOREIGN_PLANT}/watering-events"))

        assert resp.status_code == 200, resp.text
        assert resp.json() == []
        assert FOREIGN_MARKER not in resp.text

    def test_the_callers_own_plant_still_returns_its_events(self):
        client = _watering_client()

        resp = client.get(_url(f"/plant-instances/{OWN_PLANT}/watering-events"))

        assert resp.status_code == 200, resp.text
        assert [e["key"] for e in resp.json()] == ["we-a"]


class TestWateringEventsOfALocation:
    """``GET /t/{slug}/locations/{location_key}/watering-events`` (#927)."""

    def test_a_foreign_location_key_returns_nothing(self):
        client = _watering_client()

        resp = client.get(_url(f"/locations/{FOREIGN_LOCATION}/watering-events"))

        assert resp.status_code == 200, resp.text
        assert resp.json() == []
        assert FOREIGN_MARKER not in resp.text

    def test_the_callers_own_location_still_returns_its_events(self):
        client = _watering_client()

        resp = client.get(_url(f"/locations/{OWN_LOCATION}/watering-events"))

        assert resp.status_code == 200, resp.text
        assert [e["key"] for e in resp.json()] == ["we-a"]


class TestWateringStatsOfALocation:
    """``GET /t/{slug}/locations/{location_key}/watering-stats`` (#927).

    The aggregate needs the filter at least as badly as the list does: its whole
    payload is counts and sums, so an unfiltered query discloses how many events
    the other tenant recorded and how much water they applied.
    """

    def test_a_foreign_location_key_reports_zeroes_not_the_other_tenants_totals(self):
        client = _watering_client()

        resp = client.get(_url(f"/locations/{FOREIGN_LOCATION}/watering-stats"))

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total_events"] == 0
        assert body["total_volume"] == 0
        assert body["by_method"] == []

    def test_the_callers_own_location_still_reports_its_totals(self):
        client = _watering_client()

        resp = client.get(_url(f"/locations/{OWN_LOCATION}/watering-stats"))

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total_events"] == 1
        assert body["total_volume"] == 2.0


# ── 4: tasks of a plant ──────────────────────────────────────────────────────


def _tasks() -> list[dict[str, Any]]:
    return [
        {
            "_key": "task-a",
            "_id": f"{col.TASKS}/task-a",
            "tenant_key": TENANT_KEY,
            "name": "Tomaten giessen",
            "entity_type": "plant_instance",
            "entity_key": OWN_PLANT,
            "status": "pending",
            "due_date": "2026-08-03T06:00:00+00:00",
        },
        {
            "_key": "task-b",
            "_id": f"{col.TASKS}/task-b",
            "tenant_key": FOREIGN_TENANT_KEY,
            "name": FOREIGN_MARKER,
            "entity_type": "plant_instance",
            "entity_key": FOREIGN_PLANT,
            "status": "pending",
            "due_date": "2026-08-04T06:00:00+00:00",
        },
    ]


def _task_client(tasks: list[dict[str, Any]] | None = None) -> TestClient:
    rows = tasks if tasks is not None else _tasks()

    aql = ReplayingAql()
    # Dependency resolution for the queue — no tenant dimension, no blockers.
    aql.route("FOR e IN task_blocks", lambda q, b: [])
    aql.route("FOR doc IN tasks", lambda q, b: rows_and_count(rows, q, b))

    repo = ArangoTaskRepository(ReplayingDatabase(aql))
    # The real dependency resolver: the queue filters its result through it, and a
    # MagicMock would return an empty set and mask what the query returned.
    service = TaskService(repo, MagicMock(), DependencyResolver())
    return _client(tasks_router, get_task_service, service)


class TestTasksOfAPlant:
    """``GET /t/{slug}/tasks/plants/{plant_key}`` (#927).

    ``get_tasks_for_plant`` selected on ``entity_key`` alone while its
    tenant-aware twin ``get_tasks_for_entity`` sat directly below it and did the
    same job correctly.
    """

    def test_a_foreign_plant_key_returns_no_tasks(self):
        client = _task_client()

        resp = client.get(_url(f"/tasks/plants/{FOREIGN_PLANT}"))

        assert resp.status_code == 200, resp.text
        assert resp.json() == []
        assert FOREIGN_MARKER not in resp.text

    def test_the_callers_own_plant_still_returns_its_tasks(self):
        client = _task_client()

        resp = client.get(_url(f"/tasks/plants/{OWN_PLANT}"))

        assert resp.status_code == 200, resp.text
        assert [t["key"] for t in resp.json()] == ["task-a"]

    def test_a_status_filter_does_not_widen_the_tenant_scope(self):
        """The optional ``status`` filter is an *extra* predicate, never a swap."""
        client = _task_client()

        resp = client.get(_url(f"/tasks/plants/{FOREIGN_PLANT}"), params={"status": "pending"})

        assert resp.status_code == 200, resp.text
        assert resp.json() == []


class TestTaskQueueAndOverdue:
    """``/tasks/queue`` and ``/tasks/overdue`` — found alongside the five (#927).

    Neither needed a foreign key: they selected on status alone and therefore
    listed *every* tenant's tasks to any authenticated member.
    """

    def test_the_queue_lists_only_the_callers_tenant(self):
        client = _task_client()

        resp = client.get(_url("/tasks/queue"))

        assert resp.status_code == 200, resp.text
        assert [t["key"] for t in resp.json()] == ["task-a"]
        assert FOREIGN_MARKER not in resp.text

    def test_the_overdue_list_reports_only_the_callers_tenant(self):
        # Both tasks are pending and long overdue relative to "now".
        overdue = [{**t, "due_date": "2020-01-01T00:00:00+00:00"} for t in _tasks()]
        client = _task_client(overdue)

        resp = client.get(_url("/tasks/overdue"))

        assert resp.status_code == 200, resp.text
        assert [t["key"] for t in resp.json()] == ["task-a"]
        assert FOREIGN_MARKER not in resp.text


class TestTaskComments:
    """``GET /t/{slug}/tasks/{task_key}/comments`` — one of the nine (#927).

    ``TaskComment`` carries no tenant of its own, so the predicate is taken from
    the parent task. A foreign task key must answer **404**, not 403: a 403 would
    confirm that the task exists in someone else's tenant.
    """

    def _client(self) -> TestClient:
        tasks = {t["_key"]: t for t in _tasks()}
        comments = [
            {
                "_key": "c-a",
                "_id": f"{col.TASK_COMMENTS}/c-a",
                "task_key": "task-a",
                "comment_text": "erledigt",
                "created_at": "2026-08-01T09:00:00+00:00",
            },
            {
                "_key": "c-b",
                "_id": f"{col.TASK_COMMENTS}/c-b",
                "task_key": "task-b",
                "comment_text": FOREIGN_MARKER,
                "created_at": "2026-08-02T09:00:00+00:00",
            },
        ]

        def by_task(query: str, bind_vars: dict[str, Any]) -> Any:
            return apply_predicates(
                comments,
                query,
                bind_vars,
                resolvers={"task": lambda row: tasks.get(row["task_key"])},
            )

        aql = ReplayingAql()
        aql.route(f"FOR doc IN {col.TASK_COMMENTS}", by_task)
        aql.route("FOR doc IN tasks", lambda q, b: rows_and_count(list(tasks.values()), q, b))

        collection = MagicMock()
        collection.get.side_effect = lambda key: tasks.get(key)
        repo = ArangoTaskRepository(ReplayingDatabase(aql, {col.TASKS: collection}))
        service = TaskService(repo, MagicMock(), DependencyResolver())
        return _client(tasks_router, get_task_service, service)

    def test_a_foreign_task_key_is_not_found_rather_than_forbidden(self):
        client = self._client()

        resp = client.get(_url("/tasks/task-b/comments"))

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert FOREIGN_MARKER not in resp.text

    def test_the_callers_own_task_still_returns_its_comments(self):
        client = self._client()

        resp = client.get(_url("/tasks/task-a/comments"))

        assert resp.status_code == 200, resp.text
        assert [c["comment_text"] for c in resp.json()] == ["erledigt"]


# ── 5: feeding events of a plant ─────────────────────────────────────────────


def _feeding_client() -> TestClient:
    events = [
        {
            "_key": "fe-a",
            "_id": f"{col.FEEDING_EVENTS}/fe-a",
            "tenant_key": TENANT_KEY,
            "plant_key": OWN_PLANT,
            "timestamp": "2026-08-01T08:00:00+00:00",
            "volume_applied_liters": 1.0,
            "application_method": "drench",
        },
        {
            "_key": "fe-b",
            "_id": f"{col.FEEDING_EVENTS}/fe-b",
            "tenant_key": FOREIGN_TENANT_KEY,
            "plant_key": FOREIGN_PLANT,
            "timestamp": "2026-08-02T08:00:00+00:00",
            "volume_applied_liters": 9.0,
            "application_method": "drench",
            "notes": FOREIGN_MARKER,
        },
    ]

    aql = ReplayingAql()
    aql.route(f"FOR doc IN {col.FEEDING_EVENTS}", lambda q, b: rows_and_count(events, q, b))

    repo = ArangoFeedingRepository(ReplayingDatabase(aql))
    return _client(feeding_router, get_feeding_service, FeedingService(repo))


class TestFeedingEventsOfAPlant:
    """``GET /t/{slug}/feeding-events/plant/{pk}`` (#927)."""

    def test_a_foreign_plant_key_returns_nothing(self):
        client = _feeding_client()

        resp = client.get(_url(f"/feeding-events/plant/{FOREIGN_PLANT}"))

        assert resp.status_code == 200, resp.text
        assert resp.json() == []
        assert FOREIGN_MARKER not in resp.text

    def test_the_callers_own_plant_still_returns_its_events(self):
        client = _feeding_client()

        resp = client.get(_url(f"/feeding-events/plant/{OWN_PLANT}"))

        assert resp.status_code == 200, resp.text
        assert [e["key"] for e in resp.json()] == ["fe-a"]


# ── Beyond the five: watering *logs* by slot and by location ─────────────────


def _watering_log_client() -> TestClient:
    """#927 files these under "callers do check". They do not — see the router.

    ``GET /t/{slug}/slots/{slot_key}/watering-logs`` and
    ``…/locations/{location_key}/watering-logs`` forward the URL key without
    resolving it against the caller's tenant, so they were live cross-tenant
    reads exactly like the five named endpoints.
    """
    logs = [
        {
            "_key": "wl-a",
            "_id": f"{col.WATERING_LOGS}/wl-a",
            "tenant_key": TENANT_KEY,
            "slot_keys": [OWN_SLOT],
            "plant_keys": [OWN_PLANT],
            "logged_at": "2026-08-01T08:00:00+00:00",
            "volume_liters": 2.0,
            "application_method": "drench",
        },
        {
            "_key": "wl-b",
            "_id": f"{col.WATERING_LOGS}/wl-b",
            "tenant_key": FOREIGN_TENANT_KEY,
            "slot_keys": [FOREIGN_SLOT],
            "plant_keys": [FOREIGN_PLANT],
            "logged_at": "2026-08-02T08:00:00+00:00",
            "volume_liters": 42.0,
            "application_method": "drench",
            "notes": FOREIGN_MARKER,
        },
    ]
    location_of_slot = {OWN_SLOT: OWN_LOCATION, FOREIGN_SLOT: FOREIGN_LOCATION}

    def by_slot(query: str, bind_vars: dict[str, Any]) -> Any:
        slot_key = str(bind_vars["slot_id"]).split("/")[-1]
        rows = [log for log in logs if slot_key in log["slot_keys"]]
        return paginate(apply_predicates(rows, query, bind_vars), query, bind_vars)

    def location_rows(bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
        location_key = str(bind_vars["location_id"]).split("/")[-1]
        return [log for log in logs if location_of_slot[log["slot_keys"][0]] == location_key]

    def by_location(query: str, bind_vars: dict[str, Any]) -> Any:
        return paginate(apply_predicates(location_rows(bind_vars), query, bind_vars), query, bind_vars)

    def stats(query: str, bind_vars: dict[str, Any]) -> Any:
        rows = apply_predicates(location_rows(bind_vars), query, bind_vars)
        return {
            "total_events": len(rows),
            "total_volume": sum(r["volume_liters"] for r in rows),
            "by_method": [],
        }

    aql = ReplayingAql()
    aql.route("LET logs = (", stats)
    aql.route("@@has_slot", by_location)
    aql.route("@@edge_col", by_slot)
    # Name resolution for the response envelope — no tenant dimension.
    aql.route("FOR pk IN @plant_keys", lambda q, b: [])
    aql.route("FOR fk IN @fert_keys", lambda q, b: [])

    repo = ArangoWateringLogRepository(ReplayingDatabase(aql))
    service = WateringLogService(repo, WateringEngine(), MagicMock())
    return _client(watering_logs_router, get_watering_log_service, service)


class TestWateringLogsBySlotAndLocation:
    def test_a_foreign_slot_key_returns_nothing(self):
        client = _watering_log_client()

        resp = client.get(_url(f"/slots/{FOREIGN_SLOT}/watering-logs"))

        assert resp.status_code == 200, resp.text
        assert resp.json() == []
        assert FOREIGN_MARKER not in resp.text

    def test_the_callers_own_slot_still_returns_its_logs(self):
        client = _watering_log_client()

        resp = client.get(_url(f"/slots/{OWN_SLOT}/watering-logs"))

        assert resp.status_code == 200, resp.text
        assert [log["key"] for log in resp.json()] == ["wl-a"]

    def test_a_foreign_location_key_returns_nothing(self):
        client = _watering_log_client()

        resp = client.get(_url(f"/locations/{FOREIGN_LOCATION}/watering-logs"))

        assert resp.status_code == 200, resp.text
        assert resp.json() == []

    def test_the_callers_own_location_still_returns_its_logs(self):
        client = _watering_log_client()

        resp = client.get(_url(f"/locations/{OWN_LOCATION}/watering-logs"))

        assert resp.status_code == 200, resp.text
        assert [log["key"] for log in resp.json()] == ["wl-a"]


# ── Beyond the five: harvest observations and readiness ──────────────────────


def _harvest_client() -> TestClient:
    """#927 files ``get_latest_observations_by_indicator`` under "callers check".

    The harvest router does not resolve the plant against the tenant at all, so
    both ``…/harvest/plants/{plant_key}/observations`` and ``…/readiness`` were
    live cross-tenant reads. ``HarvestObservation`` carries no ``tenant_key``, so
    the predicate is taken from the plant it is about.
    """
    plants = {
        OWN_PLANT: {"_key": OWN_PLANT, "tenant_key": TENANT_KEY},
        FOREIGN_PLANT: {"_key": FOREIGN_PLANT, "tenant_key": FOREIGN_TENANT_KEY},
    }
    observations = [
        {
            "_key": "obs-a",
            "_id": f"{col.HARVEST_OBSERVATIONS}/obs-a",
            "plant_key": OWN_PLANT,
            "indicator_key": "trichome",
            "observed_at": "2026-08-01T08:00:00+00:00",
            "ripeness_assessment": "peak",
            "measurements": {"score": 0.9},
        },
        {
            "_key": "obs-b",
            "_id": f"{col.HARVEST_OBSERVATIONS}/obs-b",
            "plant_key": FOREIGN_PLANT,
            "indicator_key": "trichome",
            "observed_at": "2026-08-02T08:00:00+00:00",
            "ripeness_assessment": "peak",
            "notes": FOREIGN_MARKER,
            "measurements": {"score": 0.1},
        },
    ]

    def observations_query(query: str, bind_vars: dict[str, Any]) -> Any:
        rows = apply_predicates(
            observations,
            query,
            bind_vars,
            resolvers={"plant": lambda row: plants.get(row["plant_key"])},
        )
        if "COLLECT WITH COUNT" in query:
            return [len(rows)]
        if "COLLECT indicator" in query:
            # Newest per indicator — the readiness query.
            newest: dict[str, dict[str, Any]] = {}
            for row in sorted(rows, key=lambda r: r["observed_at"]):
                newest[row["indicator_key"]] = row
            return list(newest.values())
        return paginate(rows, query, bind_vars)

    aql = ReplayingAql()
    aql.route("@@observations", observations_query)
    # The readiness path also lists indicators; none are relevant to isolation.
    aql.route(f"FOR doc IN {col.HARVEST_INDICATORS}", lambda q, b: [0] if "COLLECT WITH COUNT" in q else [])

    repo = ArangoHarvestRepository(ReplayingDatabase(aql))
    service = HarvestService(repo, MagicMock(), MagicMock(), MagicMock())
    return _client(harvest_router, get_harvest_service, service)


class TestHarvestObservations:
    def test_a_foreign_plant_key_returns_no_observations(self):
        client = _harvest_client()

        resp = client.get(_url(f"/harvest/plants/{FOREIGN_PLANT}/observations"))

        assert resp.status_code == 200, resp.text
        assert resp.json() == []
        assert FOREIGN_MARKER not in resp.text

    def test_the_callers_own_plant_still_returns_its_observations(self):
        client = _harvest_client()

        resp = client.get(_url(f"/harvest/plants/{OWN_PLANT}/observations"))

        assert resp.status_code == 200, resp.text
        assert [o["key"] for o in resp.json()] == ["obs-a"]

    def test_a_foreign_plant_key_assesses_nothing(self):
        client = _harvest_client()

        resp = client.get(_url(f"/harvest/plants/{FOREIGN_PLANT}/readiness"))

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["overall_score"] == 0
        assert body["indicators"] == []


# ── The repository contract itself ───────────────────────────────────────────


class TestTheTenantParameterCannotBeSkipped:
    """The isolation is a property of the data-access layer, not of a call site.

    ``tenant_key`` is required and keyword-only on every method below, and the
    empty-string sentinel — the value a forgotten tenant most often takes — is
    rejected rather than silently matching every tenant.
    """

    @pytest.mark.parametrize(
        ("repo_cls", "method", "args"),
        [
            (ArangoWateringRepository, "get_by_plant", (OWN_PLANT,)),
            (ArangoWateringRepository, "get_by_location", (OWN_LOCATION,)),
            (ArangoWateringRepository, "get_stats_by_location", (OWN_LOCATION,)),
            (ArangoWateringRepository, "get_last_watering_date_for_run", ("run-1",)),
            (ArangoFeedingRepository, "get_by_plant", (OWN_PLANT,)),
            (ArangoFeedingRepository, "get_recent_runoff_events", (OWN_PLANT,)),
            (ArangoTaskRepository, "get_tasks_for_plant", (OWN_PLANT,)),
            (ArangoTaskRepository, "get_comments_for_task", ("task-a",)),
            (ArangoTaskRepository, "get_overdue_tasks", ()),
            (ArangoWateringLogRepository, "get_by_slot", (OWN_SLOT,)),
            (ArangoWateringLogRepository, "get_by_location", (OWN_LOCATION,)),
            (ArangoHarvestRepository, "get_observations_for_plant", (OWN_PLANT,)),
            (ArangoHarvestRepository, "get_latest_observations_by_indicator", (OWN_PLANT,)),
        ],
    )
    def test_an_empty_tenant_key_is_rejected_instead_of_matching_everything(self, repo_cls, method, args):
        repo = repo_cls(ReplayingDatabase(ReplayingAql()))

        with pytest.raises(ValueError, match="tenant"):
            getattr(repo, method)(*args, tenant_key="")

    @pytest.mark.parametrize(
        ("repo_cls", "method", "args"),
        [
            (ArangoWateringRepository, "get_by_plant", (OWN_PLANT,)),
            (ArangoFeedingRepository, "get_by_plant", (OWN_PLANT,)),
            (ArangoTaskRepository, "get_tasks_for_plant", (OWN_PLANT,)),
            (ArangoWateringLogRepository, "get_by_slot", (OWN_SLOT,)),
            (ArangoHarvestRepository, "get_latest_observations_by_indicator", (OWN_PLANT,)),
        ],
    )
    def test_omitting_the_tenant_entirely_is_a_type_error(self, repo_cls, method, args):
        repo = repo_cls(ReplayingDatabase(ReplayingAql()))

        with pytest.raises(TypeError):
            getattr(repo, method)(*args)


def test_the_fixture_clock_is_utc():
    """Guard for the fixtures above: their timestamps are UTC, like the app's."""
    assert datetime.now(UTC).tzinfo is UTC
