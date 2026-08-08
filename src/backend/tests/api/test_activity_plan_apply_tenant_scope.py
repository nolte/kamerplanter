"""``POST /activity-plans/apply`` sources its tenant from the path, not the body (#1000).

The endpoint used to live on the *global* ``/activity-plans`` router behind
``Depends(get_current_user)`` only, and took its tenant from
``ActivityPlanApplyRequest.tenant_key`` — a request body field. That value was
stamped onto every ``Task`` it created, and neither the plan nor the target
plant/run was verified against it. Any authenticated user could therefore create
tasks in an arbitrary tenant by typing that tenant's key into the request.

Observed red first, against that code (probe, deleted after capture):

    POST /api/v1/activity-plans/apply
    body {"workflow_template_key": "wf-shared", "plant_key": "plant-x",
          "tenant_key": "tenant-b"}   # caller is a member of tenant-a only
    -> 200 {"created_count":1,"task_keys":["task-1"],...}
       and the created Task carried tenant_key == "tenant-b"

The fix moves the route under ``/t/{tenant_slug}/``, deletes ``tenant_key`` from
the request schema, stamps the path tenant, and verifies the plant/run and the
plan against that tenant before creating anything. This suite pins all three
acceptance directions of #1000 (and the #324 rule): the negative cases and the
positive "the shared global template still applies" case, which a strict
``tenant_key == caller`` predicate would silently kill.

Real domain models flow through in-memory repository doubles that store and
return them (the #996 rule) — the stamped ``Task`` is asserted on the object the
repository actually persisted, not on a stub's call log.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.activity_plans.schemas import ActivityPlanApplyRequest
from app.api.v1.activity_plans.tenant_router import router as activity_plans_tenant_router
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_activity_plan_service,
    get_plant_instance_service,
    get_planting_run_service,
)
from app.common.enums import PlantingRunType, TenantRole
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_run import PlantingRun
from app.domain.models.task import Task, TaskTemplate, WorkflowTemplate
from app.domain.models.tenant_context import TenantContext
from app.domain.services.activity_plan_service import ActivityPlanService
from app.domain.services.plant_instance_service import PlantInstanceService
from app.domain.services.planting_run_service import PlantingRunService

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"
SLUG = {TENANT_A: "anna", TENANT_B: "bert"}

SHARED_PLAN = "wf-shared"
WATERING = "tt-water"
PRUNING = "tt-prune"


# ── In-memory repository doubles (store and return real models) ──────────────


class _FakeTaskRepo:
    """Holds a workflow, its task templates, and every ``Task`` it persists."""

    def __init__(self, workflows: dict[str, WorkflowTemplate], templates: list[TaskTemplate]) -> None:
        self._workflows = workflows
        self._templates = templates
        self.created_tasks: list[Task] = []

    def get_workflow_template_or_raise(self, key: str) -> WorkflowTemplate:
        wf = self._workflows.get(key)
        if wf is None:
            raise NotFoundError("WorkflowTemplate", key)
        return wf

    def get_task_templates_for_workflow(self, key: str) -> list[TaskTemplate]:
        return [tt for tt in self._templates if tt.workflow_template_key == key]

    def create_task(self, task: Task) -> Task:
        task.key = f"task-{len(self.created_tasks) + 1}"
        self.created_tasks.append(task)
        return task

    def create_task_activity_edge(self, task_key: str, activity_key: str) -> None:
        return None


class _FakePlantRepo:
    def __init__(self, plants: dict[str, PlantInstance]) -> None:
        self._plants = plants

    def get_or_raise(self, key: str) -> PlantInstance:
        plant = self._plants.get(key)
        if plant is None:
            raise NotFoundError("PlantInstance", key)
        return plant


class _FakeRunRepo:
    def __init__(self, runs: dict[str, PlantingRun], run_plants: dict[str, list[dict]]) -> None:
        self._runs = runs
        self._run_plants = run_plants

    def get_or_raise(self, key: str) -> PlantingRun:
        run = self._runs.get(key)
        if run is None:
            raise NotFoundError("PlantingRun", key)
        return run

    def get_run_plants(self, run_key: str, include_detached: bool = False) -> list[dict]:
        return self._run_plants.get(run_key, [])


class _Fixture:
    """Tenant-scoped router + services over stores the caller cannot influence."""

    def __init__(self) -> None:
        self.workflows: dict[str, WorkflowTemplate] = {
            SHARED_PLAN: WorkflowTemplate(_key=SHARED_PLAN, tenant_key="", name="Tomate", auto_generated=True),
        }
        self.templates: list[TaskTemplate] = [
            TaskTemplate(_key=WATERING, name="Giessen", enabled=True, workflow_template_key=SHARED_PLAN),
            TaskTemplate(_key=PRUNING, name="Ausgeizen", enabled=True, workflow_template_key=SHARED_PLAN),
        ]
        self.plants: dict[str, PlantInstance] = {}
        self.runs: dict[str, PlantingRun] = {}
        self.run_plants: dict[str, list[dict]] = {}

        self.task_repo = _FakeTaskRepo(self.workflows, self.templates)
        self.plant_repo = _FakePlantRepo(self.plants)
        self.run_repo = _FakeRunRepo(self.runs, self.run_plants)

        self.plan_service = ActivityPlanService(
            engine=MagicMock(),
            activity_repo=MagicMock(),
            phase_repo=MagicMock(),
            task_repo=self.task_repo,
            planting_run_repo=self.run_repo,
        )
        self.plant_service = PlantInstanceService(
            plant_repo=self.plant_repo,
            site_repo=MagicMock(),
            rotation_validator=MagicMock(),
            companion_engine=MagicMock(),
        )
        self.run_service = PlantingRunService(
            run_repo=self.run_repo,
            plant_repo=self.plant_repo,
            engine=MagicMock(),
        )

    # ── seeding helpers ──

    def add_plant(self, key: str, tenant_key: str) -> None:
        self.plants[key] = PlantInstance(
            _key=key,
            tenant_key=tenant_key,
            instance_id=key,
            species_key="sp1",
            planted_on=date(2026, 1, 1),
        )

    def add_run(self, key: str, tenant_key: str, plant_keys: list[str]) -> None:
        self.runs[key] = PlantingRun(
            _key=key,
            tenant_key=tenant_key,
            name="Run",
            run_type=PlantingRunType.MONOCULTURE,
        )
        self.run_plants[key] = [{"key": pk} for pk in plant_keys]
        for pk in plant_keys:
            self.add_plant(pk, tenant_key)

    def add_private_workflow(self, key: str, tenant_key: str) -> None:
        self.workflows[key] = WorkflowTemplate(_key=key, tenant_key=tenant_key, name="Fork", auto_generated=True)
        self.templates.append(
            TaskTemplate(_key=f"{key}-water", name="Giessen", enabled=True, workflow_template_key=key),
        )

    # ── HTTP ──

    def client(self, tenant_key: str) -> TestClient:
        app = FastAPI()
        app.include_router(activity_plans_tenant_router, prefix="/api/v1/t/{tenant_slug}")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
            tenant_key=tenant_key,
            tenant_slug=SLUG[tenant_key],
            user_key=f"user-{tenant_key}",
            role=TenantRole.GROWER,
        )
        app.dependency_overrides[get_activity_plan_service] = lambda: self.plan_service
        app.dependency_overrides[get_plant_instance_service] = lambda: self.plant_service
        app.dependency_overrides[get_planting_run_service] = lambda: self.run_service
        return TestClient(app)

    def apply(self, tenant_key: str, body: dict[str, Any]) -> Any:
        return self.client(tenant_key).post(
            f"/api/v1/t/{SLUG[tenant_key]}/activity-plans/apply",
            json=body,
        )


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


# ── The tenant is the path, never the body ───────────────────────────────────


class TestTheTenantIsThePathNotTheBody:
    """#1000 acceptance 1: a caller cannot create tasks in a foreign tenant."""

    def test_the_request_schema_has_no_tenant_key_field(self):
        """Deleted, not merely validated — a field that must equal the path is a trap."""
        assert "tenant_key" not in ActivityPlanApplyRequest.model_fields

    def test_created_tasks_are_stamped_with_the_path_tenant(self):
        fx = _Fixture()
        fx.add_plant("plant-x", TENANT_A)

        resp = fx.apply(TENANT_A, {"workflow_template_key": SHARED_PLAN, "plant_key": "plant-x"})

        assert resp.status_code == 200, resp.text
        assert [t.tenant_key for t in fx.task_repo.created_tasks] == [TENANT_A, TENANT_A]

    def test_a_stray_tenant_key_in_the_body_is_ignored(self):
        """The body cannot decide the tenant: an extra field changes nothing."""
        fx = _Fixture()
        fx.add_plant("plant-x", TENANT_A)

        resp = fx.apply(
            TENANT_A,
            {"workflow_template_key": SHARED_PLAN, "plant_key": "plant-x", "tenant_key": TENANT_B},
        )

        assert resp.status_code == 200, resp.text
        assert {t.tenant_key for t in fx.task_repo.created_tasks} == {TENANT_A}


