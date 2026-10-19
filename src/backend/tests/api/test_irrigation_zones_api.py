"""REQ-053 WP 7.1 (#2467) — the irrigation-zone routes through the deployed app.

``app.main`` with the real ``IrrigationZoneService``, the real tenant gate and the in-memory doubles of
``tests/support/{garden_plan,irrigation_zone}_fakes.py``. The unit tier shows what the service decides; this tier
shows how it reads on the wire and that every route sits behind the gate of §21.8 "Bewässerungszone" — one
negative per row and role (SR-010): a viewer reads but neither creates, changes, assigns nor deletes; a grower
does all of that except delete.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_irrigation_zone_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.garden_object import GardenObject
from app.domain.models.irrigation_zone import IrrigationZone
from app.domain.models.user import User
from app.domain.services.irrigation_zone_service import IrrigationZoneService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakeObjects,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)
from tests.support.irrigation_zone_fakes import FakeZones

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
def zones() -> FakeZones:
    repo = FakePlanRepo(FakeSites(make_site()))
    repo.locations["bed"] = make_location("bed", name="Bed")
    repo.locations["bed_2"] = make_location("bed_2", name="Bed 2")
    repo.objects["barrel"] = GardenObject.model_validate(
        {
            "_key": "barrel",
            "site_key": SITE,
            "object_type": "water_source",
            "geometry": {"kind": "point", "origin": [1.0, 1.0]},
            "props": {"object_type": "water_source", "water_source_kind": "rain_barrel"},
        }
    )
    fake = FakeZones(repo)
    fake.add(IrrigationZone(_key="zone_1", tenant_key=TENANT, site_key=SITE, name="South", irrigation_type="drip"))
    fake.add(IrrigationZone(_key="zone_foreign", tenant_key=OTHER_TENANT, site_key="site_x", name="Theirs"))
    return fake


@pytest.fixture
def client(zones: FakeZones) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    repo = zones._repo
    service = IrrigationZoneService(zones, repo._sites, FakeObjects(repo))

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_irrigation_zone_service] = lambda: service
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


def _code(response) -> str:
    payload = response.json()
    details = payload.get("details") or []
    return str(details[0].get("code")) if details else str(payload.get("error_code") or payload.get("code"))


class TestTheRoutes:
    def test_create_list_get_patch_assign_delete(self, client, zones: FakeZones) -> None:
        created = client(TenantRole.GROWER).post(
            f"{_BASE}/sites/{SITE}/irrigation-zones",
            json={"name": "North", "irrigation_type": "soaker_hose", "water_source_key": "barrel", "color": "#1565C0"},
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert (body["site_key"], body["irrigation_type"], body["location_keys"]) == (SITE, "soaker_hose", [])
        assert "flow_rate_ha_entity_id" not in body and "tenant_key" not in body
        key = body["key"]

        listed = client(TenantRole.VIEWER).get(f"{_BASE}/sites/{SITE}/irrigation-zones", params={"limit": 1})
        assert listed.status_code == 200 and [z["key"] for z in listed.json()] == [key]  # "North" < "South"

        assigned = client(TenantRole.GROWER).put(
            f"{_BASE}/irrigation-zones/{key}/locations", json={"location_keys": ["bed", "bed_2"]}
        )
        assert assigned.status_code == 200, assigned.text
        assert (assigned.json()["location_keys"], assigned.json()["added"]) == (["bed", "bed_2"], ["bed", "bed_2"])

        moved = client(TenantRole.GROWER).put(
            f"{_BASE}/irrigation-zones/zone_1/locations", json={"location_keys": ["bed"]}
        )
        assert moved.json()["moved_from"] == {"bed": key}
        assert client(TenantRole.VIEWER).get(f"{_BASE}/irrigation-zones/{key}").json()["location_keys"] == ["bed_2"]

        patched = client(TenantRole.GROWER).patch(
            f"{_BASE}/irrigation-zones/{key}", json={"water_source_key": None, "schedule_hint": "evenings"}
        )
        assert patched.status_code == 200, patched.text
        assert (patched.json()["water_source_key"], patched.json()["schedule_hint"]) == (None, "evenings")

        deleted = client(TenantRole.LEAD).delete(f"{_BASE}/irrigation-zones/{key}")
        assert deleted.status_code == 204, deleted.text
        assert zones._repo.locations["bed_2"].irrigation_zone_key is None
        assert client(TenantRole.VIEWER).get(f"{_BASE}/irrigation-zones/{key}").status_code == 404


class TestTheRoleMatrix:
    """§21.8 "Bewässerungszone": Lesen alle, Anlegen/Ändern ab Gärtner, Löschen nur Leitung (SR-010)."""

    @pytest.mark.parametrize(
        ("method", "path", "body"),
        [
            ("POST", f"/sites/{SITE}/irrigation-zones", {"name": "Z"}),
            ("PATCH", "/irrigation-zones/zone_1", {"name": "Z"}),
            ("PUT", "/irrigation-zones/zone_1/locations", {"location_keys": ["bed"]}),
            ("DELETE", "/irrigation-zones/zone_1", None),
        ],
        ids=["create", "change", "assign", "delete"],
    )
    def test_a_viewer_writes_nothing(self, client, zones: FakeZones, method: str, path: str, body) -> None:
        response = client(TenantRole.VIEWER).request(method, f"{_BASE}{path}", json=body)

        assert response.status_code == 403, response.text
        assert set(zones.zones) == {"zone_1", "zone_foreign"} and zones.covers == {} and zones.updates == []

    def test_a_grower_cannot_delete(self, client, zones: FakeZones) -> None:
        response = client(TenantRole.GROWER).delete(f"{_BASE}/irrigation-zones/zone_1")

        assert response.status_code == 403, response.text
        assert "zone_1" in zones.zones

    @pytest.mark.parametrize("path", [f"/sites/{SITE}/irrigation-zones", "/irrigation-zones/zone_1"])
    def test_a_viewer_reads(self, client, path: str) -> None:
        assert client(TenantRole.VIEWER).get(f"{_BASE}{path}").status_code == 200


class TestRefusals:
    @pytest.mark.parametrize(
        ("method", "path", "body"),
        [
            ("GET", "/sites/site_x/irrigation-zones", None),
            ("POST", "/sites/site_x/irrigation-zones", {"name": "Z"}),
            ("GET", "/irrigation-zones/zone_foreign", None),
            ("PATCH", "/irrigation-zones/zone_foreign", {"name": "Z"}),
            ("PUT", "/irrigation-zones/zone_foreign/locations", {"location_keys": []}),
            ("DELETE", "/irrigation-zones/zone_foreign", None),
        ],
    )
    def test_a_foreign_resource_is_a_404(self, client, zones: FakeZones, method: str, path: str, body) -> None:
        response = client(TenantRole.LEAD).request(method, f"{_BASE}{path}", json=body)

        assert response.status_code == 404, response.text
        assert "Theirs" not in response.text and OTHER_TENANT not in response.text
        assert "zone_foreign" in zones.zones

    def test_a_foreign_bed_is_reference_not_found_at_its_index(self, client, zones: FakeZones) -> None:
        response = client(TenantRole.GROWER).put(
            f"{_BASE}/irrigation-zones/zone_1/locations", json={"location_keys": ["bed", "bed_gone"]}
        )

        assert response.status_code == 422, response.text
        assert [(d["field"], d["code"]) for d in response.json()["details"]] == [
            ("location_keys[1]", "reference.not_found")
        ]
        assert zones.covers == {}

    def test_a_coupling_field_is_422_until_wp_7_4(self, client) -> None:
        response = client(TenantRole.LEAD).post(
            f"{_BASE}/sites/{SITE}/irrigation-zones", json={"name": "Z", "actuator_key": "act_1"}
        )

        assert response.status_code == 422, response.text
        assert _code(response) == "irrigation_zone.coupling_not_available"

    @pytest.mark.parametrize(
        "body",
        [
            {"name": "Z", "color": "green"},
            {"name": "Z", "application_efficiency": 0},
            {"name": "Z", "application_efficiency": 1.2},
            {"name": "Z", "irrigation_type": "flood"},
            {"name": "Z", "site_key": SITE},
            {"name": "Z", "tenant_key": TENANT},
            {"name": "  "},
            {"name": "Z", "flow_rate_ha_entity_id": "switch.valve"},
        ],
        ids=["color", "efficiency 0", "efficiency > 1", "unknown type", "site_key", "tenant_key", "blank", "entity"],
    )
    def test_the_body_is_validated(self, client, zones: FakeZones, body: dict) -> None:
        before = set(zones.zones)

        response = client(TenantRole.LEAD).post(f"{_BASE}/sites/{SITE}/irrigation-zones", json=body)

        assert response.status_code == 422, response.text
        assert set(zones.zones) == before

    def test_a_patch_cannot_clear_the_name(self, client, zones: FakeZones) -> None:
        response = client(TenantRole.GROWER).patch(f"{_BASE}/irrigation-zones/zone_1", json={"name": None})

        assert response.status_code == 422, response.text
        assert zones.updates == []

    def test_the_list_is_paginated(self, client) -> None:
        response = client(TenantRole.VIEWER).get(f"{_BASE}/sites/{SITE}/irrigation-zones", params={"limit": 201})

        assert response.status_code == 422
