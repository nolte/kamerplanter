"""REQ-053 WP 7.1 (#2467) — the irrigation-zone routes through the deployed app.

``app.main`` with the real ``IrrigationZoneService``, the real tenant gate and the in-memory doubles of
``tests/support/{garden_plan,irrigation_zone}_fakes.py``. The unit tier shows what the service decides; this tier
shows how it reads on the wire and that every route sits behind the gate of §21.8 "Bewässerungszone" — one
negative per row and role (SR-010): a viewer reads but neither creates, changes, assigns nor deletes; a grower
does all of that except delete.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_irrigation_zone_service, get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.garden_object import GardenObject
from app.domain.models.irrigation_zone import IrrigationZone, LastWatering, ZoneWateringFacts
from app.domain.models.user import User
from app.domain.services.irrigation_zone_service import IrrigationZoneService
from tests.support.care_event_fakes import FakeCareEventRepo
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
from tests.support.ha_entity_grants import grant_service
from tests.support.irrigation_zone_fakes import FakeZones

_BASE = "/api/v1/t/own"


class _Tenants:
    role = TenantRole.GROWER
    scopes: ClassVar[list[AdminScope]] = []

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        keys = {"own": TENANT, "other": OTHER_TENANT}
        if slug not in keys:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=keys[slug], slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=type(self).role, admin_scopes=list(type(self).scopes), is_active=True)

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


class _FlowSensor:
    """Home Assistant as the tests need it: every entity is a flow sensor."""

    def device_class(self, entity_id: str) -> str | None:
        return "volume_flow_rate"

    def read(self, entity_id: str) -> None:
        return None


@pytest.fixture
def care() -> FakeCareEventRepo:
    return FakeCareEventRepo()


@pytest.fixture
def client(zones: FakeZones, care: FakeCareEventRepo) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    repo = zones._repo
    zones.actuators = {"act_1": (TENANT, "bed"), "act_theirs": (OTHER_TENANT, "bed_foreign")}
    service = IrrigationZoneService(
        zones,
        repo._sites,
        FakeObjects(repo),
        care,
        ha_entity_gate=grant_service({TENANT: ["sensor.south_flow"]}),
        flow_sensor=_FlowSensor(),
    )

    def build(role: TenantRole = TenantRole.GROWER, scopes: tuple[AdminScope, ...] = ()) -> TestClient:
        _Tenants.role = role
        _Tenants.scopes = list(scopes)
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
        _Tenants.scopes = []
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

    def test_a_lead_without_the_technical_scope_cannot_set_the_coupling(self, client, zones: FakeZones) -> None:
        before = dict(zones.zones)

        response = client(TenantRole.LEAD).post(
            f"{_BASE}/sites/{SITE}/irrigation-zones", json={"name": "Z", "actuator_key": "act_1"}
        )

        assert response.status_code == 403, response.text
        assert zones.zones == before

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


class TestStatusAndWateringRound:
    def _cover(self, zones: FakeZones) -> None:
        zones.replace_zone_locations("zone_1", ["bed", "bed_2"], tenant_key=TENANT)
        zones._repo.locations["bed"] = zones._repo.locations["bed"].model_copy(update={"area_m2": 3.0})
        zones._repo.locations["bed_2"] = zones._repo.locations["bed_2"].model_copy(update={"area_m2": 1.0})

    def test_every_member_reads_the_status_and_a_foreign_zone_is_a_404(self, client, zones: FakeZones) -> None:
        zones.facts = ZoneWateringFacts(
            last_watering=LastWatering(
                at=datetime(2026, 10, 19, 6, 30, tzinfo=UTC),
                source="care_event",
                location_key="bed",
                allocation="equal",
            ),
            next_planned=None,
            consumption_liters=12.5,
        )

        found = client(TenantRole.VIEWER).get(f"{_BASE}/irrigation-zones/zone_1/status")
        foreign = client(TenantRole.LEAD).get(f"{_BASE}/irrigation-zones/zone_foreign/status")

        assert found.status_code == 200, found.text
        assert found.json() == {
            "last_watering": {
                "at": "2026-10-19T06:30:00Z",
                "source": "care_event",
                "location_key": "bed",
                "allocation": "equal",
            },
            "next_planned": None,
            "demand_liters_today": None,
            "demand_gross_liters_today": None,
            "application_efficiency": 0.88,
            "efficiency_source": "type_default",
            "consumption_liters_30d": 12.5,
            "consumption_sources": [{"source": "manual_log", "liters": 12.5}],
            "hints": [],
        }
        assert foreign.status_code == 404

    def test_a_grower_logs_a_round_and_the_viewer_cannot(self, client, zones: FakeZones, care) -> None:
        self._cover(zones)

        denied = client(TenantRole.VIEWER).post(
            f"{_BASE}/irrigation-zones/zone_1/log-watering", json={"volume_liters": 20, "allocation": "by_area"}
        )
        logged = client(TenantRole.GROWER).post(
            f"{_BASE}/irrigation-zones/zone_1/log-watering",
            json={"volume_liters": 20, "allocation": "by_area", "summary": "Morning"},
        )

        assert denied.status_code == 403 and len(care.inserted) == 2
        assert logged.status_code == 201, logged.text
        body = logged.json()
        assert {s["location_key"]: s["liters"] for s in body["shares"]} == {"bed": 15.0, "bed_2": 5.0}
        assert (body["allocation"], body["skipped_location_keys"], len(body["event_keys"])) == ("by_area", [], 2)

    @pytest.mark.parametrize(
        "body",
        [
            {"volume_liters": 20, "allocation": "measured"},
            {"volume_liters": 0, "allocation": "equal"},
            {"volume_liters": 20},
            {"volume_liters": 20, "allocation": "equal", "tenant_key": "x"},
        ],
    )
    def test_a_malformed_body_is_a_422_and_writes_nothing(self, client, zones: FakeZones, care, body) -> None:
        self._cover(zones)

        response = client(TenantRole.GROWER).post(f"{_BASE}/irrigation-zones/zone_1/log-watering", json=body)

        assert response.status_code == 422 and care.inserted == []

    def test_a_foreign_zone_is_a_404_and_a_zone_without_beds_a_422(self, client, zones: FakeZones, care) -> None:
        foreign = client(TenantRole.LEAD).post(
            f"{_BASE}/irrigation-zones/zone_foreign/log-watering", json={"volume_liters": 5, "allocation": "equal"}
        )
        empty = client(TenantRole.GROWER).post(
            f"{_BASE}/irrigation-zones/zone_1/log-watering", json={"volume_liters": 5, "allocation": "equal"}
        )

        assert foreign.status_code == 404
        assert empty.status_code == 422 and _code(empty) == "irrigation_zone.no_beds"
        assert care.inserted == []


class TestTechnicalCoupling:
    _TECH = (AdminScope.TECHNICAL,)

    def test_a_lead_with_the_technical_scope_binds_actuator_and_flow_entity(self, client, zones: FakeZones) -> None:
        response = client(TenantRole.LEAD, self._TECH).patch(
            f"{_BASE}/irrigation-zones/zone_1",
            json={
                "actuator_key": "act_1",
                "flow_rate_l_per_min": 6,
                "flow_rate_source": "ha_entity",
                "flow_rate_ha_entity_id": "sensor.south_flow",
            },
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert (body["actuator_key"], body["flow_rate_source"], body["flow_rate_ha_entity_bound"]) == (
            "act_1",
            "ha_entity",
            True,
        )
        assert "sensor.south_flow" not in response.text and "flow_rate_ha_entity_id" not in body
        assert zones.zones["zone_1"].flow_rate_ha_entity_id == "sensor.south_flow"

    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.LEAD])
    def test_without_the_scope_it_is_403_whatever_the_rank(self, client, zones: FakeZones, role) -> None:
        response = client(role).patch(f"{_BASE}/irrigation-zones/zone_1", json={"actuator_key": "act_1"})

        assert response.status_code == 403, response.text
        assert zones.zones["zone_1"].actuator_key is None

    def test_the_scope_without_a_domain_role_does_not_write(self, client) -> None:
        response = client(TenantRole.VIEWER, self._TECH).patch(
            f"{_BASE}/irrigation-zones/zone_1", json={"actuator_key": "act_1"}
        )

        assert response.status_code == 403

    def test_an_entity_that_is_not_granted_is_422_without_naming_it(self, client) -> None:
        response = client(TenantRole.LEAD, self._TECH).patch(
            f"{_BASE}/irrigation-zones/zone_1",
            json={"flow_rate_source": "ha_entity", "flow_rate_ha_entity_id": "sensor.door_contact"},
        )

        assert response.status_code == 422 and _code(response) == "HA_ENTITY_NOT_GRANTED"
        assert "door_contact" not in response.text

    def test_a_foreign_actuator_is_422_reference_not_found(self, client) -> None:
        response = client(TenantRole.LEAD, self._TECH).patch(
            f"{_BASE}/irrigation-zones/zone_1", json={"actuator_key": "act_theirs"}
        )

        assert response.status_code == 422 and _code(response) == "reference.not_found"

    def test_a_malformed_entity_id_is_a_422_of_the_shape(self, client) -> None:
        response = client(TenantRole.LEAD, self._TECH).post(
            f"{_BASE}/sites/{SITE}/irrigation-zones",
            json={"name": "Z", "flow_rate_source": "ha_entity", "flow_rate_ha_entity_id": "light.kitchen"},
        )

        assert response.status_code == 422
