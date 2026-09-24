"""REQ-020 / #1618 — API contract of ``GET /t/{slug}/favorites/nutrient-plans/matching``.

The filter itself is AQL and is measured against a real ArangoDB in
``tests/integration/test_nutrient_plan_species_matching.py``. What this module
pins is the router: that the comma-separated ``species_keys`` reach the service
as a list — bare keys and the ``species/<key>`` document-id spelling of REQ-020's
example alike — together with the caller's tenant, and that the response carries
the species relation and the matched species.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.favorites.tenant_router import router as favorites_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_favorites_service
from app.common.enums import TenantRole
from app.domain.models.tenant_context import TenantContext

TENANT_SLUG = "lisa"
TENANT_KEY = "tenant_lisa"
URL = f"/api/v1/t/{TENANT_SLUG}/favorites/nutrient-plans/matching"


def _ctx() -> TenantContext:
    return TenantContext(tenant_key=TENANT_KEY, tenant_slug=TENANT_SLUG, user_key="user_lisa", role=TenantRole.GROWER)


def _client(rows: list[dict]) -> tuple[TestClient, MagicMock]:
    service = MagicMock()
    service.get_matching_nutrient_plans.return_value = rows
    app = FastAPI()
    app.include_router(favorites_router, prefix="/api/v1/t/{tenant_slug}")
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_favorites_service] = lambda: service
    return TestClient(app), service


def test_keys_reach_the_service_as_a_list_with_the_callers_tenant() -> None:
    client, service = _client([])

    resp = client.get(URL, params={"species_keys": "solanum-lycopersicum, species/ocimum-basilicum,,"})

    assert resp.status_code == 200, resp.text
    service.get_matching_nutrient_plans.assert_called_once_with(
        ["solanum-lycopersicum", "ocimum-basilicum"], tenant_key=TENANT_KEY
    )


def test_the_response_carries_the_relation_and_the_matched_species() -> None:
    row = {
        "plan_key": "plan-tomato",
        "name": "Tomate — Plagron Terra + PK 13-14",
        "description": "",
        "substrate_type": "soil",
        "species_keys": ["solanum-lycopersicum"],
        "matched_species": ["solanum-lycopersicum"],
        "fertilizer_count": 0,
        "fertilizers": [],
    }
    client, _service = _client([row])

    resp = client.get(URL, params={"species_keys": "solanum-lycopersicum"})

    assert resp.status_code == 200, resp.text
    (body,) = resp.json()
    assert body["matched_species"] == ["solanum-lycopersicum"]
    assert body["species_keys"] == ["solanum-lycopersicum"]
    assert body["substrate_type"] == "soil"


def test_no_matching_plan_is_an_empty_list_not_an_error() -> None:
    client, _service = _client([])

    resp = client.get(URL, params={"species_keys": "daucus-carota"})

    assert resp.status_code == 200
    assert resp.json() == []


def test_the_species_keys_parameter_is_required() -> None:
    client, service = _client([])

    resp = client.get(URL)

    assert resp.status_code == 422
    service.get_matching_nutrient_plans.assert_not_called()
