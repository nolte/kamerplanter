"""REQ-053 WP 8.17 (#2660) — accept and dismiss a suggested task over HTTP (GP-API-040, GP-FR-086).

The real router and the real :class:`TaskService` over the in-memory task double. The double carries the same
predicate as the AQL statement (tenant, ``suggested == true``, open status for a dismissal), so these tests pin the
HTTP contract — status codes, the published error codes, the role gate — and the real-database tier
(``tests/integration/test_task_suggestions.py``) pins that the statement does the same.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.tasks.tenant_router import router as tasks_router
from app.common.auth import get_current_tenant, get_current_user
from app.common.dependencies import get_task_service
from app.common.enums import TaskOrigin, TaskStatus, TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.models.tenant_context import TenantContext
from app.domain.services.task_service import TaskService
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT
from tests.support.task_completion_fakes import FakeTaskRepo, bed_task

SLUG = "anna"


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message, "details": exc.details},
    )


class _Notifications:
    """Records every propagation call; a suggestion decision must make none."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def __getattr__(self, name: str):
        def _record(*_args, **_kwargs) -> None:
            self.calls.append(name)

        return _record


def _suggestion(key: str, **overrides):
    data = {"suggested": True, "suggestion_reason": "ET0 demand 4.2 L/m2 over 3 days", "origin": TaskOrigin.SYSTEM}
    return bed_task(key, **{**data, **overrides})


def _build(role: TenantRole):
    tasks = FakeTaskRepo(
        _suggestion("t_sugg"),
        _suggestion("t_sugg_started", status=TaskStatus.IN_PROGRESS),
        _suggestion("t_sugg_closed", status=TaskStatus.SKIPPED),
        bed_task("t_plain"),
        _suggestion("t_foreign", tenant_key=OTHER_TENANT),
    )
    notifications = _Notifications()
    service = TaskService(tasks, HSTValidator(), DependencyResolver(), notification_propagation=notifications)

    app = FastAPI()
    app.include_router(tasks_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT, tenant_slug=SLUG, user_key="user-1", role=role
    )
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user-1", account_type="human")
    app.dependency_overrides[get_task_service] = lambda: service
    return TestClient(app), tasks, notifications


@pytest.fixture
def api():
    return _build(TenantRole.GROWER)


def url(path: str) -> str:
    return f"/api/v1/t/{SLUG}{path}"


class TestAccept:
    def test_accepting_clears_the_flag_and_keeps_the_task_open(self, api):
        client, tasks, notifications = api

        resp = client.post(url("/tasks/t_sugg/accept-suggestion"))

        assert resp.status_code == 200
        body = resp.json()
        assert body["suggested"] is False
        assert body["suggestion_reason"] is None
        assert body["status"] == "pending"
        assert tasks.store["t_sugg"].suggested is False
        assert tasks.store["t_sugg"].origin == TaskOrigin.SYSTEM  # who proposed it stays on the task
        assert notifications.calls == []

    def test_a_task_that_is_no_suggestion_is_a_409(self, api):
        client, tasks, _ = api
        before = tasks.store["t_plain"].model_copy(deep=True)

        resp = client.post(url("/tasks/t_plain/accept-suggestion"))

        assert resp.status_code == 409
        assert resp.json()["error_code"] == "task.not_a_suggestion"
        assert tasks.store["t_plain"] == before

    def test_accepting_twice_is_a_409_the_second_time(self, api):
        client, _, _ = api

        assert client.post(url("/tasks/t_sugg/accept-suggestion")).status_code == 200
        resp = client.post(url("/tasks/t_sugg/accept-suggestion"))

        assert resp.status_code == 409
        assert resp.json()["error_code"] == "task.not_a_suggestion"

    def test_a_foreign_task_is_a_404_like_an_unknown_one_and_writes_nothing(self, api):
        client, tasks, _ = api
        before = tasks.store["t_foreign"].model_copy(deep=True)

        foreign = client.post(url("/tasks/t_foreign/accept-suggestion"))
        unknown = client.post(url("/tasks/t_nope/accept-suggestion"))

        assert foreign.status_code == unknown.status_code == 404
        assert tasks.store["t_foreign"] == before


class TestDismiss:
    def test_dismissing_closes_the_suggestion_as_skipped_with_the_reason(self, api):
        client, tasks, notifications = api

        resp = client.post(url("/tasks/t_sugg/dismiss-suggestion"), json={"reason": "  Rain is forecast  "})

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "skipped"
        assert body["completion_notes"] == "Rain is forecast"
        # Never accepted: it stays a suggestion, so every reader that leaves suggestions out keeps doing so.
        assert body["suggested"] is True
        assert tasks.store["t_sugg"].status == TaskStatus.SKIPPED
        assert notifications.calls == []

    def test_the_body_is_optional(self, api):
        client, tasks, _ = api

        resp = client.post(url("/tasks/t_sugg_started/dismiss-suggestion"))

        assert resp.status_code == 200
        assert tasks.store["t_sugg_started"].status == TaskStatus.SKIPPED
        assert tasks.store["t_sugg_started"].completion_notes is None

    def test_an_unknown_body_field_is_a_422(self, api):
        client, tasks, _ = api

        resp = client.post(url("/tasks/t_sugg/dismiss-suggestion"), json={"status": "completed"})

        assert resp.status_code == 422
        assert tasks.store["t_sugg"].status == TaskStatus.PENDING

    def test_a_task_that_is_no_suggestion_is_a_409(self, api):
        client, tasks, _ = api

        resp = client.post(url("/tasks/t_plain/dismiss-suggestion"))

        assert resp.status_code == 409
        assert resp.json()["error_code"] == "task.not_a_suggestion"
        assert tasks.store["t_plain"].status == TaskStatus.PENDING

    def test_a_closed_suggestion_is_a_409(self, api):
        client, _, _ = api

        resp = client.post(url("/tasks/t_sugg_closed/dismiss-suggestion"))

        assert resp.status_code == 409
        assert resp.json()["error_code"] == "task.suggestion_closed"

    def test_a_foreign_task_is_a_404_and_writes_nothing(self, api):
        client, tasks, _ = api

        resp = client.post(url("/tasks/t_foreign/dismiss-suggestion"))

        assert resp.status_code == 404
        assert tasks.store["t_foreign"].status == TaskStatus.PENDING


class TestTheRoleGate:
    @pytest.mark.parametrize("action", ["accept-suggestion", "dismiss-suggestion"])
    def test_a_viewer_is_refused_with_403_and_nothing_is_written(self, action):
        client, tasks, _ = _build(TenantRole.VIEWER)
        before = tasks.store["t_sugg"].model_copy(deep=True)

        resp = client.post(url(f"/tasks/t_sugg/{action}"))

        assert resp.status_code == 403
        assert tasks.store["t_sugg"] == before

    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.LEAD])
    def test_grower_and_lead_may_decide(self, role):
        client, _, _ = _build(role)

        assert client.post(url("/tasks/t_sugg/accept-suggestion")).status_code == 200
