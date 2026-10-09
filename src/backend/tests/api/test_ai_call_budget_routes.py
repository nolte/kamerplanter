"""#2110 (MT-013) — every KI route that calls an LLM charges the daily AI budget.

Through the production wiring: the service comes out of the real provider
functions in ``app.common.dependencies`` (``get_ai_assistant_service``,
``get_glossary_service``, ``get_diagnose_service``) — only their leaves are
replaced (knowledge-service adapter, repositories, Valkey client). A test that
built the service itself would prove a budget the production path might never
wire; the shape of this defect is a guard that exists and is not reached.

The witness of "no LLM call ran" is the adapter's ``ask`` mock, not the status
code alone: a 429 after the call would still spend the money.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

import app.common.dependencies as deps
from app.api.v1.auth.router import limiter
from app.api.v1.diagnose.tenant_router import router as diagnosis_router
from app.api.v1.glossar.router import router as glossary_router
from app.api.v1.ki_assistent.tenant_router import router as ai_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_tenant_repo
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.domain.interfaces.knowledge_service import AskResult, KnowledgeChunk
from app.domain.models.ai_assistant import AiConversation
from app.domain.models.glossary_term import GlossaryTerm
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_context import TenantContext

TENANT = "home"


class FakeValkey:
    """The four commands the budget uses, in process memory."""

    def __init__(self) -> None:
        self.values: dict[str, int] = {}

    def get(self, key: str) -> str | None:
        return str(self.values[key]) if key in self.values else None

    def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    def incrby(self, key: str, amount: int) -> int:
        self.values[key] = self.values.get(key, 0) + amount
        return self.values[key]

    def expire(self, key: str, seconds: int) -> bool:
        return True

    # The glossary hot cache shares the client.
    def set(self, *args, **kwargs) -> None:
        return None


class DownValkey(FakeValkey):
    def get(self, key: str) -> str | None:
        raise ConnectionError("valkey down")

    def incr(self, key: str) -> int:
        raise ConnectionError("valkey down")


_USER = {"value": "anna"}


def _ctx() -> TenantContext:
    return TenantContext(tenant_key=TENANT, tenant_slug=TENANT, user_key=_USER["value"], role=TenantRole.GROWER)


def _answer() -> AskResult:
    return AskResult(
        answer="Because the substrate is dry.",
        model_name="m",
        sources=[KnowledgeChunk(source_key="k", source_type="rag", title="t", score=0.9, language="de")],
        usage={"prompt_tokens": 1200, "completion_tokens": 300},
    )


@pytest.fixture
def adapter() -> MagicMock:
    knowledge = MagicMock()
    knowledge.ask = AsyncMock(return_value=_answer())
    return knowledge


@pytest.fixture
def valkey() -> FakeValkey:
    return FakeValkey()


@pytest.fixture
def client(monkeypatch, adapter: MagicMock, valkey: FakeValkey) -> TestClient:
    monkeypatch.setattr(settings, "ai_features_enabled", True)
    _USER["value"] = "anna"

    consent = MagicMock()
    consent.require_consent.return_value = None
    providers = MagicMock()
    providers.get_default.return_value = None  # local default, no cloud gate
    providers.list_for_tenant.return_value = []
    conversations = MagicMock()
    conversations.get_by_key.side_effect = lambda key: AiConversation(
        _key=key, tenant_key=TENANT, user_key=_USER["value"], context_type="general"
    )
    tip_cache = MagicMock()
    tip_cache.find_valid.return_value = []
    tip_cache.create.side_effect = lambda card: card
    term = GlossaryTerm(
        slug="vpd",
        labels={"de": "VPD", "en": "VPD"},
        fallback_text={"de": "Dampfdruckdefizit.", "en": "Vapour pressure deficit."},
    )
    term_repo = MagicMock()
    term_repo.resolve_slug.return_value = "vpd"
    term_repo.get_by_slug.return_value = term
    glossary_cache = MagicMock()
    glossary_cache.find_valid.return_value = None
    glossary_cache.upsert.side_effect = lambda entry: entry

    for name, value in {
        "get_knowledge_service_adapter": lambda: adapter,
        "get_ai_consent_guard": lambda: consent,
        "get_ai_audit_logger": lambda: MagicMock(),
        "get_ai_tip_cache_repo": lambda: tip_cache,
        "get_ai_conversation_repo": lambda: conversations,
        "get_ai_provider_repo": lambda: providers,
        "get_plant_repo": lambda: MagicMock(),
        "get_planting_run_repo": lambda: MagicMock(),
        "get_glossary_term_repo": lambda: term_repo,
        "get_glossary_cache_repo": lambda: glossary_cache,
        "_get_redis_client": lambda: valkey,
    }.items():
        monkeypatch.setattr(deps, name, value)

    app = FastAPI()
    app.state.limiter = limiter
    for router in (ai_router, glossary_router, diagnosis_router):
        app.include_router(router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    from app.main import app as production_app

    app.add_exception_handler(RateLimitExceeded, production_app.exception_handlers[RateLimitExceeded])

    tenant_repo = MagicMock()
    tenant_repo.get_by_key.return_value = Tenant(
        _key=TENANT,
        name="Home",
        slug=TENANT,
        owner_user_key="anna",
        settings={"ai_features_enabled": True},
    )
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_tenant_repo] = lambda: tenant_repo
    return TestClient(app)


def _explain(client: TestClient):
    return client.post(
        f"/api/v1/t/{TENANT}/ai/explain",
        json={"subject_type": "reminder", "subject_key": "r-1", "question_template_id": "care_reminder_watering"},
    )


def _tips(client: TestClient):
    return client.post(
        f"/api/v1/t/{TENANT}/ai/tips/refresh", params={"context_type": "general", "context_key": "garden"}
    )


def _daily(client: TestClient):
    return client.post(f"/api/v1/t/{TENANT}/ai/daily-tip/refresh")


def _chat(client: TestClient):
    return client.post(f"/api/v1/t/{TENANT}/ai/conversations/conv-1/messages", json={"message": "Why?"})


def _glossary(client: TestClient):
    return client.post(f"/api/v1/t/{TENANT}/glossary/term/vpd/generate")


def _knowledge(client: TestClient):
    """#2175 — the free-form knowledge question, formerly the ungated ``/api/v1/knowledge/ask``."""
    return client.post(f"/api/v1/t/{TENANT}/ai/knowledge/ask", json={"question": "What is VPD?"})


