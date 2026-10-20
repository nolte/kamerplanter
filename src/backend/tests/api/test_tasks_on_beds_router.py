"""REQ-053 WP 4.2 (#2412) — tasks on beds over HTTP: ``GET /tasks/queue?location_key``, ``POST /tasks/{key}/fan-out``,
a task bound to a garden object, and the ``suggested`` flag in the response (GP-API-030, GP-FR-080/081, §20.9).

The real router and the real :class:`TaskService` over hand-written doubles of the repositories; the cross-tenant
cases are the point — a bed, a task or a garden object of another tenant is a 404 (never a 403, never an empty
answer), and a refusal writes nothing.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.tasks.tenant_router import router as tasks_router
from app.common.auth import get_current_tenant, get_current_user
from app.common.dependencies import get_task_entity_guard, get_task_service
from app.common.enums import GardenObjectType, TenantRole
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.models.tenant_context import TenantContext
from app.domain.services.care_event_service import CareEventService
from app.domain.services.task_entity_guard import TaskEntityGuard
from app.domain.services.task_service import TaskService
from tests.support.care_event_fakes import (
    FakeAttachmentRepo,
    FakeAttachmentService,
    FakeCareEventRepo,
    FakeFertilizers,
    FakeMemberships,
)
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)
from tests.support.task_completion_fakes import FakeCompletionRepo, FakeTaskRepo, bed_task

SLUG = "anna"
GARDEN_OBJECTS = {
    "go_compost": (TENANT, "compost"),
    "go_path": (TENANT, "path"),
    "go_foreign": (OTHER_TENANT, "compost"),
}


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


class _Objects:
    def get_garden_object(self, key, *, tenant_key):
        owner, kind = GARDEN_OBJECTS.get(key, (None, None))
        if owner != tenant_key:
            raise NotFoundError("GardenObject", key)
        return SimpleNamespace(key=key, object_type=GardenObjectType(kind))


class _Located:
    """A location, resolved through its site like ``SiteService.get_location``."""

    def __init__(self, plan: FakePlanRepo) -> None:
        self._plan = plan

    def get_location(self, key, *, tenant_key):
        location = self._plan.locations.get(key)
        site = self._plan._sites.get_site_by_key(location.site_key) if location else None
        if location is None or site is None or site.tenant_key != tenant_key:
            raise NotFoundError("Location", key)
        return location


@pytest.fixture
def api():
    sites = FakeSites(make_site(), make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed")
    plan.locations["bed_child"] = make_location("bed_child", name="Row", parent_location_key="bed")
    plan.locations["loc_foreign"] = make_location("loc_foreign", name="Foreign").model_copy(
        update={"site_key": "site_foreign"}
    )
    plants = {"pi_here": (TENANT, "bed"), "pi_child": (TENANT, "bed_child"), "pi_foreign": (OTHER_TENANT, "bed")}
    care_repo = FakeCareEventRepo()
    care_repo.plants = dict(plants)
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    tasks = FakeTaskRepo(
        bed_task("t_bed"),
        bed_task("t_here", entity_type="plant_instance", entity_key="pi_here"),
        bed_task("t_sugg", suggested=True, suggestion_reason="ET0 demand 4.2 L/m2"),
        bed_task("t_foreign", tenant_key=OTHER_TENANT),
        bed_task("t_gone", entity_key="loc_foreign"),
    )
    tasks.plants = dict(plants)
    service = TaskService(
        tasks, HSTValidator(), DependencyResolver(), completion=FakeCompletionRepo(tasks, plants), care_events=care
    )
    guard = TaskEntityGuard(lambda: None, lambda: None, lambda: None, lambda: _Located(plan), lambda: _Objects())

    app = FastAPI()
    app.include_router(tasks_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT, tenant_slug=SLUG, user_key="user-1", role=TenantRole.GROWER
    )
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user-1", account_type="human")
    app.dependency_overrides[get_task_service] = lambda: service
    app.dependency_overrides[get_task_entity_guard] = lambda: guard
    return TestClient(app), tasks


def url(path: str) -> str:
    return f"/api/v1/t/{SLUG}{path}"


class TestQueueByLocation:
    def test_the_bed_queue_holds_the_bed_and_its_plants(self, api):
        client, _ = api

        resp = client.get(url("/tasks/queue"), params={"location_key": "bed"})

        assert resp.status_code == 200
        assert sorted(t["key"] for t in resp.json()) == ["t_bed", "t_here", "t_sugg"]

    def test_include_children_false_is_honoured(self, api):
        client, tasks = api
        tasks.store["t_child"] = bed_task("t_child", entity_key="bed_child")

        full = client.get(url("/tasks/queue"), params={"location_key": "bed"}).json()
        own = client.get(url("/tasks/queue"), params={"location_key": "bed", "include_children": "false"}).json()

        assert "t_child" in {t["key"] for t in full}
        assert "t_child" not in {t["key"] for t in own}

    def test_a_foreign_bed_is_a_404(self, api):
        client, _ = api

        resp = client.get(url("/tasks/queue"), params={"location_key": "loc_foreign"})

        assert resp.status_code == 404

    def test_a_foreign_tasks_never_leak_into_the_bed_queue(self, api):
        client, _ = api

        keys = {t["key"] for t in client.get(url("/tasks/queue"), params={"location_key": "bed"}).json()}

        assert "t_foreign" not in keys

    def test_plant_and_location_together_are_a_422(self, api):
        client, _ = api

        resp = client.get(url("/tasks/queue"), params={"location_key": "bed", "plant_key": "pi_here"})

        assert resp.status_code == 422

    def test_the_suggested_flag_is_in_the_response(self, api):
        client, _ = api

        by_key = {t["key"]: t for t in client.get(url("/tasks/queue"), params={"location_key": "bed"}).json()}

        assert by_key["t_sugg"]["suggested"] is True
        assert by_key["t_sugg"]["suggestion_reason"] == "ET0 demand 4.2 L/m2"
        assert by_key["t_bed"]["suggested"] is False


class TestFanOut:
    def test_one_clone_per_plant(self, api):
        client, tasks = api

        resp = client.post(url("/tasks/t_bed/fan-out"), json={})

        assert resp.status_code == 201
        assert sorted(t["entity_key"] for t in resp.json()) == ["pi_child", "pi_here"]
        assert len(tasks.cloned_from) == 2
        assert tasks.store["t_bed"].status == "skipped"

    def test_keep_source_and_include_children_flags(self, api):
        client, tasks = api

        resp = client.post(url("/tasks/t_bed/fan-out"), json={"keep_source": True, "include_children": False})

        assert [t["entity_key"] for t in resp.json()] == ["pi_here"]
        assert tasks.store["t_bed"].status == "pending"

    def test_a_foreign_task_is_a_404_and_writes_nothing(self, api):
        client, tasks = api

        resp = client.post(url("/tasks/t_foreign/fan-out"), json={})

        assert resp.status_code == 404
        assert tasks.created == []

    def test_a_task_on_a_foreign_bed_is_a_404_and_writes_nothing(self, api):
        client, tasks = api

        resp = client.post(url("/tasks/t_gone/fan-out"), json={})

        assert resp.status_code == 404
        assert tasks.created == []

    def test_a_plant_task_is_a_422(self, api):
        client, tasks = api

        resp = client.post(url("/tasks/t_here/fan-out"), json={})

        assert resp.status_code == 422
        assert tasks.created == []


class TestForEachPlant:
    """``POST /tasks`` with ``for_each_plant`` (#2462)."""

    BODY = {"name": "Mulch", "category": "maintenance", "entity_type": "location", "entity_key": "bed"}

    def test_only_the_plant_tasks_are_created_and_listed(self, api):
        client, tasks = api

        resp = client.post(url("/tasks"), json={**self.BODY, "for_each_plant": True})

        assert resp.status_code == 201
        assert sorted(t["entity_key"] for t in resp.json()) == ["pi_child", "pi_here"]
        assert {t["entity_type"] for t in resp.json()} == {"plant_instance"}
        assert {t.entity_type for t in tasks.created} == {"plant_instance"}
        assert tasks.atomic_batches == [2]

    def test_without_the_flag_one_bed_task_is_created_as_before(self, api):
        client, tasks = api

        resp = client.post(url("/tasks"), json=self.BODY)

        assert resp.status_code == 201
        assert resp.json()["entity_type"] == "location"
        assert tasks.atomic_batches == []

    def test_a_foreign_bed_is_a_404_and_writes_nothing(self, api):
        client, tasks = api

        resp = client.post(url("/tasks"), json={**self.BODY, "entity_key": "loc_foreign", "for_each_plant": True})

        assert resp.status_code == 404
        assert tasks.created == []

    def test_a_foreign_tenants_plants_are_never_tasked(self, api):
        client, _ = api

        resp = client.post(url("/tasks"), json={**self.BODY, "for_each_plant": True})

        assert "pi_foreign" not in {t["entity_key"] for t in resp.json()}

    @pytest.mark.parametrize(
        "overrides",
        [
            {"entity_type": "garden_object", "entity_key": "go_compost"},
            {"category": "care_reminder"},
            {"recurrence_rule": "FREQ=DAILY"},
        ],
    )
    def test_what_the_fan_out_refuses_is_a_422(self, api, overrides):
        client, tasks = api

        resp = client.post(url("/tasks"), json={**self.BODY, **overrides, "for_each_plant": True})

        assert resp.status_code == 422
        assert tasks.created == []

    def test_a_machine_producer_cannot_use_it(self, api):
        client, tasks = api
        client.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="svc", account_type="service")

        resp = client.post(url("/tasks"), json={**self.BODY, "for_each_plant": True})

        assert resp.status_code == 422
        assert tasks.created == []


