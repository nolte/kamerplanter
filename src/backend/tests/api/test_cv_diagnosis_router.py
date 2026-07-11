"""API tests for the REQ-038 tenant-scoped CV disease-diagnosis router.

Covers the security surface: consent gate (403), role gate (viewer→403,
grower→ok), cross-tenant confirm (404, no oracle), upload hardening
(oversize→413, non-image→415, undecodable→422) and image non-persistence.
"""

import io
from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from PIL import Image

from app.api.v1.tenant_scoped.cv_diagnosis.tenant_router import router as cv_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_cv_diagnosis_service
from app.common.enums import TenantRole
from app.common.exceptions import (
    ConsentRequiredError,
    KamerplanterError,
    NotFoundError,
)
from app.domain.models.tenant_context import TenantContext

TENANT_SLUG = "anna"


def _tenant_ctx(role: TenantRole = TenantRole.GROWER) -> TenantContext:
    return TenantContext(tenant_key="tenant_anna", tenant_slug=TENANT_SLUG, user_key="user_anna", role=role)


def _app_error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


def _build_app(service, role: TenantRole = TenantRole.GROWER) -> FastAPI:
    app = FastAPI()
    app.include_router(cv_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _app_error_handler)
    app.dependency_overrides[get_cv_diagnosis_service] = lambda: service
    # Override only get_current_tenant so the REAL require_tenant_role gate runs
    # against the injected context (viewer → real ForbiddenError → 403).
    app.dependency_overrides[get_current_tenant] = lambda: _tenant_ctx(role)
    return app


def _real_jpeg(size=(240, 240)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (0, 120, 0)).save(buf, format="JPEG")
    return buf.getvalue()


def _jpeg_upload():
    return {"image": ("leaf.jpg", _real_jpeg(), "image/jpeg")}


def _diagnosis_payload(**overrides) -> dict:
    base = {
        "key": "diag_1",
        "plant_instance_key": None,
        "inspection_key": None,
        "classifications": [],
        "phenotype": None,
        "model_meta": {"model_name": "plantdoc_disease_v1", "fine_tuned_on": ["PlantDoc"], "class_count": 3},
        "adapter_key": "local_cv_diagnosis",
        "is_confident": False,
        "disclaimer": "Nur eine Einschätzung der Bilderkennung — keine gesicherte Diagnose.",
        "confirmed_labels": [],
        "image_hash": "sha256:abc",
        "image_deleted_at": "2026-07-11T00:00:00+00:00",
        "created_at": "2026-07-11T00:00:00+00:00",
    }
    base.update(overrides)
    return base


# ── status ───────────────────────────────────────────────────────────────


def test_status_reports_availability():
    service = MagicMock()
    service.get_status.return_value = {
        "available": True,
        "feature_enabled": True,
        "adapter_key": "local_cv_diagnosis",
        "phenotype_available": True,
        "class_count": 27,
    }
    client = TestClient(_build_app(service))
    resp = client.get(f"/api/v1/t/{TENANT_SLUG}/cv-diagnosis/status")
    assert resp.status_code == 200
    assert resp.json()["available"] is True


# ── role gate ──────────────────────────────────────────────────────────────


def test_diagnose_viewer_forbidden():
    service = MagicMock()
    client = TestClient(_build_app(service, role=TenantRole.VIEWER))
    resp = client.post(f"/api/v1/t/{TENANT_SLUG}/cv-diagnosis/diagnose", files=_jpeg_upload())
    assert resp.status_code == 403
    service.diagnose.assert_not_called()


def test_diagnose_grower_ok_and_disclaimer_present():
    service = MagicMock()
    service.diagnose.return_value = _diagnosis_payload()
    client = TestClient(_build_app(service, role=TenantRole.GROWER))
    resp = client.post(f"/api/v1/t/{TENANT_SLUG}/cv-diagnosis/diagnose", files=_jpeg_upload())
    assert resp.status_code == 200
    body = resp.json()
    assert body["disclaimer"].strip() != ""
    # image non-persistence: only a hash + deletion marker travel back, no raw image
    assert body["image_hash"].startswith("sha256:")
    assert body["image_deleted_at"] is not None
    assert "image_data" not in body


# ── consent gate ─────────────────────────────────────────────────────────


def test_diagnose_without_consent_is_403():
    service = MagicMock()
    service.diagnose.side_effect = ConsentRequiredError("plant_diagnosis")
    client = TestClient(_build_app(service))
    resp = client.post(f"/api/v1/t/{TENANT_SLUG}/cv-diagnosis/diagnose", files=_jpeg_upload())
    assert resp.status_code == 403


# ── upload hardening ──────────────────────────────────────────────────────


def test_diagnose_rejects_non_image_content_type():
    service = MagicMock()
    client = TestClient(_build_app(service))
    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/cv-diagnosis/diagnose",
        files={"image": ("doc.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 415
    service.diagnose.assert_not_called()


def test_diagnose_rejects_oversize_via_content_length():
    service = MagicMock()
    client = TestClient(_build_app(service))
    # 6 MB declared > 5 MB cap → 413 before the body is even read.
    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/cv-diagnosis/diagnose",
        files={"image": ("leaf.jpg", b"\xff\xd8\xff\xe0padding", "image/jpeg")},
        headers={"content-length": str(6 * 1024 * 1024)},
    )
    assert resp.status_code == 413
    service.diagnose.assert_not_called()


def test_diagnose_rejects_undecodable_image():
    service = MagicMock()
    client = TestClient(_build_app(service))
    # JPEG content-type + magic-ish bytes but not a decodable image → 415/422.
    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/cv-diagnosis/diagnose",
        files={"image": ("leaf.jpg", b"\xff\xd8\xff\xe0 not a real jpeg body", "image/jpeg")},
    )
    assert resp.status_code in (415, 422)
    service.diagnose.assert_not_called()


# ── confirm cross-tenant fail-closed ───────────────────────────────────────


def test_confirm_unknown_or_foreign_is_404_no_oracle():
    service = MagicMock()
    service.confirm.side_effect = NotFoundError("PlantDiagnosisRequest", "diag_x")
    client = TestClient(_build_app(service))
    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/cv-diagnosis/diagnose/diag_x/confirm",
        json={"plant_key": "plant_1"},
    )
    assert resp.status_code == 404


def test_confirm_grower_creates_inspection_suggestion():
    service = MagicMock()
    service.confirm.return_value = {
        "inspection_key": "insp_1",
        "detected_disease_keys": ["disease_early_blight"],
        "detected_pest_keys": [],
        "confirmed_labels": ["tomato_early_blight"],
    }
    client = TestClient(_build_app(service))
    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/cv-diagnosis/diagnose/diag_1/confirm",
        json={"plant_key": "plant_1", "confirmed_labels": ["tomato_early_blight"]},
    )
    assert resp.status_code == 201
    assert resp.json()["inspection_key"] == "insp_1"


def test_confirm_viewer_forbidden():
    service = MagicMock()
    client = TestClient(_build_app(service, role=TenantRole.VIEWER))
    resp = client.post(
        f"/api/v1/t/{TENANT_SLUG}/cv-diagnosis/diagnose/diag_1/confirm",
        json={"plant_key": "plant_1"},
    )
    assert resp.status_code == 403
    service.confirm.assert_not_called()


# ── history ────────────────────────────────────────────────────────────────


def test_history_returns_entries():
    service = MagicMock()
    service.get_history.return_value = [_diagnosis_payload()]
    client = TestClient(_build_app(service))
    resp = client.get(f"/api/v1/t/{TENANT_SLUG}/cv-diagnosis/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
