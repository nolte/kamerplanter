"""Tests for the ``origin`` data-provenance marker (#10, REQ-001/REQ-011).

``origin`` is a server-managed ownership marker (not a geographic field). It
drives the read-only / deletion-protection logic in the frontend (UI-NFR-018):

* seeded master data defaults to ``system`` (read-only);
* the external enrichment engine promotes a species to ``enrichment``;
* user-created records are marked ``tenant`` (editable);
* for the tenant-scoped fertilizer / nutrient-plan catalogues the marker is
  derived from ``tenant_key`` (empty => shared ``system`` catalog).

These tests assert the field is actually serialised to the API (5-layer
serialisation) and that the create endpoints set / the derivation computes the
right value.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.cultivars.schemas import CultivarResponse
from app.api.v1.ipm.router import router as ipm_router
from app.api.v1.species.router import router as species_router
from app.common.auth import (
    get_active_tenant_context,
    get_active_tenant_key,
    get_creating_tenant_key,
    get_current_user,
    get_is_platform_admin,
)
from app.common.dependencies import get_family_repo, get_ipm_service, get_species_service
from app.common.enums import DataOrigin, TenantRole
from app.config.settings import settings
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.ipm import Disease, Treatment
from app.domain.models.nutrient_plan import NutrientPlan
from app.domain.models.species import Cultivar, Species
from app.domain.models.tenant_context import TenantContext


def _user() -> SimpleNamespace:
    return SimpleNamespace(key="user_1")


# ── Model defaults ───────────────────────────────────────────────────


def test_master_data_models_default_to_system_origin():
    assert Species(scientific_name="Rosa canina").origin is DataOrigin.SYSTEM
    assert Cultivar(name="Nina", species_key="sp_1").origin is DataOrigin.SYSTEM
    assert Disease(scientific_name="Botrytis cinerea", common_name="Grey mould", pathogen_type="fungal").origin is (
        DataOrigin.SYSTEM
    )
    assert Treatment(name="Neem oil", treatment_type="biological").origin is DataOrigin.SYSTEM


# ── Fertilizer / NutrientPlan derivation (router helpers) ─────────────


def test_fertilizer_origin_is_derived_from_tenant_key():
    from app.api.v1.fertilizers.tenant_router import _fert_response

    shared = Fertilizer(_key="f1", product_name="Base A", fertilizer_type="base", tenant_key="")
    owned = Fertilizer(_key="f2", product_name="My Mix", fertilizer_type="base", tenant_key="tenant_42")

    assert _fert_response(shared).origin is DataOrigin.SYSTEM
    assert _fert_response(owned).origin is DataOrigin.TENANT


def test_nutrient_plan_origin_is_derived_from_tenant_key():
    from app.api.v1.nutrient_plans.tenant_router import _plan_response

    shared = NutrientPlan(_key="p1", name="Standard", tenant_key="")
    owned = NutrientPlan(_key="p2", name="Custom", tenant_key="tenant_42")

    assert _plan_response(shared).origin is DataOrigin.SYSTEM
    assert _plan_response(owned).origin is DataOrigin.TENANT


# ── Species API: origin is served + create marks tenant ──────────────


def _species_app(service: MagicMock, *, creating_tenant_key: str = "") -> FastAPI:
    app = FastAPI()
    app.include_router(species_router, prefix="/api/v1")
    family_repo = MagicMock()
    family_repo.get_by_key.return_value = None
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[get_family_repo] = lambda: family_repo
    # The global species create route resolves the owning tenant from the caller
    # (F-3/#808), not the /t/{slug}/ path; override the resolver so the route does
    # not reach the real tenant service (and thus a datastore) in these fakes.
    app.dependency_overrides[get_creating_tenant_key] = lambda: creating_tenant_key
    # SEC-001/SEC-002 (#808): the by-key read scopes on the active tenant and the
    # write routes resolve a role-bearing context + platform-admin flag. Override
    # them so these origin fakes never reach the real tenant service / a datastore.
    app.dependency_overrides[get_active_tenant_key] = lambda: creating_tenant_key
    app.dependency_overrides[get_active_tenant_context] = lambda: TenantContext(
        tenant_key=creating_tenant_key, tenant_slug="t", user_key="user_1", role=TenantRole.LEAD
    )
    app.dependency_overrides[get_is_platform_admin] = lambda: True
    return app


def test_species_get_serves_origin():
    service = MagicMock()
    service.get_species.return_value = Species(_key="sp_1", scientific_name="Rosa canina", origin=DataOrigin.ENRICHMENT)
    client = TestClient(_species_app(service))

    resp = client.get("/api/v1/species/sp_1")

    assert resp.status_code == 200
    assert resp.json()["origin"] == "enrichment"


def test_species_create_marks_tenant_origin():
    service = MagicMock()
    service.create_species.side_effect = lambda s: s
    # A resolvable active tenant so the SEC-004 full-mode "no active tenant" guard
    # does not fire — this test is about the origin marker, not the guard.
    client = TestClient(_species_app(service, creating_tenant_key="tenant_personal_1"))

    resp = client.post("/api/v1/species", json={"scientific_name": "Ocimum basilicum"})

    assert resp.status_code == 201
    assert resp.json()["origin"] == "tenant"
    # The service received a species already marked tenant-owned.
    created = service.create_species.call_args.args[0]
    assert created.origin is DataOrigin.TENANT


def test_species_create_stamps_caller_tenant_key():
    # F-3/#808 acceptance-2: the interactive create binds the new species to the
    # tenant resolved from the authenticated caller — here the (overridden)
    # personal tenant — and never to a value from the request body.
    service = MagicMock()
    service.create_species.side_effect = lambda s: s
    client = TestClient(_species_app(service, creating_tenant_key="tenant_personal_1"))

    resp = client.post(
        "/api/v1/species",
        # A body-supplied tenant_key must be ignored: SpeciesCreate has no such
        # field, so it is dropped at the schema boundary rather than stamped.
        json={"scientific_name": "Ocimum basilicum", "tenant_key": "attacker_tenant"},
    )

    assert resp.status_code == 201
    created = service.create_species.call_args.args[0]
    assert created.tenant_key == "tenant_personal_1"


def test_species_create_defaults_global_when_no_personal_tenant(monkeypatch):
    # Fail-safe direction in LIGHT mode: an unresolvable personal tenant yields ""
    # (global), not a foreign tenant and not a failed request. SEC-004 (#808)
    # narrowed this fail-safe to light mode — in full mode an empty active tenant
    # is refused (see test_full_mode_create_without_active_tenant_is_rejected),
    # because there stamping origin=TENANT as global injects into the shared
    # catalogue. Light mode is single-tenant, so the empty key is the legitimate
    # operator context.
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    service = MagicMock()
    service.create_species.side_effect = lambda s: s
    client = TestClient(_species_app(service, creating_tenant_key=""))

    resp = client.post("/api/v1/species", json={"scientific_name": "Ocimum basilicum"})

    assert resp.status_code == 201
    created = service.create_species.call_args.args[0]
    assert created.tenant_key == ""


# ── IPM API: disease/treatment origin is served + create marks tenant ─


def _ipm_app(service: MagicMock) -> FastAPI:
    app = FastAPI()
    app.include_router(ipm_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_ipm_service] = lambda: service
    return app


def test_disease_get_serves_origin_and_create_marks_tenant():
    service = MagicMock()
    service.get_disease.return_value = Disease(
        _key="d1", scientific_name="Botrytis cinerea", common_name="Grey mould", pathogen_type="fungal"
    )
    service.create_disease.side_effect = lambda d: d
    client = TestClient(_ipm_app(service))

    got = client.get("/api/v1/ipm/diseases/d1")
    assert got.status_code == 200
    assert got.json()["origin"] == "system"

    created = client.post(
        "/api/v1/ipm/diseases",
        json={"scientific_name": "Podosphaera pannosa", "common_name": "Powdery mildew", "pathogen_type": "fungal"},
    )
    assert created.status_code == 201
    assert created.json()["origin"] == "tenant"


def test_cultivar_response_schema_exposes_origin():
    # Guards the 5-layer serialisation: the response schema must carry the field
    # so ``to_response`` passes it through to the frontend.
    assert "origin" in CultivarResponse.model_fields


# ── Update preserves the server-managed provenance marker ────────────


def test_update_species_preserves_origin():
    from app.domain.services.species_service import SpeciesService

    repo = MagicMock()
    repo.get_or_raise.return_value = Species(_key="sp_1", scientific_name="Rosa canina", origin=DataOrigin.ENRICHMENT)
    repo.update.side_effect = lambda key, s: s
    service = SpeciesService(repo, MagicMock())

    # The edit form submits a species with the default 'system' origin; the
    # enriched marker must survive the full-replace update.
    incoming = Species(_key="sp_1", scientific_name="Rosa canina", origin=DataOrigin.SYSTEM)
    updated = service.update_species("sp_1", incoming)

    assert updated.origin is DataOrigin.ENRICHMENT


def test_update_species_preserves_tenant_key():
    # F-3/#808: tenant ownership is server-managed and the edit form never submits
    # it (SpeciesCreate has no tenant_key), so a full-replace update must keep the
    # existing owner rather than reset a tenant-owned species to the global "".
    from app.domain.services.species_service import SpeciesService

    repo = MagicMock()
    repo.get_or_raise.return_value = Species(_key="sp_1", scientific_name="Rosa canina", tenant_key="tenant_42")
    repo.update.side_effect = lambda key, s: s
    service = SpeciesService(repo, MagicMock())

    incoming = Species(_key="sp_1", scientific_name="Rosa canina")  # default tenant_key ""
    updated = service.update_species("sp_1", incoming)

    assert updated.tenant_key == "tenant_42"


def test_update_cultivar_preserves_origin():
    from app.domain.services.species_service import SpeciesService

    repo = MagicMock()
    repo.get_cultivar_or_raise.return_value = Cultivar(
        _key="c1", name="Nina", species_key="sp_1", origin=DataOrigin.TENANT
    )
    repo.update_cultivar.side_effect = lambda key, c: c
    service = SpeciesService(repo, MagicMock())

    incoming = Cultivar(_key="c1", name="Nina", species_key="sp_1", origin=DataOrigin.SYSTEM)
    updated = service.update_cultivar("c1", incoming)

    assert updated.origin is DataOrigin.TENANT


def test_update_cultivar_preserves_tenant_key():
    # #1090 (the Cultivar pendant of #808): tenant ownership is server-managed and the
    # edit form never submits it (CultivarCreate has no tenant_key), so a full-replace
    # update must keep the existing owner rather than reset a tenant-owned cultivar to
    # the global "" — which would move it out of its owner's catalogue into the shared
    # one every tenant reads.
    from app.domain.services.species_service import SpeciesService

    repo = MagicMock()
    repo.get_cultivar_or_raise.return_value = Cultivar(
        _key="c1", name="Nina", species_key="sp_1", tenant_key="tenant_42"
    )
    repo.update_cultivar.side_effect = lambda key, c: c
    service = SpeciesService(repo, MagicMock())

    incoming = Cultivar(_key="c1", name="Nina", species_key="sp_1")  # default tenant_key ""
    updated = service.update_cultivar("c1", incoming)

    assert updated.tenant_key == "tenant_42"
