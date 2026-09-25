"""Cloning a task onto another entity is held to the same binding rule as creating one — #1864 sweep.

``POST /t/{slug}/tasks/{key}/clone`` accepts ``target_entity_key`` /
``target_entity_type``. Create and instantiate verify a binding with
``TaskEntityGuard`` (SEC-I01, #1102); clone did not, so the clone stored a
foreign entity key and the repository wrote a ``has_task`` edge from another
tenant's plant, run, location or tank to the new task.

The deployed ``app.main`` app, the real ``get_current_tenant``, the real guard
over tenant-scoped service doubles (``test_task_entity_guard``); only the
principal, the tenant store and the task service are doubled.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_task_entity_guard, get_task_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.task import Task
from app.domain.models.user import User
from app.domain.services.task_entity_guard import TaskEntityGuard
from tests.unit.domain.services.test_task_entity_guard import _MINE, _SiteService, _TenantScopedService


class _Tenants:
    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        if slug != "mine":
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=_MINE, slug="mine")

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        return SimpleNamespace(role=TenantRole.LEAD, admin_scopes=[], is_active=True) if tenant_key == _MINE else None

    def get_personal_tenant(self, user_key: str) -> None:
        return None


class _Tasks:
    def __init__(self) -> None:
        self.cloned: list[tuple] = []
        self.source = Task(
            _key="t1", tenant_key=_MINE, name="Gießen", entity_type="plant_instance", entity_key="plant_mine"
        )

    def get_task(self, key: str, *, tenant_key: str) -> Task:
        if key != "t1" or tenant_key != _MINE:
            raise NotFoundError("Task", key)
        return self.source

    def clone_task(
        self, key, due_date_offset_days=None, target_entity_key=None, target_entity_type=None, *, tenant_key
    ):
        self.cloned.append((target_entity_type, target_entity_key))
        return self.source.model_copy(update={"key": "t2", "entity_key": target_entity_key or "plant_mine"})


class _ForeignKeyAwareService(_TenantScopedService):
    """Owns only keys ending in ``_mine`` — everything else is another tenant's."""

    def __init__(self) -> None:
        super().__init__()

    def _check(self, key: str) -> None:
        if not key.endswith("_mine"):
            raise NotFoundError("Entity", key)

    def get_plant(self, key, *, tenant_key):
        self._check(key)

    def get_run(self, key, tenant_key=""):
        self._check(key)

    def get_tank(self, key, tenant_key=""):
        self._check(key)


@pytest.fixture
def tasks() -> _Tasks:
    return _Tasks()


@pytest.fixture
def client(tasks: _Tasks) -> Iterator[TestClient]:
    from app.main import app

    guard = TaskEntityGuard(
        _ForeignKeyAwareService, _ForeignKeyAwareService, _ForeignKeyAwareService, lambda: _SiteService()
    )
    app.dependency_overrides[get_current_user] = lambda: User(_key="lead", email="lead@example.org", display_name="L")
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_task_service] = lambda: tasks
    app.dependency_overrides[get_task_entity_guard] = lambda: guard
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


_CLONE = "/api/v1/t/mine/tasks/t1/clone"


@pytest.mark.parametrize(
    "body",
    [
        {"target_entity_key": "plant_theirs"},
        {"target_entity_key": "run_theirs", "target_entity_type": "planting_run"},
        {"target_entity_key": "tank_theirs", "target_entity_type": "tank"},
    ],
    ids=["plant-inherited-type", "run", "tank"],
)
def test_a_clone_onto_a_foreign_entity_is_refused(client: TestClient, tasks: _Tasks, body: dict) -> None:
    response = client.post(_CLONE, json=body)

    assert response.status_code == 404, response.text
    assert tasks.cloned == []


def test_a_clone_onto_an_own_entity_is_made(client: TestClient, tasks: _Tasks) -> None:
    response = client.post(_CLONE, json={"target_entity_key": "plant_mine"})

    assert response.status_code == 201, response.text
    assert tasks.cloned == [(None, "plant_mine")]
