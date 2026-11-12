"""``common_names_i18n`` through the species HTTP boundary (REQ-001, #2902).

* create/update with a language map naming only listed names → stored and echoed;
* a name outside ``common_names`` or a bad language key → 422 (a request error, not
  a bare pydantic error inside the handler that would surface as 500);
* an edit body WITHOUT the field keeps the stored map (an edit form predating the
  field must not wipe it), minus any name the edit removed from ``common_names``;
* an edit body with ``{}`` clears it deliberately.

The real :class:`SpeciesService` runs behind an in-memory repository so the keep/prune
decision in the service is exercised, not mocked.
"""

from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.species.router import router as species_router
from app.api.v1.species.schemas import SpeciesCreate
from app.common.auth import (
    get_active_tenant_context,
    get_active_tenant_key,
    get_creating_tenant_key,
    get_current_user,
    get_is_platform_admin,
)
from app.common.dependencies import get_family_repo, get_species_service
from app.common.enums import FrostTolerance, PlantCategory, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.species import GrowingPeriod, Species
from app.domain.models.tenant_context import TenantContext
from app.domain.services.species_service import SpeciesService
from tests.support.grant_fakes import NoGrantsMixin

_TENANT = "t1"


class _Repo(NoGrantsMixin):
    def __init__(self, species: list[Species]) -> None:
        self.by_key: dict[str, Species] = {s.key or "": s for s in species}
        self.created: list[Species] = []

    def get_or_raise(self, key: str) -> Species:
        found = self.by_key.get(key)
        if found is None:
            raise NotFoundError("Species", key)
        return found

    def get_by_normalized_scientific_name(self, name: str) -> Species | None:
        return None

    def get_by_normalized_scientific_name_for_tenant(self, name: str, tenant_key: str) -> Species | None:
        return None

    def find_synonym_match_candidates(self, species: Species, *, tenant_key: str) -> list[Species]:
        return []

    def upsert_by_normalized_scientific_name(self, species: Species) -> Species:
        species.key = "sp_new"
        self.created.append(species)
        self.by_key["sp_new"] = species
        return species

    def update(self, key: str, species: Species) -> Species:
        species.key = key
        self.by_key[key] = species
        return species


def _own_carrot() -> Species:
    return Species(
        _key="own",
        scientific_name="Daucus carota",
        common_names=["Carrot", "Karotte", "Möhre"],
        common_names_i18n={"de": ["Möhre", "Karotte"], "en": ["Carrot"]},
        tenant_key=_TENANT,
    )


def _client(repo: _Repo) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(species_router, prefix="/api/v1")
    service = SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[get_family_repo] = lambda: SimpleNamespace(get_by_key=lambda _key: None)
    app.dependency_overrides[get_active_tenant_key] = lambda: _TENANT
    app.dependency_overrides[get_creating_tenant_key] = lambda: _TENANT
    app.dependency_overrides[get_active_tenant_context] = lambda: TenantContext(
        tenant_key=_TENANT, tenant_slug="t", user_key="user_1", role=TenantRole.GROWER
    )
    app.dependency_overrides[get_is_platform_admin] = lambda: False
    return TestClient(app)


