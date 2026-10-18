"""REQ-053 WP 3.3 (#2393) — the manual adjacency routes through the deployed app (SR-021, GP-FR-130).

``app.main`` with the real ``AdjacencyService``, the real tenant gate and the in-memory plan repository. The
unit tier shows what the service decides; this tier shows the status codes, the gate per role and that the
refusals reach the wire before anything is written to the graph.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_adjacency_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.interfaces.graph_repository import AdjacencySync
from app.domain.models.site import Slot
from app.domain.models.user import User
from app.domain.services.adjacency_service import AdjacencyService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)

_BASE = "/api/v1/t/own"


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


class _Graph:
    def __init__(self) -> None:
        self.manual: list[tuple] = []
        self.removed: list[tuple] = []

    def set_adjacent_slots(self, a, b, *, distance_cm=None, source="derived"):
        self.manual.append((a, b, distance_cm, source))

    def remove_manual_adjacency(self, a, b):
        self.removed.append((a, b))
        return 2

    def sync_derived_adjacency(self, slot_keys, pairs):  # pragma: no cover - not reached by these routes
        return AdjacencySync()


def _slot(key: str, location_key: str) -> Slot:
    return Slot.model_validate({"_key": key, "slot_id": f"{key.upper()}_X", "location_key": location_key})


@pytest.fixture
def graph() -> _Graph:
    return _Graph()


@pytest.fixture
def client(graph: _Graph) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    own = make_site()
    elsewhere = make_site().model_copy(update={"key": "site_2"})
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"})
    sites = FakeSites(own, elsewhere, foreign)
    repo = FakePlanRepo(sites)
    repo.locations["bed"] = make_location("bed", geometry=rect(1, 1, 2, 1))
    repo.locations["far"] = make_location("far").model_copy(update={"site_key": "site_2"})
    repo.locations["alien"] = make_location("alien").model_copy(update={"site_key": "site_foreign"})
    repo.slots = [_slot("a", "bed"), _slot("b", "bed"), _slot("f", "far"), _slot("z", "alien")]
    service = AdjacencyService(sites, repo, graph)

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_adjacency_service] = lambda: service
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


class TestSettingAManualEdge:
    def test_a_grower_sets_it_with_a_distance(self, client, graph) -> None:
        response = client().put(f"{_BASE}/slots/a/adjacent/b", json={"distance_cm": 35})

        assert response.status_code == 204
        assert graph.manual == [("a", "b", 35.0, "manual")]

    def test_the_body_is_optional(self, client, graph) -> None:
        assert client().put(f"{_BASE}/slots/a/adjacent/b").status_code == 204
        assert graph.manual == [("a", "b", None, "manual")]

    def test_a_slot_of_another_site_is_422_with_the_published_code(self, client, graph) -> None:
        response = client().put(f"{_BASE}/slots/a/adjacent/f")

        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "adjacency.different_site"
        assert graph.manual == []

    def test_a_slot_of_a_foreign_tenant_is_404_like_an_unknown_one(self, client, graph) -> None:
        foreign = client().put(f"{_BASE}/slots/a/adjacent/z")
        unknown = client().put(f"{_BASE}/slots/a/adjacent/nope")

        assert foreign.status_code == unknown.status_code == 404
        assert foreign.json()["message"].replace("z", "?") == unknown.json()["message"].replace("nope", "?")
        assert graph.manual == []

    def test_the_other_tenants_url_cannot_reach_the_slots(self, client, graph) -> None:
        assert client(TenantRole.LEAD).put("/api/v1/t/other/slots/a/adjacent/b").status_code == 404
        assert graph.manual == []

    def test_a_viewer_never_reaches_the_service(self, client, graph) -> None:
        assert client(TenantRole.VIEWER).put(f"{_BASE}/slots/a/adjacent/b").status_code == 403
        assert graph.manual == []

    def test_an_unknown_body_field_is_a_422(self, client, graph) -> None:
        assert client().put(f"{_BASE}/slots/a/adjacent/b", json={"source": "derived"}).status_code == 422
        assert graph.manual == []

    def test_a_slot_cannot_be_its_own_neighbour(self, client, graph) -> None:
        response = client().put(f"{_BASE}/slots/a/adjacent/a")
        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "adjacency.same_slot"


class TestRemovingAManualEdge:
    def test_a_grower_removes_it(self, client, graph) -> None:
        assert client().delete(f"{_BASE}/slots/a/adjacent/b").status_code == 204
        assert graph.removed == [("a", "b")]

    def test_the_same_site_rule_applies(self, client, graph) -> None:
        assert client().delete(f"{_BASE}/slots/a/adjacent/f").status_code == 422
        assert client().delete(f"{_BASE}/slots/a/adjacent/z").status_code == 404
        assert graph.removed == []

    def test_a_viewer_is_refused(self, client, graph) -> None:
        assert client(TenantRole.VIEWER).delete(f"{_BASE}/slots/a/adjacent/b").status_code == 403
        assert graph.removed == []
