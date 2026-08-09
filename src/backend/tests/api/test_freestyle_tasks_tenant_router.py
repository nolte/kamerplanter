"""``POST /t/{slug}/tasks`` — FreeStyle machine-created tasks (REQ-006, #1082).

Covers the six acceptance criteria end to end through the real router, the real
:class:`TaskService` and the real :class:`ArangoTaskRepository` against the
replaying database double, so what is asserted is behaviour — an insert that did
or did not happen, a status code, a tenant predicate that actually filtered — not
that a stub was called.

The double's ``tasks`` collection stores inserts back into its own map and the
idempotency lookup reads from that same map, so a re-post in one test sees the
task an earlier post in the same test created — the flow a real producer drives.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.tasks.tenant_router import router as tasks_router
from app.common.auth import get_current_tenant, get_current_user
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.task_service import TaskService
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase, apply_predicates

TENANT_A_SLUG = "anna"
TENANT_A = "tenant-a"
TENANT_B = "tenant-b"
SOURCE = "goose/leaf-analysis"
PLANT_KEY = "plant-1"

_LOOKUP_MARKER = "doc.external_ref == @external_ref"


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


class _RecordingCollection:
    """Insert/update-recording collection; inserts are also stored so a later
    idempotency lookup in the same test can find them."""

    def __init__(self, name: str) -> None:
        self._name = name
        self.docs: dict[str, dict[str, Any]] = {}
        self.inserted: list[dict[str, Any]] = []

    def get(self, key: str) -> dict[str, Any] | None:
        return self.docs.get(key)

    def insert(self, data: dict[str, Any], return_new: bool = False) -> dict[str, Any]:
        key = data.get("_key") or f"{self._name}-{len(self.inserted) + 1}"
        doc = {**data, "_key": key, "_id": f"{self._name}/{key}"}
        self.inserted.append(doc)
        self.docs[key] = doc
        return {"new": doc}

    def update(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        key = data["_key"]
        stored = {**self.docs.get(key, {}), **data}
        self.docs[key] = stored
        return {"new": stored}


def _build(account_type: str, tenant_key: str = TENANT_A) -> tuple[TestClient, _RecordingCollection]:
    tasks = _RecordingCollection(col.TASKS)
    has_task = _RecordingCollection(col.HAS_TASK)

    def _lookup(query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
        return apply_predicates(list(tasks.docs.values()), query, bind_vars)[:1]

    aql = ReplayingAql().route(_LOOKUP_MARKER, _lookup)
    db = ReplayingDatabase(aql, {col.TASKS: tasks, col.HAS_TASK: has_task})
    service = TaskService(ArangoTaskRepository(db), MagicMock(), MagicMock())

    app = FastAPI()
    app.include_router(tasks_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=tenant_key, tenant_slug=TENANT_A_SLUG, user_key="user-1", role=TenantRole.GROWER
    )
    app.dependency_overrides[get_current_user] = lambda: User(
        key="user-1", email="prod@example.com", display_name="Producer", account_type=account_type
    )
    from app.common.dependencies import get_task_service

    app.dependency_overrides[get_task_service] = lambda: service
    return TestClient(app), tasks


def _url(slug: str = TENANT_A_SLUG) -> str:
    return f"/api/v1/t/{slug}/tasks"


def _freestyle_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "name": "Blattschaden pruefen",
        "instruction": "Analyse meldet moegliche Chlorose.",
        "category": "ipm",
        "origin": "pipeline",
        "source": SOURCE,
        "source_run_ref": "run-42",
        "external_ref": "leaf/2026-08-09/42",
        "entity_key": PLANT_KEY,
        "entity_type": "plant_instance",
        "due_date": "2026-08-12T00:00:00+00:00",
    }
    body.update(overrides)
    return body


class TestServiceAccountCreate:
    def test_ac1_and_ac2_service_account_creates_a_marked_instance_bound_task(self) -> None:
        """AC-1/AC-2: a service account POSTs an instance-bound FreeStyle task; it is
        created, marked machine-generated, and carries its producer + run reference."""
        client, tasks = _build("service")

        resp = client.post(_url(), json=_freestyle_body())

        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["origin"] == "pipeline"
        assert data["source"] == SOURCE
        assert data["source_run_ref"] == "run-42"
        assert data["category"] == "ipm"  # semantic category preserved, orthogonal to origin
        assert data["entity_key"] == PLANT_KEY
        assert len(tasks.inserted) == 1
        assert tasks.inserted[0]["origin"] == "pipeline"

    def test_ac3_reposting_same_external_ref_updates_not_duplicates(self) -> None:
        """AC-3: re-posting the same external_ref returns the existing task (200), no duplicate."""
        client, tasks = _build("service")

        first = client.post(_url(), json=_freestyle_body())
        assert first.status_code == 201, first.text
        first_key = first.json()["key"]

        second = client.post(_url(), json=_freestyle_body(name="Blattschaden pruefen (aktualisiert)"))

        assert second.status_code == 200, second.text
        assert second.json()["key"] == first_key
        assert second.json()["name"] == "Blattschaden pruefen (aktualisiert)"
        assert len(tasks.inserted) == 1  # still exactly one row

    def test_ac5_producer_recurrence_rule_is_rejected(self) -> None:
        """AC-5: a producer path is one-off — a real recurrence rule is refused (422)."""
        client, tasks = _build("service")

        resp = client.post(_url(), json=_freestyle_body(recurrence_rule="FREQ=WEEKLY"))

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        assert tasks.inserted == []


class TestOriginTrust:
    def test_ac4_interactive_user_defaults_to_user_origin(self) -> None:
        """AC-4: an ordinary interactive create is user-authored, keeping existing clients working."""
        client, tasks = _build("user")

        resp = client.post(_url(), json={"name": "Giessen", "instruction": "Giess die Pflanze."})

        assert resp.status_code == 201, resp.text
        assert resp.json()["origin"] == "user"

    def test_interactive_user_cannot_spoof_pipeline_origin_or_dedup_key(self) -> None:
        """#1000: a normal user body claiming pipeline provenance is overridden server-side."""
        client, tasks = _build("user")

        resp = client.post(
            _url(),
            json={
                "name": "Manuelle Aufgabe",
                "instruction": "",
                "origin": "pipeline",
                "source": "attacker/forged",
                "external_ref": "forged-key",
            },
        )

        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["origin"] == "user"
        assert data["source"] == ""
        assert data["external_ref"] is None
        assert tasks.inserted[0]["origin"] == "user"

    def test_service_account_without_origin_still_marks_pipeline(self) -> None:
        client, tasks = _build("service")

        resp = client.post(
            _url(),
            json={"name": "Auto", "instruction": "", "source": SOURCE, "external_ref": "k1", "origin": "user"},
        )

        # A service account is a machine producer; a body origin of "user" is not a
        # valid machine origin, so it is normalised to the default pipeline.
        assert resp.status_code == 201, resp.text
        assert resp.json()["origin"] == "pipeline"


