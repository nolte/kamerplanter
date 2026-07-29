"""REQ-034 §7 — API tests for the plant-instance photo gallery router.

End-to-end through ``TestClient`` against a real local-fs storage adapter
(``tmp_path``) and in-memory repositories. Covers the happy-path lifecycle
(upload → list → cover → delete), the per-instance quota 409 (AC-15), and the
viewer 403 / read paths (AC-13).
"""

from __future__ import annotations

import io
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from PIL import Image

from app.api.v1.plant_instances.photo_router import router as photo_router
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_attachment_service,
    get_identification_service,
    get_plant_photo_service,
)
from app.common.enums import TenantRole
from app.common.exceptions import AdapterNotAvailableError, KamerplanterError, NotFoundError
from app.config.settings import Settings
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.domain.interfaces.attachment_repository import UNSET, _Unset
from app.domain.interfaces.plant_identification_adapter import (
    IdentificationResult,
    IdentificationSuggestion,
)
from app.domain.models.attachment import Attachment
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species
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

    def update_metadata(self, key, tenant_key, *, caption=UNSET, taken_on=UNSET):
        att = self.get(key, tenant_key)
        if att is None:
            return None
        update: dict = {}
        if not isinstance(caption, _Unset):
            update["caption"] = caption
        if not isinstance(taken_on, _Unset):
            update["taken_on"] = taken_on
        updated = att.model_copy(update=update)
        self._store[key] = updated
        return updated

    def update_quality_assessment(self, key, tenant_key, assessment):
        att = self.get(key, tenant_key)
        if att is None:
            return None
        updated = att.model_copy(update={"quality_assessment": assessment})
        self._store[key] = updated
        return updated

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

    def get_or_raise(self, key):
        plant = self.get_by_key(key)
        if plant is None:
            raise NotFoundError("PlantInstance", key)
        return plant

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


class _StubIdentificationService:
    """Stub for the identification service used by the assess endpoints."""

    def __init__(self, result=None, raise_exc=None, adapters=None) -> None:
        self._result = result
        self._raise = raise_exc
        self._adapters = adapters or []

    def assess_quality(self, image_data, *, adapter_key, tenant_key, user_key, organ=None, language="de"):
        if self._raise is not None:
            raise self._raise
        return self._result

    def list_assessment_adapters(self):
        return self._adapters


class _FakeSpeciesRepo:
    def __init__(self, species: dict[str, Species] | None = None) -> None:
        self._species = species or {}

    def get_by_key(self, key):
        return self._species.get(key)


