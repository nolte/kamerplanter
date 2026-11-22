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
        common_names_i18n={"de": ["Basilikum"], "en": ["Basil"]},
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
    service.list_plants_window.return_value = [_plant()]
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
        # The language map rides along so the client can pick the UI-language name (#2902).
        "common_names_i18n": {"de": ["Basilikum"], "en": ["Basil"]},
    }
    assert body["cultivar"] == {"name": "Genovese"}


def test_plant_instances_list_null_species_when_unresolved():
    service = MagicMock()
    plant = _plant()
    plant.cultivar_key = None
    service.list_plants_window.return_value = [plant]
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


# --- #3032: one resolver call per distinct key per request ---------------------

_PAGE_SIZE = 40


def _page_of_plants() -> list[PlantInstance]:
    """A page of plants sharing one species, one cultivar and one phase key."""
    return [
        PlantInstance(
            _key=f"p-{i}",
            instance_id=f"BASIL-{i:03d}",
            species_key="basil",
            cultivar_key="genovese",
            current_phase_key="phase-veg",
            planted_on=date(2026, 1, 1),
            tenant_key=TENANT_KEY,
        )
        for i in range(_PAGE_SIZE)
    ]


def _plant_client(service: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(plant_router, prefix="/api/v1/t/test-slug")
    app.dependency_overrides[get_plant_instance_service] = lambda: service
    app.dependency_overrides[get_current_tenant] = _ctx
    return TestClient(app)


def test_plant_instances_list_resolves_each_shared_label_once():
    """#3032: a page of rows sharing species/cultivar/phase costs one lookup each."""
    service = MagicMock()
    service.list_plants_window.return_value = _page_of_plants()
    service.resolve_phase_name.return_value = "vegetative"
    service.resolve_species.return_value = _species()
    service.resolve_cultivar.return_value = _cultivar()

    resp = _plant_client(service).get("/api/v1/t/test-slug/plant-instances")

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == _PAGE_SIZE
    assert all(r["current_phase"] == "vegetative" for r in rows)
    assert all(r["species"]["scientific_name"] == "Ocimum basilicum" for r in rows)
    assert all(r["cultivar"] == {"name": "Genovese"} for r in rows)
    service.resolve_species.assert_called_once_with("basil", tenant_key=TENANT_KEY)
    service.resolve_cultivar.assert_called_once_with("genovese")
    service.resolve_phase_name.assert_called_once_with("phase-veg")


def test_plant_instances_list_memoises_unreadable_species_as_null():
    """#2082 stays: an unreadable species is null on every row — and looked up once."""
    service = MagicMock()
    service.list_plants_window.return_value = _page_of_plants()
    service.resolve_phase_name.return_value = "vegetative"
    service.resolve_species.return_value = None
    service.resolve_cultivar.return_value = _cultivar()

    rows = _plant_client(service).get("/api/v1/t/test-slug/plant-instances").json()

    assert all(r["species"] is None for r in rows)
    assert service.resolve_species.call_count == 1


def test_plant_instances_single_plant_resolves_with_fresh_memo():
    """Single-plant responses keep resolving their own labels per request."""
    service = MagicMock()
    plant = _page_of_plants()[0]
    service.get_plant.return_value = plant
    service.resolve_phase_name.return_value = "vegetative"
    service.resolve_species.return_value = _species()
    service.resolve_cultivar.return_value = _cultivar()
    client = _plant_client(service)

    for _ in range(2):
        body = client.get("/api/v1/t/test-slug/plant-instances/p-0").json()
        assert body["current_phase"] == "vegetative"
        assert body["species"]["scientific_name"] == "Ocimum basilicum"
        assert body["cultivar"] == {"name": "Genovese"}

    # No memo leaks across requests: each request resolved once.
    assert service.resolve_species.call_count == 2
    assert service.resolve_cultivar.call_count == 2
    assert service.resolve_phase_name.call_count == 2


def test_plant_instances_list_builds_a_fresh_memo_per_request():
    """The list memo lives for one request: a second page request resolves again."""
    service = MagicMock()
    service.list_plants_window.return_value = _page_of_plants()
    service.resolve_phase_name.return_value = "vegetative"
    service.resolve_species.return_value = _species()
    service.resolve_cultivar.return_value = _cultivar()
    client = _plant_client(service)

    for _ in range(2):
        assert client.get("/api/v1/t/test-slug/plant-instances").status_code == 200

    assert service.resolve_species.call_count == 2
    assert service.resolve_cultivar.call_count == 2
    assert service.resolve_phase_name.call_count == 2


def _run_rows() -> list[dict]:
    return [
        {
            "_key": f"p-{i}",
            "instance_id": f"BASIL-{i:03d}",
            "species_key": "basil",
            "cultivar_key": "genovese",
            "plant_name": None,
            "planted_on": "2026-01-01",
            "current_phase": "vegetative",
        }
        for i in range(_PAGE_SIZE)
    ]


def _run_client(run_service: MagicMock, species_repo: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(run_router, prefix="/api/v1/t/test-slug")
    app.dependency_overrides[get_planting_run_service] = lambda: run_service
    app.dependency_overrides[get_species_repo] = lambda: species_repo
    app.dependency_overrides[get_current_tenant] = _ctx
    return TestClient(app)


def test_run_plants_list_resolves_each_shared_label_once():
    """#3032: the planting-run plant list shares the same per-request memo."""
    run_service = MagicMock()
    run_service.get_plants.return_value = _run_rows()
    species_repo = MagicMock()
    species_repo.get_by_key.return_value = _species()
    species_repo.get_cultivar_by_key.return_value = _cultivar()

    resp = _run_client(run_service, species_repo).get("/api/v1/t/test-slug/planting-runs/run-1/plants")

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == _PAGE_SIZE
    # The run route passes the stored phase label through; it does not resolve phases.
    assert all(r["current_phase"] == "vegetative" for r in rows)
    assert all(r["species"]["common_names"] == ["Basilikum", "Basil"] for r in rows)
    assert all(r["cultivar"] == {"name": "Genovese"} for r in rows)
    species_repo.get_by_key.assert_called_once_with("basil")
    species_repo.get_cultivar_by_key.assert_called_once_with("genovese")


def test_run_plants_list_foreign_private_species_is_null():
    """#2082: another tenant's private species resolves to null — once per request."""
    run_service = MagicMock()
    run_service.get_plants.return_value = _run_rows()
    foreign = _species()
    foreign.tenant_key = "t-other"
    species_repo = MagicMock()
    species_repo.get_by_key.return_value = foreign
    species_repo.is_granted_to.return_value = False
    species_repo.get_cultivar_by_key.return_value = _cultivar()

    rows = _run_client(run_service, species_repo).get("/api/v1/t/test-slug/planting-runs/run-1/plants").json()

    assert all(r["species"] is None for r in rows)
    assert all(r["cultivar"] == {"name": "Genovese"} for r in rows)
    assert species_repo.get_by_key.call_count == 1
    species_repo.is_granted_to.assert_called_once_with("basil", TENANT_KEY)


def test_run_plants_list_builds_a_fresh_memo_per_request():
    """The run-plants memo lives for one request as well."""
    run_service = MagicMock()
    run_service.get_plants.return_value = _run_rows()
    species_repo = MagicMock()
    species_repo.get_by_key.return_value = _species()
    species_repo.get_cultivar_by_key.return_value = _cultivar()
    client = _run_client(run_service, species_repo)

    for _ in range(2):
        assert client.get("/api/v1/t/test-slug/planting-runs/run-1/plants").status_code == 200

    assert species_repo.get_by_key.call_count == 2
    assert species_repo.get_cultivar_by_key.call_count == 2