class TestBindingTypes:
    @pytest.mark.parametrize("key", ["bed", "bed_child"])
    def test_a_task_binds_to_an_own_location(self, api, key):
        client, tasks = api

        resp = client.post(url("/tasks"), json={"name": "Mulch", "entity_type": "location", "entity_key": key})

        assert resp.status_code == 201
        assert resp.json()["entity_type"] == "location"

    def test_a_task_binds_to_an_own_compost(self, api):
        client, _ = api

        resp = client.post(
            url("/tasks"), json={"name": "Turn", "entity_type": "garden_object", "entity_key": "go_compost"}
        )

        assert resp.status_code == 201
        assert resp.json()["entity_type"] == "garden_object"

    def test_a_task_on_a_path_object_is_a_422(self, api):
        client, tasks = api

        resp = client.post(url("/tasks"), json={"name": "x", "entity_type": "garden_object", "entity_key": "go_path"})

        assert resp.status_code == 422
        assert tasks.created == []

    def test_a_foreign_garden_object_is_a_404(self, api):
        client, tasks = api

        resp = client.post(
            url("/tasks"), json={"name": "x", "entity_type": "garden_object", "entity_key": "go_foreign"}
        )

        assert resp.status_code == 404
        assert tasks.created == []

    def test_a_foreign_location_is_a_404(self, api):
        client, tasks = api

        resp = client.post(url("/tasks"), json={"name": "x", "entity_type": "location", "entity_key": "loc_foreign"})

        assert resp.status_code == 404
        assert tasks.created == []

    def test_an_entity_type_outside_the_allowlist_is_a_422(self, api):
        client, tasks = api

        resp = client.post(url("/tasks"), json={"name": "x", "entity_type": "greenhouse"})

        assert resp.status_code == 422
        assert tasks.created == []