_GENERATING = {
    "explain": _explain,
    "tips": _tips,
    "daily": _daily,
    "chat": _chat,
    "glossary": _glossary,
    "knowledge": _knowledge,
}


@pytest.mark.parametrize("route", sorted(_GENERATING))
def test_the_call_past_the_users_daily_budget_is_refused_before_the_llm(
    route: str, client: TestClient, adapter: MagicMock, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "ai_budget_user_calls_per_day", 2)
    call = _GENERATING[route]

    # Two different glossary terms / days are not needed: the budget counts
    # calls, and the second call of every route reaches the LLM again (the
    # caches above answer "miss").
    for _ in range(2):
        assert call(client).status_code == 200
    calls_before = adapter.ask.await_count

    refused = call(client)

    assert refused.status_code == 429, refused.text
    assert refused.json()["error_code"] == "AI_BUDGET_EXCEEDED"
    assert refused.json()["details"][0]["code"] == "user_calls"
    assert 1 <= int(refused.headers["Retry-After"]) <= 86_400
    assert adapter.ask.await_count == calls_before, "the refused call reached the LLM"


def test_the_51st_call_of_a_day_is_refused_at_the_default_budget(client: TestClient, adapter: MagicMock) -> None:
    assert settings.ai_budget_user_calls_per_day == 50

    statuses = []
    for call in range(50):
        # 50 calls inside one test minute would trip the per-minute route limit
        # (``rate_limit_inference``) first; clearing it every 20 calls keeps the
        # daily budget the only bound this test measures.
        if call % 20 == 0:
            limiter.reset()
        statuses.append(_explain(client).status_code)
    assert statuses == [200] * 50
    limiter.reset()

    refused = _explain(client)
    assert refused.status_code == 429
    assert refused.json()["error_code"] == "AI_BUDGET_EXCEEDED"
    assert adapter.ask.await_count == 50


