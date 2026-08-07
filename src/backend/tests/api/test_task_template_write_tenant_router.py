"""``POST /t/{slug}/tasks/templates`` — the parent workflow is now resolved (#965).

The write-surface sweep in #948 left this endpoint alone because
``TaskTemplate`` carries no ``tenant_key`` and #947 had shown what a predicate
on a non-existent field does: it blocks every row, not the foreign ones. The
anchor is the parent instead — ``WorkflowTemplate`` *does* carry ``tenant_key``,
and ``workflow_templates`` is one of ``backfill_tenant_key``'s
``TOP_LEVEL_COLLECTIONS``, so the field is populated rather than merely
declared.

Exercised end to end through the real router and the real repository against
the replaying database double, so what is asserted is that the edge is not
written — not that a stub was called in a particular order.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.tasks.tenant_router import router as tasks_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_task_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.models.tenant_context import TenantContext
from app.domain.services.task_service import TaskService
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_WORKFLOW = "wf-a1"
FOREIGN_WORKFLOW = "wf-b1"
SYSTEM_WORKFLOW = "wf-sys"

WORKFLOWS: dict[str, dict[str, Any]] = {
    OWN_WORKFLOW: {
        "_key": OWN_WORKFLOW,
        "_id": f"{col.WORKFLOW_TEMPLATES}/{OWN_WORKFLOW}",
        "tenant_key": TENANT_KEY,
        "name": "Eigener Workflow",
    },
    FOREIGN_WORKFLOW: {
        "_key": FOREIGN_WORKFLOW,
        "_id": f"{col.WORKFLOW_TEMPLATES}/{FOREIGN_WORKFLOW}",
        "tenant_key": FOREIGN_TENANT_KEY,
        "name": "Fremder Workflow",
    },
    SYSTEM_WORKFLOW: {
        "_key": SYSTEM_WORKFLOW,
        "_id": f"{col.WORKFLOW_TEMPLATES}/{SYSTEM_WORKFLOW}",
        "tenant_key": "",
        "name": "Tomato Standard",
        "is_system": True,
    },
}


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


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


def _client() -> tuple[TestClient, _RecordingCollection, _RecordingCollection]:
    templates = _RecordingCollection(col.TASK_TEMPLATES)
    edges = _RecordingCollection(col.WF_CONTAINS)
    collections = {
        col.WORKFLOW_TEMPLATES: _RecordingCollection(col.WORKFLOW_TEMPLATES, dict(WORKFLOWS)),
        col.TASK_TEMPLATES: templates,
        col.WF_CONTAINS: edges,
    }
    repo = ArangoTaskRepository(ReplayingDatabase(ReplayingAql(), collections))
    service = TaskService(repo, MagicMock(), MagicMock())

    app = FastAPI()
    app.include_router(tasks_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user-1",
        role=TenantRole.GROWER,
    )
    app.dependency_overrides[get_task_service] = lambda: service
    return TestClient(app), templates, edges


def _url(path: str) -> str:
    return f"/api/v1/t/{TENANT_SLUG}{path}"


def _body(workflow_template_key: str | None) -> dict[str, Any]:
    body: dict[str, Any] = {"name": "Giessen", "instruction": "Giess die Pflanze."}
    if workflow_template_key is not None:
        body["workflow_template_key"] = workflow_template_key
    return body


class TestTaskTemplateCreateResolvesItsParentWorkflow:
    def test_a_foreign_workflow_is_not_found_and_writes_nothing(self):
        client, templates, edges = _client()

        resp = client.post(_url("/tasks/templates"), json=_body(FOREIGN_WORKFLOW))

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert templates.inserted == []
        assert edges.inserted == []

    def test_an_unknown_workflow_looks_exactly_the_same(self):
        """No oracle: 'exists in another tenant' and 'does not exist' are one answer."""
        client, _, _ = _client()

        foreign = client.post(_url("/tasks/templates"), json=_body(FOREIGN_WORKFLOW))
        unknown = client.post(_url("/tasks/templates"), json=_body("does-not-exist"))

        assert foreign.status_code == unknown.status_code == 404
        assert foreign.json()["error_code"] == unknown.json()["error_code"]

    def test_the_callers_own_workflow_still_gets_its_template_and_edge(self):
        client, templates, edges = _client()

        resp = client.post(_url("/tasks/templates"), json=_body(OWN_WORKFLOW))

        assert resp.status_code == 201, resp.text
        assert [t["workflow_template_key"] for t in templates.inserted] == [OWN_WORKFLOW]
        assert [e["_from"] for e in edges.inserted] == [f"{col.WORKFLOW_TEMPLATES}/{OWN_WORKFLOW}"]

    def test_a_globally_seeded_system_workflow_resolves_but_refuses_the_write(self):
        """#965 item 3; the route-level story is in
        ``test_system_workflow_children_tenant_router``.

        The hybrid-catalogue direction is unchanged — the workflow still
        resolves, so #324 does not recur — but the write is refused with the
        parent guard's 422, not this route's 404.
        """
        client, templates, edges = _client()

        resp = client.post(_url("/tasks/templates"), json=_body(SYSTEM_WORKFLOW))

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        assert templates.inserted == []
        assert edges.inserted == []

    def test_a_standalone_template_without_a_parent_is_still_creatable(self):
        client, templates, edges = _client()

        resp = client.post(_url("/tasks/templates"), json=_body(None))

        assert resp.status_code == 201, resp.text
        assert len(templates.inserted) == 1
        assert edges.inserted == []
