"""The child-write routes of a system workflow, end to end (#965 item 3).

``PUT``/``DELETE /t/{slug}/tasks/workflows/{key}`` already refuse a globally
seeded system template. The routes that write its *children* did not: the parent
was resolved with hybrid-catalog **read** access, which admits ``tenant_key ==
""`` by design, so a task template or a phase could be written into "Tomato
Standard" — and, because the listing filters on the denormalised parent field,
show up for every tenant.

Exercised through the real router and the real repository against the replaying
database double, so what is asserted is that nothing was written — not that a
stub was called in some order. The refusal is a 422 ``VALIDATION_ERROR``, the
same answer the parent's own guard gives; the 404 stays reserved for a foreign
or unknown parent, which the caller may not even read.
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

OWN_PHASE = "ph-own"
SYSTEM_PHASE = "ph-sys"

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

OWN_TEMPLATE = "tt-own"
SYSTEM_TEMPLATE = "tt-sys"
FOREIGN_TEMPLATE = "tt-foreign"
ORPHAN_TEMPLATE = "tt-orphan"

TASK_TEMPLATES: dict[str, dict[str, Any]] = {
    key: {
        "_key": key,
        "_id": f"{col.TASK_TEMPLATES}/{key}",
        "name": "Giessen",
        **({"workflow_template_key": parent} if parent else {}),
    }
    for key, parent in (
        (OWN_TEMPLATE, OWN_WORKFLOW),
        (SYSTEM_TEMPLATE, SYSTEM_WORKFLOW),
        (FOREIGN_TEMPLATE, FOREIGN_WORKFLOW),
        (ORPHAN_TEMPLATE, None),
    )
}

PHASES: dict[str, dict[str, Any]] = {
    OWN_PHASE: {
        "_key": OWN_PHASE,
        "_id": f"{col.WORKFLOW_PHASES}/{OWN_PHASE}",
        "workflow_template_key": OWN_WORKFLOW,
        "name": "Vegetativ",
    },
    SYSTEM_PHASE: {
        "_key": SYSTEM_PHASE,
        "_id": f"{col.WORKFLOW_PHASES}/{SYSTEM_PHASE}",
        "workflow_template_key": SYSTEM_WORKFLOW,
        "name": "Vegetativ",
    },
}


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


class _RecordingCollection:
    """Write-recording collection double, so "wrote nothing" is assertable."""

    def __init__(self, name: str, docs: dict[str, dict[str, Any]] | None = None) -> None:
        self._name = name
        self._docs = docs or {}
        self.inserted: list[dict[str, Any]] = []
        self.updated: list[dict[str, Any]] = []
        self.deleted: list[str] = []

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
        self.updated.append(stored)
        return {"new": stored}

    def delete(self, key: str) -> bool:
        self._docs.pop(key, None)
        self.deleted.append(key)
        return True


class _Fixture:
    def __init__(self, role: TenantRole = TenantRole.GROWER) -> None:
        # Delete of a task template / phase is lead-only (REQ-049 §2.3); tests
        # that exercise a delete pass ``role=TenantRole.LEAD`` so the request
        # reaches the system-ownership guard under test instead of the role gate.
        self._role = role
        self.templates = _RecordingCollection(
            col.TASK_TEMPLATES,
            {k: dict(v) for k, v in TASK_TEMPLATES.items()},
        )
        self.phases = _RecordingCollection(col.WORKFLOW_PHASES, {k: dict(v) for k, v in PHASES.items()})
        self.contains_edges = _RecordingCollection(col.WF_CONTAINS)
        self.phase_edges = _RecordingCollection(col.WF_HAS_PHASE)

    @property
    def client(self) -> TestClient:
        aql = (
            ReplayingAql()
            # ``delete_phase`` detaches the phase's edges and unlinks its task
            # templates before removing the document; ``delete_task_template``
            # detaches its own two edge kinds. None of the four returns rows.
            .route(col.WF_HAS_PHASE, lambda query, bind_vars: [])
            .route(col.WF_CONTAINS, lambda query, bind_vars: [])
            .route(col.INSTANCE_OF, lambda query, bind_vars: [])
            .route(col.TASK_TEMPLATES, lambda query, bind_vars: [])
        )
        collections = {
            col.WORKFLOW_TEMPLATES: _RecordingCollection(col.WORKFLOW_TEMPLATES, dict(WORKFLOWS)),
            col.TASK_TEMPLATES: self.templates,
            col.WORKFLOW_PHASES: self.phases,
            col.WF_CONTAINS: self.contains_edges,
            col.WF_HAS_PHASE: self.phase_edges,
        }
        repo = ArangoTaskRepository(ReplayingDatabase(aql, collections))
        service = TaskService(repo, MagicMock(), MagicMock())

        app = FastAPI()
        app.include_router(tasks_router, prefix="/api/v1/t/{tenant_slug}")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
            tenant_key=TENANT_KEY,
            tenant_slug=TENANT_SLUG,
            user_key="user-1",
            role=self._role,
        )
        app.dependency_overrides[get_task_service] = lambda: service
        return TestClient(app)


def _url(path: str) -> str:
    return f"/api/v1/t/{TENANT_SLUG}{path}"


class TestTaskTemplateChildrenOfASystemWorkflow:
    def test_attaching_a_task_template_to_a_system_workflow_is_refused(self):
        fx = _Fixture()

        resp = fx.client.post(
            _url("/tasks/templates"),
            json={"name": "Giessen", "workflow_template_key": SYSTEM_WORKFLOW},
        )

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        assert fx.templates.inserted == []
        assert fx.contains_edges.inserted == []

    def test_the_callers_own_workflow_still_accepts_a_task_template(self):
        fx = _Fixture()

        resp = fx.client.post(
            _url("/tasks/templates"),
            json={"name": "Giessen", "workflow_template_key": OWN_WORKFLOW},
        )

        assert resp.status_code == 201, resp.text
        assert [t["workflow_template_key"] for t in fx.templates.inserted] == [OWN_WORKFLOW]

    def test_a_foreign_workflow_still_answers_not_found_rather_than_refused(self):
        """The two refusals stay distinct: 404 "you may not read it", 422 "read yes, write no"."""
        fx = _Fixture()

        foreign = fx.client.post(
            _url("/tasks/templates"),
            json={"name": "Giessen", "workflow_template_key": FOREIGN_WORKFLOW},
        )

        assert foreign.status_code == 404, foreign.text
        assert foreign.json()["error_code"] == "ENTITY_NOT_FOUND"


class TestTheExistingTaskTemplatesOfASystemWorkflow:
    """``PUT``/``DELETE /tasks/templates/{key}`` never looked at the parent at all."""

    def test_editing_a_system_workflows_task_template_in_place_is_refused(self):
        fx = _Fixture()

        resp = fx.client.put(_url(f"/tasks/templates/{SYSTEM_TEMPLATE}"), json={"name": "Umbenannt"})

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        assert fx.templates.updated == []

    def test_deleting_a_system_workflows_task_template_is_refused(self):
        fx = _Fixture(role=TenantRole.LEAD)

        resp = fx.client.delete(_url(f"/tasks/templates/{SYSTEM_TEMPLATE}"))

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        assert fx.templates.deleted == []

    def test_the_callers_own_task_template_is_still_editable_and_deletable(self):
        fx = _Fixture(role=TenantRole.LEAD)

        updated = fx.client.put(_url(f"/tasks/templates/{OWN_TEMPLATE}"), json={"name": "Umbenannt"})
        deleted = fx.client.delete(_url(f"/tasks/templates/{OWN_TEMPLATE}"))

        assert updated.status_code == 200, updated.text
        assert updated.json()["name"] == "Umbenannt"
        assert deleted.status_code == 204, deleted.text
        assert fx.templates.deleted == [OWN_TEMPLATE]

    def test_a_task_template_with_no_parent_workflow_is_left_alone(self):
        """No anchor, so no refusal — the orphan question is not settled here."""
        fx = _Fixture(role=TenantRole.LEAD)

        updated = fx.client.put(_url(f"/tasks/templates/{ORPHAN_TEMPLATE}"), json={"name": "Umbenannt"})
        deleted = fx.client.delete(_url(f"/tasks/templates/{ORPHAN_TEMPLATE}"))

        assert updated.status_code == 200, updated.text
        assert deleted.status_code == 204, deleted.text

    def test_a_foreign_tenants_task_template_is_still_reachable(self):
        """#965 item 1, deliberately still open — anchoring on the parent's
        *tenant* needs the orphan-ownership field, not a guard on this path."""
        fx = _Fixture()

        updated = fx.client.put(_url(f"/tasks/templates/{FOREIGN_TEMPLATE}"), json={"name": "Umbenannt"})

        assert updated.status_code == 200, updated.text


class TestPhaseChildrenOfASystemWorkflow:
    def test_creating_a_phase_in_a_system_workflow_is_refused(self):
        fx = _Fixture()

        resp = fx.client.post(
            _url(f"/tasks/workflows/{SYSTEM_WORKFLOW}/phases"),
            json={"name": "Neue Phase"},
        )

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        assert fx.phases.inserted == []
        assert fx.phase_edges.inserted == []

    def test_updating_a_system_workflows_phase_is_refused(self):
        fx = _Fixture()

        resp = fx.client.put(_url(f"/tasks/phases/{SYSTEM_PHASE}"), json={"name": "Umbenannt"})

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        assert fx.phases.updated == []

    def test_deleting_a_system_workflows_phase_is_refused(self):
        fx = _Fixture(role=TenantRole.LEAD)

        resp = fx.client.delete(_url(f"/tasks/phases/{SYSTEM_PHASE}"))

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        assert fx.phases.deleted == []

    def test_the_callers_own_workflow_still_accepts_a_phase(self):
        fx = _Fixture()

        resp = fx.client.post(
            _url(f"/tasks/workflows/{OWN_WORKFLOW}/phases"),
            json={"name": "Neue Phase"},
        )

        assert resp.status_code == 201, resp.text
        assert [p["workflow_template_key"] for p in fx.phases.inserted] == [OWN_WORKFLOW]

    def test_the_callers_own_phase_is_still_editable_and_deletable(self):
        fx = _Fixture(role=TenantRole.LEAD)

        updated = fx.client.put(_url(f"/tasks/phases/{OWN_PHASE}"), json={"name": "Umbenannt"})
        deleted = fx.client.delete(_url(f"/tasks/phases/{OWN_PHASE}"))

        assert updated.status_code == 200, updated.text
        assert updated.json()["name"] == "Umbenannt"
        assert deleted.status_code == 204, deleted.text
        assert fx.phases.deleted == [OWN_PHASE]


class TestReadingASystemWorkflowIsUntouched:
    def test_the_detail_route_still_serves_a_system_workflow(self):
        """#324's counter-example: the strict direction must not hide the global catalogue."""
        fx = _Fixture()

        resp = fx.client.get(_url(f"/tasks/workflows/{SYSTEM_WORKFLOW}"))

        assert resp.status_code == 200, resp.text
        assert resp.json()["is_system"] is True
