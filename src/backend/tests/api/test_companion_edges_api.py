"""WP 8.15 (#2658) — ``GET /locations/{key}/companion-edges`` through the deployed app.

``app.main`` with the real ``CompanionOverlayService``, the real tenant gate and the in-memory doubles: every role may
read, another tenant's bed is a 404 that names nothing, the list is capped at 500 with ``truncated``, and the status
on the wire equals what the engine says for the same pair.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_companion_overlay_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.engines.companion_planting_engine import CompanionPlantingEngine
from app.domain.models.garden_plan import SlotSpeciesHint
from app.domain.models.site import Slot
from app.domain.models.user import User
from app.domain.services.companion_overlay_service import MAX_COMPANION_EDGES, CompanionOverlayService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)
from tests.support.rotation_fakes import FakeRotationGraph, FakeSpecies, make_species

_OWN = "/api/v1/t/own/locations/bed/companion-edges"
_OTHER = "/api/v1/t/other/locations/bed/companion-edges"


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


def _slot(key: str, x: float) -> Slot:
    return Slot.model_validate(
        {
            "_key": key,
            "slot_id": key.upper() + "_X",
            "location_key": "bed",
            "geometry": {"kind": "point", "origin": [x, 0.5]},
        }
    )


class _ActivePlants:
    def __init__(self, plan: FakePlanRepo) -> None:
        self._plan = plan

    def get_active_by_slot(self, slot_key, *, tenant_key):
        return [SimpleNamespace(species_key=h.species_key) for h in self._plan.species_hints if h.slot_key == slot_key]


@pytest.fixture
def world() -> SimpleNamespace:
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed", geometry=rect(1.0, 2.0, w=4, h=2))
    plan.slots = [_slot("s1", 0.5), _slot("s2", 1.0), _slot("s3", 1.5)]
    graph = FakeRotationGraph()
    species = FakeSpecies(*(make_species(key, "fam") for key in ("tomato", "basil", "fennel")))
    return SimpleNamespace(
        plan=plan,
        graph=graph,
        service=CompanionOverlayService(sites, plan, graph),  # type: ignore[arg-type]
        engine=CompanionPlantingEngine(graph, _ActivePlants(plan), species),  # type: ignore[arg-type]
    )


def _stand(world, **by_slot: str) -> None:  # type: ignore[no-untyped-def]
    world.plan.species_hints = [SlotSpeciesHint(slot_key=k, species_key=v) for k, v in by_slot.items()]


@pytest.fixture
def client(world) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    def build(role: TenantRole = TenantRole.VIEWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(_key="u_sabine", email="s@example.org", display_name="S")
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_companion_overlay_service] = lambda: world.service
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.VIEWER
        app.dependency_overrides.clear()


@pytest.mark.parametrize("role", [TenantRole.VIEWER, TenantRole.GROWER, TenantRole.LEAD])
def test_every_role_may_read_the_layer(client, world, role) -> None:  # type: ignore[no-untyped-def]
    _stand(world, s1="tomato", s2="basil")
    world.graph.adjacent = {"s1": ["s2"]}
    world.graph.compatible = {"tomato": {"basil": 0.9}, "basil": {"tomato": 0.9}}
    world.graph.distances[("s1", "s2")] = 50.0

    response = client(role).get(_OWN)

    assert response.status_code == 200
    body = response.json()
    assert (body["location_key"], body["total"], body["truncated"]) == ("bed", 1, False)
    (edge,) = body["edges"]
    assert edge == {
        "slot_a": {
            "slot_key": "s1",
            "position": {"x": 1.5, "y": 2.5},
            "species_keys": ["tomato"],
            "species_truncated": False,
        },
        "slot_b": {
            "slot_key": "s2",
            "position": {"x": 2.0, "y": 2.5},
            "species_keys": ["basil"],
            "species_truncated": False,
        },
        "status": "compatible",
        "reason_code": "companion.compatible",
        "reason": None,
        "score": 0.9,
        "deciding": {
            "species_a_key": "basil",
            "species_a_name": "Test basil",
            "species_b_key": "tomato",
            "species_b_name": "Test tomato",
        },
        "distance_cm": 50.0,
    }


def test_another_tenants_bed_is_a_404_that_names_nothing(client, world) -> None:  # type: ignore[no-untyped-def]
    _stand(world, s1="tomato", s2="basil")
    world.graph.adjacent = {"s1": ["s2"]}

    response = client(TenantRole.LEAD).get(_OTHER)

    assert response.status_code == 404
    for leak in (TENANT, "site_1", "tomato", "s1"):
        assert leak not in response.text


def test_an_unknown_bed_is_the_same_404(client) -> None:  # type: ignore[no-untyped-def]
    response = client().get("/api/v1/t/own/locations/nowhere/companion-edges")

    assert response.status_code == 404
    assert TENANT not in response.text and "site_1" not in response.text


def test_more_than_500_pairs_are_capped_and_flagged(client, world) -> None:  # type: ignore[no-untyped-def]
    count = MAX_COMPANION_EDGES + 2
    world.plan.slots = [_slot(f"s{i:04d}", 0.001 * i) for i in range(count)]
    _stand(world, **{f"s{i:04d}": "tomato" for i in range(count)})
    world.graph.adjacent = {f"s{i:04d}": [f"s{i + 1:04d}"] for i in range(count - 1)}

    body = client().get(_OWN).json()

    assert (len(body["edges"]), body["total"], body["truncated"]) == (500, 501, True)
    keys = [(e["slot_a"]["slot_key"], e["slot_b"]["slot_key"]) for e in body["edges"]]
    assert keys == sorted(keys)  # one status, so ordered by slot keys: deterministic


@pytest.mark.parametrize(
    ("compatible", "incompatible"),
    [
        ({"tomato": {"basil": 0.9}, "basil": {"tomato": 0.9}}, {}),
        ({}, {"tomato": ["basil"], "basil": ["tomato"]}),
        ({"tomato": {"basil": 0.9}, "basil": {"tomato": 0.9}}, {"tomato": ["basil"], "basil": ["tomato"]}),
        ({}, {}),
    ],
    ids=["compatible", "incompatible", "conflicting", "unknown"],
)
def test_the_status_on_the_wire_equals_the_engine_for_the_same_pair(  # type: ignore[no-untyped-def]
    client, world, compatible, incompatible
) -> None:
    world.graph.compatible, world.graph.incompatible = compatible, incompatible
    world.graph.adjacent = {"s1": ["s2"], "s2": ["s1"]}
    _stand(world, s1="tomato", s2="basil")

    (edge,) = client().get(_OWN).json()["edges"]
    _stand(world, s2="basil")
    ok, warnings, benefits = world.engine.check_compatibility("tomato", "s1", tenant_key=TENANT)
    engine_status = "incompatible" if not ok else ("compatible" if benefits else "unknown")

    assert edge["status"] == engine_status