# ── A foreign or unknown target is refused with the same 404 ─────────────────


class TestAForeignTargetIsRefused:
    """#1000 acceptance 3: no cross-tenant existence oracle — foreign == unknown == 404."""

    def test_applying_to_a_plant_of_another_tenant_is_404(self):
        fx = _Fixture()
        fx.add_plant("plant-b", TENANT_B)

        resp = fx.apply(TENANT_A, {"workflow_template_key": SHARED_PLAN, "plant_key": "plant-b"})

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert fx.task_repo.created_tasks == []

    def test_applying_to_an_unknown_plant_gets_the_same_answer(self):
        fx = _Fixture()

        resp = fx.apply(TENANT_A, {"workflow_template_key": SHARED_PLAN, "plant_key": "nope"})

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"

    def test_applying_to_a_run_of_another_tenant_is_404(self):
        fx = _Fixture()
        fx.add_run("run-b", TENANT_B, ["p1", "p2"])

        resp = fx.apply(TENANT_A, {"workflow_template_key": SHARED_PLAN, "run_key": "run-b"})

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert fx.task_repo.created_tasks == []

    def test_applying_another_tenants_private_plan_is_404(self):
        """The plan is resolved for the caller's tenant: a foreign fork is not readable."""
        fx = _Fixture()
        fx.add_plant("plant-a", TENANT_A)
        fx.add_private_workflow("wf-b", TENANT_B)

        resp = fx.apply(TENANT_A, {"workflow_template_key": "wf-b", "plant_key": "plant-a"})

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert fx.task_repo.created_tasks == []


