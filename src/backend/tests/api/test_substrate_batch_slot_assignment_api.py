"""``POST /substrates/batches/{batch_key}/assign-slot/{slot_key}`` stays inside the caller's tenant — #1864.

Through the deployed ``app.main`` app: the tenant is resolved by the real
``get_active_tenant_context`` from the real ``_resolve_active_tenant`` (personal
tenant, or ``X-Active-Tenant``), and the real ``SubstrateService`` decides. Only
the principal and the stores are doubled.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_substrate_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.user import User
from app.domain.services.substrate_service import SubstrateService
from tests.unit.domain.services.test_substrate_batch_slot_assignment_scope import _Anchors, _SubstrateRepo

_ROLES = {"grower": TenantRole.GROWER, "viewer": TenantRole.VIEWER}


class _TenantService:
    """The caller's personal tenant is ``t_a``; they hold nothing in ``t_b``."""

    def __init__(self, role: TenantRole) -> None:
        self._role = role

    def get_personal_tenant(self, user_key: str) -> SimpleNamespace:
        return SimpleNamespace(key="t_a", slug="personal-a")

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        if tenant_key == "t_a":
            return SimpleNamespace(role=self._role, admin_scopes=[], is_active=True)
        return None

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        tenants = {"personal-a": "t_a", "club-b": "t_b"}
        if slug not in tenants:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=tenants[slug], slug=slug)


@pytest.fixture
def repo() -> _SubstrateRepo:
    return _SubstrateRepo()


@pytest.fixture(params=["grower"])
def client(request: pytest.FixtureRequest, repo: _SubstrateRepo) -> Iterator[TestClient]:
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="caller", email="caller@example.org", display_name="Caller"
    )
    app.dependency_overrides[get_tenant_service] = lambda: _TenantService(_ROLES[request.param])
    app.dependency_overrides[get_substrate_service] = lambda: SubstrateService(repo, slot_anchors=_Anchors())  # type: ignore[arg-type]
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _link(client: TestClient, batch: str, slot: str, **headers: str):
    return client.post(f"/api/v1/substrates/batches/{batch}/assign-slot/{slot}", headers=headers)


@pytest.mark.parametrize(
    ("batch", "slot"),
    [("b_b", "slot_b"), ("b_b", "slot_a"), ("b_a", "slot_b")],
    ids=["both-of-b", "b-batch-into-a-slot", "a-batch-into-b-slot"],
)
def test_a_member_of_a_cannot_link_anything_of_b(
    client: TestClient, repo: _SubstrateRepo, batch: str, slot: str
) -> None:
    response = _link(client, batch, slot)

    assert response.status_code == 404, response.text
    assert repo.edges == []


def test_naming_the_other_tenant_in_the_header_is_refused(client: TestClient, repo: _SubstrateRepo) -> None:
    response = _link(client, "b_b", "slot_b", **{"X-Active-Tenant": "club-b"})

    assert response.status_code == 403
    assert repo.edges == []


def test_a_grower_links_their_own_batch_to_their_own_slot(client: TestClient, repo: _SubstrateRepo) -> None:
    response = _link(client, "b_a", "slot_a")

    assert response.status_code == 201, response.text
    assert repo.edges == [("b_a", "slot_a")]


@pytest.mark.parametrize("client", ["viewer"], indirect=True)
def test_a_viewer_may_not_link(client: TestClient, repo: _SubstrateRepo) -> None:
    response = _link(client, "b_a", "slot_a")

    assert response.status_code == 403
    assert repo.edges == []
