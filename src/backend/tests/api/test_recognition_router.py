"""API tests for the REQ-029 recognition routers (status + tenant-scoped)."""

import io
from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from PIL import Image

from app.api.v1.recognition import tenant_router as tenant_recognition_module
from app.api.v1.recognition.router import router as recognition_router
from app.api.v1.recognition.tenant_router import router as tenant_recognition_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_identification_service, get_reference_image_service
from app.common.enums import TenantRole
from app.common.exceptions import (
    ConsentRequiredError,
    KamerplanterError,
    NotFoundError,
    RateLimitError,
)
from app.config.settings import settings
from app.domain.models.tenant_context import TenantContext

TENANT_SLUG = "anna"


def _tenant_ctx(role: TenantRole = TenantRole.ADMIN) -> TenantContext:
    return TenantContext(
        tenant_key="tenant_anna",
        tenant_slug=TENANT_SLUG,
        user_key="user_anna",
        role=role,
    )


def _app_error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _build_app(service, reference_service=None, role: TenantRole = TenantRole.ADMIN):
    app = FastAPI()
    app.include_router(recognition_router, prefix="/api/v1")
    app.include_router(tenant_recognition_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _app_error_handler)
    app.dependency_overrides[get_identification_service] = lambda: service
    app.dependency_overrides[get_current_tenant] = lambda: _tenant_ctx(role)
    if reference_service is not None:
        app.dependency_overrides[get_reference_image_service] = lambda: reference_service
    return app


def _jpeg_upload():
    return {"image": ("plant.jpg", b"\xff\xd8\xff\xe0fake-jpeg-bytes", "image/jpeg")}


def _real_jpeg_upload():
    """A genuinely decodable small JPEG (passes the SEC-004 decode/bomb guard)."""
    buf = io.BytesIO()
    Image.new("RGB", (240, 240), (0, 120, 0)).save(buf, format="JPEG")
    return {"image": ("plant.jpg", buf.getvalue(), "image/jpeg")}


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


# ── issue #630 — link the created plant instance to the identification ────


