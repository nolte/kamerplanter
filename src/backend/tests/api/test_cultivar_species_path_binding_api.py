"""The ``species_key`` path segment is load-bearing on the by-key routes (SEC-007, #1090).

End-to-end pendant of ``tests/unit/domain/services/test_cultivar_species_path_binding.py``:
the real :class:`SpeciesService` runs behind a fake repository, so these tests
prove the *route wiring* — that the router actually threads its ``species_key``
path parameter into the service — and not merely that the service would honour it
if asked.

Before the fix, ``/api/v1/species/{species_key}/cultivars/{cultivar_key}`` ignored
its first path segment entirely:

* GET and DELETE resolved (and deleted) a cultivar under any species key;
* PUT went further — the router builds ``Cultivar(species_key=species_key, …)``
  from the *path*, so a PUT under the wrong species silently re-parented the
  document while the ``has_cultivar`` edge, written once at create time, stayed on
  the old species.

Measured red-first on 2026-08-10 against the pre-fix code:
``test_get_under_a_wrong_species_is_404`` → 200,
``test_delete_under_a_wrong_species_is_404`` → 204 with the row gone,
``test_put_under_a_wrong_species_does_not_re_parent`` → 200 and the stored
``species_key`` had become ``sp_rose``.

Delimitation: the ownership/role matrix of these same routes is pinned in
``test_cultivar_authorization_api.py`` and is never restated here; this module
varies only the species segment.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.cultivars.router import router as cultivars_router
from app.common.auth import (
    get_active_tenant_context,
    get_active_tenant_key,
    get_current_user,
    get_is_platform_admin,
)
from app.common.dependencies import get_species_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.species import Cultivar, Species
from app.domain.models.tenant_context import TenantContext
from app.domain.services.species_service import SpeciesService


class _FakeRepo:
    def __init__(self) -> None:
        self._species = {
            "sp_basil": Species(_key="sp_basil", scientific_name="Ocimum basilicum", tenant_key=""),
            "sp_rose": Species(_key="sp_rose", scientific_name="Rosa canina", tenant_key=""),
        }
        self._cultivars = {
            "cv_own": Cultivar(_key="cv_own", name="Own Basil", species_key="sp_basil", tenant_key="t1"),
            "cv_global": Cultivar(_key="cv_global", name="Genovese", species_key="sp_basil", tenant_key=""),
        }
        self.updated: list[str] = []
        self.deleted: list[str] = []

    def get_or_raise(self, key: str) -> Species:
        species = self._species.get(key)
        if species is None:
            raise NotFoundError("Species", key)
        return species

    def get_cultivar_or_raise(self, key: str) -> Cultivar:
        cultivar = self._cultivars.get(key)
        if cultivar is None:
            raise NotFoundError("Cultivar", key)
        return cultivar

    def update_cultivar(self, key: str, cultivar: Cultivar) -> Cultivar:
        self.updated.append(key)
        stored = cultivar.model_copy(update={"key": key})
        self._cultivars[key] = stored
        return stored

    def delete_cultivar(self, key: str) -> bool:
        self.deleted.append(key)
        self._cultivars.pop(key, None)
        return True


def _client(repo: _FakeRepo) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(cultivars_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_species_service] = lambda: SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]
    app.dependency_overrides[get_active_tenant_key] = lambda: "t1"
    app.dependency_overrides[get_active_tenant_context] = lambda: TenantContext(
        tenant_key="t1", tenant_slug="own", user_key="user_1", role=TenantRole.LEAD
    )
    app.dependency_overrides[get_is_platform_admin] = lambda: False
    return TestClient(app)


@pytest.fixture
def repo() -> _FakeRepo:
    return _FakeRepo()


@pytest.fixture
def client(repo: _FakeRepo) -> TestClient:
    return _client(repo)


def _payload(species_key: str = "sp_rose") -> dict[str, str]:
    """A PUT body. ``species_key`` is required by the schema but excluded by the
    router, which builds the model from the *path* — so the value here is only ever
    the client's own claim, never the one that decides anything."""
    return {"name": "Edited name", "species_key": species_key}


# ── GET ──────────────────────────────────────────────────────────────────────


def test_get_under_a_wrong_species_is_404(client):
    assert client.get("/api/v1/species/sp_rose/cultivars/cv_own").status_code == 404


def test_get_under_the_owning_species_is_200(client):
    resp = client.get("/api/v1/species/sp_basil/cultivars/cv_own")

    assert resp.status_code == 200
    assert resp.json()["name"] == "Own Basil"


def test_a_wrong_species_and_an_unknown_cultivar_are_the_same_answer(client):
    wrong = client.get("/api/v1/species/sp_rose/cultivars/cv_own")
    absent = client.get("/api/v1/species/sp_rose/cultivars/cv_nope")

    assert wrong.status_code == absent.status_code == 404


def test_a_global_cultivar_under_a_wrong_species_is_404_not_403(client):
    # Check-order proof at the HTTP boundary: the mismatch is decided before the
    # global-catalogue arm, so a non-admin gets 404 ("no such resource") rather than
    # a 403 confirming cv_global exists and is global.
    assert client.get("/api/v1/species/sp_rose/cultivars/cv_global").status_code == 404
    assert client.put("/api/v1/species/sp_rose/cultivars/cv_global", json=_payload()).status_code == 404


# ── PUT ──────────────────────────────────────────────────────────────────────


def test_put_under_a_wrong_species_does_not_re_parent(client, repo):
    resp = client.put("/api/v1/species/sp_rose/cultivars/cv_own", json=_payload("sp_rose"))

    assert resp.status_code == 404
    assert repo.updated == [], "the mis-addressed PUT still reached the repository"
    stored = repo.get_cultivar_or_raise("cv_own")
    assert stored.species_key == "sp_basil", "the PUT re-parented the cultivar onto the URL's species"
    assert stored.name == "Own Basil", "the mis-addressed PUT overwrote the cultivar's fields"


def test_put_under_the_owning_species_is_unchanged(client, repo):
    resp = client.put("/api/v1/species/sp_basil/cultivars/cv_own", json=_payload("sp_basil"))

    assert resp.status_code == 200
    assert resp.json()["name"] == "Edited name"
    assert repo.get_cultivar_or_raise("cv_own").species_key == "sp_basil"


def test_a_body_claiming_another_species_cannot_re_parent_either(client, repo):
    # The router builds the model from the path and ignores the body's species_key;
    # the service then carries the *stored* parent over it. Two independent reasons
    # the payload cannot move a cultivar between species.
    resp = client.put("/api/v1/species/sp_basil/cultivars/cv_own", json=_payload("sp_rose"))

    assert resp.status_code == 200
    assert resp.json()["species_key"] == "sp_basil"
    assert repo.get_cultivar_or_raise("cv_own").species_key == "sp_basil"


# ── DELETE ───────────────────────────────────────────────────────────────────


def test_delete_under_a_wrong_species_is_404_and_keeps_the_row(client, repo):
    resp = client.delete("/api/v1/species/sp_rose/cultivars/cv_own")

    assert resp.status_code == 404
    assert repo.deleted == []
    assert repo.get_cultivar_or_raise("cv_own").name == "Own Basil"


def test_delete_under_the_owning_species_is_unchanged(client, repo):
    assert client.delete("/api/v1/species/sp_basil/cultivars/cv_own").status_code == 204
    assert repo.deleted == ["cv_own"]
