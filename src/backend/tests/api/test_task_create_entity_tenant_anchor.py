"""The task-create route runs the entity anchor before anything is written (#1102).

The guard's own decisions are unit-tested in
`tests/unit/domain/services/test_task_entity_guard.py`. This file asserts the
part a unit test structurally cannot see: that the **route** invokes it, invokes
it with the caller's tenant, and invokes it *before* the task is created — so a
refusal writes neither the task nor the `has_task` edge.

A gate placed after the create would answer 404 and still have stored the
cross-boundary reference, which is the entire finding. The task service is
therefore a recorder, and "refused" is asserted as *no create call*, never as a
status code alone.

## Real vs doubled

**Real**: the tasks router, its dependency graph, the real `TaskEntityGuard`, and
the error handler that shapes the 404. **Doubled**: the four entity services the
guard consults, and the task service.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.tasks.tenant_router import router as tasks_router
from app.common import auth as auth_mod
from app.common.dependencies import get_task_entity_guard, get_task_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.tenant_context import TenantContext
from app.domain.services.task_entity_guard import TaskEntityGuard

_MINE = "tenant_acme"


class _RecordingTaskService:
    """Records creates, so a refusal is provable as an absent call."""

    def __init__(self) -> None:
        self.created: list[Any] = []

    def create_task_idempotent(self, task: Any, *, actor_user_key: str = "") -> tuple[Any, bool]:
        self.created.append(task)
        task.key = "task_1"
        return task, True


class _ForeignEntityService:
    """Every lookup is a foreign row."""

    def get_plant(self, key, *, tenant_key=""):
        raise NotFoundError("PlantInstance", key)

    def get_run(self, key, *, tenant_key=""):
        raise NotFoundError("PlantingRun", key)

    def get_tank(self, key, *, tenant_key=""):
        raise NotFoundError("Tank", key)


class _OwnEntityService:
    def get_plant(self, key, *, tenant_key=""):
        return SimpleNamespace(key=key, tenant_key=_MINE)

    def get_run(self, key, *, tenant_key=""):
        return SimpleNamespace(key=key, tenant_key=_MINE)

    def get_tank(self, key, *, tenant_key=""):
        return SimpleNamespace(key=key, tenant_key=_MINE)


class _SiteService:
    def __init__(self, *, foreign: bool = False) -> None:
        self._foreign = foreign
        self.seen_tenants: list[str] = []

    def get_location(self, key):
        return SimpleNamespace(key=key, site_key="site_1", tenant_key="")

    def get_site(self, key, *, tenant_key=""):
        self.seen_tenants.append(tenant_key)
        if self._foreign:
            raise NotFoundError("Site", key)
        return SimpleNamespace(key=key, tenant_key=_MINE)


def _client(service: _RecordingTaskService, *, foreign: bool, sites: _SiteService | None = None) -> TestClient:
    entities: Any = _ForeignEntityService() if foreign else _OwnEntityService()
    site_service = sites if sites is not None else _SiteService(foreign=foreign)
    guard = TaskEntityGuard(lambda: entities, lambda: entities, lambda: entities, lambda: site_service)

    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(tasks_router, prefix="/api/v1/t/{tenant_slug}")
    # `account_type` is read by `_resolve_task_provenance`: an interactive user
    # gets origin=USER and cleared producer fields. Both create paths funnel
    # through this one endpoint, so the guard covers the FreeStyle path too.
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="user_1", account_type="user")
    app.dependency_overrides[get_task_service] = lambda: service
    app.dependency_overrides[get_task_entity_guard] = lambda: guard
    app.dependency_overrides[auth_mod.get_current_tenant] = lambda: TenantContext(
        tenant_key=_MINE, tenant_slug="acme", user_key="user_1", role=TenantRole.LEAD, admin_scopes=[]
    )
    return TestClient(app)


def _body(entity_type: str | None = None, entity_key: str | None = None) -> dict:
    # `name`, not `title` — and a first draft of this file used `title`, which
    # 422'd. The refusal tests passed anyway, because a 422 creates no task
    # either: `test_no_task_is_created` is only meaningful next to the status
    # assertion that proves the request got as far as the guard.
    body: dict = {"name": "Water the tomatoes"}
    if entity_type is not None:
        body["entity_type"] = entity_type
    if entity_key is not None:
        body["entity_key"] = entity_key
    return body


@pytest.fixture
def service() -> _RecordingTaskService:
    return _RecordingTaskService()


@pytest.mark.parametrize("entity_type", ["plant_instance", "planting_run", "tank", "location"])
class TestAForeignBindingIsRefused:
    def test_it_answers_404(self, service: _RecordingTaskService, entity_type: str) -> None:
        """404, not 403 — a 403 would confirm the key names a real entity somewhere."""
        response = _client(service, foreign=True).post("/api/v1/t/acme/tasks", json=_body(entity_type, "foreign_key"))

        assert response.status_code == 404, response.text

    def test_no_task_is_created(self, service: _RecordingTaskService, entity_type: str) -> None:
        """The assertion the status code cannot make.

        A guard running *after* the create would answer 404 with the task and its
        `has_task` edge already written — which is the finding, not the fix.
        """
        _client(service, foreign=True).post("/api/v1/t/acme/tasks", json=_body(entity_type, "foreign_key"))

        assert service.created == []


class TestOwnAndUnboundBindingsStillWork:
    @pytest.mark.parametrize("entity_type", ["plant_instance", "planting_run", "tank", "location"])
    def test_an_own_entity_is_accepted(self, service: _RecordingTaskService, entity_type: str) -> None:
        response = _client(service, foreign=False).post("/api/v1/t/acme/tasks", json=_body(entity_type, "e1"))

        assert response.status_code == 201, response.text
        assert len(service.created) == 1

    def test_an_unbound_task_is_accepted(self, service: _RecordingTaskService) -> None:
        response = _client(service, foreign=True).post("/api/v1/t/acme/tasks", json=_body())

        assert response.status_code == 201, response.text
        assert len(service.created) == 1

    def test_a_type_that_writes_no_edge_is_accepted(self, service: _RecordingTaskService) -> None:
        """`generic` and friends produce no edge, so there is nothing to anchor."""
        response = _client(service, foreign=True).post("/api/v1/t/acme/tasks", json=_body("generic", "whatever"))

        assert response.status_code == 201, response.text


class TestTheAnchorUsesTheCallersTenant:
    def test_the_site_lookup_carries_the_active_tenant(self, service: _RecordingTaskService) -> None:
        """Anchoring against the wrong tenant would pass every check and protect nothing."""
        sites = _SiteService()

        _client(service, foreign=False, sites=sites).post("/api/v1/t/acme/tasks", json=_body("location", "loc_1"))

        assert sites.seen_tenants == [_MINE]
