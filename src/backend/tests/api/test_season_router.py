"""REQ-047 §4.4 — season / overwintering tenant-router API tests.

Focus on the additive ``GET /plants/{plant_key}/overwintering/status`` endpoint,
which always answers 200 (unlike the profile read's 404) so the detail page can
tell "winter-hardy" apart from "profile is materialised in autumn".
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.season.tenant_router import router as season_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_overwintering_profile_service
from app.common.enums import FrostTolerance, HardinessRating, SiteType, TenantRole, WinterAction
from app.common.exceptions import KamerplanterError
from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext
from app.domain.services.overwintering_profile_service import OverwinteringProfileService

TENANT_SLUG = "anna"
TENANT_KEY = "tenant_anna"


class _FakeRepo(IOverwinteringProfileRepository):
    def __init__(self) -> None:
        self.store: dict[str, OverwinteringProfile] = {}
        self._seq = 0

    def get_profile_by_key(self, key):
        return self.store.get(key)

    def get_profile_by_plant_key(self, plant_key):
        return next((p for p in self.store.values() if p.plant_key == plant_key), None)

    def get_profile_by_run_key(self, run_key):
        return next((p for p in self.store.values() if p.planting_run_key == run_key), None)

    def create_profile(self, profile):
        self._seq += 1
        key = f"ow{self._seq}"
        stored = profile.model_copy(update={"key": key})
        self.store[key] = stored
        return stored

    def update_profile(self, key, profile):
        stored = profile.model_copy(update={"key": key})
        self.store[key] = stored
        return stored

    def delete_profile(self, key):
        return self.store.pop(key, None) is not None

    def list_by_tenant(self, tenant_key, offset=0, limit=50):
        items = [p for p in self.store.values() if p.tenant_key == tenant_key]
        return items[offset : offset + limit], len(items)

    def create_subject_edge(self, profile_key, *, plant_key=None, planting_run_key=None):
        pass

    def create_winter_quarter_edge(self, profile_key, location_key):
        pass


class _PlantRepoStub:
    def get_by_key(self, key):  # noqa: ANN001, ANN201
        return PlantInstance(
            _key=key,
            tenant_key=TENANT_KEY,
            instance_id="i1",
            species_key="s1",
            site_key="site1",
            planted_on=date(2024, 1, 1),
        )


class _SpeciesRepoStub:
    def get_by_key(self, key):  # noqa: ANN001, ANN201
        # Moderate frost sensitivity → half_hardy → yellow ampel (Fragaria-style).
        return SimpleNamespace(frost_sensitivity=FrostTolerance.MODERATE, hardiness_zones=["7a"])


class _SiteRepoStub:
    def get_site_by_key(self, key):  # noqa: ANN001, ANN201
        return SimpleNamespace(tenant_key=TENANT_KEY, climate_zone="7a", type=SiteType.OUTDOOR)


def _ctx() -> TenantContext:
    return TenantContext(tenant_key=TENANT_KEY, tenant_slug=TENANT_SLUG, user_key="user_anna", role=TenantRole.LEAD)


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


def _build(*, with_context: bool = True) -> tuple[FastAPI, OverwinteringProfileService]:
    service = OverwinteringProfileService(
        _FakeRepo(),
        plant_repo=_PlantRepoStub() if with_context else None,
        species_repo=_SpeciesRepoStub() if with_context else None,
        site_repo=_SiteRepoStub() if with_context else None,
    )
    app = FastAPI()
    app.include_router(season_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: _ctx()
    app.dependency_overrides[get_overwintering_profile_service] = lambda: service
    return app, service


def _url(plant_key: str) -> str:
    return f"/api/v1/t/{TENANT_SLUG}/plants/{plant_key}/overwintering/status"


class TestPlantOverwinteringStatusRoute:
    def test_no_profile_yellow_returns_200_will_materialize(self) -> None:
        app, _service = _build()
        client = TestClient(app)

        resp = client.get(_url("p1"))
        assert resp.status_code == 200
        body = resp.json()
        assert body == {
            "has_profile": False,
            "hardiness_light": "yellow",
            "will_materialize": True,
            "site_overwinterable": True,
        }

    def test_existing_profile_returns_has_profile(self) -> None:
        app, service = _build()
        service._repo.create_profile(
            OverwinteringProfile(
                plant_key="p1",
                hardiness_rating=HardinessRating.NEEDS_PROTECTION,
                winter_action=WinterAction.FLEECE,
                winter_action_month=10,
                tenant_key=TENANT_KEY,
            )
        )
        client = TestClient(app)

        resp = client.get(_url("p1"))
        assert resp.status_code == 200
        body = resp.json()
        assert body["has_profile"] is True
        assert body["hardiness_light"] == "yellow"
        assert body["will_materialize"] is False

    def test_unresolvable_context_returns_unknown_200(self) -> None:
        app, _service = _build(with_context=False)
        client = TestClient(app)

        resp = client.get(_url("p1"))
        assert resp.status_code == 200
        assert resp.json() == {
            "has_profile": False,
            "hardiness_light": None,
            "will_materialize": False,
            "site_overwinterable": False,
        }
