"""NFR-013 — API tests for the attachment routers (tenant + token).

End-to-end through ``TestClient`` against a real local-fs storage adapter
(``tmp_path``) and an in-memory attachment repository. Covers the full
lifecycle (upload → list → download → delete), type rejection (415), the
viewer 403 path, and local-fs token redemption.
"""

from __future__ import annotations

import io

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from PIL import Image

from app.api.v1.attachments.tenant_router import router as tenant_attachments_router
from app.api.v1.attachments.token_router import router as token_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_attachment_service, get_object_storage
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.config.settings import Settings
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.domain.models.attachment import Attachment
from app.domain.models.tenant_context import TenantContext
from app.domain.services.attachment_service import AttachmentService

TENANT_SLUG = "anna"


def _make_jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (160, 120), (90, 160, 60)).save(buffer, format="JPEG")
    return buffer.getvalue()


class _FakeRepo:
    def __init__(self) -> None:
        self._store: dict[str, Attachment] = {}
        self._seq = 0

    def create(self, attachment: Attachment) -> Attachment:
        self._seq += 1
        key = f"att{self._seq}"
        stored = attachment.model_copy(update={"key": key})
        self._store[key] = stored
        return stored

    def get(self, key, tenant_key):
        att = self._store.get(key)
        return att if att and att.tenant_key == tenant_key else None

    def delete(self, key, tenant_key):
        if self.get(key, tenant_key):
            del self._store[key]
            return True
        return False

    def find_by_user(self, tenant_key, user_key, categories=None):
        return list(self._store.values())

    def find_by_sha256(self, tenant_key, sha256):
        for a in self._store.values():
            if a.tenant_key == tenant_key and a.sha256 == sha256:
                return a
        return None

    def count_by_tenant(self, tenant_key):
        return len(self._store)

    def sum_bytes_by_tenant(self, tenant_key):
        return sum(a.byte_size for a in self._store.values())

    def list_by_tenant(self, tenant_key, category=None, offset=0, limit=50):
        items = [a for a in self._store.values() if a.tenant_key == tenant_key]
        if category is not None:
            items = [a for a in items if a.category == category]
        return items[offset : offset + limit], len(items)


def _ctx(role: TenantRole) -> TenantContext:
    return TenantContext(
        tenant_key="tenant_anna",
        tenant_slug=TENANT_SLUG,
        user_key="user_anna",
        role=role,
    )


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


