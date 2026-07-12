"""REQ-036 §3 / §1.3 — API tests for the KI diagnosis endpoints.

Builds a minimal app mounting the tenant diagnosis router with dependency
overrides and asserts the shared three-stage KI toggle (404 → 403 → 403 → 200)
plus the symptom catalogue and analyse happy path.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.diagnose.tenant_router import router as diagnosis_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_diagnose_service, get_tenant_repo
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import ConsentRequiredError, KamerplanterError
from app.config.settings import settings
from app.domain.interfaces.knowledge_service import ConfidenceLevel
from app.domain.models.diagnosis import DiagnosisCandidate, DiagnosisResult
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_context import TenantContext


def _ctx() -> TenantContext:
    return TenantContext(tenant_key="home", tenant_slug="home", user_key="anna", role=TenantRole.GROWER)


def _tenant(ai_enabled: bool) -> Tenant:
    return Tenant(
        _key="home",
        name="Home",
        slug="home",
        owner_user_key="anna",
        settings={"ai_features_enabled": ai_enabled},
    )


def _build_app(*, tenant_ai_enabled: bool = True, service: MagicMock | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(diagnosis_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]

    tenant_repo = MagicMock()
    tenant_repo.get_by_key.return_value = _tenant(tenant_ai_enabled)

    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_tenant_repo] = lambda: tenant_repo
    if service is not None:
        app.dependency_overrides[get_diagnose_service] = lambda: service
    return app


@pytest.fixture(autouse=True)
def _enable_flag(monkeypatch):
    monkeypatch.setattr(settings, "ai_features_enabled", True)
    yield


def _ok_result() -> DiagnosisResult:
    return DiagnosisResult(
        candidates=[
            DiagnosisCandidate(
                rank=1,
                name="Spider mites",
                scientific_name="Tetranychus urticae",
                category="pest_visible",
                confidence=0.85,
                confidence_level=ConfidenceLevel.HIGH,
                explanation="Webbing present.",
                recommended_actions=["Increase humidity"],
                matched_pest_key="pest-1",
                matched_pest_detail_url="/pflanzenschutz/pests/pest-1",
            )
        ],
        answer_summary="Webbing present.",
        uses_tenant_data=True,
        confidence=ConfidenceLevel.HIGH,
        model_name="gemma3:12b",
        status="ok",
    )


def test_stage1_flag_off_returns_404(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_features_enabled", False)
    client = TestClient(_build_app())

    resp = client.get("/api/v1/diagnosis/symptoms")
    assert resp.status_code == 404


def test_stage2_tenant_disabled_returns_403_marker() -> None:
    client = TestClient(_build_app(tenant_ai_enabled=False))

    resp = client.get("/api/v1/diagnosis/symptoms")
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "AI_DISABLED_FOR_TENANT"


def test_symptoms_endpoint_returns_catalog() -> None:
    from app.domain.services.diagnose_service import DiagnoseService

    service = MagicMock(spec=DiagnoseService)
    service.list_symptoms.return_value = SymptomCatalogFixture.entries()
    client = TestClient(_build_app(service=service))

    resp = client.get("/api/v1/diagnosis/symptoms", params={"language": "en"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["symptoms"]) == 1
    assert body["symptoms"][0]["label"] == "Yellowing of lower leaves"


def test_analyze_happy_path_returns_top_candidates() -> None:
    service = MagicMock()
    service.diagnose = AsyncMock(return_value=_ok_result())
    client = TestClient(_build_app(service=service))

    resp = client.post(
        "/api/v1/diagnosis/analyze",
        json={"symptom_slugs": ["webbing_on_leaves"], "language": "de"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["candidates"][0]["matched_pest_detail_url"] == "/pflanzenschutz/pests/pest-1"
    assert body["uses_tenant_data"] is True


def test_analyze_missing_consent_returns_403() -> None:
    service = MagicMock()
    service.diagnose = AsyncMock(side_effect=ConsentRequiredError("ai_tenant_data_access"))
    client = TestClient(_build_app(service=service))

    resp = client.post(
        "/api/v1/diagnosis/analyze",
        json={"symptom_slugs": ["leaf_spots"]},
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"


def test_analyze_rejects_empty_symptom_list() -> None:
    service = MagicMock()
    service.diagnose = AsyncMock(return_value=_ok_result())
    client = TestClient(_build_app(service=service))

    resp = client.post("/api/v1/diagnosis/analyze", json={"symptom_slugs": []})
    assert resp.status_code == 422


class SymptomCatalogFixture:
    """Small fixture returning a single catalogue entry for the symptoms test."""

    @staticmethod
    def entries():
        from app.domain.models.diagnosis import SymptomCatalogEntry, SymptomCategory

        return [
            SymptomCatalogEntry(
                slug="leaves_yellowing_lower",
                category=SymptomCategory.LEAF_COLOR_CHANGE,
                label_de="Vergilbung der unteren Blaetter",
                label_en="Yellowing of lower leaves",
                applicable_phases=["vegetative"],
                common_causes_hint_de="Stickstoffmangel.",
                common_causes_hint_en="Nitrogen deficiency.",
            )
        ]
