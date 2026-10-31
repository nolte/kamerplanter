"""#2544 review (SCR-001) — the slot-level rotation check obeys the bed's switch (GP-FR-137, D-09).

A same-family planting in a slot used to be ``CRITICAL`` and refused with ``ROTATION_VIOLATION`` whatever the bed's
switch said, on three routes: ``POST /plant-instances`` with a ``slot_key``, ``POST /planting-runs/{key}/create-plants``
and the hint ``POST /plant-instances/slots/{slot_key}/validate-planting``. A bed that is off (``rotation_enabled =
False``, ``rotation_exempt = True``, or a ``tent`` not switched on) must not refuse; a tent switched on still does.

The real :class:`CropRotationValidator` with ``site_repo`` runs over in-memory repositories; the history of every
slot holds a tomato of the same family, so the only variable is the bed.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.plant_instances.tenant_router import router as plants_router
from app.common import auth as auth_mod
from app.common.auth import get_current_user
from app.common.dependencies import get_plant_instance_service, get_planting_run_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Slot
from app.domain.models.species import Species
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.plant_instance_service import PlantInstanceService
from app.domain.services.species_service import SpeciesService
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT, make_location
from tests.support.planting_reservation_fakes import build_world

#: (bed key, location overrides, does the slot check still refuse?)
BEDS: list[tuple[str, dict, bool]] = [
    ("bed_off", {"rotation_enabled": False}, False),
    ("bed_exempt", {"rotation_exempt": True}, False),
    ("tent_default", {"location_type_key": "tent"}, False),
    ("tent_on", {"location_type_key": "tent", "rotation_enabled": True}, True),
]
BED_IDS = [bed for bed, _, _ in BEDS]

_TOMATO = Species(_key="sp_tomato", tenant_key="", scientific_name="Solanum lycopersicum", family_key="solanaceae")
_PAST = PlantInstance(
    key="plant_past",
    instance_id="TOM-OLD",
    species_key="sp_tomato",
    tenant_key=TENANT,
    planted_on=date(2025, 4, 1),
)


class _SpeciesRepo:
    """The reads of the validator (``get_by_key``) and of the species service (``get_or_raise``)."""

    def get_by_key(self, key: str) -> Species | None:
        return _TOMATO if key == _TOMATO.key else None

    def get_or_raise(self, key: str) -> Species:
        found = self.get_by_key(key)
        if found is None:
            raise NotFoundError("Species", key)
        return found

    def is_granted_to(self, key: str, tenant_key: str) -> bool:
        return False


@pytest.fixture(autouse=True)
def _no_family_catalogue(monkeypatch: pytest.MonkeyPatch) -> None:
    """``validate_planting`` looks the planned family up through the provider; no family is nitrogen-fixing here."""
    families = MagicMock()
    families.get_by_key.return_value = None
    monkeypatch.setattr("app.common.dependencies.get_family_repo", lambda: families)


def _history_repo() -> MagicMock:
    """Every slot's history holds a tomato planted last year: a same-family planting is CRITICAL on an on-bed."""
    repo = MagicMock()
    repo.get_history_by_slot.return_value = [_PAST]
    return repo


def _world_with_beds() -> SimpleNamespace:
    world = build_world()
    for bed, overrides, _ in BEDS:
        world.plan.locations[bed] = make_location(bed, **overrides)
    world.plan.slots = [Slot(_key=f"slot_{bed}", slot_id=f"{bed.upper()}_001", location_key=bed) for bed in BED_IDS]
    return world


def _validator(world: SimpleNamespace, history: MagicMock) -> CropRotationValidator:
    return CropRotationValidator(history, _SpeciesRepo(), None, site_repo=world.sites)


# ── POST /plant-instances with a slot_key, and the hint route ────────────────


