"""Cross-tenant *writes* on key-anchored endpoints (#948).

#927/#947 swept the read surface. The write surface has the same shape —
"tenant-scoped route, entity key from the URL or the body, no ownership check
before the write" — and is arguably worse: instead of reading another tenant's
data you write **into** it. A harvest observation attributed to a foreign plant
becomes part of that tenant's harvest record, and ``assess_readiness`` reads
observations back, so an injected one moves their readiness verdict.

The check lives in the **repository**, following the precedent #926/#947 set for
reads, and is *declarative*: a repository names its caller-supplied foreign
references in ``_owned_reference_fields`` and ``BaseArangoRepository.create``
verifies every one of them before the insert. The next endpoint that writes a
feeding event or a watering log gets the check whether or not its author
remembers. Where the row carries no ``tenant_key`` of its own — a harvest
observation is tenant-resolved through the plant it is about — the tenant is a
required keyword-only argument instead, which is equally impossible to omit.

Every case below is pinned in both directions: a foreign key answers **404**
(never 403, which would confirm the entity exists elsewhere) and writes nothing,
and the caller's own key still writes successfully.
"""

from __future__ import annotations

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
from app.common.exceptions import KamerplanterError, NotFoundError
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
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_PLANT = "plant-a1"
FOREIGN_PLANT = "plant-b1"

PLANTS: dict[str, dict[str, Any]] = {
    OWN_PLANT: {"_key": OWN_PLANT, "_id": f"{col.PLANT_INSTANCES}/{OWN_PLANT}", "tenant_key": TENANT_KEY},
    FOREIGN_PLANT: {
        "_key": FOREIGN_PLANT,
        "_id": f"{col.PLANT_INSTANCES}/{FOREIGN_PLANT}",
        "tenant_key": FOREIGN_TENANT_KEY,
    },
}


# ── Harness ──────────────────────────────────────────────────────────────────


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _client(router, dependency, service, role: TenantRole = TenantRole.GROWER) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user-1",
        role=role,
    )
    app.dependency_overrides[dependency] = lambda: service
    return TestClient(app)


def _url(path: str) -> str:
    return f"/api/v1/t/{TENANT_SLUG}{path}"


