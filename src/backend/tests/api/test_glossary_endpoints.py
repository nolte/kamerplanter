"""REQ-035 §3 — API tests for the glossary endpoints.

Builds a minimal app mounting the tenant + public + admin glossary routers with
dependency overrides, and asserts the read/list responses, the invalid-slug 422
(§9), and the admin cache-invalidation surface.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from app.api.v1.auth.router import limiter
from app.api.v1.glossar.admin_router import router as admin_router
from app.api.v1.glossar.public_router import router as public_router
from app.api.v1.glossar.router import router as tenant_router
from app.common.auth import get_current_tenant, require_platform_admin
from app.common.dependencies import get_glossary_service, get_glossary_term_repo
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError, ValidationError
from app.config.settings import settings
from app.domain.models.glossary_term import (
    GlossaryTerm,
    GlossaryTermAnswer,
    GlossaryTermSummary,
)
from app.domain.models.tenant_context import TenantContext


@pytest.fixture(autouse=True)
def _enable_ai_flag(monkeypatch):
    """Stage-1 operator flag on by default; the kill-switch test flips it off."""
    monkeypatch.setattr(settings, "ai_features_enabled", True)
    yield


def _ctx() -> TenantContext:
    return TenantContext(tenant_key="home", tenant_slug="home", user_key="anna", role=TenantRole.GROWER)


def _answer(slug: str = "vpd", *, is_fallback: bool = False) -> GlossaryTermAnswer:
    return GlossaryTermAnswer(
        slug=slug,
        label="VPD",
        long_label="Vapor Pressure Deficit",
        category="umwelt",
        answer_text="VPD ist ...",
        expertise_level="beginner",
        language="de",
        is_fallback=is_fallback,
    )


def _build_app(service: MagicMock) -> FastAPI:
    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(tenant_router, prefix="/api/v1/t/{tenant_slug}")
    app.include_router(public_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RateLimitExceeded, lambda r, e: None)  # type: ignore[arg-type]

    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[require_platform_admin] = lambda: SimpleAdmin()
    app.dependency_overrides[get_glossary_service] = lambda: service
    return app


class SimpleAdmin:
    user_key = "root"


@pytest.fixture
def service() -> MagicMock:
    svc = MagicMock()
    svc.list_terms.return_value = [GlossaryTermSummary(slug="vpd", label="VPD", category="umwelt")]
    svc.get_term = AsyncMock(return_value=_answer())
    svc.invalidate_cache.return_value = 3
    return svc


# ── Tenant path ────────────────────────────────────────────────────


def test_tenant_list_terms(service) -> None:
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/t/home/glossary/terms", params={"language": "de"})
    assert resp.status_code == 200
    assert resp.json()[0]["slug"] == "vpd"


def test_tenant_get_term(service) -> None:
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/t/home/glossary/term/vpd", params={"expertise": "beginner"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["slug"] == "vpd"
    assert body["is_fallback"] is False
    # The tenant path forwards the tenant context (cloud gate), context stays null.
    assert service.get_term.await_args.kwargs["tenant_key"] == "home"


def test_tenant_get_term_invalid_expertise_returns_422(service) -> None:
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/t/home/glossary/term/vpd", params={"expertise": "guru"})
    assert resp.status_code == 422  # Literal query-param validation (§9)


def test_tenant_get_term_service_validation_error_maps_422(service) -> None:
    service.get_term = AsyncMock(side_effect=ValidationError("bad slug"))
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/t/home/glossary/term/vpd")
    assert resp.status_code == 422


# ── Public / light-mode path ───────────────────────────────────────


def test_public_get_term(service, monkeypatch) -> None:
    # The in-memory slowapi limiter spawns a background ``threading.Timer``; the
    # HA thread checker flags it as lingering, so disable rate limiting here.
    monkeypatch.setattr(limiter, "enabled", False)
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/public/glossary/term/vpd")
    assert resp.status_code == 200
    # Public path passes neither tenant nor user (local provider only, §6).
    assert "tenant_key" not in service.get_term.await_args.kwargs


def test_public_list_terms(service, monkeypatch) -> None:
    monkeypatch.setattr(limiter, "enabled", False)
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/public/glossary/terms")
    assert resp.status_code == 200
    assert resp.json()[0]["category"] == "umwelt"


# ── Stage-1 operator kill-switch (SEC-G2) ──────────────────────────


def test_public_term_flag_off_returns_404(service, monkeypatch) -> None:
    monkeypatch.setattr(limiter, "enabled", False)
    monkeypatch.setattr(settings, "ai_features_enabled", False)
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/public/glossary/term/vpd")
    assert resp.status_code == 404
    service.get_term.assert_not_awaited()


def test_public_terms_flag_off_returns_404(service, monkeypatch) -> None:
    monkeypatch.setattr(limiter, "enabled", False)
    monkeypatch.setattr(settings, "ai_features_enabled", False)
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/public/glossary/terms")
    assert resp.status_code == 404
    service.list_terms.assert_not_called()


def test_tenant_term_flag_off_returns_404(service, monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_features_enabled", False)
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/t/home/glossary/term/vpd")
    assert resp.status_code == 404
    service.get_term.assert_not_awaited()


def test_tenant_terms_flag_off_returns_404(service, monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_features_enabled", False)
    client = TestClient(_build_app(service))
    resp = client.get("/api/v1/t/home/glossary/terms")
    assert resp.status_code == 404
    service.list_terms.assert_not_called()


# ── Admin path ─────────────────────────────────────────────────────


def test_admin_invalidate_all(service) -> None:
    client = TestClient(_build_app(service))
    resp = client.post("/api/v1/admin/glossary/cache/invalidate-all")
    assert resp.status_code == 200
    assert resp.json()["removed"] == 3
    service.invalidate_cache.assert_called_with(None)


def test_admin_invalidate_slug(service) -> None:
    client = TestClient(_build_app(service))
    resp = client.post("/api/v1/admin/glossary/term/vpd/cache/invalidate")
    assert resp.status_code == 200
    service.invalidate_cache.assert_called_with("vpd")


def test_admin_list_terms(service) -> None:
    app = _build_app(service)
    repo = MagicMock()
    repo.list_all_including_inactive.return_value = [GlossaryTerm(slug="vpd", labels={"de": "VPD"}, is_active=False)]
    app.dependency_overrides[get_glossary_term_repo] = lambda: repo
    client = TestClient(app)
    resp = client.get("/api/v1/admin/glossary/terms")
    assert resp.status_code == 200
    assert resp.json()[0]["is_active"] is False
