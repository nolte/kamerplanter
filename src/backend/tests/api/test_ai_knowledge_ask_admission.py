"""#2175 — the free-form knowledge question is admitted like every other KI call.

``POST /api/v1/knowledge/ask`` answered any logged-in account with an LLM call:
no KI toggle, no consent, no daily budget, a viewer and a service account
included. It is now ``POST /api/v1/t/{tenant_slug}/ai/knowledge/ask`` on the
KI-Assistent tenant router, and the old path is gone.

Through the production wiring, like the #2174 ``wired_contribution`` fixture:
the service comes out of the real ``get_ai_assistant_service`` provider, the
consent check is the real :class:`ConsentGuard` over an in-memory consent store,
the budget the real :class:`AiCallBudget` over an in-memory Valkey. Only the
leaves are replaced. A provider that forgot the consent guard or the budget
makes the refusals here fail.

The witness of "no LLM call ran" is the adapter's ``ask`` mock — a refusal
answered after the call would still have spent it — and the Valkey counters for
"nothing was charged".
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

import app.common.dependencies as deps
from app.api.v1.auth.router import limiter
from app.api.v1.ki_assistent.tenant_router import router as ai_router
from app.api.v1.knowledge.router import router as knowledge_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_auth_provider, get_knowledge_client, get_tenant_repo
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.data_access.external.knowledge_service_adapter import KnowledgeServiceUnavailableError
from app.domain.guards.consent_guard import AI_CLOUD_PROCESSING, AI_TENANT_DATA_ACCESS
from app.domain.interfaces.knowledge_service import AskResult, KnowledgeChunk
from app.domain.models.ai_assistant import AiProviderConfig
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_context import TenantContext
from tests.api.test_ai_call_budget_routes import DownValkey, FakeValkey
from tests.api.test_expensive_routes_per_user_limit import _TokenAuth
from tests.support.fake_consent_repo import FakeConsentRepo

TENANT = "home"
USER = "anna"
ASK = f"/api/v1/t/{TENANT}/ai/knowledge/ask"
BODY = {
    "question": "Why are the lower leaves yellow?",
    "top_k": 3,
    "doc_language": "de",
    "prompt_language": "de",
    "context": {"species": "Solanum lycopersicum", "phase": "flowering", "ec": 2.1},
}


def _answer() -> AskResult:
    return AskResult(
        answer="Most likely a nitrogen deficiency.",
        question_type="diagnosis",
        model_name="qwen",
        sources=[
            KnowledgeChunk(
                source_key="guide:n",
                source_type="knowledge_guide",
                title="Nitrogen",
                content="Lower leaves yellow first.",
                score=0.91,
                metadata={"chapter": 3},
            )
        ],
        usage={"prompt_tokens": 1200, "completion_tokens": 300},
    )


def _tenant(*, ai_enabled: bool = True, allow_cloud: bool = False) -> Tenant:
    return Tenant(
        _key=TENANT,
        name="Home",
        slug=TENANT,
        owner_user_key=USER,
        settings={"ai_features_enabled": ai_enabled, "ai_allow_cloud_providers": allow_cloud},
    )


@pytest.fixture
def wired(monkeypatch):
    """The REAL ``get_ai_assistant_service`` provider, its storage swapped for doubles."""
    monkeypatch.setattr(settings, "ai_features_enabled", True)
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    limiter.reset()

    adapter = MagicMock()
    adapter.ask = AsyncMock(return_value=_answer())
    consent_repo = FakeConsentRepo()
    valkey = FakeValkey()
    audit_repo = MagicMock()
    audit_repo.create.side_effect = lambda entry: entry
    providers = MagicMock()
    providers.get_default.return_value = None  # local default — no cloud gate
    providers.list_for_tenant.return_value = []
    state = SimpleNamespace(role=TenantRole.GROWER, tenant=_tenant())

    for name, value in {
        "get_knowledge_service_adapter": lambda: adapter,
        "get_consent_repo": lambda: consent_repo,
        "get_ai_audit_repo": lambda: audit_repo,
        "get_ai_tip_cache_repo": MagicMock,
        "get_ai_conversation_repo": MagicMock,
        "get_ai_provider_repo": lambda: providers,
        "get_plant_repo": MagicMock,
        "get_planting_run_repo": MagicMock,
        "_get_redis_client": lambda: valkey,
    }.items():
        monkeypatch.setattr(deps, name, value)

    tenant_repo = MagicMock()
    tenant_repo.get_by_key.side_effect = lambda key: state.tenant

    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(ai_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    from app.main import app as production_app

    app.add_exception_handler(RateLimitExceeded, production_app.exception_handlers[RateLimitExceeded])
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT, tenant_slug=TENANT, user_key=USER, role=state.role
    )
    app.dependency_overrides[get_tenant_repo] = lambda: tenant_repo
    # No override for get_ai_assistant_service — the provider itself runs.
    yield SimpleNamespace(
        client=TestClient(app),
        adapter=adapter,
        consent_repo=consent_repo,
        valkey=valkey,
        audit_repo=audit_repo,
        providers=providers,
        state=state,
    )
    limiter.reset()


def _assert_nothing_spent(wired) -> None:
    wired.adapter.ask.assert_not_awaited()
    assert wired.valkey.values == {}, "a refused question was charged against the daily budget"


# ── refusals ────────────────────────────────────────────────────────


def test_a_viewer_is_refused_and_nothing_is_spent(wired):
    wired.consent_repo.set(USER, AI_TENANT_DATA_ACCESS, granted=True)
    wired.state.role = TenantRole.VIEWER

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"
    _assert_nothing_spent(wired)


def test_the_operator_flag_off_answers_404(wired, monkeypatch):
    """Stage 1 — the KI API looks non-existent (§1.3)."""
    wired.consent_repo.set(USER, AI_TENANT_DATA_ACCESS, granted=True)
    monkeypatch.setattr(settings, "ai_features_enabled", False)

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 404
    _assert_nothing_spent(wired)


def test_the_tenant_toggle_off_answers_403_disabled_for_tenant(wired):
    """Stage 2 — the garden has KI switched off."""
    wired.consent_repo.set(USER, AI_TENANT_DATA_ACCESS, granted=True)
    wired.state.tenant = _tenant(ai_enabled=False)

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "AI_DISABLED_FOR_TENANT"
    assert resp.json()["message"] == "ai.disabled_for_tenant"
    _assert_nothing_spent(wired)


@pytest.mark.parametrize("state", ["never_asked", "revoked"])
def test_without_consent_the_question_is_refused_before_the_llm(wired, state: str):
    """Stage 3 — the question and its plant context leave the installation."""
    if state == "revoked":
        wired.consent_repo.set(USER, AI_TENANT_DATA_ACCESS, granted=False)

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"
    assert (USER, AI_TENANT_DATA_ACCESS) in wired.consent_repo.reads
    _assert_nothing_spent(wired)


def test_a_question_without_context_needs_the_consent_too(wired):
    """No context is not a consent-free knowledge question here: the free text and
    the account still leave under a tenant. The consent-free path is the
    light-mode ``/public/ai/ask``."""
    resp = wired.client.post(ASK, json={"question": "What is VPD?"})

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"
    _assert_nothing_spent(wired)


def test_a_cloud_provider_additionally_needs_the_cloud_consent(wired):
    wired.consent_repo.set(USER, AI_TENANT_DATA_ACCESS, granted=True)
    wired.state.tenant = _tenant(allow_cloud=True)
    wired.providers.get_default.return_value = AiProviderConfig(
        _key="p-cloud", tenant_key=TENANT, provider_type="anthropic", display_name="Cloud", model_name="c"
    )

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"
    assert (USER, AI_CLOUD_PROCESSING) in wired.consent_repo.reads
    _assert_nothing_spent(wired)


def test_the_call_past_the_daily_budget_is_refused_before_the_llm(wired, monkeypatch):
    wired.consent_repo.set(USER, AI_TENANT_DATA_ACCESS, granted=True)
    monkeypatch.setattr(settings, "ai_budget_user_calls_per_day", 1)
    assert wired.client.post(ASK, json=BODY).status_code == 200

    refused = wired.client.post(ASK, json=BODY)

    assert refused.status_code == 429, refused.text
    assert refused.json()["error_code"] == "AI_BUDGET_EXCEEDED"
    assert refused.json()["details"][0]["code"] == "user_calls"
    assert 1 <= int(refused.headers["Retry-After"]) <= 86_400
    assert wired.adapter.ask.await_count == 1, "the refused call reached the LLM"


def test_a_valkey_outage_refuses_the_call_with_503(wired, monkeypatch):
    wired.consent_repo.set(USER, AI_TENANT_DATA_ACCESS, granted=True)
    monkeypatch.setattr(deps, "_get_redis_client", lambda: DownValkey())

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 503
    assert resp.json()["error_code"] == "AI_BUDGET_UNAVAILABLE"
    wired.adapter.ask.assert_not_awaited()


def test_in_light_mode_the_tenant_route_refuses_like_its_siblings(wired, monkeypatch):
    """REQ-027: light mode has no consent mechanism, so nobody holds
    ``ai_tenant_data_access`` and the tenant KI routes refuse; the light-mode
    knowledge question is ``POST /api/v1/public/ai/ask``."""
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"
    _assert_nothing_spent(wired)


# ── admitted ────────────────────────────────────────────────────────


def test_an_admitted_question_is_answered_and_charged_once(wired):
    wired.consent_repo.set(USER, AI_TENANT_DATA_ACCESS, granted=True)

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["answer"] == "Most likely a nitrogen deficiency."
    assert body["question_type"] == "diagnosis"
    assert body["model"] == "qwen"
    assert body["usage"] == {"prompt_tokens": 1200, "completion_tokens": 300}
    assert body["sources"][0]["content"] == "Lower leaves yellow first."
    assert body["sources"][0]["metadata"] == {"chapter": 3}

    wired.adapter.ask.assert_awaited_once()
    args, kwargs = wired.adapter.ask.await_args
    assert args == (BODY["question"],)
    assert kwargs["top_k"] == 3
    assert kwargs["doc_language"] == "de"
    assert kwargs["prompt_language"] == "de"
    assert kwargs["context"].to_ks_payload() == BODY["context"]

    calls = {k: v for k, v in wired.valkey.values.items() if ":calls:" in k}
    assert sorted(calls.values()) == [1, 1], calls  # one user + one tenant charge
    assert any(k.endswith(f":u:{USER}") for k in calls)
    tokens = [v for k, v in wired.valkey.values.items() if ":tokens:" in k]
    assert tokens == [1500]

    entry = wired.audit_repo.create.call_args.args[0]
    assert (entry.endpoint, entry.status, entry.user_key) == ("knowledge.ask", "ok", USER)
    assert entry.question_hash != BODY["question"]


def test_an_unreachable_knowledge_service_is_a_502_and_audited(wired):
    wired.consent_repo.set(USER, AI_TENANT_DATA_ACCESS, granted=True)
    wired.adapter.ask.side_effect = KnowledgeServiceUnavailableError("down")

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 502
    assert resp.json()["error_code"] == "EXTERNAL_SOURCE_ERROR"
    assert "down" not in resp.text
    entry = wired.audit_repo.create.call_args.args[0]
    assert entry.status == "knowledge_service_error"


# ── the old route ───────────────────────────────────────────────────


def test_the_tenantless_ask_route_is_gone_and_search_stays():
    knowledge = MagicMock()
    knowledge.search.return_value = {"query": "vpd", "results": [], "total": 0}
    app = FastAPI()
    app.include_router(knowledge_router, prefix="/api/v1")
    app.dependency_overrides[get_auth_provider] = _TokenAuth
    app.dependency_overrides[get_knowledge_client] = lambda: knowledge
    client = TestClient(app)
    headers = {"Authorization": "Bearer token-anna"}

    old = client.post("/api/v1/knowledge/ask", json={"question": "What is VPD?"}, headers=headers)
    search = client.get("/api/v1/knowledge/search", params={"q": "vpd"}, headers=headers)

    assert old.status_code in (404, 405)
    assert search.status_code == 200
    knowledge.ask.assert_not_called()


def test_the_production_app_serves_the_ask_only_under_the_tenant():
    """The OpenAPI document of the mounted app — not the router objects, whose
    nesting a flat scan of ``app.routes`` does not see."""
    from app.main import app as production_app

    paths = production_app.openapi()["paths"]
    assert "post" in paths["/api/v1/t/{tenant_slug}/ai/knowledge/ask"]
    assert not [p for p in paths if p.endswith("/knowledge/ask") and "/ai/" not in p]
