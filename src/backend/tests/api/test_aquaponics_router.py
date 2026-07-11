"""REQ-026 — API tests for the tenant-scoped aquaponics router and the global
fish-species router. A real :class:`AquaponikService` (with its real engines) is
wired over an in-memory fake repository, exercising the full request stack."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.aquaponik.tenant_router import router as aquaponics_router
from app.api.v1.fish_species.router import router as fish_species_router
from app.common.auth import get_current_tenant, get_current_user, require_tenant_role
from app.common.dependencies import get_aquaponik_service
from app.common.enums import FishFeedCategory, TemperatureZone, TenantRole
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.aquaponik import (
    AquaponicSystem,
    FishFeedingEvent,
    FishSpecies,
    FishStock,
    SupplementationEvent,
    WaterTest,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.aquaponik_service import AquaponikService

TENANT_SLUG = "mein-garten"
TENANT_KEY = "tenant_garten"
OTHER_TENANT = "tenant_other"


def _tilapia() -> FishSpecies:
    return FishSpecies(
        _key="tilapia_nile",
        scientific_name="Oreochromis niloticus",
        common_name_de="Nil-Tilapia",
        common_name_en="Nile Tilapia",
        temperature_zone=TemperatureZone.WARMWATER,
        temperature_min_c=18,
        temperature_max_c=34,
        temperature_optimal_min_c=26,
        temperature_optimal_max_c=30,
        temperature_lethal_low_c=12,
        temperature_lethal_high_c=38,
        ph_min=6.5,
        ph_max=8.5,
        do_minimum_mgl=2.0,
        do_optimal_mgl=5.0,
        do_stress_mgl=3.0,
        max_tan_mgl=2.0,
        max_nitrite_mgl=1.0,
        max_nitrate_mgl=200,
        feed_type=FishFeedCategory.OMNIVORE,
        max_stocking_density_kg_per_1000l=25,
        market_weight_g=500,
    )


class FakeAquaponikRepo:
    """In-memory stand-in for ``ArangoAquaponikRepository``."""

    def __init__(self) -> None:
        self.systems: dict[str, AquaponicSystem] = {}
        self.stocks: dict[str, FishStock] = {}
        self.water_tests: dict[str, WaterTest] = {}
        self.feedings: dict[str, FishFeedingEvent] = {}
        self.supplements: dict[str, SupplementationEvent] = {}
        self.species: dict[str, FishSpecies] = {"tilapia_nile": _tilapia()}
        self.compat_edges: dict[str, list[dict]] = {}
        self._seq = 0

    def _next(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}{self._seq}"

    # species
    def list_species(self, temperature_zone=None, feed_type=None):
        items = list(self.species.values())
        if temperature_zone:
            items = [s for s in items if s.temperature_zone.value == temperature_zone]
        if feed_type:
            items = [s for s in items if s.feed_type.value == feed_type]
        return items

    def get_species(self, key):
        return self.species.get(key)

    def get_species_or_raise(self, key):
        s = self.species.get(key)
        if s is None:
            raise NotFoundError("FishSpecies", key)
        return s

    def get_compatible_plants(self, key, compatible=True):
        return self.compat_edges.get(f"{key}:{compatible}", [])

    # systems
    def get_or_raise(self, key):
        s = self.systems.get(key)
        if s is None:
            raise NotFoundError("AquaponicSystem", key)
        return s

    def list_systems(self, tenant_key):
        return [s for s in self.systems.values() if s.tenant_key == tenant_key]

    def create_system(self, system):
        key = self._next("sys")
        stored = system.model_copy(update={"key": key})
        self.systems[key] = stored
        return stored

    def update(self, key, system):
        stored = system.model_copy(update={"key": key})
        self.systems[key] = stored
        return stored

    def delete_system(self, key):
        self.systems.pop(key, None)
        return True

    # stocks
    def list_stocks(self, system_key):
        return [s for s in self.stocks.values() if s.system_key == system_key]

    def create_stock(self, stock):
        key = self._next("stock")
        stored = stock.model_copy(update={"key": key})
        self.stocks[key] = stored
        return stored

    def get_stock_or_raise(self, key):
        s = self.stocks.get(key)
        if s is None:
            raise NotFoundError("FishStock", key)
        return s

    def update_stock(self, key, stock):
        stored = stock.model_copy(update={"key": key})
        self.stocks[key] = stored
        return stored

    def delete_stock(self, key):
        self.stocks.pop(key, None)
        return True

    # water tests
    def create_water_test(self, water_test):
        key = self._next("wt")
        stored = water_test.model_copy(update={"key": key})
        self.water_tests[key] = stored
        return stored

    def list_water_tests(self, system_key, offset=0, limit=50):
        items = [w for w in self.water_tests.values() if w.system_key == system_key]
        items.sort(key=lambda w: w.tested_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return items[offset : offset + limit]

    def get_latest_water_test(self, system_key):
        items = self.list_water_tests(system_key, 0, 1)
        return items[0] if items else None

    # feedings
    def create_feeding(self, feeding):
        key = self._next("feed")
        stored = feeding.model_copy(update={"key": key})
        self.feedings[key] = stored
        return stored

    def list_feedings(self, system_key, offset=0, limit=50):
        items = [f for f in self.feedings.values() if f.system_key == system_key]
        return items[offset : offset + limit]

    # supplements
    def create_supplementation(self, event):
        key = self._next("supp")
        stored = event.model_copy(update={"key": key})
        self.supplements[key] = stored
        return stored

    def list_supplementations(self, system_key, offset=0, limit=50):
        items = [s for s in self.supplements.values() if s.system_key == system_key]
        return items[offset : offset + limit]


def _ctx() -> TenantContext:
    return TenantContext(tenant_key=TENANT_KEY, tenant_slug=TENANT_SLUG, user_key="user_1", role=TenantRole.ADMIN)


def _user() -> User:
    return User(_key="user_1", email="grower@example.com", display_name="Grower")


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code})


def _build() -> tuple[TestClient, FakeAquaponikRepo]:
    repo = FakeAquaponikRepo()
    service = AquaponikService(repo)  # type: ignore[arg-type]

    app = FastAPI()
    app.include_router(aquaponics_router, prefix="/api/v1/t/{tenant_slug}")
    app.include_router(fish_species_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[require_tenant_role(TenantRole.ADMIN)] = _ctx
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_aquaponik_service] = lambda: service
    return TestClient(app), repo


def _base(path: str = "") -> str:
    return f"/api/v1/t/{TENANT_SLUG}/aquaponics{path}"


_SYSTEM_BODY = {
    "name": "Tilapia-Salat DWC",
    "system_type": "dwc",
    "total_volume_liters": 640,
    "grow_area_m2": 4.0,
    "biofilter_type": "mbbr",
    "biofilter_volume_liters": 40,
    "daily_feed_target_g": 67.5,
}


class TestSystemCrud:
    def test_create_and_get_system(self):
        client, _repo = _build()
        resp = client.post(_base("/systems"), json=_SYSTEM_BODY)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["cycling_status"] == "new"
        key = body["key"]
        resp = client.get(_base(f"/systems/{key}"))
        assert resp.status_code == 200
        assert resp.json()["name"] == _SYSTEM_BODY["name"]

    def test_dwc_requires_biofilter(self):
        client, _repo = _build()
        body = {**_SYSTEM_BODY}
        del body["biofilter_type"]
        resp = client.post(_base("/systems"), json=body)
        assert resp.status_code == 422

    def test_list_systems(self):
        client, _repo = _build()
        client.post(_base("/systems"), json=_SYSTEM_BODY)
        resp = client.get(_base("/systems"))
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_update_system(self):
        client, _repo = _build()
        key = client.post(_base("/systems"), json=_SYSTEM_BODY).json()["key"]
        resp = client.patch(_base(f"/systems/{key}"), json={"daily_feed_target_g": 80})
        assert resp.status_code == 200
        assert resp.json()["daily_feed_target_g"] == 80

    def test_cycling_status_override(self):
        client, _repo = _build()
        key = client.post(_base("/systems"), json=_SYSTEM_BODY).json()["key"]
        resp = client.post(_base(f"/systems/{key}/cycling-status"), json={"cycling_status": "cycled"})
        assert resp.status_code == 200
        assert resp.json()["cycling_status"] == "cycled"

    def test_delete_empty_system(self):
        client, _repo = _build()
        key = client.post(_base("/systems"), json=_SYSTEM_BODY).json()["key"]
        resp = client.delete(_base(f"/systems/{key}"))
        assert resp.status_code == 204

    def test_get_unknown_system_404(self):
        client, _repo = _build()
        resp = client.get(_base("/systems/nope"))
        assert resp.status_code == 404

    def test_cross_tenant_system_not_found(self):
        client, repo = _build()
        # Foreign system exists but belongs to another tenant.
        foreign = AquaponicSystem(
            _key="foreign",
            tenant_key=OTHER_TENANT,
            name="Foreign",
            system_type="media_bed",
            total_volume_liters=100,
            grow_area_m2=1,
        )
        repo.systems["foreign"] = foreign
        resp = client.get(_base("/systems/foreign"))
        assert resp.status_code == 404


class TestStocksAndWaterTests:
    def _system(self, client) -> str:
        return client.post(_base("/systems"), json=_SYSTEM_BODY).json()["key"]

    def test_create_stock_and_biomass(self):
        client, _repo = _build()
        sys_key = self._system(client)
        resp = client.post(
            _base(f"/systems/{sys_key}/fish-stocks"),
            json={
                "name": "Tilapia März",
                "species_key": "tilapia_nile",
                "count": 15,
                "avg_weight_g": 150,
                "stocking_date": "2026-03-01",
            },
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["total_biomass_kg"] == 2.25

    def test_stock_unknown_species_404(self):
        client, _repo = _build()
        sys_key = self._system(client)
        resp = client.post(
            _base(f"/systems/{sys_key}/fish-stocks"),
            json={
                "name": "X",
                "species_key": "unknown",
                "count": 5,
                "avg_weight_g": 100,
                "stocking_date": "2026-03-01",
            },
        )
        assert resp.status_code == 404

    def test_mortality_and_delete_conflict(self):
        client, _repo = _build()
        sys_key = self._system(client)
        stock_key = client.post(
            _base(f"/systems/{sys_key}/fish-stocks"),
            json={
                "name": "Tilapia",
                "species_key": "tilapia_nile",
                "count": 15,
                "avg_weight_g": 150,
                "stocking_date": "2026-03-01",
            },
        ).json()["key"]
        # Deleting a stock with live fish is a 409 conflict.
        resp = client.delete(_base(f"/systems/{sys_key}/fish-stocks/{stock_key}"))
        assert resp.status_code == 409
        # Record mortality of all fish, then delete succeeds.
        resp = client.post(_base(f"/systems/{sys_key}/fish-stocks/{stock_key}/mortality"), json={"deaths": 15})
        assert resp.status_code == 200
        assert resp.json()["count"] == 0
        resp = client.delete(_base(f"/systems/{sys_key}/fish-stocks/{stock_key}"))
        assert resp.status_code == 204

    def test_water_test_computes_free_ammonia(self):
        client, _repo = _build()
        sys_key = self._system(client)
        resp = client.post(
            _base(f"/systems/{sys_key}/water-tests"),
            json={
                "ph": 7.0,
                "ammonia_tan_mgl": 1.0,
                "nitrite_mgl": 0.05,
                "nitrate_mgl": 40,
                "temperature_c": 25,
                "source": "test_kit",
            },
        )
        assert resp.status_code == 201, resp.text
        assert abs(resp.json()["free_ammonia_mgl"] - 0.0057) < 0.001

    def test_water_quality_status_and_cycling_progress(self):
        client, _repo = _build()
        sys_key = self._system(client)
        client.post(
            _base(f"/systems/{sys_key}/fish-stocks"),
            json={
                "name": "Tilapia",
                "species_key": "tilapia_nile",
                "count": 15,
                "avg_weight_g": 150,
                "stocking_date": "2026-03-01",
            },
        )
        client.post(
            _base(f"/systems/{sys_key}/water-tests"),
            json={
                "ph": 7.5,
                "ammonia_tan_mgl": 3.0,
                "nitrite_mgl": 0.2,
                "nitrate_mgl": 30,
                "temperature_c": 28,
            },
        )
        status = client.get(_base(f"/systems/{sys_key}/water-quality-status"))
        assert status.status_code == 200
        assert any(e["severity"] == "critical" for e in status.json())

        progress = client.get(_base(f"/systems/{sys_key}/cycling-progress"))
        assert progress.status_code == 200
        assert "progress_percent" in progress.json()

        chart = client.get(_base(f"/systems/{sys_key}/nitrogen-cycle-chart"))
        assert chart.status_code == 200
        assert len(chart.json()) == 1


class TestFeedingSupplementHealth:
    def _system_with_stock(self, client) -> tuple[str, str]:
        sys_key = client.post(_base("/systems"), json=_SYSTEM_BODY).json()["key"]
        stock_key = client.post(
            _base(f"/systems/{sys_key}/fish-stocks"),
            json={
                "name": "Tilapia",
                "species_key": "tilapia_nile",
                "count": 15,
                "avg_weight_g": 150,
                "stocking_date": "2026-03-01",
            },
        ).json()["key"]
        return sys_key, stock_key

    def test_feeding_and_recommendation(self):
        client, _repo = _build()
        sys_key, stock_key = self._system_with_stock(client)
        resp = client.post(
            _base(f"/systems/{sys_key}/fish-stocks/{stock_key}/feeding-events"),
            json={"amount_g": 60, "water_temp_c": 28},
        )
        assert resp.status_code == 201
        rec = client.get(_base(f"/systems/{sys_key}/feeding-recommendation"))
        assert rec.status_code == 200
        assert rec.json()["recommended_g"] >= 0

    def test_fcr_analysis(self):
        client, _repo = _build()
        sys_key, _stock = self._system_with_stock(client)
        resp = client.get(_base(f"/systems/{sys_key}/fcr-analysis"))
        assert resp.status_code == 200
        assert "fcr" in resp.json()

    def test_supplementation_and_deficiency(self):
        client, _repo = _build()
        sys_key, _stock = self._system_with_stock(client)
        resp = client.post(
            _base(f"/systems/{sys_key}/supplementation-events"),
            json={"supplement_type": "fe_dtpa", "amount_ml": 5, "target_parameter": "iron"},
        )
        assert resp.status_code == 201
        # deficiency-check without a water test is a 422.
        resp = client.get(_base(f"/systems/{sys_key}/deficiency-check"))
        assert resp.status_code == 422
        client.post(
            _base(f"/systems/{sys_key}/water-tests"),
            json={
                "ph": 7.0,
                "ammonia_tan_mgl": 0.1,
                "nitrite_mgl": 0.05,
                "nitrate_mgl": 40,
                "temperature_c": 26,
                "iron_ppm": 0.5,
            },
        )
        resp = client.get(_base(f"/systems/{sys_key}/deficiency-check"))
        assert resp.status_code == 200
        assert any(f["nutrient"] == "iron" for f in resp.json()["findings"])

    def test_supplementation_requires_amount(self):
        client, _repo = _build()
        sys_key, _stock = self._system_with_stock(client)
        resp = client.post(
            _base(f"/systems/{sys_key}/supplementation-events"),
            json={"supplement_type": "fe_dtpa", "target_parameter": "iron"},
        )
        assert resp.status_code == 422

    def test_safety_alerts_health(self):
        client, _repo = _build()
        sys_key, _stock = self._system_with_stock(client)
        client.post(
            _base(f"/systems/{sys_key}/water-tests"),
            json={
                "ph": 7.5,
                "ammonia_tan_mgl": 3.0,
                "nitrite_mgl": 0.2,
                "nitrate_mgl": 30,
                "temperature_c": 28,
                "kh_dh": 3.0,
            },
        )
        assert client.get(_base(f"/systems/{sys_key}/safety-status")).status_code == 200
        alerts = client.get(_base(f"/systems/{sys_key}/alerts"))
        assert alerts.status_code == 200
        assert all(a["severity"] in ("critical", "warning") for a in alerts.json())
        assert client.get(_base(f"/systems/{sys_key}/fish-health")).status_code == 200


class TestFishSpeciesRouter:
    def test_list_species(self):
        client, _repo = _build()
        resp = client.get("/api/v1/fish-species")
        assert resp.status_code == 200
        assert resp.json()[0]["common_name_de"] == "Nil-Tilapia"

    def test_get_species(self):
        client, _repo = _build()
        resp = client.get("/api/v1/fish-species/tilapia_nile")
        assert resp.status_code == 200

    def test_by_temperature_zone(self):
        client, _repo = _build()
        resp = client.get("/api/v1/fish-species/by-temperature-zone/warmwater")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert client.get("/api/v1/fish-species/by-temperature-zone/coldwater").json() == []

    def test_compatible_plants(self):
        client, repo = _build()
        repo.compat_edges["tilapia_nile:True"] = [
            {"species_key": "tomato", "common_name": "Tomate", "temperature_match": 0.8}
        ]
        resp = client.get("/api/v1/fish-species/tilapia_nile/compatible-plants")
        assert resp.status_code == 200
        assert resp.json()["compatible"][0]["species_key"] == "tomato"

    def test_unknown_species_404(self):
        client, _repo = _build()
        assert client.get("/api/v1/fish-species/nope").status_code == 404
