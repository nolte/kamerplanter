"""GET /api/v1/species is tenant-aware — both directions end-to-end (F-5, #808).

Proves the route wiring, not just the repository: the global species list route
resolves the caller's active tenant with :func:`get_active_tenant_key` and threads
it into ``SpeciesService.list_species``. The fake service models the repository's
hybrid-catalogue union, so:

* acceptance-1 — the response carries the global seed catalogue plus the caller's
  own-tenant species;
* acceptance-2 (verifies_sprint_value) — a foreign tenant's species is absent.

Red-first: had the route kept the pre-F-5 ``list_species(offset, limit)`` call,
the fake would receive ``tenant_key=None`` (its unscoped whole-catalogue branch)
and ``Cannabis sativa`` — the foreign row — would appear in the response.
"""

from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.species.router import router as species_router
from app.common.auth import get_active_tenant_key, get_current_user
from app.common.dependencies import get_family_repo, get_species_service
from app.domain.models.species import Species


def _user() -> SimpleNamespace:
    return SimpleNamespace(key="user_1")


class _FakeUnionService:
    """Models SpeciesService.list_species over a hybrid-catalogue union."""

    _CATALOGUE = [
        Species(_key="global_seed", scientific_name="Rosa canina", tenant_key=""),
        Species(_key="own", scientific_name="Ocimum basilicum", tenant_key="tenant_self"),
        Species(_key="foreign", scientific_name="Cannabis sativa", tenant_key="tenant_other"),
    ]

    def list_species(self, offset: int = 0, limit: int = 50, *, tenant_key: str | None = None):
        if tenant_key is None:
            rows = list(self._CATALOGUE)
        else:
            rows = [s for s in self._CATALOGUE if s.tenant_key in (tenant_key, "", None)]
        return rows[offset : offset + limit], len(rows)


def _species_app(*, active_tenant_key: str) -> FastAPI:
    app = FastAPI()
    app.include_router(species_router, prefix="/api/v1")
    family_repo = SimpleNamespace(get_by_key=lambda _key: None)
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_species_service] = _FakeUnionService
    app.dependency_overrides[get_family_repo] = lambda: family_repo
    app.dependency_overrides[get_active_tenant_key] = lambda: active_tenant_key
    return app


def _names(payload) -> set[str]:
    return {item["scientific_name"] for item in payload["items"]}


def test_own_tenant_list_includes_global_and_own_excludes_foreign():
    client = TestClient(_species_app(active_tenant_key="tenant_self"))

    resp = client.get("/api/v1/species")

    assert resp.status_code == 200
    body = resp.json()
    # acceptance-1: global seed + own species present.
    assert _names(body) == {"Rosa canina", "Ocimum basilicum"}
    # acceptance-2: the foreign tenant's species does not leak.
    assert "Cannabis sativa" not in _names(body)
    assert body["total"] == 2


def test_other_tenant_list_isolates_the_other_direction():
    client = TestClient(_species_app(active_tenant_key="tenant_other"))

    body = client.get("/api/v1/species").json()

    assert _names(body) == {"Rosa canina", "Cannabis sativa"}
    assert "Ocimum basilicum" not in _names(body)


def test_anonymous_caller_sees_only_the_global_catalogue():
    client = TestClient(_species_app(active_tenant_key=""))

    body = client.get("/api/v1/species").json()

    assert _names(body) == {"Rosa canina"}
    assert body["total"] == 1