def _build(
    tmp_path,
    role: TenantRole = TenantRole.LEAD,
    *,
    max_photos: int = 50,
    species_key: str = "",
    species_name: str | None = None,
    ident_result=None,
    ident_raise=None,
    ident_adapters=None,
):
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
        species_key=species_key,  # empty → reference hook is never dispatched
        planted_on=date(2026, 6, 1),
    )
    plant_repo = _FakePlantRepo(plant)
    species = {species_key: Species(scientific_name=species_name)} if species_key and species_name else {}
    ident = _StubIdentificationService(result=ident_result, raise_exc=ident_raise, adapters=ident_adapters)
    photo_service = PlantPhotoService(
        plant_repo,
        att_repo,
        att_service,
        settings,
        identification_service=ident,
        species_repo=_FakeSpeciesRepo(species),
    )

    app = FastAPI()
    app.include_router(photo_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: _ctx(role)
    app.dependency_overrides[get_attachment_service] = lambda: att_service
    app.dependency_overrides[get_plant_photo_service] = lambda: photo_service
    app.dependency_overrides[get_identification_service] = lambda: ident

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


class TestMetadata:
    def test_patch_sets_caption_and_taken_on(self, tmp_path):
        app, _pr, _ar = _build(tmp_path)
        client = TestClient(app)
        att = _upload(client)
        resp = client.patch(_base(f"/{att}"), json={"caption": "My tomato", "taken_on": "2026-06-01"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["caption"] == "My tomato"
        assert body["taken_on"] == "2026-06-01"
        # created_at is still present so the FE can fall back when taken_on is null.
        assert body["created_at"] is not None
        # List reflects the change.
        listing = client.get(_base()).json()
        assert listing["photos"][0]["caption"] == "My tomato"

    def test_patch_only_caption_keeps_taken_on(self, tmp_path):
        app, _pr, _ar = _build(tmp_path)
        client = TestClient(app)
        att = _upload(client)
        client.patch(_base(f"/{att}"), json={"caption": "a", "taken_on": "2026-06-01"})
        # Omit taken_on entirely → it must survive (true PATCH).
        resp = client.patch(_base(f"/{att}"), json={"caption": "b"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["caption"] == "b"
        assert body["taken_on"] == "2026-06-01"

    def test_patch_explicit_null_clears_caption(self, tmp_path):
        app, _pr, _ar = _build(tmp_path)
        client = TestClient(app)
        att = _upload(client)
        client.patch(_base(f"/{att}"), json={"caption": "to clear"})
        resp = client.patch(_base(f"/{att}"), json={"caption": None})
        assert resp.status_code == 200
        assert resp.json()["caption"] is None

    def test_caption_too_long_422(self, tmp_path):
        app, _pr, _ar = _build(tmp_path)
        client = TestClient(app)
        att = _upload(client)
        resp = client.patch(_base(f"/{att}"), json={"caption": "x" * 501})
        # 422 — either from the schema max_length or the service guard.
        assert resp.status_code == 422

    def test_taken_on_future_422(self, tmp_path):
        app, _pr, _ar = _build(tmp_path)
        client = TestClient(app)
        att = _upload(client)
        future = (datetime.now(UTC).date() + timedelta(days=1)).isoformat()
        resp = client.patch(_base(f"/{att}"), json={"taken_on": future})
        assert resp.status_code == 422
        assert resp.json()["error_code"] == "VALIDATION_ERROR"

    def test_patch_unknown_attachment_404(self, tmp_path):
        app, _pr, _ar = _build(tmp_path)
        client = TestClient(app)
        _upload(client)
        resp = client.patch(_base("/ghost"), json={"caption": "x"})
        assert resp.status_code == 404


def _ident_result(pairs, *, is_plant=True):
    return IdentificationResult(
        suggestions=[
            IdentificationSuggestion(rank=i + 1, scientific_name=n, confidence=c, external_id=f"plantnet:{i}")
            for i, (n, c) in enumerate(pairs)
        ],
        is_plant=is_plant,
    )


class TestAssess:
    def test_assess_persists_and_returns_verdict(self, tmp_path):
        app, _pr, att_repo = _build(
            tmp_path,
            species_key="sp1",
            species_name="Ocimum basilicum",
            ident_result=_ident_result([("Ocimum basilicum", 0.95)]),
        )
        client = TestClient(app)
        att = _upload(client)
        resp = client.post(_base(f"/{att}/assess"), json={"adapter": "plantnet"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        qa = body["quality_assessment"]
        assert qa is not None
        assert qa["rating"] == "good"
        assert qa["is_plant"] is True
        assert qa["expected_species_matched"] is True
        assert qa["adapter"] == "plantnet"
        assert qa["suggestions"][0]["scientific_name"] == "Ocimum basilicum"

        # Persisted: the listing now shows the assessment (visible afterwards).
        listing = client.get(_base()).json()
        photo = next(p for p in listing["photos"] if p["attachment_id"] == att)
        assert photo["quality_assessment"]["rating"] == "good"

    def test_assess_poor_when_not_a_plant(self, tmp_path):
        app, _pr, _ar = _build(
            tmp_path,
            species_key="sp1",
            species_name="Ocimum basilicum",
            ident_result=_ident_result([], is_plant=False),
        )
        client = TestClient(app)
        att = _upload(client)
        resp = client.post(_base(f"/{att}/assess"), json={"adapter": "plantnet"})
        assert resp.status_code == 200
        assert resp.json()["quality_assessment"]["rating"] == "poor"

    def test_assess_adapter_unavailable_409(self, tmp_path):
        app, _pr, _ar = _build(
            tmp_path,
            ident_raise=AdapterNotAvailableError("local_embedding", "adapter is not configured"),
        )
        client = TestClient(app)
        att = _upload(client)
        resp = client.post(_base(f"/{att}/assess"), json={"adapter": "local_embedding"})
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "ADAPTER_NOT_AVAILABLE"

    def test_assess_unknown_photo_404(self, tmp_path):
        app, _pr, _ar = _build(tmp_path, ident_result=_ident_result([]))
        client = TestClient(app)
        _upload(client)
        resp = client.post(_base("/ghost/assess"), json={"adapter": "plantnet"})
        assert resp.status_code == 404

    def test_assess_invalid_adapter_422(self, tmp_path):
        app, _pr, _ar = _build(tmp_path, ident_result=_ident_result([]))
        client = TestClient(app)
        att = _upload(client)
        resp = client.post(_base(f"/{att}/assess"), json={"adapter": "bogus"})
        assert resp.status_code == 422

    def test_list_assessment_adapters(self, tmp_path):
        adapters = [
            {"key": "plantnet", "available": True, "external": True, "requires_consent": True},
            {"key": "local_embedding", "available": False, "external": False, "requires_consent": False},
        ]
        app, _pr, _ar = _build(tmp_path, ident_adapters=adapters)
        client = TestClient(app)
        resp = client.get(_base("/assess/adapters"))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        keys = {a["key"]: a for a in body["adapters"]}
        assert keys["plantnet"]["available"] is True
        assert keys["local_embedding"]["available"] is False

    def test_viewer_can_list_adapters(self, tmp_path):
        adapters = [{"key": "plantnet", "available": True, "external": True, "requires_consent": True}]
        app, _pr, _ar = _build(tmp_path, role=TenantRole.VIEWER, ident_adapters=adapters)
        client = TestClient(app)
        resp = client.get(_base("/assess/adapters"))
        assert resp.status_code == 200


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

    def test_viewer_cannot_edit_metadata(self, tmp_path):
        app, _pr, _ar = _build(tmp_path, role=TenantRole.VIEWER)
        client = TestClient(app)
        resp = client.patch(_base("/whatever"), json={"caption": "x"})
        assert resp.status_code == 403

    def test_viewer_cannot_assess(self, tmp_path):
        app, _pr, _ar = _build(tmp_path, role=TenantRole.VIEWER)
        client = TestClient(app)
        resp = client.post(_base("/whatever/assess"), json={"adapter": "plantnet"})
        assert resp.status_code == 403


@pytest.fixture(autouse=True)
def _restore_delay():
    import app.tasks.storage_tasks as storage_tasks

    original = storage_tasks.generate_thumbnails.delay
    yield
    storage_tasks.generate_thumbnails.delay = original
