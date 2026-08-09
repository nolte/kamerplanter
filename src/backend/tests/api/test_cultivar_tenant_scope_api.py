"""The cultivar GET routes are tenant-aware — both directions end-to-end (C-3, #1090).

Proves the *route wiring*, not just the service: both cultivar reads
(``GET /api/v1/species/{species_key}/cultivars`` and ``…/{cultivar_key}``)
resolve the caller's active tenant with :func:`get_active_tenant_key` and thread
it into :class:`SpeciesService`. The fake service models the repository's
hybrid-catalogue union, so:

* the response carries the global cultivar catalogue plus the caller's own rows;
* a foreign tenant's cultivar is absent from the list and answers 404 by key —
  never 403, so the endpoint is no cross-tenant existence oracle;
* a foreign tenant's *species* answers 404 rather than an empty cultivar list
  (operator decision Q3).

Red-first: with the pre-C-3 route (``list_cultivars(species_key)`` /
``get_cultivar(cultivar_key)``) the fake receives ``tenant_key=None``, takes its
unscoped branch, and ``Foreign Basil`` appears in the response.

The HTTP route is unchanged by #1090 — only the router module moved (K2).
"""

from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.cultivars.router import router as cultivars_router
from app.common.auth import get_active_tenant_key, get_current_user
from app.common.dependencies import get_species_service
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.species import Cultivar, Species

_SPECIES = [
    Species(_key="sp_global", scientific_name="Ocimum basilicum", tenant_key=""),
    Species(_key="sp_foreign", scientific_name="Cannabis sativa", tenant_key="tenant_other"),
]

_CULTIVARS = [
    Cultivar(_key="cv_global", name="Genovese", species_key="sp_global", tenant_key=""),
    Cultivar(_key="cv_own", name="Own Basil", species_key="sp_global", tenant_key="tenant_self"),
    Cultivar(_key="cv_foreign", name="Foreign Basil", species_key="sp_global", tenant_key="tenant_other"),
]


class _FakeUnionService:
    """Models SpeciesService's cultivar reads over the hybrid-catalogue union."""

    def _species(self, species_key: str, tenant_key: str | None) -> Species:
        for species in _SPECIES:
            if species.key == species_key:
                if tenant_key is not None and species.tenant_key not in (tenant_key, ""):
                    raise NotFoundError("Species", species_key)
                return species
        raise NotFoundError("Species", species_key)

    def list_cultivars(self, species_key: str, *, tenant_key: str | None = None) -> list[Cultivar]:
        self._species(species_key, tenant_key)
        rows = [c for c in _CULTIVARS if c.species_key == species_key]
        if tenant_key is None:
            return rows
        return [c for c in rows if c.tenant_key in (tenant_key, "", None)]

    def get_cultivar(self, key: str, *, tenant_key: str | None = None) -> Cultivar:
        for cultivar in _CULTIVARS:
            if cultivar.key == key:
                if tenant_key is not None and cultivar.tenant_key not in (tenant_key, ""):
                    raise NotFoundError("Cultivar", key)
                return cultivar
        raise NotFoundError("Cultivar", key)


def _app(*, active_tenant_key: str) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(cultivars_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_species_service] = _FakeUnionService
    app.dependency_overrides[get_active_tenant_key] = lambda: active_tenant_key
    return app


def _names(payload) -> set[str]:
    return {item["name"] for item in payload}


# ── List route ───────────────────────────────────────────────────────────────


def test_list_includes_global_and_own_and_excludes_foreign():
    client = TestClient(_app(active_tenant_key="tenant_self"))

    resp = client.get("/api/v1/species/sp_global/cultivars")

    assert resp.status_code == 200
    assert _names(resp.json()) == {"Genovese", "Own Basil"}
    assert "Foreign Basil" not in _names(resp.json())


def test_list_isolates_the_other_direction():
    client = TestClient(_app(active_tenant_key="tenant_other"))

    body = client.get("/api/v1/species/sp_global/cultivars").json()

    assert _names(body) == {"Genovese", "Foreign Basil"}
    assert "Own Basil" not in _names(body)


def test_anonymous_caller_lists_exactly_the_global_catalogue():
    # "" is the resolved key for an anonymous / light-mode caller (REQ-027): global
    # only, never an error, never every tenant's rows.
    client = TestClient(_app(active_tenant_key=""))

    resp = client.get("/api/v1/species/sp_global/cultivars")

    assert resp.status_code == 200
    assert _names(resp.json()) == {"Genovese"}


def test_listing_cultivars_of_a_foreign_species_is_404_not_an_empty_list():
    # Operator decision Q3: an empty 200 would confirm the species key exists.
    client = TestClient(_app(active_tenant_key="tenant_self"))

    resp = client.get("/api/v1/species/sp_foreign/cultivars")

    assert resp.status_code == 404


# ── By-key route ─────────────────────────────────────────────────────────────


def test_get_resolves_a_global_cultivar_for_every_tenant():
    client = TestClient(_app(active_tenant_key="tenant_self"))

    resp = client.get("/api/v1/species/sp_global/cultivars/cv_global")

    assert resp.status_code == 200
    assert resp.json()["name"] == "Genovese"


def test_get_resolves_the_callers_own_cultivar():
    client = TestClient(_app(active_tenant_key="tenant_self"))

    resp = client.get("/api/v1/species/sp_global/cultivars/cv_own")

    assert resp.status_code == 200
    assert resp.json()["name"] == "Own Basil"


def test_get_of_a_foreign_cultivar_is_404_never_403():
    client = TestClient(_app(active_tenant_key="tenant_self"))

    resp = client.get("/api/v1/species/sp_global/cultivars/cv_foreign")

    assert resp.status_code == 404


def test_a_foreign_cultivar_is_indistinguishable_from_an_absent_one():
    # No existence oracle: identical status for "not yours" and "not there".
    client = TestClient(_app(active_tenant_key="tenant_self"))

    foreign = client.get("/api/v1/species/sp_global/cultivars/cv_foreign")
    absent = client.get("/api/v1/species/sp_global/cultivars/cv_missing")

    assert foreign.status_code == absent.status_code == 404


def test_anonymous_caller_cannot_read_a_tenant_owned_cultivar_by_key():
    client = TestClient(_app(active_tenant_key=""))

    assert client.get("/api/v1/species/sp_global/cultivars/cv_own").status_code == 404
    assert client.get("/api/v1/species/sp_global/cultivars/cv_global").status_code == 200