# ── The caller can still apply within their own tenant (the #324 half) ───────


class TestApplyingWithinTheCallersOwnTenant:
    """#1000 acceptance 2: the shared global template still applies — kills the over-broad predicate."""

    def test_the_shared_global_template_applies(self):
        """``tenant_key == ""`` — a strict ``== caller`` predicate would match nothing (#324)."""
        fx = _Fixture()
        fx.add_plant("plant-a", TENANT_A)

        resp = fx.apply(TENANT_A, {"workflow_template_key": SHARED_PLAN, "plant_key": "plant-a"})

        assert resp.status_code == 200, resp.text
        assert resp.json()["created_count"] == 2
        assert {t.tenant_key for t in fx.task_repo.created_tasks} == {TENANT_A}

    def test_the_callers_own_forked_plan_applies(self):
        fx = _Fixture()
        fx.add_plant("plant-a", TENANT_A)
        fx.add_private_workflow("wf-a", TENANT_A)

        resp = fx.apply(TENANT_A, {"workflow_template_key": "wf-a", "plant_key": "plant-a"})

        assert resp.status_code == 200, resp.text
        assert resp.json()["created_count"] == 1
        assert [t.tenant_key for t in fx.task_repo.created_tasks] == [TENANT_A]

    def test_applying_to_a_run_creates_tasks_for_every_plant(self):
        fx = _Fixture()
        fx.add_run("run-a", TENANT_A, ["p1", "p2"])

        resp = fx.apply(TENANT_A, {"workflow_template_key": SHARED_PLAN, "run_key": "run-a"})

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["plant_count"] == 2
        assert body["total_tasks"] == 4  # 2 enabled templates x 2 plants
        assert {t.tenant_key for t in fx.task_repo.created_tasks} == {TENANT_A}

    def test_neither_plant_nor_run_is_a_validation_error(self):
        fx = _Fixture()

        resp = fx.apply(TENANT_A, {"workflow_template_key": SHARED_PLAN})

        assert resp.status_code == 422, resp.text
        assert fx.task_repo.created_tasks == []


# ── The route moved off the global router ────────────────────────────────────


class TestTheRouteMoved:
    def test_apply_is_on_the_tenant_scoped_router(self):
        paths = {(route.path, method) for route in activity_plans_tenant_router.routes for method in route.methods}
        assert ("/activity-plans/apply", "POST") in paths

    def test_the_global_activity_plans_router_is_gone(self):
        """It had nothing left on it once ``/apply`` moved, so the module was removed."""
        import importlib

        try:
            importlib.import_module("app.api.v1.activity_plans.router")
        except ModuleNotFoundError:
            return
        raise AssertionError("app.api.v1.activity_plans.router should have been removed")
