"""REQ-053 WP 10.11 (#2832, W-016) - the tent rules of a location on the wire.

``app.main`` with the real ``GardenResourceService``, the real tenant gate and the in-memory repository of
``tests/support/garden_plan_fakes.py``: ``PATCH /locations/{key}`` takes ``adjacency_factor`` and ``lighting`` (a value
the model refuses is 422, never 500), ``GET /locations/{key}`` answers them, and the summary carries
``supports_layout`` and the light-schedule hints of a tent.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_garden_resource_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.garden_plan import BedCounters
from app.domain.models.tent_hint import PlantPhotoperiod
from app.domain.models.user import User
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    FakeObjects,
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


@pytest.fixture
def repo() -> FakePlanRepo:
    repository = FakePlanRepo(FakeSites(make_site()))
    repository.locations["tent"] = make_location(
        "tent", name="Zelt", geometry=rect(1, 1, 1.2, 1.2), location_type_key="tent"
    )
    repository.dispatched = []
    return repository


@pytest.fixture
def client(repo: FakePlanRepo) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    service = GardenResourceService(
        repo._sites,
        repo,
        FakeObjects(repo),
        GardenPlanService(repo._sites, repo),
        dispatch_adjacency=repo.dispatched.append,
    )

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_garden_resource_service] = lambda: service
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


class TestPatch:
    def test_a_grower_sets_factor_and_lighting(self, client, repo) -> None:
        body = {"adjacency_factor": 2.0, "lighting": {"lamp_height_cm": 180, "canopy_distance_cm": 35}}

        response = client().patch(f"{_BASE}/locations/tent", json=body)

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["adjacency_factor"] == 2.0
        assert data["lighting"] == {"lamp_height_cm": 180.0, "canopy_distance_cm": 35.0, "fixture_geometry": None}
        assert repo.dispatched == ["tent"]

    def test_the_location_reads_answer_them(self, client) -> None:
        """``LocationResponse`` carries both; the summary (a ``LocationResponse``) is the read the page uses."""
        client().patch(f"{_BASE}/locations/tent", json={"adjacency_factor": 1.2})

        data = client().get(f"{_BASE}/locations/tent/summary").json()

        assert data["adjacency_factor"] == 1.2
        assert data["lighting"] is None

    @pytest.mark.parametrize(
        "body",
        [
            {"adjacency_factor": 0},
            {"adjacency_factor": 11},
            {"adjacency_factor": "2"},
            {"lighting": {"lamp_height_cm": 50, "canopy_distance_cm": 70}},
            {"lighting": {"lamp_height_cm": 2000}},
            {"lighting": {"lamp_height_cm": 100, "watts": 600}},
        ],
        ids=["factor zero", "factor above ten", "factor string", "canopy above lamp", "lamp too high", "unknown key"],
    )
    def test_a_refused_value_is_422_and_writes_nothing(self, client, repo, body) -> None:
        response = client().patch(f"{_BASE}/locations/tent", json=body)

        assert response.status_code == 422, response.text
        assert repo.field_updates == []

    def test_a_viewer_gets_403(self, client, repo) -> None:
        response = client(TenantRole.VIEWER).patch(f"{_BASE}/locations/tent", json={"adjacency_factor": 2.0})

        assert response.status_code == 403
        assert repo.field_updates == []

    def test_another_tenants_location_is_404(self, client, repo) -> None:
        response = client().patch("/api/v1/t/other/locations/tent", json={"adjacency_factor": 2.0})

        assert response.status_code == 404
        assert repo.field_updates == []


class TestSummary:
    def test_a_tent_supports_a_layout(self, client) -> None:
        data = client().get(f"{_BASE}/locations/tent/summary").json()

        assert (data["supports_layout"], data["is_bed"], data["tent_hints"]) == (True, False, [])

    def test_the_conflict_hint_appears_and_disappears(self, client, repo) -> None:
        repo.counters["tent"] = BedCounters(active_plant_count=2)
        repo.photoperiods["tent"] = [
            PlantPhotoperiod("p1", "Vegetative", 18.0),
            PlantPhotoperiod("p2", "Flowering", 12.0),
        ]

        hints = client().get(f"{_BASE}/locations/tent/summary").json()["tent_hints"]

        assert hints == [
            {
                "code": "tent.photoperiod_conflict",
                "severity": "warning",
                "groups": [
                    {"photoperiod_hours": 18.0, "plant_count": 1, "phase_names": ["Vegetative"]},
                    {"photoperiod_hours": 12.0, "plant_count": 1, "phase_names": ["Flowering"]},
                ],
                "unknown_plant_count": 0,
            }
        ]

        repo.photoperiods["tent"] = [
            PlantPhotoperiod("p1", "Flowering", 12.0),
            PlantPhotoperiod("p2", "Flowering", 12.0),
        ]

        assert client().get(f"{_BASE}/locations/tent/summary").json()["tent_hints"] == []
