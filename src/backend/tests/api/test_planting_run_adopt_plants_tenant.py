"""#1973 — ``POST /t/{slug}/planting-runs/{key}/adopt-plants`` must not link a
plant of another tenant into the caller's run.

Drives the real route and the real ``PlantingRunService``; only the repositories
are doubled. The plant double is unscoped on purpose, like the real
``PlantInstanceRepository.get_by_key``: it answers any key whatever its tenant.
"""

from datetime import date
from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.planting_runs.tenant_router import router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_planting_run_service
from app.common.enums import PlantingRunStatus, PlantingRunType, TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.models.tenant_context import TenantContext
from app.domain.services.planting_run_service import PlantingRunService
from tests.conftest import wire_get_or_raise

SLUG = "anna"
OWN = "tenant_anna"
FOREIGN = "tenant_bob"
RUN_KEY = "run_1"


def _plant(key: str, tenant_key: str) -> PlantInstance:
    return PlantInstance(
        _key=key,
        instance_id=key.upper(),
        species_key="sp_tomato",
        planted_on=date(2026, 1, 1),
        tenant_key=tenant_key,
    )


def _build(plants: dict[str, PlantInstance]):
    run_repo = MagicMock()
    run_repo.get_by_key.return_value = PlantingRun(
        _key=RUN_KEY,
        tenant_key=OWN,
        name="Tomaten",
        run_type=PlantingRunType.MONOCULTURE,
        status=PlantingRunStatus.PLANNED,
    )
    wire_get_or_raise(run_repo, "PlantingRun")
    run_repo.get_entries.return_value = [
        PlantingRunEntry(_key="e1", run_key=RUN_KEY, species_key="sp_tomato", quantity=2, id_prefix="TOM")
    ]
    run_repo.get_runs_for_plant.return_value = []
    plant_repo = MagicMock()
    plant_repo.get_by_key.side_effect = lambda key: plants.get(key)
    service = PlantingRunService(run_repo=run_repo, plant_repo=plant_repo, engine=MagicMock())

    app = FastAPI()
    app.include_router(router, prefix=f"/api/v1/t/{SLUG}")

    @app.exception_handler(KamerplanterError)
    def _handler(request: Request, exc: KamerplanterError):
        return JSONResponse(status_code=exc.status_code, content={"message": exc.message})

    ctx = TenantContext(tenant_key=OWN, tenant_slug=SLUG, user_key="u", role=TenantRole.LEAD)
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    app.dependency_overrides[get_planting_run_service] = lambda: service
    return TestClient(app), run_repo


def test_foreign_tenant_plant_is_not_linked():
    client, run_repo = _build({"p_foreign": _plant("p_foreign", FOREIGN)})
    resp = client.post(
        f"/api/v1/t/{SLUG}/planting-runs/{RUN_KEY}/adopt-plants",
        json={"plant_keys": ["p_foreign"]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["adopted_count"] == 0
    assert body["skipped"][0]["reason"] == "Plant not found"
    run_repo.link_run_to_plant.assert_not_called()


def test_foreign_reads_exactly_like_unknown():
    client, _ = _build({"p_foreign": _plant("p_foreign", FOREIGN)})
    url = f"/api/v1/t/{SLUG}/planting-runs/{RUN_KEY}/adopt-plants"
    foreign = client.post(url, json={"plant_keys": ["p_foreign"]}).json()["skipped"][0]["reason"]
    unknown = client.post(url, json={"plant_keys": ["p_ghost"]}).json()["skipped"][0]["reason"]
    assert foreign == unknown


def test_own_plant_is_still_adopted():
    client, run_repo = _build({"p_own": _plant("p_own", OWN)})
    resp = client.post(
        f"/api/v1/t/{SLUG}/planting-runs/{RUN_KEY}/adopt-plants",
        json={"plant_keys": ["p_own"]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["adopted_keys"] == ["p_own"]
    run_repo.link_run_to_plant.assert_called_once_with(RUN_KEY, "p_own")


def test_mixed_batch_links_only_own():
    client, run_repo = _build({"p_own": _plant("p_own", OWN), "p_foreign": _plant("p_foreign", FOREIGN)})
    resp = client.post(
        f"/api/v1/t/{SLUG}/planting-runs/{RUN_KEY}/adopt-plants",
        json={"plant_keys": ["p_foreign", "p_own"]},
    )
    assert resp.json()["adopted_keys"] == ["p_own"]
    run_repo.link_run_to_plant.assert_called_once_with(RUN_KEY, "p_own")


def test_repeated_key_is_linked_once():
    client, run_repo = _build({"p_own": _plant("p_own", OWN)})
    resp = client.post(
        f"/api/v1/t/{SLUG}/planting-runs/{RUN_KEY}/adopt-plants",
        json={"plant_keys": ["p_own", "p_own"]},
    )
    assert resp.json()["adopted_count"] == 1
    run_repo.link_run_to_plant.assert_called_once_with(RUN_KEY, "p_own")