def test_a_valkey_outage_refuses_the_call_with_503(monkeypatch, client: TestClient, adapter: MagicMock) -> None:
    monkeypatch.setattr(deps, "_get_redis_client", lambda: DownValkey())

    resp = _explain(client)

    assert resp.status_code == 503
    assert resp.json()["error_code"] == "AI_BUDGET_UNAVAILABLE"
    adapter.ask.assert_not_awaited()


def test_a_refused_chat_message_is_an_http_429_not_a_broken_stream(
    client: TestClient, adapter: MagicMock, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "ai_budget_user_calls_per_day", 1)
    assert _chat(client).status_code == 200

    refused = _chat(client)

    assert refused.status_code == 429
    assert refused.headers["content-type"].startswith("application/json")
    assert adapter.ask.await_count == 1


def test_the_tenant_budget_is_shared_by_its_members(client: TestClient, adapter: MagicMock, monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_budget_tenant_calls_per_day", 3)
    for user in ("anna", "ben", "cleo"):
        _USER["value"] = user
        assert _explain(client).status_code == 200

    _USER["value"] = "dora"
    refused = _explain(client)

    assert refused.status_code == 429
    assert refused.json()["details"][0]["code"] == "tenant_calls"
    assert adapter.ask.await_count == 3


def test_a_member_past_the_personal_budget_does_not_use_up_the_tenants(
    client: TestClient, valkey: FakeValkey, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "ai_budget_user_calls_per_day", 1)
    monkeypatch.setattr(settings, "ai_budget_tenant_calls_per_day", 3)
    assert _explain(client).status_code == 200
    for _ in range(5):
        assert _explain(client).status_code == 429

    _USER["value"] = "ben"
    assert _explain(client).status_code == 200


def test_the_tokens_of_an_answer_count_against_the_tenants_token_budget(
    client: TestClient, adapter: MagicMock, monkeypatch
) -> None:
    # One answer reports 1 500 tokens (1 200 prompt + 300 completion).
    monkeypatch.setattr(settings, "ai_budget_tenant_tokens_per_day", 3000)
    assert _explain(client).status_code == 200
    assert _explain(client).status_code == 200

    refused = _explain(client)

    assert refused.status_code == 429
    assert refused.json()["details"][0]["code"] == "tenant_tokens"
    assert adapter.ask.await_count == 2


def test_the_cost_of_a_tenant_is_countable(client: TestClient) -> None:
    for _ in range(2):
        assert _explain(client).status_code == 200

    usage = deps.get_ai_call_budget().usage(TENANT)

    assert usage.day == datetime.now(UTC).date().isoformat()
    assert (usage.calls, usage.tokens) == (2, 3000)


def test_the_ki_diagnosis_charges_the_budget(client: TestClient, monkeypatch) -> None:
    """REQ-036 — the structured diagnosis is an LLM call like the others (#2110 class sweep)."""
    from app.domain.engines.diagnosis_analysis_engine import DiagnosisAnalysisEngine

    monkeypatch.setattr(settings, "ai_budget_user_calls_per_day", 1)
    analyze = AsyncMock(return_value=([], _answer()))
    monkeypatch.setattr(DiagnosisAnalysisEngine, "analyze", analyze)
    for name in ("get_ipm_repo", "get_species_repo", "get_ai_context_builder"):
        monkeypatch.setattr(deps, name, lambda: MagicMock())

    body = {"symptom_slugs": ["yellow-leaves"], "language": "de"}
    first = client.post(f"/api/v1/t/{TENANT}/diagnosis/analyze", json=body)
    second = client.post(f"/api/v1/t/{TENANT}/diagnosis/analyze", json=body)

    assert first.status_code == 200, first.text
    assert second.status_code == 429, second.text
    assert second.json()["error_code"] == "AI_BUDGET_EXCEEDED"
    assert analyze.await_count == 1
