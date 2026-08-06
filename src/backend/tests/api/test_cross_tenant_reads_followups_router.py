"""The cross-tenant reads that survived #947 (#952).

Three leftovers of the #927 family, none of them closed by that PR:

1. ``GET /t/{slug}/plant-instances/{plant_key}/watering-volume-suggestion``
   loaded the plant straight from the URL key and then fed ``plant.tenant_key``
   into the reads #947 had just scoped. The filter compared the record's tenant
   with **itself** — a tautology, so the hardening did not apply on this path and
   a foreign key answered 200 with a recommendation derived from the other
   tenant's plant, substrate and sensors.
2. ``resolve_plant_names`` dereferenced ``plant_keys`` through an unfiltered
   ``DOCUMENT()`` loop, so a log referencing a foreign plant read that plant's
   display name back out of every watering-log response.
3. ``get_tasks_for_run`` was the last query in ``task_repository`` still scanning
   ``tasks`` with no tenant predicate at all (pinned in the repository's own unit
   tests rather than here — it has no endpoint yet, which is the point).

Both directions are pinned throughout: a strict filter that also hides the
caller's own rows is the #324 regression class and not a fix.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.watering_events.tenant_router import router as watering_events_router
from app.api.v1.watering_logs.tenant_router import router as watering_logs_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_watering_log_service, get_watering_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.watering_log_repository import ArangoWateringLogRepository
from app.domain.engines.watering_engine import WateringEngine
from app.domain.engines.watering_volume_engine import WateringVolumeEngine
from app.domain.models.tenant_context import TenantContext
from app.domain.services.watering_log_service import WateringLogService
from app.domain.services.watering_service import WateringService
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase, apply_predicates

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_PLANT = "plant-a1"
FOREIGN_PLANT = "plant-b1"

#: The foreign plant's display name — the thing that must not come back.
FOREIGN_MARKER = "Fremde-Geheimpflanze"


# ── Harness ──────────────────────────────────────────────────────────────────


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _client(router, dependency, service) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user-1",
        role=TenantRole.GROWER,
    )
    app.dependency_overrides[dependency] = lambda: service
    return TestClient(app)


def _url(path: str) -> str:
    return f"/api/v1/t/{TENANT_SLUG}{path}"


# ── 1: the volume suggestion ─────────────────────────────────────────────────


class _PlantRepo:
    """Answers by key regardless of tenant — like the real ``get_by_key``."""

    def __init__(self, plants: dict[str, Any]) -> None:
        self._plants = plants

    def get_by_key(self, key: str) -> Any:
        return self._plants.get(key)


def _plant(key: str, tenant_key: str) -> SimpleNamespace:
    return SimpleNamespace(
        key=key,
        tenant_key=tenant_key,
        species_key="sp-tomato",
        cultivar_key=None,
        substrate_key=None,
        substrate_type_override=None,
        current_phase_key=None,
        container_volume_liters=None,
    )


class _SpeciesRepo:
    def get_by_key(self, key: str) -> Any:  # noqa: ARG002
        guide = SimpleNamespace(volume_ml_min=200, volume_ml_max=400, seasonal_adjustments=None)
        return SimpleNamespace(waterlogging_tolerance=None, watering_guide=guide)


def _volume_client() -> TestClient:
    plants = {
        OWN_PLANT: _plant(OWN_PLANT, TENANT_KEY),
        FOREIGN_PLANT: _plant(FOREIGN_PLANT, FOREIGN_TENANT_KEY),
    }
    site_repo = MagicMock()
    site_repo.get_slot_for_plant.return_value = None
    service = WateringService(
        repo=MagicMock(),
        engine=WateringEngine(),
        site_repo=site_repo,
        volume_engine=WateringVolumeEngine(),
        plant_repo=_PlantRepo(plants),
        species_repo=_SpeciesRepo(),
    )
    return _client(watering_events_router, get_watering_service, service)


class TestWateringVolumeSuggestion:
    """``GET /t/{slug}/plant-instances/{plant_key}/watering-volume-suggestion`` (#952)."""

    def test_a_foreign_plant_key_is_not_found_rather_than_answered(self):
        client = _volume_client()

        resp = client.get(_url(f"/plant-instances/{FOREIGN_PLANT}/watering-volume-suggestion"))

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"

    def test_the_callers_own_plant_still_gets_a_recommendation(self):
        client = _volume_client()

        resp = client.get(_url(f"/plant-instances/{OWN_PLANT}/watering-volume-suggestion"))

        assert resp.status_code == 200, resp.text
        assert resp.json()["volume_ml"] > 0


# ── 2: plant-name resolution on watering logs ────────────────────────────────


def _watering_log_client() -> TestClient:
    """A log of the caller's own tenant that references a foreign plant.

    That is a legacy row: the write path accepted ``plant_keys`` from the body
    with no ownership check, so such rows exist in the wild. The name resolution
    therefore has to hold on its own — it cannot assume the reference is clean.
    """
    logs = {
        "wl-own": {
            "_key": "wl-own",
            "_id": f"{col.WATERING_LOGS}/wl-own",
            "tenant_key": TENANT_KEY,
            "slot_keys": ["slot-a1"],
            "plant_keys": [OWN_PLANT, FOREIGN_PLANT],
            "logged_at": "2026-08-01T08:00:00+00:00",
            "volume_liters": 2.0,
            "application_method": "drench",
        },
    }
    plants = [
        {
            "_key": OWN_PLANT,
            "_id": f"{col.PLANT_INSTANCES}/{OWN_PLANT}",
            "tenant_key": TENANT_KEY,
            "plant_name": "Meine Tomate",
        },
        {
            "_key": FOREIGN_PLANT,
            "_id": f"{col.PLANT_INSTANCES}/{FOREIGN_PLANT}",
            "tenant_key": FOREIGN_TENANT_KEY,
            "plant_name": FOREIGN_MARKER,
        },
    ]

    def resolve_names(query: str, bind_vars: dict[str, Any]) -> Any:
        wanted = set(bind_vars["plant_keys"])
        rows = [p for p in plants if p["_key"] in wanted]
        # ``pi`` is the AQL variable the DOCUMENT() lookup binds — resolve it to
        # the plant itself so whatever predicate the query spells out is applied.
        rows = apply_predicates(rows, query, bind_vars, resolvers={"pi": lambda row: row})
        return [{"key": p["_key"], "name": p.get("plant_name") or p["_key"]} for p in rows]

    aql = ReplayingAql()
    aql.route("FOR pk IN @plant_keys", resolve_names)
    aql.route("FOR fk IN @fert_keys", lambda q, b: [])

    collection = MagicMock()
    collection.get.side_effect = lambda key: logs.get(key)
    repo = ArangoWateringLogRepository(ReplayingDatabase(aql, {col.WATERING_LOGS: collection}))
    service = WateringLogService(repo, WateringEngine(), MagicMock())
    return _client(watering_logs_router, get_watering_log_service, service)


class TestResolvedPlantNamesOnAWateringLog:
    """``GET /t/{slug}/watering-logs/{key}`` resolves names, so it must scope them (#952)."""

    def test_a_foreign_plant_reference_does_not_yield_its_name(self):
        client = _watering_log_client()

        resp = client.get(_url("/watering-logs/wl-own"))

        assert resp.status_code == 200, resp.text
        assert FOREIGN_MARKER not in resp.text
        # The key the caller supplied is echoed back; the *name* behind it is not.
        resolved = {p["key"]: p["name"] for p in resp.json()["resolved_plants"]}
        assert resolved[FOREIGN_PLANT] == FOREIGN_PLANT

    def test_the_callers_own_plant_is_still_named(self):
        client = _watering_log_client()

        resp = client.get(_url("/watering-logs/wl-own"))

        assert resp.status_code == 200, resp.text
        resolved = {p["key"]: p["name"] for p in resp.json()["resolved_plants"]}
        assert resolved[OWN_PLANT] == "Meine Tomate"
