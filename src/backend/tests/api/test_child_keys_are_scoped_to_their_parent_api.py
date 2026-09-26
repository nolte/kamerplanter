"""#1867 through the deployed app: a member of tenant A cannot touch tenant B's child rows.

The real ``get_current_tenant`` resolves ``/t/club-a/``; the real
``PlantingRunService`` / ``TankService`` / ``FertilizerService`` decide over the
repository doubles of ``tests/unit/domain/services/test_child_keys_are_scoped_to_their_parent.py``.
Only the principal and the stores are doubled. The routes' request shapes are
unchanged by the fix, so this file runs unmodified against the develop code —
which is how it shows the defect.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import (
    get_fertilizer_service,
    get_planting_run_service,
    get_tank_service,
    get_tenant_service,
)
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.user import User
from app.domain.services.fertilizer_service import FertilizerService
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.tank_service import TankService
from tests.unit.domain.services.test_child_keys_are_scoped_to_their_parent import _FertRepo, _RunRepo, _TankRepo


class _TenantService:
    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        if slug != "club-a":
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key="t_a", slug="club-a")

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        if tenant_key == "t_a":
            return SimpleNamespace(role=TenantRole.LEAD, admin_scopes=[], is_active=True)
        return None

    def get_personal_tenant(self, user_key: str) -> None:
        return None


@pytest.fixture
def repos() -> SimpleNamespace:
    return SimpleNamespace(run=_RunRepo(), tank=_TankRepo(), fert=_FertRepo())


@pytest.fixture
def client(repos: SimpleNamespace) -> Iterator[TestClient]:
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: User(_key="lead", email="lead@example.org", display_name="L")
    app.dependency_overrides[get_tenant_service] = _TenantService
    app.dependency_overrides[get_planting_run_service] = lambda: PlantingRunService(repos.run, None, None)  # type: ignore[arg-type]
    app.dependency_overrides[get_tank_service] = lambda: TankService(repos.tank, None)  # type: ignore[arg-type]
    app.dependency_overrides[get_fertilizer_service] = lambda: FertilizerService(repos.fert)  # type: ignore[arg-type]
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


_BASE = "/api/v1/t/club-a"


def test_b_s_run_entry_is_neither_updated_nor_deleted_through_a_s_run(
    client: TestClient, repos: SimpleNamespace
) -> None:
    put = client.put(f"{_BASE}/planting-runs/run_a/entries/e_b", json={"quantity": 9})
    delete = client.delete(f"{_BASE}/planting-runs/run_a/entries/e_b")

    assert (put.status_code, delete.status_code) == (404, 404)
    assert repos.run.writes == []
    assert repos.run.entries["e_b"].tenant_key == "t_b"


def test_b_s_tank_schedule_is_neither_updated_nor_deleted_through_a_s_tank(
    client: TestClient, repos: SimpleNamespace
) -> None:
    put = client.put(f"{_BASE}/tanks/tank_a/schedules/s_b", json={"interval_days": 1})
    delete = client.delete(f"{_BASE}/tanks/tank_a/schedules/s_b")

    assert (put.status_code, delete.status_code) == (404, 404)
    assert repos.tank.writes == []


def test_b_s_incompatibility_cannot_be_removed_through_a_global_product(
    client: TestClient, repos: SimpleNamespace
) -> None:
    response = client.delete(f"{_BASE}/fertilizers/g1/incompatibilities/f_b")

    assert response.status_code == 404
    assert repos.fert.removed == []


def test_a_global_to_global_edge_is_not_a_member_s_to_remove(client: TestClient, repos: SimpleNamespace) -> None:
    response = client.delete(f"{_BASE}/fertilizers/g1/incompatibilities/g2")

    assert response.status_code == 403
    assert repos.fert.removed == []


def test_own_children_still_work(client: TestClient, repos: SimpleNamespace) -> None:
    assert client.put(f"{_BASE}/planting-runs/run_a/entries/e_a", json={"quantity": 4}).status_code == 200
    assert client.put(f"{_BASE}/tanks/tank_a/schedules/s_a", json={"interval_days": 14}).status_code == 200
    assert client.delete(f"{_BASE}/fertilizers/f_a/incompatibilities/g1").status_code == 204
