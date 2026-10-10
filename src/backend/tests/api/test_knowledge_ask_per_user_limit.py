"""#2110 class sweep — the knowledge question is an LLM call and carries a per-user limit.

Since #2175 the question lives at ``POST /api/v1/t/{tenant_slug}/ai/knowledge/ask``
behind the KI admission (toggle, consent, daily budget); the per-account minute
bound ``rate_limit_inference`` stays on top of it. Measured through the
production principal resolution: ``get_current_user`` runs for real (only the
auth provider is a fake), so the bucket key comes from the request state the
real dependency writes — and through the real ``get_ai_assistant_service``
provider, so the admission the limit sits on top of is the production one.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

import app.common.dependencies as deps
from app.api.v1.auth.router import limiter
from app.api.v1.ki_assistent.tenant_router import router as ai_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_auth_provider, get_tenant_repo
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.domain.interfaces.knowledge_service import AskResult
from app.domain.models.tenant import Tenant
from tests.api.test_ai_call_budget_routes import FakeValkey
from tests.api.test_expensive_routes_per_user_limit import TENANT_SLUG, _tenant, _TokenAuth
from tests.support.fake_consent_repo import GrantAllConsentRepo

ASK = f"/api/v1/t/{TENANT_SLUG}/ai/knowledge/ask"


@pytest.fixture
def wired(monkeypatch):
    from app.main import app as production_app

    monkeypatch.setattr(settings, "ai_features_enabled", True)
    # The daily budget is not the bound under test here.
    monkeypatch.setattr(settings, "ai_budget_user_calls_per_day", 0)
    monkeypatch.setattr(settings, "ai_budget_tenant_calls_per_day", 0)
    monkeypatch.setattr(settings, "ai_budget_tenant_tokens_per_day", 0)
    limiter.reset()

    knowledge = MagicMock()
    knowledge.ask = AsyncMock(return_value=AskResult(answer="a", model_name="m"))
    providers = MagicMock()
    providers.get_default.return_value = None
    providers.get_system_default.return_value = None  # platform model local: no cloud gate
    for name, value in {
        "get_knowledge_service_adapter": lambda: knowledge,
        "get_consent_repo": GrantAllConsentRepo,
        "get_ai_audit_repo": MagicMock,
        "get_ai_tip_cache_repo": MagicMock,
        "get_ai_conversation_repo": MagicMock,
        "get_ai_provider_repo": lambda: providers,
        "get_plant_repo": MagicMock,
        "get_planting_run_repo": MagicMock,
        "_get_redis_client": FakeValkey,
    }.items():
        monkeypatch.setattr(deps, name, value)

    tenant_repo = MagicMock()
    tenant_repo.get_by_key.return_value = Tenant(
        _key="tenant_anna",
        name="Anna",
        slug=TENANT_SLUG,
        owner_user_key="user_anna",
        settings={"ai_features_enabled": True},
    )

    app = FastAPI()
    app.include_router(ai_router, prefix="/api/v1/t/{tenant_slug}")
    app.state.limiter = limiter
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RateLimitExceeded, production_app.exception_handlers[RateLimitExceeded])
    app.dependency_overrides[get_auth_provider] = _TokenAuth
    app.dependency_overrides[get_current_tenant] = _tenant
    app.dependency_overrides[get_tenant_repo] = lambda: tenant_repo
    yield TestClient(app), knowledge
    limiter.reset()


def _ask(client: TestClient, token: str) -> int:
    return client.post(
        ASK,
        json={"question": "What is VPD?"},
        headers={"Authorization": f"Bearer {token}"},
    ).status_code


def test_the_call_past_the_per_minute_budget_is_refused_per_account(wired) -> None:
    client, knowledge = wired
    budget = int(settings.rate_limit_inference.split("/")[0])

    assert [_ask(client, "token-anna") for _ in range(budget)] == [200] * budget
    assert _ask(client, "token-anna") == 429
    assert knowledge.ask.await_count == budget
    # Another account behind the same address keeps its own budget.
    assert _ask(client, "token-ben") == 200