def _build(tmp_path, role: TenantRole = TenantRole.ADMIN):
    repo = _FakeRepo()
    adapter = LocalFsStorageAdapter(
        root=str(tmp_path),
        public_base_url="http://testserver/api/v1/attachments/token",
        signing_secret="api-test-secret",
        max_object_size_bytes=25 * 1024 * 1024,
    )
    settings = Settings()
    service = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)

    app = FastAPI()
    app.include_router(tenant_attachments_router, prefix="/api/v1/t/{tenant_slug}")
    app.include_router(token_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: _ctx(role)
    app.dependency_overrides[get_attachment_service] = lambda: service
    app.dependency_overrides[get_object_storage] = lambda: adapter

    # Thumbnails dispatch via Celery .delay — patch on the module the service imports.
    import app.tasks.storage_tasks as storage_tasks

    storage_tasks.generate_thumbnails.delay = lambda *a, **k: None  # type: ignore[assignment]
    return app, service, adapter


def _base(path: str = "") -> str:
    return f"/api/v1/t/{TENANT_SLUG}/attachments{path}"


class TestLifecycle:
    def test_upload_list_download_delete(self, tmp_path):
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)

        # Upload
        resp = client.post(
            _base(),
            files={"file": ("plant.jpg", _make_jpeg(), "image/jpeg")},
            data={"category": "diary"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        attachment_id = body["attachment_id"]
        assert body["uri"] == _base(f"/{attachment_id}")
        assert body["thumbnail_uris"]["small"].endswith("/thumbnails/128")
        # Never leak storage internals (NFR-013 AC-04).
        assert "storage_key" not in body
        assert "bucket" not in resp.text.lower()

        # List
        resp = client.get(_base())
        assert resp.status_code == 200
        listing = resp.json()
        assert listing["total"] == 1
        assert listing["items"][0]["attachment_id"] == attachment_id

        # Download (local-fs → proxy stream with ETag + cache header)
        resp = client.get(_base(f"/{attachment_id}"))
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("image/jpeg")
        assert resp.headers["cache-control"] == "private, max-age=86400"
        assert resp.headers["etag"]
        assert len(resp.content) > 0

        # Delete
        resp = client.delete(_base(f"/{attachment_id}"))
        assert resp.status_code == 204

        # Gone
        resp = client.get(_base(f"/{attachment_id}"))
        assert resp.status_code == 404


class TestTypeRejection:
    def test_415_on_disallowed_type(self, tmp_path):
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        resp = client.post(
            _base(),
            files={"file": ("note.txt", b"hello world", "text/plain")},
            data={"category": "diary"},
        )
        assert resp.status_code == 415
        assert resp.json()["error_code"] == "INVALID_FILE_TYPE"

    def test_415_on_magic_byte_mismatch(self, tmp_path):
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        # PNG bytes declared as JPEG.
        png = io.BytesIO()
        Image.new("RGB", (8, 8)).save(png, format="PNG")
        resp = client.post(
            _base(),
            files={"file": ("fake.jpg", png.getvalue(), "image/jpeg")},
            data={"category": "diary"},
        )
        assert resp.status_code == 415


class TestViewerForbidden:
    def test_viewer_can_read_but_not_upload(self, tmp_path):
        app, _service, _adapter = _build(tmp_path, role=TenantRole.VIEWER)
        client = TestClient(app)

        # Read is allowed.
        resp = client.get(_base())
        assert resp.status_code == 200

        # Upload is forbidden.
        resp = client.post(
            _base(),
            files={"file": ("plant.jpg", _make_jpeg(), "image/jpeg")},
            data={"category": "diary"},
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "FORBIDDEN"

    def test_viewer_cannot_delete(self, tmp_path):
        app, _service, _adapter = _build(tmp_path, role=TenantRole.VIEWER)
        client = TestClient(app)
        resp = client.delete(_base("/whatever"))
        assert resp.status_code == 403


class TestTokenRedemption:
    def test_local_fs_token_download(self, tmp_path):
        app, service, adapter = _build(tmp_path)
        client = TestClient(app)

        # Upload to get a real object.
        resp = client.post(
            _base(),
            files={"file": ("plant.jpg", _make_jpeg(), "image/jpeg")},
            data={"category": "diary"},
        )
        attachment_id = resp.json()["attachment_id"]

        # Explicit presign-download yields a token URL.
        resp = client.get(_base(f"/{attachment_id}/presign-download"))
        assert resp.status_code == 200
        url = resp.json()["download_url"]
        assert "/api/v1/attachments/token/" in url

        # Redeem the token path (strip host).
        token_path = url.split("testserver", 1)[-1] if "testserver" in url else url
        resp = client.get(token_path)
        assert resp.status_code == 200
        assert len(resp.content) > 0

    def test_invalid_token_rejected(self, tmp_path):
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        resp = client.get("/api/v1/attachments/token/not-a-valid-token")
        assert resp.status_code == 401

    def test_token_for_other_tenant_key_is_rejected(self, tmp_path):
        # SEC-001 — a validly-signed token whose key prefix does not match the
        # bound tenant_key must be rejected (cross-tenant replay).
        app, _service, adapter = _build(tmp_path)
        client = TestClient(app)

        # Forge a properly-signed token (same secret) whose key belongs to a
        # different tenant than the embedded tenant_key claim.
        token = adapter._make_token(
            {
                "op": "download",
                "key": "t/tenant_bob/diary/2026/06/x.jpg",
                "tenant_key": "tenant_anna",
                "exp": 2_000_000_000,
                "disposition": None,
            }
        )
        resp = client.get(f"/api/v1/attachments/token/{token}")
        assert resp.status_code == 401

    def test_token_without_tenant_claim_is_rejected(self, tmp_path):
        # A legacy/unbound token (no tenant_key) is no longer accepted.
        app, _service, adapter = _build(tmp_path)
        client = TestClient(app)
        token = adapter._make_token(
            {"op": "download", "key": "t/tenant_anna/diary/x.jpg", "exp": 2_000_000_000, "disposition": None}
        )
        resp = client.get(f"/api/v1/attachments/token/{token}")
        assert resp.status_code == 401


class TestPresignUploadDisabled:
    def test_presign_upload_returns_409(self, tmp_path):
        # SEC-003 — presigned upload is disabled for ALL backends.
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        resp = client.post(
            _base("/presign-upload"),
            json={"category": "diary", "mime_type": "image/jpeg"},
        )
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "PRESIGN_UPLOAD_UNSUPPORTED"


class TestUploadSizeGuard:
    def test_oversized_content_length_rejected_without_reading(self, tmp_path):
        # SEC-005 — an oversized Content-Length is rejected with 413 up front.
        app, service, _adapter = _build(tmp_path)
        max_bytes = service.max_upload_bytes()
        client = TestClient(app)
        resp = client.post(
            _base(),
            files={"file": ("plant.jpg", _make_jpeg(), "image/jpeg")},
            data={"category": "diary"},
            headers={"Content-Length": str(max_bytes + 1)},
        )
        assert resp.status_code == 413
        assert resp.json()["error_code"] == "FILE_TOO_LARGE"

    def test_oversized_body_rejected_chunked(self, tmp_path):
        # SEC-005 — even with a small/zero size limit the chunked read caps RAM
        # and rejects with 413 (the Content-Length path may not trip for a tiny
        # multipart, so this exercises the streaming guard).
        repo = _FakeRepo()
        adapter = LocalFsStorageAdapter(
            root=str(tmp_path),
            public_base_url="http://testserver/api/v1/attachments/token",
            signing_secret="api-test-secret",
            max_object_size_bytes=25 * 1024 * 1024,
        )
        settings = Settings(storage_max_file_size_mb=0)
        service = AttachmentService(storage=adapter, attachment_repo=repo, settings=settings)

        app = FastAPI()
        app.include_router(tenant_attachments_router, prefix="/api/v1/t/{tenant_slug}")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_tenant] = lambda: _ctx(TenantRole.ADMIN)
        app.dependency_overrides[get_attachment_service] = lambda: service
        client = TestClient(app)

        resp = client.post(
            _base(),
            files={"file": ("plant.jpg", _make_jpeg(), "image/jpeg")},
            data={"category": "diary"},
        )
        assert resp.status_code == 413


class TestDownloadHeaders:
    def test_image_download_has_nosniff(self, tmp_path):
        # SEC-009 — every download carries X-Content-Type-Options: nosniff.
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        resp = client.post(
            _base(),
            files={"file": ("plant.jpg", _make_jpeg(), "image/jpeg")},
            data={"category": "diary"},
        )
        attachment_id = resp.json()["attachment_id"]
        resp = client.get(_base(f"/{attachment_id}"))
        assert resp.status_code == 200
        assert resp.headers["x-content-type-options"] == "nosniff"
        # image/* may render inline → no forced attachment disposition.
        assert resp.headers.get("content-disposition", "") != "attachment"

    def test_non_image_download_forces_attachment(self, tmp_path):
        # SEC-009 — a non-image MIME type is forced to download. A CSV upload in
        # the ``import`` category goes through the normal proxy pipeline (no
        # manual event-loop juggling), then the download must carry
        # Content-Disposition: attachment.
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)

        csv_bytes = b"name,scientific_name\nTomato,Solanum lycopersicum\n"
        resp = client.post(
            _base(),
            files={"file": ("plants.csv", csv_bytes, "text/csv")},
            data={"category": "import"},
        )
        assert resp.status_code == 201, resp.text
        attachment_id = resp.json()["attachment_id"]

        resp = client.get(_base(f"/{attachment_id}"))
        assert resp.status_code == 200
        assert resp.headers["x-content-type-options"] == "nosniff"
        assert resp.headers["content-disposition"] == "attachment"


@pytest.fixture(autouse=True)
def _restore_delay():
    """Restore the real Celery ``.delay`` after each test patched it."""
    import app.tasks.storage_tasks as storage_tasks

    original = storage_tasks.generate_thumbnails.delay
    yield
    storage_tasks.generate_thumbnails.delay = original
