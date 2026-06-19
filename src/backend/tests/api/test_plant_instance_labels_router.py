"""API tests: plant responses embed denormalized species/cultivar labels.

Both the plant-instances list and the planting-run plants list resolve the
species_key/cultivar_key into embedded summaries so the frontend can render a
speaking name (e.g. "BASIL-001 (Basilikum – Genovese)") without N+1 fetches.
"""

from datetime import date
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.plant_instances.tenant_router import router as plant_router
from app.api.v1.planting_runs.tenant_router import router as run_router
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_plant_instance_service,
    get_planting_run_service,
    get_species_repo,
)
from app.common.enums import TenantRole
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Cultivar, Species
from app.domain.models.tenant_context import TenantContext

TENANT_KEY = "t-test-1"


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug="test-slug",
        user_key="user-1",
        role=TenantRole.GROWER,
    )


def _species() -> Species:
    return Species(
        _key="basil",
        scientific_name="Ocimum basilicum",
        common_names=["Basilikum", "Basil"],
        genus="Ocimum",
    )


def _cultivar() -> Cultivar:
    return Cultivar(_key="genovese", name="Genovese", species_key="basil")


def _plant() -> PlantInstance:
    return PlantInstance(
        _key="p-1",
        instance_id="BASIL-001",
        species_key="basil",
        cultivar_key="genovese",
        plant_name=None,
        planted_on=date(2026, 1, 1),
        tenant_key=TENANT_KEY,
    )


def test_plant_instances_list_embeds_species_and_cultivar():
    service = MagicMock()
    service.list_plants.return_value = ([_plant()], 1)
    service.resolve_phase_name.return_value = ""
    service.resolve_species.return_value = _species()
    service.resolve_cultivar.return_value = _cultivar()

    app = FastAPI()
    app.include_router(plant_router, prefix="/api/v1/t/test-slug")
    app.dependency_overrides[get_plant_instance_service] = lambda: service
    app.dependency_overrides[get_current_tenant] = _ctx
    client = TestClient(app)

    resp = client.get("/api/v1/t/test-slug/plant-instances")
    assert resp.status_code == 200
    body = resp.json()[0]
    assert body["instance_id"] == "BASIL-001"
    assert body["species"] == {
        "scientific_name": "Ocimum basilicum",
        "common_names": ["Basilikum", "Basil"],
    }
    assert body["cultivar"] == {"name": "Genovese"}


def test_plant_instances_list_null_species_when_unresolved():
    service = MagicMock()
    plant = _plant()
    plant.cultivar_key = None
    service.list_plants.return_value = ([plant], 1)
    service.resolve_phase_name.return_value = ""
    service.resolve_species.return_value = None
    service.resolve_cultivar.return_value = None

    app = FastAPI()
    app.include_router(plant_router, prefix="/api/v1/t/test-slug")
    app.dependency_overrides[get_plant_instance_service] = lambda: service
    app.dependency_overrides[get_current_tenant] = _ctx
    client = TestClient(app)

    body = client.get("/api/v1/t/test-slug/plant-instances").json()[0]
    assert body["species"] is None
    assert body["cultivar"] is None


def test_run_plants_list_embeds_species_and_cultivar_with_cache():
    run_service = MagicMock()
    run_service.get_run.return_value = MagicMock()
    run_service.get_plants.return_value = [
        {
            "_key": "p-1",
            "instance_id": "BASIL-001",
            "species_key": "basil",
            "cultivar_key": "genovese",
            "plant_name": None,
            "planted_on": "2026-01-01",
            "current_phase": "",
        },
        {
            "_key": "p-2",
            "instance_id": "BASIL-002",
            "species_key": "basil",
            "cultivar_key": "genovese",
            "plant_name": "Küchenbasilikum",
            "planted_on": "2026-01-02",
            "current_phase": "",
        },
    ]

    species_repo = MagicMock()
    species_repo.get_by_key.return_value = _species()
    species_repo.get_cultivar_by_key.return_value = _cultivar()

    app = FastAPI()
    app.include_router(run_router, prefix="/api/v1/t/test-slug")
    app.dependency_overrides[get_planting_run_service] = lambda: run_service
    app.dependency_overrides[get_species_repo] = lambda: species_repo
    app.dependency_overrides[get_current_tenant] = _ctx
    client = TestClient(app)

    resp = client.get("/api/v1/t/test-slug/planting-runs/run-1/plants")
    assert resp.status_code == 200
    rows = resp.json()
    assert rows[0]["species"]["common_names"][0] == "Basilikum"
    assert rows[0]["cultivar"] == {"name": "Genovese"}
    assert rows[1]["species"]["scientific_name"] == "Ocimum basilicum"
    # Two plants share one species/cultivar — each looked up only once (cache).
    assert species_repo.get_by_key.call_count == 1
    assert species_repo.get_cultivar_by_key.call_count == 1
