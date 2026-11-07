"""WP 8.7 (#2650, GP-FR-122, GP-API-066) — ``GET /locations/{key}/soil-analyses`` through the deployed app.

``app.main`` with the real ``SoilAnalysisService``, the real tenant gate and the in-memory doubles of the care-event
tier: the status codes, that every role may read, that another tenant's bed is a 404 that names nothing, that the
list is bounded and that series of different methods are never merged on the wire.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_soil_analysis_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.care_event import CareEvent
from app.domain.models.site import SoilProfile
from app.domain.models.user import User
from app.domain.services.soil_analysis_service import SoilAnalysisService
from tests.support.care_event_fakes import FakeCareEventRepo
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT, FakePlanRepo, FakeSites, make_location, make_site

_OWN = "/api/v1/t/own/locations/bed/soil-analyses"
_OTHER = "/api/v1/t/other/locations/bed/soil-analyses"
NOW = datetime.now(UTC)


class _Tenants:
    role = TenantRole.VIEWER

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        keys = {"own": TENANT, "other": OTHER_TENANT}
        if slug not in keys:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=keys[slug], slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=type(self).role, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str) -> None:
        return None


def _measure(parameter: str, value: float, unit: str, **extra) -> dict:  # type: ignore[no-untyped-def]
    return {"parameter": parameter, "value": value, "unit": unit, "source": "lab", **extra}


@pytest.fixture
def world() -> SimpleNamespace:
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed")
    repo = FakeCareEventRepo()
    return SimpleNamespace(repo=repo, plan=plan, service=SoilAnalysisService(sites, repo))  # type: ignore[arg-type]


def _store(world, days_ago: int, measurements: list[dict], **extra) -> None:  # type: ignore[no-untyped-def]
    world.repo._store(
        CareEvent(
            tenant_key=TENANT,
            site_key="site_1",
            location_key="bed",
            category="soil_analysis",
            summary="Soil analysis",
            performed_at=NOW - timedelta(days=days_ago),
            measurements=measurements,
            **extra,
        )
    )


@pytest.fixture
def client(world) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    def build(role: TenantRole = TenantRole.VIEWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(_key="u_sabine", email="s@example.org", display_name="S")
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_soil_analysis_service] = lambda: world.service
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.VIEWER
        app.dependency_overrides.clear()


@pytest.mark.parametrize("role", [TenantRole.VIEWER, TenantRole.GROWER, TenantRole.LEAD])
def test_every_role_may_read_the_series(client, world, role) -> None:  # type: ignore[no-untyped-def]
    _store(world, 5, [_measure("ph", 6.4, "pH", ph_method="cacl2")])

    response = client(role).get(_OWN)

    assert response.status_code == 200
    body = response.json()
    assert body["location_key"] == "bed" and body["analyses"] == 1 and body["truncated"] is False
    assert body["series"][0]["parameter"] == "ph" and body["series"][0]["method"] == "cacl2"


def test_two_methods_are_two_series_with_the_change_marked(client, world) -> None:  # type: ignore[no-untyped-def]
    _store(world, 120, [_measure("ec", 0.8, "mS/cm", ec_method="ratio_1_5")])
    _store(world, 60, [_measure("ec", 2.4, "mS/cm", ec_method="saturated_paste")])

    body = client().get(_OWN, params={"parameter": "ec"}).json()

    assert [(s["method"], [p["value"] for p in s["points"]]) for s in body["series"]] == [
        ("ratio_1_5", [0.8]),
        ("saturated_paste", [2.4]),
    ]
    assert [(c["from_method"], c["to_method"]) for c in body["method_changes"]] == [("ratio_1_5", "saturated_paste")]


def test_a_series_never_carries_two_units(client, world) -> None:  # type: ignore[no-untyped-def]
    """#2706: 1100 uS/cm and 1.1 mS/cm by the same method are two series, each naming its unit; nothing converted."""
    _store(world, 30, [_measure("ec", 1100, "uS/cm", ec_method="sensor")])
    _store(world, 10, [_measure("ec", 1.1, "mS/cm", ec_method="sensor")])

    body = client().get(_OWN, params={"parameter": "ec"}).json()

    assert [(s["method"], s["unit"], [p["value"] for p in s["points"]]) for s in body["series"]] == [
        ("sensor", "mS/cm", [1.1]),
        ("sensor", "uS/cm", [1100.0]),
    ]
    assert body["method_changes"] == []


def test_spellings_of_one_unit_are_one_series_with_the_normalised_unit(client, world) -> None:  # type: ignore[no-untyped-def]
    _store(world, 30, [_measure("ec", 1.0, "mS/cm", ec_method="sensor")])
    _store(world, 20, [_measure("ec", 1.1, "dS/m", ec_method="sensor")])
    _store(world, 10, [_measure("ec", 1.2, " MS/CM", ec_method="sensor")])

    body = client().get(_OWN, params={"parameter": "ec"}).json()

    assert [(s["unit"], len(s["points"])) for s in body["series"]] == [("mS/cm", 3)]
    assert [p["unit"] for p in body["series"][0]["points"]] == ["mS/cm", "dS/m", " MS/CM"]  # each as entered


def test_a_content_class_is_only_what_the_lab_stated(client, world) -> None:  # type: ignore[no-untyped-def]
    _store(world, 5, [_measure("p", 12, "mg_per_100g", extraction_method="cal", content_class="C")])
    _store(world, 4, [_measure("k", 9, "mg_per_100g", source="test_kit")])

    points = {s["parameter"]: s["points"][0] for s in client().get(_OWN).json()["series"]}

    assert points["p"]["content_class"] == "C" and points["k"]["content_class"] is None


def test_another_tenants_bed_is_a_404_that_names_nothing(client, world) -> None:  # type: ignore[no-untyped-def]
    _store(world, 5, [_measure("ph", 6.4, "pH")])

    response = client(TenantRole.LEAD).get(_OTHER)

    assert response.status_code == 404
    assert TENANT not in response.text and "site_1" not in response.text  # neither the owner nor the site behind it


def test_the_list_is_bounded_and_says_when_it_was_cut(client, world) -> None:  # type: ignore[no-untyped-def]
    for day in range(1, 8):
        _store(world, day, [_measure("humus", float(day), "%")])

    cut = client().get(_OWN, params={"limit": 3}).json()

    assert cut["analyses"] == 3 and cut["truncated"] is True
    assert client().get(_OWN, params={"limit": 501}).status_code == 422
    assert client().get(_OWN, params={"limit": 0}).status_code == 422


def test_an_unknown_parameter_and_an_inverted_range_are_422(client) -> None:  # type: ignore[no-untyped-def]
    assert client().get(_OWN, params={"parameter": "gold"}).status_code == 422
    assert client().get(_OWN, params={"from": "2026-06-02T00:00:00", "to": "2026-06-01T00:00:00Z"}).status_code == 422


def test_the_liming_hint_comes_from_the_current_profile_and_never_an_amount(client, world) -> None:  # type: ignore[no-untyped-def]
    assert client().get(_OWN).json()["liming_hint"] == {"status": "not_assessable", "reason": "no_ph"}

    world.plan.locations["bed"] = make_location(
        "bed",
        soil_profile=SoilProfile(
            growing_medium_kind="native_soil", soil_texture="loam", ph=5.5, ph_method="cacl2", target_ph=6.2
        ),
    )
    hint = client().get(_OWN).json()["liming_hint"]

    assert hint == {"status": "likely", "reason": "below_target"}  # status and reason only - no amount field
