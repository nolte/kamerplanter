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


@pytest.fixture(autouse=True)
def _restore_delay():
    """Restore the real Celery ``.delay`` after each test patched it."""
    import app.tasks.storage_tasks as storage_tasks

    original = storage_tasks.generate_thumbnails.delay
    yield
    storage_tasks.generate_thumbnails.delay = original
