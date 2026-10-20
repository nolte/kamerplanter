"""REQ-053 WP 7.8 / 7.9 (#2474, #2475) - the bed-template routes and ``place-template`` through the deployed app.

``app.main`` with the real ``BedTemplateService`` / ``GardenPlanService``, the real tenant gate and the in-memory
doubles of ``tests/support``. The unit tier shows what the services decide; this tier shows how it reads on the wire
and that every route sits behind the gate of §21.8 "Beetvorlage" - one negative per row and role (SR-010): a viewer
reads but neither creates, changes nor deletes; a grower creates and changes but does not delete; a system template
is a platform admin's, a tenant's role does not reach it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user, get_is_platform_admin
from app.common.dependencies import get_bed_template_service, get_garden_plan_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.bed_template import BedTemplate
from app.domain.models.site import SitePlan
from app.domain.models.user import User
from app.domain.services.bed_template_service import BedTemplateService
from app.domain.services.garden_plan_service import GardenPlanService
from tests.support.bed_template_fakes import FakeTemplates
from tests.support.garden_plan_fakes import OTHER_TENANT, SITE, TENANT, FakePlanRepo, FakeSites, make_site

_BASE = "/api/v1/t/own"
_RECT = {"kind": "rect", "origin": [0, 0], "width_m": 2, "length_m": 1, "rotation_deg": 0}


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


def _template(key: str, tenant: str | None, name: str) -> BedTemplate:
    return BedTemplate(_key=key, tenant_key=tenant, name=name, location_type_key="bed", default_geometry=_RECT)


@pytest.fixture
def templates() -> FakeTemplates:
    fake = FakeTemplates()
    fake.add(_template("sys_bed", None, "System bed"))
    fake.add(_template("own", TENANT, "Own bed"))
    fake.add(_template("theirs", OTHER_TENANT, "Their bed"))
    return fake


@pytest.fixture
def plan_repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(
        boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}, plan_revision=5
    )
    return FakePlanRepo(FakeSites(site))


@pytest.fixture
def client(templates: FakeTemplates, plan_repo: FakePlanRepo) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    service = BedTemplateService(templates)
    plans = GardenPlanService(plan_repo._sites, plan_repo, template_repo=templates)
    state = {"platform_admin": False}

    def build(role: TenantRole = TenantRole.GROWER, *, platform_admin: bool = False) -> TestClient:
        _Tenants.role = role
        state["platform_admin"] = platform_admin
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_is_platform_admin] = lambda: state["platform_admin"]
    app.dependency_overrides[get_bed_template_service] = lambda: service
    app.dependency_overrides[get_garden_plan_service] = lambda: plans
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


class TestTheRoutes:
    def test_list_create_patch_delete(self, client, templates: FakeTemplates) -> None:
        listed = client(TenantRole.VIEWER).get(f"{_BASE}/bed-templates")
        assert listed.status_code == 200, listed.text
        assert [t["key"] for t in listed.json()] == ["own", "sys_bed"]  # by name; never "theirs"
        assert {t["key"]: t["is_system"] for t in listed.json()} == {"own": False, "sys_bed": True}
        assert all("tenant_key" not in t and "created_by" not in t for t in listed.json())

        created = client(TenantRole.GROWER).post(
            f"{_BASE}/bed-templates",
            json={"name": "Herb bed", "location_type_key": "raised_bed", "default_geometry": _RECT, "height_m": 0.4},
        )
        assert created.status_code == 201, created.text
        key = created.json()["key"]
        assert (created.json()["is_system"], created.json()["height_m"]) == (False, 0.4)
        assert templates.templates[key].tenant_key == TENANT and templates.templates[key].created_by == "u_sabine"

        patched = client(TenantRole.GROWER).patch(
            f"{_BASE}/bed-templates/{key}", json={"name": "Herbs", "height_m": None}
        )
        assert patched.status_code == 200, patched.text
        assert (patched.json()["name"], patched.json()["height_m"]) == ("Herbs", None)

        assert client(TenantRole.LEAD).delete(f"{_BASE}/bed-templates/{key}").status_code == 204
        assert key not in templates.templates

    def test_the_list_is_bounded_by_the_page_parameters(self, client) -> None:
        response = client(TenantRole.VIEWER).get(f"{_BASE}/bed-templates", params={"limit": 1, "offset": 1})

        assert response.status_code == 200 and [t["key"] for t in response.json()] == ["sys_bed"]


class TestTheRoleMatrix:
    """§21.8 "Beetvorlage": Lesen alle, Anlegen/Ändern ab Gärtner, Löschen nur Leitung, global nur Plattform-Admin."""

    @pytest.mark.parametrize(
        ("method", "path", "body"),
        [
            ("POST", "/bed-templates", {"name": "T", "location_type_key": "bed", "default_geometry": _RECT}),
            ("PATCH", "/bed-templates/own", {"name": "T"}),
            ("DELETE", "/bed-templates/own", None),
        ],
        ids=["create", "change", "delete"],
    )
    def test_a_viewer_writes_nothing(self, client, templates: FakeTemplates, method: str, path: str, body) -> None:
        response = client(TenantRole.VIEWER).request(method, f"{_BASE}{path}", json=body)

        assert response.status_code == 403, response.text
        assert templates.writes == []

    def test_a_grower_cannot_delete(self, client, templates: FakeTemplates) -> None:
        response = client(TenantRole.GROWER).delete(f"{_BASE}/bed-templates/own")

        assert response.status_code == 403, response.text
        assert "own" in templates.templates

    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.LEAD])
    def test_a_tenant_cannot_change_or_delete_a_system_template(
        self, client, templates: FakeTemplates, role: TenantRole
    ) -> None:
        patched = client(role).patch(f"{_BASE}/bed-templates/sys_bed", json={"name": "Mine"})
        deleted = client(role).delete(f"{_BASE}/bed-templates/sys_bed")

        assert (patched.status_code, deleted.status_code) == (403, 403)
        assert templates.templates["sys_bed"].name == "System bed" and templates.writes == []

    def test_a_platform_admin_changes_and_deletes_a_system_template(self, client, templates: FakeTemplates) -> None:
        patched = client(TenantRole.LEAD, platform_admin=True).patch(
            f"{_BASE}/bed-templates/sys_bed", json={"name": "Curated"}
        )
        deleted = client(TenantRole.LEAD, platform_admin=True).delete(f"{_BASE}/bed-templates/sys_bed")

        assert (patched.status_code, patched.json()["is_system"], deleted.status_code) == (200, True, 204)
        assert "sys_bed" not in templates.templates


class TestRefusals:
    @pytest.mark.parametrize(
        ("method", "path", "body"),
        [
            ("PATCH", "/bed-templates/theirs", {"name": "T"}),
            ("DELETE", "/bed-templates/theirs", None),
        ],
    )
    def test_a_foreign_template_is_a_404(self, client, templates: FakeTemplates, method: str, path: str, body) -> None:
        response = client(TenantRole.LEAD, platform_admin=True).request(method, f"{_BASE}{path}", json=body)

        assert response.status_code == 404, response.text
        assert "Their bed" not in response.text and OTHER_TENANT not in response.text
        assert "theirs" in templates.templates and templates.writes == []

    def test_another_tenants_templates_are_not_listed_under_its_slug_either(self, client) -> None:
        response = client(TenantRole.VIEWER).get("/api/v1/t/other/bed-templates")

        assert [t["key"] for t in response.json()] == ["sys_bed", "theirs"]

    @pytest.mark.parametrize(
        "body",
        [
            {"name": "T", "location_type_key": "bed", "default_geometry": _RECT, "tenant_key": TENANT},
            {"name": "T", "location_type_key": "bed", "default_geometry": _RECT, "created_by": "u_x"},
            {"name": "T", "location_type_key": "bed", "default_geometry": _RECT, "height_m": 2},
            {"name": "T", "location_type_key": "bed", "default_geometry": _RECT, "default_layout": {"spacing_cm": 4}},
            {"name": "T", "location_type_key": "bed", "default_geometry": {"kind": "point", "origin": [0, 0]}},
            {"name": "T", "location_type_key": "bed", "default_geometry": _RECT, "soil_profile_defaults": {"ph": 6}},
            {"name": " ", "location_type_key": "bed", "default_geometry": _RECT},
        ],
        ids=["tenant_key", "created_by", "height", "spacing", "point", "soil ph", "blank name"],
    )
    def test_the_body_is_validated(self, client, templates: FakeTemplates, body: dict) -> None:
        response = client(TenantRole.GROWER).post(f"{_BASE}/bed-templates", json=body)

        assert response.status_code == 422, response.text
        assert templates.writes == []

    def test_a_location_type_that_does_not_exist_is_reference_not_found(self, client, templates) -> None:
        response = client(TenantRole.GROWER).post(
            f"{_BASE}/bed-templates",
            json={"name": "T", "location_type_key": "nope", "default_geometry": _RECT},
        )

        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "reference.not_found"
        assert templates.writes == []


class TestPlaceTemplate:
    _PATH = f"{_BASE}/sites/{SITE}/plan/place-template"

    def test_it_returns_the_batch_response(self, client, plan_repo: FakePlanRepo) -> None:
        response = client(TenantRole.GROWER).post(
            self._PATH,
            json={"template_key": "sys_bed", "origin": [4, 1], "rotation_deg": 90, "expected_revision": 5},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        (real,) = body["key_map"].values()
        assert body["plan_revision"] == 6 and body["derived"][real]["area_m2"] == 2.0
        assert plan_repo.locations[real].template_key == "sys_bed"

        plan = client(TenantRole.VIEWER).get(f"{_BASE}/sites/{SITE}/plan")
        assert plan.status_code == 200, plan.text
        (placed,) = [loc for loc in plan.json()["locations"] if loc["key"] == real]
        assert placed["template_key"] == "sys_bed"  # provenance is part of the read model

    def test_a_viewer_places_nothing(self, client, plan_repo: FakePlanRepo) -> None:
        response = client(TenantRole.VIEWER).post(
            self._PATH, json={"template_key": "sys_bed", "origin": [4, 1], "expected_revision": 5}
        )

        assert response.status_code == 403, response.text
        assert plan_repo.applied == []

    def test_a_stale_revision_is_409(self, client, plan_repo: FakePlanRepo) -> None:
        response = client(TenantRole.GROWER).post(
            self._PATH, json={"template_key": "sys_bed", "origin": [4, 1], "expected_revision": 3}
        )

        assert response.status_code == 409, response.text
        assert response.json()["details"][0]["code"] == "plan.revision_conflict"

    def test_a_foreign_template_is_422_reference_not_found(self, client, plan_repo: FakePlanRepo) -> None:
        response = client(TenantRole.GROWER).post(
            self._PATH, json={"template_key": "theirs", "origin": [4, 1], "expected_revision": 5}
        )

        assert response.status_code == 422, response.text
        assert response.json()["details"][0]["code"] == "reference.not_found"
        assert plan_repo.applied == []

    def test_a_bed_outside_the_boundary_is_422(self, client, plan_repo: FakePlanRepo) -> None:
        response = client(TenantRole.GROWER).post(
            self._PATH, json={"template_key": "sys_bed", "origin": [9.5, 9.5], "expected_revision": 5}
        )

        assert response.status_code == 422, response.text
        assert "geometry.outside_parent" in {d["code"] for d in response.json()["details"]}

    @pytest.mark.parametrize(
        "body",
        [
            {"template_key": "sys_bed", "origin": [4, 1]},
            {"template_key": "sys_bed", "origin": [4], "expected_revision": 5},
            {"template_key": "sys_bed", "origin": [4, 1], "rotation_deg": 360, "expected_revision": 5},
            {"template_key": "", "origin": [4, 1], "expected_revision": 5},
            {"template_key": "sys_bed", "origin": [4, 1], "expected_revision": 5, "name": "x"},
        ],
        ids=["no revision", "short origin", "rotation 360", "blank key", "extra field"],
    )
    def test_the_body_is_validated(self, client, plan_repo: FakePlanRepo, body: dict) -> None:
        response = client(TenantRole.GROWER).post(self._PATH, json=body)

        assert response.status_code == 422, response.text
        assert plan_repo.applied == []

    def test_a_foreign_site_is_a_404(self, client) -> None:
        response = client(TenantRole.GROWER).post(
            f"{_BASE}/sites/site_foreign/plan/place-template",
            json={"template_key": "sys_bed", "origin": [4, 1], "expected_revision": 5},
        )

        assert response.status_code == 404, response.text
