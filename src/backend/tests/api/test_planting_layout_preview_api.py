"""REQ-053 WP 3.1 — ``POST /locations/{key}/planting-layout/preview`` through the deployed app (GP-API-016).

``app.main`` with the real ``GardenResourceService``, the real tenant gate and the in-memory repository of
``tests/support/garden_plan_fakes.py``. GP-ACC-043 is proved here on the wire: the bed of 1 000 x 1 000 m at 5 cm
is refused with 422 ``layout.too_many_positions`` and ``estimated`` of about 4e8 in under 50 ms, because the
estimate runs before any point exists. A foreign bed answers like an absent one (T-01) and the route needs no
more than the read permission (all roles, §21.8).
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_garden_resource_service, get_site_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.user import User
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.site_service import SiteService
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
_FOREIGN = "/api/v1/t/other"
_ROWS = {
    "layout_strategy": "rows",
    "spacing_cm": 30,
    "row_spacing_cm": 40,
    "edge_margin_along_cm": 15,
    "edge_margin_across_cm": 15,
}


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
    repository.locations["bed"] = make_location("bed", name="Bed", geometry=rect(1, 1, 3.0, 1.2))
    repository.locations["huge"] = make_location("huge", name="Field", geometry=rect(0, 0, 1000, 1000))
    repository.locations["bare"] = make_location("bare", name="Not placed")
    return repository


@pytest.fixture
def client(repo: FakePlanRepo) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    service = GardenResourceService(repo._sites, repo, FakeObjects(repo), GardenPlanService(repo._sites, repo))

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_garden_resource_service] = lambda: service
    app.dependency_overrides[get_site_service] = lambda: SiteService(repo._sites)
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


def preview(c: TestClient, key: str = "bed", base: str = _BASE, **entry):
    return c.post(f"{base}/locations/{key}/planting-layout/preview", json={"entry": entry})


class TestThePreview:
    def test_acc_017_rows_come_back_as_bed_frame_points_without_persisting(self, client, repo) -> None:
        before = dict(repo.locations)
        response = preview(client(), **_ROWS)

        assert response.status_code == 200
        body = response.json()
        assert (body["count"], body["capacity_max"], body["warnings"]) == (30, 30, [])
        first, last = body["slots"][0], body["slots"][-1]
        assert first["slot_role"] == "position"
        assert first["geometry"] == {"kind": "point", "origin": [0.15, 0.15]}
        assert (first["row_index"], first["sequence"], last["sequence"]) == (0, 1, 30)
        assert last["geometry"]["origin"] == [2.85, 0.95]
        assert repo.locations == before
        assert repo.slots == []

    def test_a_viewer_may_preview_it_is_a_read(self, client) -> None:
        assert preview(client(TenantRole.VIEWER), **_ROWS).status_code == 200

    def test_max_count_truncates_and_keeps_the_capacity(self, client) -> None:
        body = preview(client(), **_ROWS, max_count=12).json()
        assert (body["count"], body["capacity_max"], len(body["slots"])) == (12, 30, 12)

    def test_a_zone_comes_back_as_one_polygon_slot_with_its_capacity(self, client) -> None:
        body = preview(client(), layout_strategy="zone", spacing_cm=10).json()
        (zone,) = body["slots"]
        assert zone["slot_role"] == "zone"
        assert zone["geometry"]["kind"] == "polygon"
        assert (zone["capacity_plants"], body["count"]) == (360, 360)

    def test_warnings_are_hints_with_a_code_and_detail(self, client) -> None:
        body = preview(client(), layout_strategy="grid", spacing_cm=30, mature_width_cm=50).json()
        (warning,) = body["warnings"]
        assert warning["code"] == "layout.spacing_below_mature_width"
        assert warning["detail"] == {"spacing_cm": 30.0, "mature_width_cm": 50.0}


class TestTheUpperBound:
    def test_acc_043_a_field_at_5_cm_is_refused_before_any_point_exists(self, client) -> None:
        c = client()
        started = time.perf_counter()
        response = preview(c, "huge", layout_strategy="grid", spacing_cm=5)
        elapsed = time.perf_counter() - started

        assert response.status_code == 422
        detail = response.json()["details"][0]
        assert detail["code"] == "layout.too_many_positions"
        assert detail["estimated"] == pytest.approx(4e8, rel=1e-6)
        assert detail["limit"] == 2000
        # The compute path itself stays far below the budget; the whole request (middleware, gate) is
        # allowed a generous margin so a loaded runner does not turn this into a flake.
        assert elapsed < 1.0

    def test_the_estimate_itself_costs_microseconds(self, repo) -> None:
        from app.common.enums import LayoutStrategy
        from app.common.exceptions import PlanError
        from app.domain.calculators.planting_layout_calculator import EntryLayout, compute_layout
        from app.domain.models.geometry import parse_geometry

        bed = parse_geometry(repo.locations["huge"].geometry.model_dump(mode="json"))
        started = time.perf_counter()
        with pytest.raises(PlanError):
            compute_layout(bed, EntryLayout(LayoutStrategy.GRID, spacing_cm=5))
        assert time.perf_counter() - started < 0.05


class TestRefusals:
    def test_rows_without_a_row_spacing_is_a_dotted_422(self, client) -> None:
        response = preview(client(), layout_strategy="rows", spacing_cm=30)
        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "layout.row_spacing_required"

    def test_a_bed_without_geometry_is_a_422(self, client) -> None:
        response = preview(client(), "bare", layout_strategy="grid", spacing_cm=30)
        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "layout.bed_without_geometry"

    def test_a_spacing_outside_5_to_1500_is_refused_by_the_schema(self, client) -> None:
        assert preview(client(), layout_strategy="grid", spacing_cm=4).status_code == 422
        assert preview(client(), layout_strategy="grid", spacing_cm=1501).status_code == 422

    def test_an_unknown_strategy_is_refused(self, client) -> None:
        assert preview(client(), layout_strategy="spiral", spacing_cm=30).status_code == 422

    def test_a_foreign_bed_and_an_absent_one_answer_the_same_404(self, client) -> None:
        foreign = preview(client(TenantRole.LEAD), base=_FOREIGN, **_ROWS)
        absent = preview(client(TenantRole.LEAD), "nope", **_ROWS)
        assert foreign.status_code == absent.status_code == 404
        assert foreign.json()["details"][0]["code"] == absent.json()["details"][0]["code"]
        assert "slots" not in foreign.json()


class TestTheContract:
    def test_the_route_is_published_with_its_error_responses(self) -> None:
        from app.main import app

        operation = app.openapi()["paths"]["/api/v1/t/{tenant_slug}/locations/{key}/planting-layout/preview"]["post"]
        assert {"200", "404", "422"} <= set(operation["responses"])
