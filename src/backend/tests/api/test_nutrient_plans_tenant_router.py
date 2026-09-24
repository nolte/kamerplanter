"""REQ-004 — API tests for creating a tenant-scoped nutrient plan (#966).

``POST /t/{slug}/nutrient-plans`` answered 500 for every request the UI sent,
because the request schema declared ``reference_substrate_type`` as optional
while the domain model declares it non-nullable with a ``soil`` default. The
splat ``NutrientPlan(**body.model_dump())`` always emits the key, so an omitted
field arrived as an explicit ``None`` — and an explicit ``None`` *disables* a
Pydantic default, which only applies to a **missing** key.

These tests pin the boundary contract of the create endpoint: omission falls
back to the domain default, a bad value is rejected by the API layer with 422,
and neither path may produce a 500.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.nutrient_plans.tenant_router import router as nutrient_plans_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_nutrient_plan_service
from app.common.enums import SubstrateType, TenantRole
from app.common.error_handlers import (
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.common.exceptions import KamerplanterError
from app.domain.models.nutrient_plan import NutrientPlan
from app.domain.models.tenant_context import TenantContext

TENANT_SLUG = "lisa"
TENANT_KEY = "tenant_lisa"

# The payload the create dialog actually sends (NutrientPlanCreateDialog.onSubmit):
# no ``reference_substrate_type`` — that field only exists in the edit tab.
_UI_CREATE_PAYLOAD = {
    "name": "Tomaten Freiland 2026",
    "description": "Organische Basisdüngung",
    "recommended_substrate_type": None,
    "author": "Lisa",
    "is_template": False,
    "tags": ["outdoor"],
}


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user_lisa",
        role=TenantRole.LEAD,
    )


def _build() -> tuple[TestClient, MagicMock]:
    stored = NutrientPlan(_key="plan_1", name="Bestandsplan", tenant_key=TENANT_KEY)
    service = MagicMock()
    service.create_plan.side_effect = lambda plan: plan.model_copy(update={"key": "plan_1"})
    service.get_plan.return_value = stored
    service.update_plan.side_effect = lambda key, data: stored.model_copy(update=data)

    app = FastAPI()
    app.include_router(nutrient_plans_router, prefix="/api/v1/t/{tenant_slug}")
    # Mirror the production handler wiring so an unhandled error shows up as the
    # 500 the client sees, instead of surfacing as a test-time exception.
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_nutrient_plan_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False), service


def _created_plan(service: MagicMock) -> NutrientPlan:
    return service.create_plan.call_args.args[0]


_URL = f"/api/v1/t/{TENANT_SLUG}/nutrient-plans"


class TestCreatePlanSubstrateDefaults:
    def test_omitted_reference_substrate_type_defaults_to_soil(self):
        """The UI payload omits the field entirely — this is TC-004-015 ('Minimal')."""
        client, service = _build()

        resp = client.post(_URL, json=_UI_CREATE_PAYLOAD)

        assert resp.status_code == 201, resp.text
        assert resp.json()["reference_substrate_type"] == "soil"
        assert _created_plan(service).reference_substrate_type is SubstrateType.SOIL

    def test_bare_minimal_payload_defaults_to_soil(self):
        """Only ``name`` is required; every other default must still hold."""
        client, service = _build()

        resp = client.post(_URL, json={"name": "Minimal"})

        assert resp.status_code == 201, resp.text
        plan = _created_plan(service)
        assert plan.reference_substrate_type is SubstrateType.SOIL
        assert plan.recommended_substrate_type is None
        assert plan.tenant_key == TENANT_KEY
        assert plan.version == "1.0"
        assert plan.tags == []

    def test_explicit_reference_substrate_type_is_honoured(self):
        client, service = _build()

        resp = client.post(_URL, json={**_UI_CREATE_PAYLOAD, "reference_substrate_type": "coco"})

        assert resp.status_code == 201, resp.text
        assert resp.json()["reference_substrate_type"] == "coco"
        assert _created_plan(service).reference_substrate_type is SubstrateType.COCO

    def test_invalid_reference_substrate_type_is_rejected_with_422(self):
        client, service = _build()

        resp = client.post(_URL, json={**_UI_CREATE_PAYLOAD, "reference_substrate_type": "gravel"})

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        service.create_plan.assert_not_called()

    def test_explicit_null_reference_substrate_type_is_rejected_with_422(self):
        """``null`` is not a substrate type: omit the field to get the default."""
        client, service = _build()

        resp = client.post(_URL, json={**_UI_CREATE_PAYLOAD, "reference_substrate_type": None})

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        service.create_plan.assert_not_called()

    def test_invalid_recommended_substrate_type_is_rejected_with_422(self):
        """The nullable sibling field validates at the boundary too, never as a 500."""
        client, service = _build()

        resp = client.post(_URL, json={**_UI_CREATE_PAYLOAD, "recommended_substrate_type": "gravel"})

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        service.create_plan.assert_not_called()


class TestUpdatePlanSubstrateValidation:
    """The update path never 500'd — it did something worse: it accepted anything.

    ``update_plan`` assigns the request values onto the loaded domain model, and
    Pydantic does not validate on assignment. A bogus substrate string was therefore
    persisted and poisoned every later read of the plan. The enum-typed request
    schema rejects it at the boundary instead.
    """

    def test_invalid_reference_substrate_type_is_rejected_with_422(self):
        client, service = _build()

        resp = client.put(f"{_URL}/plan_1", json={"reference_substrate_type": "gravel"})

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        service.update_plan.assert_not_called()

    def test_valid_reference_substrate_type_is_forwarded(self):
        client, service = _build()

        resp = client.put(f"{_URL}/plan_1", json={"reference_substrate_type": "coco"})

        assert resp.status_code == 200, resp.text
        assert service.update_plan.call_args.args[1]["reference_substrate_type"] is SubstrateType.COCO

    def test_omitted_fields_stay_out_of_the_update(self):
        client, service = _build()

        resp = client.put(f"{_URL}/plan_1", json={"name": "Neuer Name"})

        assert resp.status_code == 200, resp.text
        assert service.update_plan.call_args.args[1] == {"name": "Neuer Name"}


# ── #1618: the species relation on create / update ──────────────────────────


VISIBLE_SPECIES = {"solanum-lycopersicum", "ocimum-basilicum"}


def _build_with_real_service(stored: NutrientPlan | None = None) -> tuple[TestClient, MagicMock, MagicMock]:
    """The real :class:`NutrientPlanService` over doubles, so its species check runs.

    The species double answers ``list_visible_keys`` with a fixed set — the one
    method the service calls — and records the tenant it was asked about, so a
    test can pin that the check asks about the *plan's* tenant.
    """
    from app.domain.services.nutrient_plan_service import NutrientPlanService

    stored = stored or NutrientPlan(_key="plan_1", name="Bestandsplan", tenant_key=TENANT_KEY)
    repo = MagicMock()
    repo.create.side_effect = lambda plan: plan.model_copy(update={"key": "plan_1"})
    repo.get_or_raise.return_value = stored
    repo.update.side_effect = lambda key, plan: plan
    species_repo = MagicMock()
    species_repo.list_visible_keys.return_value = set(VISIBLE_SPECIES)
    service = NutrientPlanService(repo, MagicMock(), MagicMock(), species_repo=species_repo)

    app = FastAPI()
    app.include_router(nutrient_plans_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_nutrient_plan_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False), repo, species_repo


class TestPlanSpeciesRelation:
    def test_create_links_the_given_species_and_returns_them(self):
        client, repo, species_repo = _build_with_real_service()

        resp = client.post(_URL, json={"name": "Tomate", "species_keys": ["solanum-lycopersicum"]})

        assert resp.status_code == 201, resp.text
        assert resp.json()["species_keys"] == ["solanum-lycopersicum"]
        assert repo.create.call_args.args[0].species_keys == ["solanum-lycopersicum"]
        species_repo.list_visible_keys.assert_called_once_with(tenant_key=TENANT_KEY)

    def test_create_without_species_stores_an_empty_relation(self):
        client, repo, species_repo = _build_with_real_service()

        resp = client.post(_URL, json={"name": "Ohne Art"})

        assert resp.status_code == 201, resp.text
        assert resp.json()["species_keys"] == []
        assert repo.create.call_args.args[0].species_keys == []
        species_repo.list_visible_keys.assert_not_called()

    def test_create_with_a_species_the_tenant_cannot_see_is_422(self):
        """Unknown and foreign-private keys look alike on purpose: no existence oracle."""
        client, repo, _species_repo = _build_with_real_service()

        resp = client.post(_URL, json={"name": "Fremd", "species_keys": ["solanum-lycopersicum", "foreign-private"]})

        assert resp.status_code == 422, resp.text
        body = resp.json()
        assert body["error_code"] == "VALIDATION_ERROR"
        assert "foreign-private" in str(body["details"])
        assert "solanum-lycopersicum" not in str(body["details"])
        repo.create.assert_not_called()

    def test_duplicate_and_blank_keys_are_normalised_on_create(self):
        client, repo, _species_repo = _build_with_real_service()

        resp = client.post(
            _URL,
            json={"name": "Doppelt", "species_keys": [" ocimum-basilicum", "ocimum-basilicum", ""]},
        )

        assert resp.status_code == 201, resp.text
        assert repo.create.call_args.args[0].species_keys == ["ocimum-basilicum"]

    def test_update_replaces_the_relation(self):
        client, repo, _species_repo = _build_with_real_service()

        resp = client.put(f"{_URL}/plan_1", json={"species_keys": ["ocimum-basilicum", "ocimum-basilicum "]})

        assert resp.status_code == 200, resp.text
        assert resp.json()["species_keys"] == ["ocimum-basilicum"]
        assert repo.update.call_args.args[1].species_keys == ["ocimum-basilicum"]

    def test_update_with_an_empty_list_clears_the_relation(self):
        stored = NutrientPlan(
            _key="plan_1", name="Bestandsplan", tenant_key=TENANT_KEY, species_keys=["solanum-lycopersicum"]
        )
        client, repo, _species_repo = _build_with_real_service(stored)

        resp = client.put(f"{_URL}/plan_1", json={"species_keys": []})

        assert resp.status_code == 200, resp.text
        assert repo.update.call_args.args[1].species_keys == []

    def test_update_without_the_field_leaves_the_relation_alone(self):
        stored = NutrientPlan(
            _key="plan_1", name="Bestandsplan", tenant_key=TENANT_KEY, species_keys=["solanum-lycopersicum"]
        )
        client, repo, species_repo = _build_with_real_service(stored)

        resp = client.put(f"{_URL}/plan_1", json={"name": "Neu"})

        assert resp.status_code == 200, resp.text
        assert repo.update.call_args.args[1].species_keys == ["solanum-lycopersicum"]
        species_repo.list_visible_keys.assert_not_called()

    def test_update_with_a_species_the_tenant_cannot_see_is_422(self):
        client, repo, _species_repo = _build_with_real_service()

        resp = client.put(f"{_URL}/plan_1", json={"species_keys": ["foreign-private"]})

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        repo.update.assert_not_called()


def test_the_production_factory_wires_the_species_repository(monkeypatch):
    """Without it every create/update that names a species would raise (#1618)."""
    from app.common import dependencies

    sentinel = MagicMock()
    for name in ("get_nutrient_plan_repo", "get_fertilizer_repo", "get_site_repo"):
        monkeypatch.setattr(dependencies, name, MagicMock)
    monkeypatch.setattr(dependencies, "get_species_repo", lambda: sentinel)

    service = dependencies.get_nutrient_plan_service()

    assert service._species_repo is sentinel