class TestCreate:
    def test_a_language_map_is_stored_and_echoed(self) -> None:
        repo = _Repo([])
        resp = _client(repo).post(
            "/api/v1/species",
            json={
                "scientific_name": "Pisum sativum",
                "common_names": ["Pea", "Erbse"],
                "common_names_i18n": {"de": ["Erbse"], "en": ["Pea"]},
            },
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["common_names_i18n"] == {"de": ["Erbse"], "en": ["Pea"]}
        assert repo.created[0].common_names_i18n == {"de": ["Erbse"], "en": ["Pea"]}

    def test_a_create_without_the_map_stores_none(self) -> None:
        repo = _Repo([])
        resp = _client(repo).post("/api/v1/species", json={"scientific_name": "Pisum sativum", "common_names": ["Pea"]})

        assert resp.status_code == 201, resp.text
        assert resp.json()["common_names_i18n"] == {}

    def test_a_name_outside_common_names_is_a_422_and_writes_nothing(self) -> None:
        repo = _Repo([])
        resp = _client(repo).post(
            "/api/v1/species",
            json={"scientific_name": "Pisum sativum", "common_names": ["Pea"], "common_names_i18n": {"de": ["Erbse"]}},
        )

        assert resp.status_code == 422, resp.text
        assert repo.created == []

    def test_an_uppercase_language_key_is_a_422(self) -> None:
        repo = _Repo([])
        resp = _client(repo).post(
            "/api/v1/species",
            json={
                "scientific_name": "Pisum sativum",
                "common_names": ["Erbse"],
                "common_names_i18n": {"DE": ["Erbse"]},
            },
        )

        assert resp.status_code == 422, resp.text
        assert repo.created == []


class TestUpdate:
    def test_an_edit_without_the_map_keeps_the_stored_one(self) -> None:
        repo = _Repo([_own_carrot()])
        resp = _client(repo).put(
            "/api/v1/species/own",
            json={"scientific_name": "Daucus carota", "common_names": ["Carrot", "Karotte", "Möhre"]},
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["common_names_i18n"] == {"de": ["Möhre", "Karotte"], "en": ["Carrot"]}

    def test_an_edit_without_the_map_drops_a_removed_name_from_it(self) -> None:
        repo = _Repo([_own_carrot()])
        resp = _client(repo).put(
            "/api/v1/species/own",
            json={"scientific_name": "Daucus carota", "common_names": ["Möhre"]},
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["common_names_i18n"] == {"de": ["Möhre"]}
        assert repo.by_key["own"].common_names_i18n == {"de": ["Möhre"]}

    def test_an_edit_with_an_empty_map_clears_it(self) -> None:
        repo = _Repo([_own_carrot()])
        resp = _client(repo).put(
            "/api/v1/species/own",
            json={"scientific_name": "Daucus carota", "common_names": ["Möhre"], "common_names_i18n": {}},
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["common_names_i18n"] == {}

    def test_an_edit_with_a_map_naming_an_unlisted_name_is_a_422(self) -> None:
        repo = _Repo([_own_carrot()])
        resp = _client(repo).put(
            "/api/v1/species/own",
            json={
                "scientific_name": "Daucus carota",
                "common_names": ["Möhre"],
                "common_names_i18n": {"de": ["Möhre", "Karotte"]},
            },
        )

        assert resp.status_code == 422, resp.text
        assert repo.by_key["own"].common_names == ["Carrot", "Karotte", "Möhre"]


def test_a_read_returns_the_map() -> None:
    resp = _client(_Repo([_own_carrot()])).get("/api/v1/species/own")

    assert resp.status_code == 200, resp.text
    assert resp.json()["common_names_i18n"] == {"de": ["Möhre", "Karotte"], "en": ["Carrot"]}


def test_a_full_round_trip_without_the_map_keeps_every_field() -> None:
    """The client contract of the edit form and the growing-periods tab (#2902).

    ``PUT`` replaces the species, so the frontend sends every ``SpeciesCreate`` field it
    loaded (``speciesToUpdatePayload``) and leaves the language map out. Sending back
    what ``GET`` returned, minus the map, must therefore change nothing — not the names,
    not the map, not any other field.
    """
    stored = _own_carrot()
    stored.family_key = "fam_api"
    stored.genus = "Daucus"
    stored.description = "Wurzelgemüse"
    stored.synonyms = ["Daucus sativus"]
    stored.plant_category = PlantCategory.OUTDOOR_VEGETABLE
    stored.frost_sensitivity = FrostTolerance.HARDY
    stored.support_required = True
    stored.growing_periods = [GrowingPeriod(label="Frühjahr", direct_sow_months=[3, 4], harvest_months=[7])]
    before = stored.model_dump()
    repo = _Repo([stored])
    client = _client(repo)

    loaded = client.get("/api/v1/species/own").json()
    body = {field: loaded[field] for field in SpeciesCreate.model_fields if field != "common_names_i18n"}
    resp = client.put("/api/v1/species/own", json=body)

    assert resp.status_code == 200, resp.text
    after = repo.by_key["own"].model_dump()
    for field in [*SpeciesCreate.model_fields, "common_names_i18n"]:
        assert after[field] == before[field], field
