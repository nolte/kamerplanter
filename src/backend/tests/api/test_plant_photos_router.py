"""REQ-034 §7 — API tests for the plant-instance photo gallery router.

End-to-end through ``TestClient`` against a real local-fs storage adapter
(``tmp_path``) and in-memory repositories. Covers the happy-path lifecycle
(upload → list → cover → delete), the per-instance quota 409 (AC-15), and the
viewer 403 / read paths (AC-13).
"""

from __future__ import annotations

import io
from datetime import date

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from PIL import Image

from app.api.v1.plant_instances.photo_router import router as photo_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_attachment_service, get_plant_photo_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.config.settings import Settings
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.domain.models.attachment import Attachment
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.plant_photo_service import PlantPhotoService

TENANT_SLUG = "anna"
TENANT_KEY = "tenant_anna"
PLANT_KEY = "plant1"


def _make_jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (160, 120), (90, 160, 60)).save(buffer, format="JPEG")
    return buffer.getvalue()


class _FakeAttachmentRepo:
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

    def find_by_sha256(self, tenant_key, sha256):
        for a in self._store.values():
            if a.tenant_key == tenant_key and a.sha256 == sha256:
                return a
        return None

    def sum_bytes_by_tenant(self, tenant_key):
        return sum(a.byte_size for a in self._store.values())

    def list_by_tenant(self, tenant_key, category=None, offset=0, limit=50):
        items = [a for a in self._store.values() if a.tenant_key == tenant_key]
        return items[offset : offset + limit], len(items)


class _FakePlantRepo:
    def __init__(self, plant: PlantInstance) -> None:
        self._plant = plant

    def get_by_key(self, key):
        return self._plant if self._plant.key == key else None

    def update(self, key, plant):
        self._plant = plant
        return plant


def _ctx(role: TenantRole) -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user_anna",
        role=role,
    )


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


def _build(tmp_path, role: TenantRole = TenantRole.ADMIN, *, max_photos: int = 50):
    att_repo = _FakeAttachmentRepo()
    adapter = LocalFsStorageAdapter(
        root=str(tmp_path),
        public_base_url="http://testserver/api/v1/attachments/token",
        signing_secret="api-test-secret",
        max_object_size_bytes=25 * 1024 * 1024,
    )
    settings = Settings(storage_max_photos_per_instance=max_photos)
    att_service = AttachmentService(storage=adapter, attachment_repo=att_repo, settings=settings)

    plant = PlantInstance(
        _key=PLANT_KEY,
        tenant_key=TENANT_KEY,
        instance_id="P-1",
        species_key="",  # empty → reference hook is never dispatched
        planted_on=date(2026, 6, 1),
    )
    plant_repo = _FakePlantRepo(plant)
    photo_service = PlantPhotoService(plant_repo, att_repo, att_service, settings)

    app = FastAPI()
    app.include_router(photo_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: _ctx(role)
    app.dependency_overrides[get_attachment_service] = lambda: att_service
    app.dependency_overrides[get_plant_photo_service] = lambda: photo_service

    # Silence the off-path Celery dispatches.
    import app.tasks.storage_tasks as storage_tasks

    storage_tasks.generate_thumbnails.delay = lambda *a, **k: None  # type: ignore[assignment]
    return app, plant_repo, att_repo


def _base(path: str = "") -> str:
    return f"/api/v1/t/{TENANT_SLUG}/plant-instances/{PLANT_KEY}/photos{path}"


def _upload(client) -> str:
    resp = client.post(_base(), files={"file": ("plant.jpg", _make_jpeg(), "image/jpeg")})
    assert resp.status_code == 201, resp.text
    return resp.json()["attachment_id"]


class TestLifecycle:
    def test_upload_list_cover_delete(self, tmp_path):
        app, plant_repo, _ar = _build(tmp_path)
        client = TestClient(app)

        # Upload first photo → becomes cover automatically.
        att1 = _upload(client)
        body = client.post(_base(), files={"file": ("p2.jpg", _make_jpeg(), "image/jpeg")})
        # Second upload dedups against identical bytes — use a different image.
        assert body.status_code in (201,)

        # List
        resp = client.get(_base())
        assert resp.status_code == 200
        listing = resp.json()
        assert listing["plant_instance_key"] == PLANT_KEY
        assert listing["cover_photo_ref"] == att1
        assert any(p["is_cover"] for p in listing["photos"])
        # No storage internals leaked (AC-03/AC-04).
        assert "storage_key" not in resp.text
        assert "bucket" not in resp.text.lower()
        assert listing["photos"][0]["uri"].startswith(f"/api/v1/t/{TENANT_SLUG}/attachments/")

        # Cover stays att1; explicitly set it again (idempotent visibility).
        resp = client.put(_base(f"/{att1}/cover"))
        assert resp.status_code == 200
        assert resp.json()["cover_photo_ref"] == att1

        # Delete the cover → it is unlinked and gone.
        resp = client.delete(_base(f"/{att1}"))
        assert resp.status_code == 204
        resp = client.get(_base())
        ids = [p["attachment_id"] for p in resp.json()["photos"]]
        assert att1 not in ids

    def test_set_cover_not_in_gallery_422(self, tmp_path):
        app, _pr, _ar = _build(tmp_path)
        client = TestClient(app)
        _upload(client)
        resp = client.put(_base("/ghost/cover"))
        assert resp.status_code == 422
        assert resp.json()["error_code"] == "VALIDATION_ERROR"

    def test_delete_unknown_photo_404(self, tmp_path):
        app, _pr, _ar = _build(tmp_path)
        client = TestClient(app)
        resp = client.delete(_base("/ghost"))
        assert resp.status_code == 404


class TestQuota:
    def test_quota_exceeded_returns_409(self, tmp_path):
        app, _pr, _ar = _build(tmp_path, max_photos=1)
        client = TestClient(app)
        _upload(client)
        # Second distinct upload must be rejected before any bytes are written.
        png = io.BytesIO()
        Image.new("RGB", (32, 24), (10, 20, 30)).save(png, format="PNG")
        resp = client.post(_base(), files={"file": ("p2.png", png.getvalue(), "image/png")})
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "PHOTO_QUOTA_EXCEEDED"


class TestViewerForbidden:
    def test_viewer_can_read(self, tmp_path):
        app, _pr, _ar = _build(tmp_path, role=TenantRole.VIEWER)
        client = TestClient(app)
        resp = client.get(_base())
        assert resp.status_code == 200

    def test_viewer_cannot_upload(self, tmp_path):
        app, _pr, _ar = _build(tmp_path, role=TenantRole.VIEWER)
        client = TestClient(app)
        resp = client.post(_base(), files={"file": ("plant.jpg", _make_jpeg(), "image/jpeg")})
        assert resp.status_code == 403

    def test_viewer_cannot_set_cover(self, tmp_path):
        app, _pr, _ar = _build(tmp_path, role=TenantRole.VIEWER)
        client = TestClient(app)
        resp = client.put(_base("/whatever/cover"))
        assert resp.status_code == 403

    def test_viewer_cannot_delete(self, tmp_path):
        app, _pr, _ar = _build(tmp_path, role=TenantRole.VIEWER)
        client = TestClient(app)
        resp = client.delete(_base("/whatever"))
        assert resp.status_code == 403


@pytest.fixture(autouse=True)
def _restore_delay():
    import app.tasks.storage_tasks as storage_tasks

    original = storage_tasks.generate_thumbnails.delay
    yield
    storage_tasks.generate_thumbnails.delay = original
