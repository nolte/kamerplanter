"""API tests for the REQ-029 recognition routers (status + tenant-scoped)."""

import io
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from PIL import Image

from app.api.v1.recognition import tenant_router as tenant_recognition_module
from app.api.v1.recognition.router import router as recognition_router
from app.api.v1.recognition.tenant_router import router as tenant_recognition_router
from app.common import dependencies
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
from app.data_access.external import inference_service_client
from app.domain.engines.consent_engine import REFERENCE_CONTRIBUTION
from app.domain.models.tenant_context import TenantContext
from tests.support.fake_consent_repo import FakeConsentRepo
from tests.support.fake_contribution_marker import FakeContributionMarker
from tests.support.fake_species_repo import FakeSpeciesRepo

TENANT_SLUG = "anna"


def _tenant_ctx(role: TenantRole = TenantRole.LEAD) -> TenantContext:
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


def _build_app(service, reference_service=None, role: TenantRole = TenantRole.LEAD):
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


# ── #2174 — the interactive contribution reads the reference_contribution opt-in ──


class _CountingRedis:
    """Dict-backed stand-in for the quota counter, so a consumed quota is visible."""

    def __init__(self) -> None:
        self.counters: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    def expire(self, key: str, seconds: int) -> bool:
        return True

    def ttl(self, key: str) -> int:
        return 60


@pytest.fixture
def wired_contribution(monkeypatch):
    """The REAL ``get_reference_image_service`` provider, its storage swapped for doubles.

    The consent check lives in the service and its collaborators come from the
    provider — so this exercises the wiring in ``dependencies.py`` too: a
    provider that forgot the consent repo makes every case here fail.
    """
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    monkeypatch.setattr(settings, "reference_image_use_wikimedia", False)

    consent_repo = FakeConsentRepo()
    marker = FakeContributionMarker()
    redis = _CountingRedis()
    species_repo = FakeSpeciesRepo()
    species_repo.add("species_monstera", "Monstera deliciosa")  # global (tenant_key="")
    species_repo.add("species_ben_private", "Philodendron privatum", tenant_key="tenant_ben")
    inference = MagicMock()
    inference.embed.return_value = [0.1] * 4
    inference.upsert_reference.return_value = {"status": "ok", "dim": 4}

    monkeypatch.setattr(dependencies, "get_consent_repo", lambda: consent_repo)
    monkeypatch.setattr(dependencies, "get_system_settings_repo", lambda: marker)
    monkeypatch.setattr(dependencies, "_get_redis_client", lambda: redis)
    monkeypatch.setattr(dependencies, "get_species_repo", lambda: species_repo)
    monkeypatch.setattr(dependencies, "get_identification_repo", MagicMock)
    monkeypatch.setattr(dependencies, "get_reference_image_repo", MagicMock)
    monkeypatch.setattr(inference_service_client, "InferenceServiceClient", lambda *a, **k: inference)

    app = FastAPI()
    app.include_router(tenant_recognition_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _app_error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: _tenant_ctx(TenantRole.GROWER)
    # No override for get_reference_image_service — the provider itself runs.
    return SimpleNamespace(
        client=TestClient(app),
        consent_repo=consent_repo,
        marker=marker,
        redis=redis,
        species_repo=species_repo,
        inference=inference,
    )


def _contribute(client: TestClient, species_key: str = "species_monstera"):
    return client.post(
        f"/api/v1/t/{TENANT_SLUG}/identification/reference",
        files=_real_jpeg_upload(),
        data={"species_key": species_key},
    )


def _assert_nothing_contributed(wired) -> None:
    assert wired.redis.counters == {}
    assert wired.marker.writes == 0
    assert wired.species_repo.lookups == []
    wired.inference.embed.assert_not_called()
    wired.inference.upsert_reference.assert_not_called()


def test_contribute_reference_without_consent_returns_403_and_contributes_nothing(wired_contribution):
    resp = _contribute(wired_contribution.client)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"
    assert wired_contribution.consent_repo.reads == [("user_anna", REFERENCE_CONTRIBUTION)]
    _assert_nothing_contributed(wired_contribution)


def test_contribute_reference_with_consent_returns_202(wired_contribution):
    wired_contribution.consent_repo.set("user_anna", REFERENCE_CONTRIBUTION, granted=True)

    resp = _contribute(wired_contribution.client)

    assert resp.status_code == 202
    assert resp.json()["pending_review"] is True
    assert wired_contribution.redis.counters == {"ident_ratelimit:contribute:user_anna": 1}
    assert wired_contribution.marker.writes == 1
    wired_contribution.inference.upsert_reference.assert_called_once()


def test_contribute_reference_with_revoked_consent_returns_403(wired_contribution):
    wired_contribution.consent_repo.set("user_anna", REFERENCE_CONTRIBUTION, granted=False)

    resp = _contribute(wired_contribution.client)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"
    _assert_nothing_contributed(wired_contribution)


def test_contribute_reference_in_light_mode_returns_409_even_with_consent(wired_contribution, monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    wired_contribution.consent_repo.set("user_anna", REFERENCE_CONTRIBUTION, granted=True)

    resp = _contribute(wired_contribution.client)

    assert resp.status_code == 409
    assert resp.json()["error_code"] == "ADAPTER_NOT_AVAILABLE"
    _assert_nothing_contributed(wired_contribution)


def test_contribute_reference_to_another_tenants_private_species_returns_404(wired_contribution):
    """A grower with consent in tenant_anna cannot reach tenant_ben's private species.

    Same answer as an unknown key — neither a contribution nor an existence
    oracle (404 vs 202) for another tenant's catalogue.
    """
    wired_contribution.consent_repo.set("user_anna", REFERENCE_CONTRIBUTION, granted=True)

    foreign = _contribute(wired_contribution.client, "species_ben_private")
    unknown = _contribute(wired_contribution.client, "species_ghost")

    assert foreign.status_code == 404
    assert foreign.json()["error_code"] == unknown.json()["error_code"]
    assert unknown.status_code == 404
    assert wired_contribution.redis.counters == {}
    assert wired_contribution.marker.writes == 0
    wired_contribution.inference.embed.assert_not_called()
    wired_contribution.inference.upsert_reference.assert_not_called()
