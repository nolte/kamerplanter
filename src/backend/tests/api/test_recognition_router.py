"""API tests for the REQ-029 recognition routers (status + tenant-scoped)."""

from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.recognition.router import router as recognition_router
from app.api.v1.recognition.tenant_router import router as tenant_recognition_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_identification_service, get_reference_image_service
from app.common.enums import TenantRole
from app.common.exceptions import ConsentRequiredError, KamerplanterError
from app.config.settings import settings
from app.domain.models.tenant_context import TenantContext

TENANT_SLUG = "anna"


def _tenant_ctx() -> TenantContext:
    return TenantContext(
        tenant_key="tenant_anna",
        tenant_slug=TENANT_SLUG,
        user_key="user_anna",
        role=TenantRole.ADMIN,
    )


def _app_error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _build_app(service, reference_service=None):
    app = FastAPI()
    app.include_router(recognition_router, prefix="/api/v1")
    app.include_router(tenant_recognition_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _app_error_handler)
    app.dependency_overrides[get_identification_service] = lambda: service
    app.dependency_overrides[get_current_tenant] = _tenant_ctx
    if reference_service is not None:
        app.dependency_overrides[get_reference_image_service] = lambda: reference_service
    return app


def _jpeg_upload():
    return {"image": ("plant.jpg", b"\xff\xd8\xff\xe0fake-jpeg-bytes", "image/jpeg")}


def test_status_is_public():
    service = MagicMock()
    service.get_status.return_value = {
        "available": True,
        "primary_adapter": "plantnet",
        "active_adapter": "plantnet",
        "supports_health": False,
        "adapters": {"plantnet": {"configured": True, "supports_health": False, "rate_limit_per_day": 500}},
    }
    client = TestClient(_build_app(service))

    resp = client.get("/api/v1/recognition/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert body["primary_adapter"] == "plantnet"


def test_status_unavailable():
    service = MagicMock()
    service.get_status.return_value = {
        "available": False,
        "primary_adapter": "plantnet",
        "active_adapter": None,
        "supports_health": False,
        "adapters": {},
    }
    client = TestClient(_build_app(service))

    resp = client.get("/api/v1/recognition/status")
    assert resp.status_code == 200
    assert resp.json()["available"] is False


def test_identify_rejects_non_image_content_type():
    service = MagicMock()
    client = TestClient(_build_app(service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/identify",
        files={"image": ("doc.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 415
    service.identify_plant.assert_not_called()


def test_identify_consent_gate_returns_403():
    service = MagicMock()
    service.identify_plant.side_effect = ConsentRequiredError("plant_identification")
    client = TestClient(_build_app(service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/identify",
        files=_jpeg_upload(),
        data={"organ": "leaf"},
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"


def test_identify_success_returns_suggestions():
    service = MagicMock()
    service.identify_plant.return_value = {
        "request_key": "ident_1",
        "is_plant": True,
        "suggestions": [
            {
                "rank": 1,
                "scientific_name": "Monstera deliciosa",
                "common_names": ["Swiss Cheese Plant"],
                "family": "Araceae",
                "genus": "Monstera",
                "confidence": 0.94,
                "external_id": "plantnet:2868543",
                "image_url": None,
                "gbif_id": 2868543,
                "matched_species_key": "species_monstera",
                "species_in_database": True,
                "auto_accept": True,
            }
        ],
    }
    client = TestClient(_build_app(service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/identify",
        files=_jpeg_upload(),
        data={"organ": "leaf", "language": "de"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["request_key"] == "ident_1"
    assert body["suggestions"][0]["external_id"] == "plantnet:2868543"

    _, kwargs = service.identify_plant.call_args
    assert kwargs["tenant_key"] == "tenant_anna"
    assert kwargs["user_key"] == "user_anna"


def test_select_result():
    service = MagicMock()
    service.select_result.return_value = {
        "request_key": "ident_1",
        "selected_rank": 1,
        "matched_species_key": "species_monstera",
        "scientific_name": "Monstera deliciosa",
        "common_names": ["Swiss Cheese Plant"],
        "family": "Araceae",
        "genus": "Monstera",
        "gbif_id": 2868543,
        "confidence": 0.94,
        "species_in_database": True,
    }
    client = TestClient(_build_app(service))

    resp = client.post(f"/api/v1/t/{TENANT_SLUG}/identification/ident_1/select?selected_rank=1")
    assert resp.status_code == 200
    assert resp.json()["matched_species_key"] == "species_monstera"
    service.select_result.assert_called_once_with("ident_1", 1, tenant_key="tenant_anna")


# ── issue #447 — reuse identification photo as a DINOv2 reference ─────────


def test_contribute_reference_returns_409_when_dinov2_disabled(monkeypatch):
    """The reference opt-in is only available with the self-hosted adapter on."""
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    reference_service = MagicMock()
    client = TestClient(_build_app(MagicMock(), reference_service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files=_jpeg_upload(),
        data={"species_key": "species_monstera", "scientific_name": "Monstera deliciosa"},
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "ADAPTER_NOT_AVAILABLE"
    reference_service.contribute_user_reference.assert_not_called()


def test_contribute_reference_rejects_non_image(monkeypatch):
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    reference_service = MagicMock()
    client = TestClient(_build_app(MagicMock(), reference_service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files={"image": ("doc.txt", b"hello", "text/plain")},
        data={"species_key": "species_monstera", "scientific_name": "Monstera deliciosa"},
    )
    assert resp.status_code == 415
    reference_service.contribute_user_reference.assert_not_called()


def test_contribute_reference_success(monkeypatch):
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    reference_service = MagicMock()
    reference_service.contribute_user_reference.return_value = {
        "status": "ok",
        "species_key": "species_monstera",
        "dim": 768,
        "model": "dinov2",
    }
    client = TestClient(_build_app(MagicMock(), reference_service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files=_jpeg_upload(),
        data={"species_key": "species_monstera", "scientific_name": "Monstera deliciosa"},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body == {"indexed": True, "species_key": "species_monstera", "dim": 768}

    args, _ = reference_service.contribute_user_reference.call_args
    assert args[0] == "species_monstera"
    assert args[1] == "Monstera deliciosa"
    assert isinstance(args[2], bytes)