class TestTenantIsolation:
    def test_ac6_producer_in_a_cannot_dedup_against_bs_task(self) -> None:
        """AC-6 (negative): the same external_ref in tenant B is invisible to a
        producer in tenant A, so A creates its own task rather than hitting B's.

        Red-first: drop the tenant predicate from ``find_task_by_external_ref`` and
        the second post resolves to tenant B's row — a 200 idempotent hit with only
        one row across both tenants, instead of the two rows asserted here.
        """
        # A shared repository/store across two tenant contexts.
        tasks = _RecordingCollection(col.TASKS)
        has_task = _RecordingCollection(col.HAS_TASK)

        def _lookup(query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
            return apply_predicates(list(tasks.docs.values()), query, bind_vars)[:1]

        aql = ReplayingAql().route(_LOOKUP_MARKER, _lookup)
        db = ReplayingDatabase(aql, {col.TASKS: tasks, col.HAS_TASK: has_task})
        service = TaskService(ArangoTaskRepository(db), MagicMock(), MagicMock())

        from app.common.dependencies import get_task_service

        def _client_for(tenant_key: str) -> TestClient:
            app = FastAPI()
            app.include_router(tasks_router, prefix="/api/v1/t/{tenant_slug}")
            app.add_exception_handler(KamerplanterError, _error_handler)
            app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
                tenant_key=tenant_key, tenant_slug=tenant_key, user_key="svc", role=TenantRole.GROWER
            )
            app.dependency_overrides[get_current_user] = lambda: User(
                key="svc", email="svc@example.com", display_name="svc", account_type="service"
            )
            app.dependency_overrides[get_task_service] = lambda: service
            return TestClient(app)

        shared_ref = "leaf/shared-ref"
        b = _client_for(TENANT_B).post(
            f"/api/v1/t/{TENANT_B}/tasks",
            json=_freestyle_body(external_ref=shared_ref, entity_key=None, entity_type=None),
        )
        assert b.status_code == 201, b.text

        a = _client_for(TENANT_A).post(
            f"/api/v1/t/{TENANT_A}/tasks",
            json=_freestyle_body(external_ref=shared_ref, entity_key=None, entity_type=None),
        )

        assert a.status_code == 201, a.text  # a fresh create, NOT an idempotent hit
        assert a.json()["key"] != b.json()["key"]
        assert len(tasks.inserted) == 2
        tenants = {doc["tenant_key"] for doc in tasks.inserted}
        assert tenants == {TENANT_A, TENANT_B}