def test_link_plant_instance_success():
    service = MagicMock()
    service.link_plant_instance.return_value = {
        "request_key": "ident_1",
        "plant_instance_key": "plant_42",
    }
    client = TestClient(_build_app(service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/ident_1/instance",
        json={"plant_instance_key": "plant_42"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"request_key": "ident_1", "plant_instance_key": "plant_42"}
    service.link_plant_instance.assert_called_once_with("ident_1", "plant_42", tenant_key="tenant_anna")


def test_link_plant_instance_rejects_empty_key():
    service = MagicMock()
    client = TestClient(_build_app(service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/ident_1/instance",
        json={"plant_instance_key": ""},
    )
    assert resp.status_code == 422
    service.link_plant_instance.assert_not_called()


def test_link_plant_instance_foreign_instance_returns_404():
    """A plant instance from another tenant surfaces as a 404 (no leakage)."""
    service = MagicMock()
    service.link_plant_instance.side_effect = NotFoundError("PlantInstance", "plant_foreign")
    client = TestClient(_build_app(service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/ident_1/instance",
        json={"plant_instance_key": "plant_foreign"},
    )
    assert resp.status_code == 404


def test_history_surfaces_plant_instance_key():
    """The history DTO exposes the linked plant instance key (#630)."""
    service = MagicMock()
    service.get_history.return_value = [
        {
            "key": "ident_1",
            "adapter_key": "plantnet",
            "request_type": "identification",
            "image_organ": "auto",
            "status": "completed",
            "results": [],
            "selected_result_rank": 1,
            "plant_instance_key": "plant_42",
            "created_at": "2026-06-15T10:00:00Z",
        },
        {
            "key": "ident_2",
            "adapter_key": "plantnet",
            "request_type": "identification",
            "image_organ": "auto",
            "status": "completed",
            "results": [],
            "selected_result_rank": None,
            "created_at": "2026-06-14T10:00:00Z",
        },
    ]
    client = TestClient(_build_app(service))

    resp = client.get(f"/api/v1/t/{TENANT_SLUG}/identification/history")
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["plant_instance_key"] == "plant_42"
    # An entry without a link reports null, never omits the field.
    assert body[1]["plant_instance_key"] is None


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
        "accepted": True,
        "pending_review": True,
        "species_key": "species_monstera",
        "dim": 768,
        "source_record_id": "sha256:abc",
    }
    client = TestClient(_build_app(MagicMock(), reference_service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files=_real_jpeg_upload(),
        # A client-supplied scientific_name is present but must be ignored (SEC-003).
        data={"species_key": "species_monstera", "scientific_name": "Attacker spoofus"},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body == {
        "accepted": True,
        "pending_review": True,
        "species_key": "species_monstera",
        "dim": 768,
    }

    # SEC-003 — the endpoint no longer forwards a client scientific_name; the
    # service derives it from the resolved species record. It passes the
    # contributor + tenant provenance (SEC-005) instead.
    args, kwargs = reference_service.contribute_user_reference.call_args
    assert args[0] == "species_monstera"
    assert isinstance(args[1], bytes)
    assert kwargs["user_key"] == "user_anna"
    assert kwargs["tenant_key"] == "tenant_anna"
    assert "scientific_name" not in kwargs


def test_contribute_reference_viewer_forbidden(monkeypatch):
    """SEC-001 — a viewer must not be able to write to the global index."""
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    reference_service = MagicMock()
    client = TestClient(_build_app(MagicMock(), reference_service, role=TenantRole.VIEWER))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files=_real_jpeg_upload(),
        data={"species_key": "species_monstera"},
    )
    assert resp.status_code == 403
    reference_service.contribute_user_reference.assert_not_called()


def test_contribute_reference_grower_allowed(monkeypatch):
    """SEC-001 — a grower (not just admin) may contribute."""
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    reference_service = MagicMock()
    reference_service.contribute_user_reference.return_value = {
        "accepted": True,
        "pending_review": True,
        "species_key": "species_monstera",
        "dim": 384,
    }
    client = TestClient(_build_app(MagicMock(), reference_service, role=TenantRole.GROWER))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files=_real_jpeg_upload(),
        data={"species_key": "species_monstera"},
    )
    assert resp.status_code == 202
    reference_service.contribute_user_reference.assert_called_once()


def test_contribute_reference_unknown_species_returns_404(monkeypatch):
    """SEC-003 — an unknown species is a 404 (surfaced from the service)."""
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    reference_service = MagicMock()
    reference_service.contribute_user_reference.side_effect = NotFoundError("Species", "species_ghost")
    client = TestClient(_build_app(MagicMock(), reference_service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files=_real_jpeg_upload(),
        data={"species_key": "species_ghost"},
    )
    assert resp.status_code == 404


def test_contribute_reference_rate_limited_returns_429(monkeypatch):
    """SEC-002 — the per-user contribution quota surfaces as 429."""
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    reference_service = MagicMock()
    reference_service.contribute_user_reference.side_effect = RateLimitError("contribute")
    client = TestClient(_build_app(MagicMock(), reference_service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files=_real_jpeg_upload(),
        data={"species_key": "species_monstera"},
    )
    assert resp.status_code == 429


def test_contribute_reference_undecodable_image_returns_422(monkeypatch):
    """SEC-004/006 — JPEG magic but corrupt bytes are a 422, never a 500."""
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    reference_service = MagicMock()
    client = TestClient(_build_app(MagicMock(), reference_service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files=_jpeg_upload(),  # valid magic bytes, undecodable body
        data={"species_key": "species_monstera"},
    )
    assert resp.status_code == 422
    reference_service.contribute_user_reference.assert_not_called()


def test_contribute_reference_oversize_returns_413(monkeypatch):
    """SEC-004 — an upload over the size cap is a 413 before any embedding."""
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    monkeypatch.setattr(settings, "identification_max_image_size_mb", 0)
    reference_service = MagicMock()
    client = TestClient(_build_app(MagicMock(), reference_service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files=_real_jpeg_upload(),
        data={"species_key": "species_monstera"},
    )
    assert resp.status_code == 413
    reference_service.contribute_user_reference.assert_not_called()


def test_contribute_reference_pixel_bomb_returns_413(monkeypatch):
    """SEC-004 — a decodable image whose pixel count exceeds the cap is a 413."""
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    monkeypatch.setattr(tenant_recognition_module, "_MAX_IMAGE_PIXELS", 100)
    reference_service = MagicMock()
    client = TestClient(_build_app(MagicMock(), reference_service))

    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files=_real_jpeg_upload(),  # 240x240 = 57600 px > 100 px cap
        data={"species_key": "species_monstera"},
    )
    assert resp.status_code == 413
    reference_service.contribute_user_reference.assert_not_called()
