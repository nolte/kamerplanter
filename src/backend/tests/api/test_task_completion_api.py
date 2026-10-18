"""REQ-053 WP 4.3 (#2413) — the atomic task completion through the deployed app (GP-API-031/032, GP-FR-149).

``app.main`` with the real ``TaskService`` / ``CareEventService``, the real tenant gate and the in-memory doubles of
``tests/support/task_completion_fakes.py``. The unit tier shows what the service decides; this tier shows how it
reads on the wire: the status, the dotted code, that a body cannot carry the server-owned fields (SR-009), and — per
route — that **another tenant's task answers 404** (GP-NFR-050) and is left untouched.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_care_event_service, get_task_service, get_tenant_service
from app.common.enums import TaskCategory, TaskStatus, TenantRole
from app.common.exceptions import NotFoundError
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.models.care_event import CareEvent
from app.domain.models.user import User
from app.domain.services.care_event_service import CareEventService
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
    USER,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)
from tests.support.task_completion_fakes import FakeCompletionRepo, FakeHarvests, FakeTaskRepo, bed_task

_OWN = "/api/v1/t/own/tasks"
_OTHER = "/api/v1/t/other/tasks"


class _Tenants:
    role = TenantRole.GROWER

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        keys = {"own": TENANT, "other": OTHER_TENANT}
        if slug not in keys:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=keys[slug], slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=type(self).role, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str) -> None:
        return None


@pytest.fixture
def world() -> SimpleNamespace:
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed", geometry=rect(1, 1, 2, 1)).model_copy(
        update={"area_m2": 2.5}
    )
    care_repo = FakeCareEventRepo()
    plants = {"pi_here": (TENANT, "bed"), "pi_foreign": (OTHER_TENANT, "bed")}
    care_repo.plants = dict(plants)
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    tasks = FakeTaskRepo(
        bed_task("t1"),
        bed_task("t2"),
        bed_task("t_feed", TaskCategory.FEEDING),
        bed_task("t_foreign", tenant_key=OTHER_TENANT),
    )
    completion = FakeCompletionRepo(tasks, plants)
    service = TaskService(
        tasks,
        HSTValidator(),
        DependencyResolver(),
        completion=completion,
        care_events=care,
        harvests=FakeHarvests(),
        fertilizers=FakeFertilizers(),
    )
    return SimpleNamespace(tasks=tasks, completion=completion, service=service, care=care, care_repo=care_repo)


@pytest.fixture
def client(world) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(_key=USER, email="s@example.org", display_name="Sabine")
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_task_service] = lambda: world.service
    app.dependency_overrides[get_care_event_service] = lambda: world.care
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


class TestComplete:
    def test_a_bare_tap_completes_and_logs_the_task(self, client, world) -> None:
        # GP-FR-084: every field but the instant is optional; a tap on "Erledigt" without input is valid.
        response = client().post(f"{_OWN}/t1/complete", json={})

        assert response.status_code == 200, response.text
        assert response.json()["status"] == "completed"
        (write,) = world.completion.completed
        assert (write.event.trigger, write.event.task_key, write.event.performed_by_user_key) == ("task", "t1", USER)

    def test_the_care_fields_of_a_feeding_reach_the_event_and_the_document(self, client, world) -> None:
        # GP-ACC-024
        response = client().post(
            f"{_OWN}/t_feed/complete",
            json={
                "product_ref": {"kind": "fertilizer", "key": "fert_global"},
                "quantity": 2,
                "unit": "l_per_m2",
                "plant_keys": ["pi_here"],
            },
        )

        assert response.status_code == 200, response.text
        (write,) = world.completion.completed
        assert write.event.quantity_total == 5.0
        assert write.domain.collection == "feeding_events"

    @pytest.mark.parametrize(
        ("offset", "code"),
        [
            (timedelta(minutes=10), "care_event.performed_in_future"),
            (-timedelta(days=400), "care_event.too_old"),
        ],
    )
    def test_the_instant_is_held_to_the_window(self, client, world, offset, code) -> None:
        # GP-ACC-025
        response = client().post(f"{_OWN}/t1/complete", json={"performed_at": (datetime.now(UTC) + offset).isoformat()})

        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == code
        assert world.completion.completed == []

    @pytest.mark.parametrize(
        "forged",
        [
            {"trigger": "system"},
            {"task_key": "t2"},
            {"source_ref": {"collection": "feeding_events", "key": "x"}},
            {"performed_by_user_key": "u_tom"},
            {"created_by": "u_tom"},
            {"tenant_key": OTHER_TENANT},
        ],
    )
    def test_a_body_cannot_carry_the_server_owned_fields(self, client, world, forged) -> None:
        response = client().post(f"{_OWN}/t1/complete", json=forged)

        assert response.status_code == 422
        assert world.completion.completed == []

    def test_a_plant_of_another_tenant_is_422_not_found(self, client, world) -> None:
        response = client().post(f"{_OWN}/t1/complete", json={"plant_keys": ["pi_foreign"]})

        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "reference.not_found"
        assert world.completion.completed == []

    def test_another_tenants_task_is_404_and_untouched(self, client, world) -> None:
        response = client().post(f"{_OWN}/t_foreign/complete", json={})

        assert response.status_code == 404
        assert world.tasks.store["t_foreign"].status == TaskStatus.PENDING
        assert world.completion.completed == []
        assert client().post(f"{_OWN}/t1/complete", json={}).status_code == 200  # the positive control

    def test_a_viewer_is_refused_at_the_gate(self, client, world) -> None:
        response = client(TenantRole.VIEWER).post(f"{_OWN}/t1/complete", json={})

        assert response.status_code == 403
        assert world.completion.completed == []


class TestBatch:
    def test_one_event_per_task(self, client, world) -> None:
        response = client().post(
            f"{_OWN}/batch/status",
            json={"task_keys": ["t1", "t2"], "action": "complete", "quantity": 4, "unit": "l"},
        )

        assert response.status_code == 200, response.text
        assert response.json() == {"succeeded": ["t1", "t2"], "failed": []}
        assert [w.event.task_key for w in world.completion.completed] == ["t1", "t2"]

    def test_a_foreign_key_is_404_for_the_whole_batch(self, client, world) -> None:
        response = client().post(f"{_OWN}/batch/status", json={"task_keys": ["t1", "t_foreign"], "action": "complete"})

        assert response.status_code == 404
        assert world.completion.completed == []
        assert world.tasks.store["t1"].status == TaskStatus.PENDING

    def test_more_than_200_tasks_are_422(self, client, world) -> None:
        response = client().post(
            f"{_OWN}/batch/status", json={"task_keys": [f"t{i}" for i in range(201)], "action": "complete"}
        )

        assert response.status_code == 422
        assert world.completion.completed == []

    def test_a_body_cannot_carry_the_server_owned_fields(self, client, world) -> None:
        response = client().post(
            f"{_OWN}/batch/status", json={"task_keys": ["t1"], "action": "complete", "trigger": "system"}
        )

        assert response.status_code == 422


class TestReopen:
    @pytest.fixture
    def done(self, world) -> None:
        world.tasks.store["t1"] = world.tasks.store["t1"].model_copy(update={"status": TaskStatus.COMPLETED})
        world.completion.open_event = CareEvent(
            _key="ce_1",
            tenant_key=TENANT,
            site_key="site_1",
            location_key="bed",
            category="watering",
            summary="x",
            performed_at=datetime.now(UTC),
            trigger="task",
            task_key="t1",
            created_by=USER,
            created_at=datetime.now(UTC) - timedelta(seconds=20),
        )

    def test_undo_reopens_and_voids_in_one_write(self, client, world, done) -> None:
        response = client().post(f"{_OWN}/t1/reopen", json={"undo": True})

        assert response.status_code == 200, response.text
        assert response.json()["status"] == "pending"
        (write,) = world.completion.reopened
        assert (write.event_key, write.void_reason) == ("ce_1", "undo")

    def test_a_plain_reopen_leaves_the_care_line(self, client, world, done) -> None:
        response = client().post(f"{_OWN}/t1/reopen")

        assert response.status_code == 200
        assert world.completion.reopened == []

    def test_a_late_undo_by_a_grower_is_403_and_nothing_changes(self, client, world, done) -> None:
        world.completion.open_event = world.completion.open_event.model_copy(
            update={"created_at": datetime.now(UTC) - timedelta(minutes=30)}
        )

        response = client().post(f"{_OWN}/t1/reopen", json={"undo": True})

        assert response.status_code == 403
        assert world.completion.reopened == []
        assert world.tasks.store["t1"].status == TaskStatus.COMPLETED

    def test_another_tenants_task_is_404(self, client, world) -> None:
        world.tasks.store["t_foreign"] = world.tasks.store["t_foreign"].model_copy(
            update={"status": TaskStatus.COMPLETED}
        )

        assert client().post(f"{_OWN}/t_foreign/reopen", json={"undo": True}).status_code == 404
        assert world.completion.reopened == []

    def test_a_body_that_names_more_than_undo_is_422(self, client, world, done) -> None:
        assert client().post(f"{_OWN}/t1/reopen", json={"void_reason": "x"}).status_code == 422
