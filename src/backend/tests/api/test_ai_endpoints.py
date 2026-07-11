"""REQ-031 §5 / §1.3 — API tests for the KI-Assistent three-stage toggle.

Builds a minimal app mounting the tenant + public KI routers with dependency
overrides, and asserts the 404 (stage 1) / 403 (stage 2) / 403 (stage 3) / 200
ladder plus the light-mode public ask.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from app.api.v1.auth.router import limiter
from app.api.v1.ki_assistent.public_router import router as public_router
from app.api.v1.ki_assistent.tenant_router import router as tenant_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_ai_assistant_service, get_tenant_repo
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import ConsentRequiredError, KamerplanterError
from app.config.settings import settings
from app.domain.models.ai_assistant import AiTipCard
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
    app.state.limiter = limiter
    app.include_router(tenant_router, prefix="/api/v1")
    app.include_router(public_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RateLimitExceeded, lambda r, e: None)  # type: ignore[arg-type]

    tenant_repo = MagicMock()
    tenant_repo.get_by_key.return_value = _tenant(tenant_ai_enabled)

    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_tenant_repo] = lambda: tenant_repo
    if service is not None:
        app.dependency_overrides[get_ai_assistant_service] = lambda: service
    return app


@pytest.fixture(autouse=True)
def _enable_flag(monkeypatch):
    """Default every test to stage-1 enabled; individual tests flip it off."""
    monkeypatch.setattr(settings, "ai_features_enabled", True)
    yield


def test_stage1_flag_off_returns_404(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_features_enabled", False)
    app = _build_app()
    client = TestClient(app)

    resp = client.get("/api/v1/ai/tips", params={"context_type": "planting_run", "context_key": "run-1"})
    assert resp.status_code == 404


def test_stage2_tenant_disabled_returns_403_marker() -> None:
    app = _build_app(tenant_ai_enabled=False)
    client = TestClient(app)

    resp = client.get("/api/v1/ai/tips", params={"context_type": "planting_run", "context_key": "run-1"})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "AI_DISABLED_FOR_TENANT"


def test_stage3_missing_consent_returns_403() -> None:
    service = MagicMock()
    service.get_tips.side_effect = ConsentRequiredError("ai_tenant_data_access")
    app = _build_app(service=service)
    client = TestClient(app)

    resp = client.get("/api/v1/ai/tips", params={"context_type": "planting_run", "context_key": "run-1"})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"


def test_tips_returns_ai_response_schema_with_consent() -> None:
    service = MagicMock()
    service.get_tips.return_value = [
        AiTipCard(
            tenant_key="home",
            context_type="planting_run",
            context_key="run-1",
            tip_type="care",
            priority="medium",
            title="Water in the morning",
            body="Water your tomato early to reduce fungal risk.",
            uses_tenant_data=True,
        )
    ]
    app = _build_app(service=service)
    client = TestClient(app)

    resp = client.get("/api/v1/ai/tips", params={"context_type": "planting_run", "context_key": "run-1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["tips"][0]["uses_tenant_data"] is True
    assert body["tips"][0]["title"] == "Water in the morning"


def test_public_ask_available_without_auth(monkeypatch) -> None:
    # The in-memory slowapi limiter spawns a background ``threading.Timer`` for
    # window expiry; disable it here so it does not leak a lingering thread.
    monkeypatch.setattr(limiter, "enabled", False)
    service = MagicMock()

    async def _ask(question, *, language="de"):  # noqa: ANN001, ARG001
        return SimpleNamespace(
            answer_text="VPD is the vapour pressure deficit.",
            sources=[],
            language="de",
            language_mismatch_warning=False,
            uses_tenant_data=False,
            uses_cloud_provider=False,
            confidence="high",
            model_name="gemma3:12b",
            provider_type="ollama",
            kb_version=None,
            generated_at=None,
        )

    service.ask_public = _ask
    app = _build_app(service=service)
    client = TestClient(app)

    resp = client.post("/api/v1/public/ai/ask", json={"question": "What is VPD?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["uses_tenant_data"] is False
    assert body["answer_text"].startswith("VPD")