@pytest.fixture
def plant_api() -> Iterator[SimpleNamespace]:
    world = _world_with_beds()
    plants = MagicMock()
    plants.create.side_effect = lambda p: p.model_copy(update={"key": "plant_new"})
    plants.get_history_by_slot.return_value = [_PAST]
    companion = MagicMock()
    companion.check_compatibility.return_value = (True, [], [])
    service = PlantInstanceService(
        plants,
        world.sites,
        _validator(world, plants),
        companion,
        species_service=SpeciesService(_SpeciesRepo(), MagicMock(), MagicMock()),
    )
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(plants_router, prefix="/api/v1/t/{tenant_slug}")
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="u1", account_type="human")
    app.dependency_overrides[get_plant_instance_service] = lambda: service
    app.dependency_overrides[auth_mod.get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT, tenant_slug="own", user_key="u1", role=TenantRole.LEAD, admin_scopes=[]
    )
    yield SimpleNamespace(client=TestClient(app), plants=plants)


def _plant_body(bed: str) -> dict:
    return {
        "instance_id": f"TOM-{bed}",
        "species_key": "sp_tomato",
        "planted_on": "2026-05-01",
        "site_key": "site_1",
        "location_key": bed,
        "slot_key": f"slot_{bed}",
    }


@pytest.mark.parametrize(("bed", "overrides", "refused"), BEDS, ids=BED_IDS)
def test_post_plant_instance_follows_the_beds_switch(plant_api, bed: str, overrides: dict, refused: bool) -> None:
    response = plant_api.client.post("/api/v1/t/own/plant-instances", json=_plant_body(bed))

    if refused:
        assert response.status_code == 422, response.text
        assert response.json()["error_code"] == "ROTATION_VIOLATION"
        plant_api.plants.create.assert_not_called()
    else:
        assert response.status_code == 201, response.text
        plant_api.plants.create.assert_called_once()


@pytest.mark.parametrize(("bed", "overrides", "refused"), BEDS, ids=BED_IDS)
def test_the_hint_route_follows_the_beds_switch(plant_api, bed: str, overrides: dict, refused: bool) -> None:
    response = plant_api.client.post(
        f"/api/v1/t/own/plant-instances/slots/slot_{bed}/validate-planting", json={"species_key": "sp_tomato"}
    )

    assert response.status_code == 200, response.text
    assert response.json()["valid"] is (not refused)
    if not refused:
        plant_api.plants.get_history_by_slot.assert_not_called()


# ── POST /planting-runs/{key}/create-plants ──────────────────────────────


class _Tenants:
    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        keys = {"own": TENANT, "other": OTHER_TENANT}
        if slug not in keys:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=keys[slug], slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=TenantRole.GROWER, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str) -> None:
        return None


@pytest.fixture
def run_api() -> Iterator[Callable[[], SimpleNamespace]]:
    from app.main import app

    world = _world_with_beds()
    companion = MagicMock()
    world.service._rotation = _validator(world, _history_repo())
    world.service._companion = companion
    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_planting_run_service] = lambda: world.service
    try:
        yield lambda: SimpleNamespace(client=TestClient(app), world=world)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(("bed", "overrides", "refused"), BEDS, ids=BED_IDS)
def test_create_plants_of_a_run_follows_the_beds_switch(run_api, bed: str, overrides: dict, refused: bool) -> None:
    api = run_api()
    created = api.client.post(
        "/api/v1/t/own/planting-runs",
        json={
            "name": "Tomatoes 2026",
            "run_type": "monoculture",
            "location_key": bed,
            "entries": [{"species_key": "sp_tomato", "quantity": 1, "id_prefix": "TOM"}],
        },
    )
    assert created.status_code == 201, created.text

    response = api.client.post(f"/api/v1/t/own/planting-runs/{created.json()['key']}/create-plants")

    if refused:
        assert response.status_code == 422, response.text
        assert response.json()["error_code"] == "ROTATION_VIOLATION"
        assert api.world.plants.created == []
    else:
        assert response.status_code == 201, response.text
        assert response.json()["assigned_slots"] == [f"slot_{bed}"]


def test_the_wired_slot_validators_read_the_beds_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Both production constructions hand the validator a ``site_repo`` - without it the switch is never read."""
    from app.common import dependencies

    monkeypatch.setattr(dependencies, "get_db", MagicMock)
    for build in (dependencies.get_plant_instance_service, dependencies.get_planting_run_service):
        service = build()
        assert service._rotation._sites is not None, build.__name__
