"""#2936 — the IPM API serves and accepts the names of a disease per language.

``common_names_i18n`` travels through ``GET``/``POST``/``PUT /ipm/diseases``, the
treatment detail's disease refs and the pest detail's beneficials; an invalid language
key is a 422 at the schema boundary, and an update without the field keeps the map.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.ipm.router import router as ipm_router
from app.common.auth import get_current_user, get_is_platform_admin, require_platform_admin
from app.common.dependencies import get_ipm_service
from app.domain.models.beneficial import Beneficial
from app.domain.models.ipm import Disease, Pest, Treatment
from app.domain.services.ipm_service import IpmService

_MILDEW = {"en": ["Powdery Mildew"], "de": ["Echter Mehltau"]}


def _user() -> SimpleNamespace:
    return SimpleNamespace(key="user_1")


def _client(service: object) -> TestClient:
    app = FastAPI()
    app.include_router(ipm_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_ipm_service] = lambda: service
    app.dependency_overrides[require_platform_admin] = _user
    app.dependency_overrides[get_is_platform_admin] = lambda: True
    return TestClient(app)


def _mildew() -> Disease:
    return Disease(
        _key="d1",
        scientific_name="Erysiphe spp.",
        common_name="Powdery Mildew",
        pathogen_type="fungal",
        common_names_i18n=_MILDEW,
    )


def test_a_disease_is_served_with_its_names_per_language() -> None:
    service = MagicMock()
    service.get_disease.return_value = _mildew()

    body = _client(service).get("/api/v1/ipm/diseases/d1").json()

    assert body["common_name"] == "Powdery Mildew"
    assert body["common_names_i18n"] == _MILDEW


def test_a_created_disease_keeps_its_names_and_an_invalid_key_is_a_422() -> None:
    service = MagicMock()
    service.create_disease.side_effect = lambda d, *, is_platform_admin: d
    client = _client(service)
    payload = {"scientific_name": "Erysiphe spp.", "common_name": "Powdery Mildew", "pathogen_type": "fungal"}

    created = client.post("/api/v1/ipm/diseases", json={**payload, "common_names_i18n": {"de": [" Echter Mehltau "]}})
    refused = client.post("/api/v1/ipm/diseases", json={**payload, "common_names_i18n": {"DE": ["Echter Mehltau"]}})

    assert created.status_code == 201
    assert created.json()["common_names_i18n"] == {"de": ["Echter Mehltau"]}
    assert refused.status_code == 422


def test_an_update_without_the_field_keeps_the_map_and_an_empty_map_clears_it() -> None:
    repo = MagicMock()
    repo.get_disease_or_raise.side_effect = lambda key: _mildew()
    repo.update_disease.side_effect = lambda key, disease: disease
    client = _client(IpmService(repo, MagicMock(), MagicMock(), MagicMock()))

    kept = client.put("/api/v1/ipm/diseases/d1", json={"description": "white coating"})
    cleared = client.put("/api/v1/ipm/diseases/d1", json={"common_names_i18n": {}})
    refused = client.put("/api/v1/ipm/diseases/d1", json={"common_names_i18n": {"de": ["  "]}})

    assert kept.json()["common_names_i18n"] == _MILDEW
    assert cleared.json()["common_names_i18n"] == {}
    assert refused.status_code == 422


def test_treatment_detail_and_pest_detail_carry_the_names_per_language() -> None:
    service = MagicMock()
    service.get_treatment_detail.return_value = {
        "treatment": Treatment(_key="t1", name="Sulfur", treatment_type="chemical", safety_interval_days=3),
        "targeted_pests": [],
        "targeted_diseases": [_mildew()],
    }
    mites = {"de": ["Raubmilben"], "en": ["Predatory mites"]}
    service.get_pest_detail.return_value = {
        "pest": Pest(_key="p1", scientific_name="Tetranychus urticae", common_name="Spider Mites"),
        "treatments": [],
        "beneficials": [
            Beneficial(
                _key="b1",
                slug="predatory_mite",
                common_name="Raubmilben",
                common_names_i18n=mites,
                scientific_name="Phytoseiidae",
            )
        ],
        "detection_symptom_hint": None,
    }
    client = _client(service)

    treatment = client.get("/api/v1/ipm/treatments/t1/detail").json()
    pest = client.get("/api/v1/ipm/pests/p1/detail").json()

    assert treatment["targeted_diseases"][0]["common_names_i18n"] == _MILDEW
    assert pest["beneficials"][0]["common_names_i18n"] == mites