class _RecordingCollection:
    """Insert-recording collection double, so "wrote nothing" is assertable."""

    def __init__(self, name: str, docs: dict[str, dict[str, Any]] | None = None) -> None:
        self._name = name
        self._docs = docs or {}
        self.inserted: list[dict[str, Any]] = []

    def get(self, key: str) -> dict[str, Any] | None:
        return self._docs.get(key)

    def insert(self, data: dict[str, Any], return_new: bool = False) -> dict[str, Any]:
        key = f"{self._name}-{len(self.inserted) + 1}"
        doc = {"_key": key, "_id": f"{self._name}/{key}", **data}
        self.inserted.append(doc)
        return {"new": doc}

    def update(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        key = data["_key"]
        stored = {**self._docs.get(key, {}), **data}
        self._docs[key] = stored
        return {"new": stored}


def _plants_collection() -> _RecordingCollection:
    return _RecordingCollection(col.PLANT_INSTANCES, dict(PLANTS))


def _edge_sink() -> _RecordingCollection:
    """Edges are irrelevant to the assertions but must accept an insert."""
    return _RecordingCollection("edges")


# ── 1: harvest observations — the endpoint #948 names ────────────────────────


def _harvest_client() -> tuple[TestClient, _RecordingCollection]:
    observations = _RecordingCollection(col.HARVEST_OBSERVATIONS)
    collections = {
        col.PLANT_INSTANCES: _plants_collection(),
        col.HARVEST_OBSERVATIONS: observations,
        col.HARVEST_BATCHES: _RecordingCollection(col.HARVEST_BATCHES),
        col.OBSERVED_FOR_HARVEST: _edge_sink(),
        col.USES_INDICATOR: _edge_sink(),
        col.HARVESTED_AS: _edge_sink(),
    }
    repo = ArangoHarvestRepository(ReplayingDatabase(ReplayingAql(), collections))
    service = HarvestService(repo, MagicMock(), MagicMock(), MagicMock())
    return _client(harvest_router, get_harvest_service, service), observations


class TestHarvestObservationWrite:
    """``POST /t/{slug}/harvest/plants/{plant_key}/observations`` (#948)."""

    def test_a_foreign_plant_key_is_not_found_and_writes_nothing(self):
        client, observations = _harvest_client()

        resp = client.post(
            _url(f"/harvest/plants/{FOREIGN_PLANT}/observations"),
            json={"indicator_key": "trichome", "ripeness_assessment": "peak"},
        )

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert observations.inserted == []

    def test_an_unknown_plant_key_looks_exactly_the_same(self):
        """No oracle: 'exists in another tenant' and 'does not exist' are one answer."""
        client, _ = _harvest_client()

        foreign = client.post(
            _url(f"/harvest/plants/{FOREIGN_PLANT}/observations"),
            json={"indicator_key": "trichome", "ripeness_assessment": "peak"},
        )
        unknown = client.post(
            _url("/harvest/plants/does-not-exist/observations"),
            json={"indicator_key": "trichome", "ripeness_assessment": "peak"},
        )

        assert foreign.status_code == unknown.status_code == 404
        assert foreign.json()["error_code"] == unknown.json()["error_code"]

    def test_the_callers_own_plant_still_records_an_observation(self):
        client, observations = _harvest_client()

        resp = client.post(
            _url(f"/harvest/plants/{OWN_PLANT}/observations"),
            json={"indicator_key": "trichome", "ripeness_assessment": "peak"},
        )

        assert resp.status_code == 201, resp.text
        assert [o["plant_key"] for o in observations.inserted] == [OWN_PLANT]


class TestHarvestBatchWrite:
    """``POST /t/{slug}/harvest/plants/{plant_key}/batches`` — same shape (#948)."""

    def _client(self) -> tuple[TestClient, _RecordingCollection]:
        batches = _RecordingCollection(col.HARVEST_BATCHES)
        collections = {
            col.PLANT_INSTANCES: _plants_collection(),
            col.HARVEST_BATCHES: batches,
            col.HARVEST_OBSERVATIONS: _RecordingCollection(col.HARVEST_OBSERVATIONS),
            col.HARVESTED_AS: _edge_sink(),
        }
        aql = ReplayingAql()
        # ``batch_id`` uniqueness probe on the generated identifier — no tenant
        # dimension, so an empty answer is the right one here.
        aql.route(f"FOR doc IN {col.HARVEST_BATCHES}", lambda q, b: [])
        repo = ArangoHarvestRepository(ReplayingDatabase(aql, collections))
        ipm = MagicMock()
        ipm.check_harvest_safety.return_value = (True, [])
        service = HarvestService(repo, ipm, MagicMock(), MagicMock())
        return _client(harvest_router, get_harvest_service, service), batches

    def test_a_foreign_plant_key_is_not_found_and_writes_nothing(self):
        client, batches = self._client()

        resp = client.post(_url(f"/harvest/plants/{FOREIGN_PLANT}/batches"), json={"wet_weight_g": 100.0})

        assert resp.status_code == 404, resp.text
        assert batches.inserted == []

    def test_the_callers_own_plant_still_creates_a_batch(self):
        client, batches = self._client()

        resp = client.post(_url(f"/harvest/plants/{OWN_PLANT}/batches"), json={"wet_weight_g": 100.0})

        assert resp.status_code == 201, resp.text
        assert [b["plant_key"] for b in batches.inserted] == [OWN_PLANT]


# ── 2: feeding events — the key comes from the body ──────────────────────────


def _feeding_client() -> tuple[TestClient, _RecordingCollection]:
    events = _RecordingCollection(col.FEEDING_EVENTS)
    collections = {
        col.PLANT_INSTANCES: _plants_collection(),
        col.FEEDING_EVENTS: events,
        col.FED_BY: _edge_sink(),
        col.FEEDING_USED: _edge_sink(),
    }
    repo = ArangoFeedingRepository(ReplayingDatabase(ReplayingAql(), collections))
    return _client(feeding_router, get_feeding_service, FeedingService(repo)), events


class TestFeedingEventWrite:
    """``POST /t/{slug}/feeding-events`` — ``plant_key`` from the body (#948)."""

    def test_a_foreign_plant_key_is_not_found_and_writes_nothing(self):
        client, events = _feeding_client()

        resp = client.post(
            _url("/feeding-events"),
            json={"plant_key": FOREIGN_PLANT, "volume_applied_liters": 1.0},
        )

        assert resp.status_code == 404, resp.text
        assert events.inserted == []

    def test_the_callers_own_plant_still_records_a_feeding(self):
        client, events = _feeding_client()

        resp = client.post(
            _url("/feeding-events"),
            json={"plant_key": OWN_PLANT, "volume_applied_liters": 1.0},
        )

        assert resp.status_code == 201, resp.text
        assert [e["plant_key"] for e in events.inserted] == [OWN_PLANT]


# ── 3: watering logs and events — ``plant_keys`` from the body ───────────────


def _watering_log_client() -> tuple[TestClient, _RecordingCollection]:
    logs = _RecordingCollection(col.WATERING_LOGS)
    collections = {
        col.PLANT_INSTANCES: _plants_collection(),
        col.WATERING_LOGS: logs,
        col.LOG_SLOT: _edge_sink(),
        col.LOG_PLANT: _edge_sink(),
        col.LOG_FERTILIZER: _edge_sink(),
    }
    aql = ReplayingAql()
    aql.route("FOR pk IN @plant_keys", lambda q, b: [])
    aql.route("FOR fk IN @fert_keys", lambda q, b: [])
    repo = ArangoWateringLogRepository(ReplayingDatabase(aql, collections))
    service = WateringLogService(repo, WateringEngine(), MagicMock())
    return _client(watering_logs_router, get_watering_log_service, service), logs


class TestWateringLogWrite:
    """``POST /t/{slug}/watering-logs`` — the write half of #952's name leak."""

    def test_a_foreign_plant_key_is_not_found_and_writes_nothing(self):
        client, logs = _watering_log_client()

        resp = client.post(
            _url("/watering-logs"),
            json={"volume_liters": 1.0, "plant_keys": [FOREIGN_PLANT]},
        )

        assert resp.status_code == 404, resp.text
        assert logs.inserted == []

    def test_one_foreign_key_among_own_ones_still_rejects_the_whole_write(self):
        """Partial acceptance would persist the foreign reference all the same."""
        client, logs = _watering_log_client()

        resp = client.post(
            _url("/watering-logs"),
            json={"volume_liters": 1.0, "plant_keys": [OWN_PLANT, FOREIGN_PLANT]},
        )

        assert resp.status_code == 404, resp.text
        assert logs.inserted == []

    def test_the_callers_own_plants_still_create_a_log(self):
        client, logs = _watering_log_client()

        resp = client.post(
            _url("/watering-logs"),
            json={"volume_liters": 1.0, "plant_keys": [OWN_PLANT]},
        )

        assert resp.status_code == 201, resp.text
        assert [log["plant_keys"] for log in logs.inserted] == [[OWN_PLANT]]


def _watering_event_client() -> tuple[TestClient, _RecordingCollection]:
    events = _RecordingCollection(col.WATERING_EVENTS)
    collections = {
        col.PLANT_INSTANCES: _plants_collection(),
        col.WATERING_EVENTS: events,
        col.WATERED_PLANT: _edge_sink(),
    }
    site_repo = MagicMock()
    site_repo.get_slot_for_plant.return_value = None
    repo = ArangoWateringRepository(ReplayingDatabase(ReplayingAql(), collections))
    service = WateringService(repo, WateringEngine(), site_repo)
    return _client(watering_events_router, get_watering_service, service), events


class TestWateringEventWrite:
    """``POST /t/{slug}/watering-events`` — ``plant_keys`` from the body (#948).

    This repository's ``create`` is hand-written rather than delegating to the
    base, so it is the one place the declaration is not applied automatically —
    worth its own pair of tests for exactly that reason.
    """

    def test_a_foreign_plant_key_is_not_found_and_writes_nothing(self):
        client, events = _watering_event_client()

        resp = client.post(
            _url("/watering-events"),
            json={"volume_liters": 1.0, "plant_keys": [FOREIGN_PLANT]},
        )

        assert resp.status_code == 404, resp.text
        assert events.inserted == []

    def test_the_callers_own_plants_still_create_an_event(self):
        client, events = _watering_event_client()

        resp = client.post(
            _url("/watering-events"),
            json={"volume_liters": 1.0, "plant_keys": [OWN_PLANT]},
        )

        assert resp.status_code == 201, resp.text
        assert [e["plant_keys"] for e in events.inserted] == [[OWN_PLANT]]


# ── 4: the batch task routes the sweep turned up ─────────────────────────────


def _tasks() -> dict[str, dict[str, Any]]:
    return {
        "task-a": {
            "_key": "task-a",
            "_id": f"{col.TASKS}/task-a",
            "tenant_key": TENANT_KEY,
            "name": "Tomaten giessen",
            "status": "pending",
        },
        "task-b": {
            "_key": "task-b",
            "_id": f"{col.TASKS}/task-b",
            "tenant_key": FOREIGN_TENANT_KEY,
            "name": "Fremde Aufgabe",
            "status": "pending",
        },
    }


def _task_client(role: TenantRole = TenantRole.GROWER) -> tuple[TestClient, _RecordingCollection]:
    tasks = _RecordingCollection(col.TASKS, _tasks())
    aql = ReplayingAql()
    aql.route("FOR e IN task_blocks", lambda q, b: [])
    aql.route("REMOVE", lambda q, b: [])
    aql.route("FOR doc IN", lambda q, b: [])
    repo = ArangoTaskRepository(ReplayingDatabase(aql, {col.TASKS: tasks}))
    service = TaskService(repo, MagicMock(), DependencyResolver())
    return _client(tasks_router, get_task_service, service, role=role), tasks


class TestBatchTaskWrites:
    """``POST /t/{slug}/tasks/batch/{status,delete,assign}`` — found by the sweep.

    Every *single*-task route resolves its key with
    ``service.get_task(key, tenant_key=ctx.tenant_key)`` first. All three batch
    routes forgot that line while taking their ``task_keys`` from the body, so a
    member of tenant A could complete, skip, delete or reassign another tenant's
    tasks in bulk. The batch envelope reports per-key failures, so a foreign key
    lands in ``failed`` with the same text an unknown key produces — no oracle.
    """

    def test_a_foreign_task_cannot_be_status_changed(self):
        client, tasks = _task_client()

        resp = client.post(_url("/tasks/batch/status"), json={"task_keys": ["task-b"], "action": "skip"})

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["succeeded"] == []
        assert [f["key"] for f in body["failed"]] == ["task-b"]
        assert tasks.get("task-b")["status"] == "pending"

    def test_a_foreign_task_cannot_be_assigned_away(self):
        client, _ = _task_client()

        resp = client.post(
            _url("/tasks/batch/assign"),
            json={"task_keys": ["task-b"], "assigned_to_user_key": "user-1"},
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["succeeded"] == []

    def test_a_foreign_task_cannot_be_deleted(self):
        # Batch delete is lead-only (REQ-049 §2.3); act as lead so the request
        # reaches the cross-tenant filtering under test, not the role gate.
        client, _ = _task_client(role=TenantRole.LEAD)

        resp = client.post(_url("/tasks/batch/delete"), json={"task_keys": ["task-b"]})

        assert resp.status_code == 200, resp.text
        assert resp.json()["succeeded"] == []

    def test_the_callers_own_task_is_still_processed(self):
        client, _ = _task_client()

        resp = client.post(_url("/tasks/batch/status"), json={"task_keys": ["task-a"], "action": "skip"})

        assert resp.status_code == 200, resp.text
        assert resp.json()["succeeded"] == ["task-a"]

    def test_a_mixed_batch_processes_only_the_callers_own(self):
        client, _ = _task_client()

        resp = client.post(
            _url("/tasks/batch/status"),
            json={"task_keys": ["task-a", "task-b"], "action": "skip"},
        )

        body = resp.json()
        assert body["succeeded"] == ["task-a"]
        assert [f["key"] for f in body["failed"]] == ["task-b"]


# ── 5: the repository contract itself ────────────────────────────────────────


class TestTheOwnershipCheckIsDeclaredNotRemembered:
    """The mechanism, not the call site — the #926/#947 precedent for writes."""

    @pytest.mark.parametrize(
        ("repo_cls", "field", "collection"),
        [
            (ArangoFeedingRepository, "plant_key", col.PLANT_INSTANCES),
            (ArangoWateringLogRepository, "plant_keys", col.PLANT_INSTANCES),
            (ArangoWateringRepository, "plant_keys", col.PLANT_INSTANCES),
            (ArangoHarvestRepository, "plant_key", col.PLANT_INSTANCES),
        ],
    )
    def test_each_write_repository_declares_its_foreign_references(self, repo_cls, field, collection):
        assert repo_cls._owned_reference_fields.get(field) == collection

    def test_a_harvest_observation_cannot_be_written_without_naming_a_tenant(self):
        """It carries no tenant of its own, so the argument is required instead."""
        repo = ArangoHarvestRepository(ReplayingDatabase(ReplayingAql(), {}))

        with pytest.raises(TypeError):
            repo.create_observation(MagicMock())  # type: ignore[call-arg]

    def test_a_tenantless_row_skips_the_check_but_says_so(self):
        """Fail-open here is unreachable from a router and must not be silent."""
        import structlog.testing

        from app.domain.models.feeding_event import FeedingEvent

        collections = {
            col.PLANT_INSTANCES: _plants_collection(),
            col.FEEDING_EVENTS: _RecordingCollection(col.FEEDING_EVENTS),
            col.FED_BY: _edge_sink(),
            col.FEEDING_USED: _edge_sink(),
        }
        repo = ArangoFeedingRepository(ReplayingDatabase(ReplayingAql(), collections))

        with structlog.testing.capture_logs() as logs:
            repo.create(FeedingEvent(plant_key=FOREIGN_PLANT, volume_applied_liters=1.0))

        assert any(entry["event"] == "owned_reference_check_skipped_tenantless_row" for entry in logs)

    def test_a_stamped_row_with_a_foreign_reference_raises_not_found(self):
        from app.domain.models.feeding_event import FeedingEvent

        collections = {
            col.PLANT_INSTANCES: _plants_collection(),
            col.FEEDING_EVENTS: _RecordingCollection(col.FEEDING_EVENTS),
        }
        repo = ArangoFeedingRepository(ReplayingDatabase(ReplayingAql(), collections))

        with pytest.raises(NotFoundError):
            repo.create(FeedingEvent(tenant_key=TENANT_KEY, plant_key=FOREIGN_PLANT, volume_applied_liters=1.0))
