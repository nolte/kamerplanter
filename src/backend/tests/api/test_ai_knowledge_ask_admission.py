"""#2175 — the free-form knowledge question is admitted like every other KI call.

``POST /api/v1/knowledge/ask`` answered any logged-in account with an LLM call:
no KI toggle, no consent, no daily budget, a viewer and a service account
included. It is now ``POST /api/v1/t/{tenant_slug}/ai/knowledge/ask`` on the
KI-Assistent tenant router, and the old path is gone.

The consent is the question's own purpose ``ai_knowledge_question`` (operator
decision 2026-10-09), not a re-worded ``ai_tenant_data_access``: a question that
carries plant ``context`` additionally needs ``ai_tenant_data_access``, so tenant
data never leaves under the question-only consent.

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
from app.domain.guards.consent_guard import AI_CLOUD_PROCESSING, AI_KNOWLEDGE_QUESTION, AI_TENANT_DATA_ACCESS
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
    providers.get_system_default.return_value = None  # no platform provider — labelled local
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


def _grant(wired, *purposes: str) -> None:
    for purpose in purposes:
        wired.consent_repo.set(USER, purpose, granted=True)


def _admit(wired) -> None:
    """Both consents a question with plant context needs."""
    _grant(wired, AI_KNOWLEDGE_QUESTION, AI_TENANT_DATA_ACCESS)


def _assert_nothing_spent(wired) -> None:
    wired.adapter.ask.assert_not_awaited()
    assert wired.valkey.values == {}, "a refused question was charged against the daily budget"


# ── refusals ────────────────────────────────────────────────────────


def test_a_viewer_is_refused_and_nothing_is_spent(wired):
    _admit(wired)
    wired.state.role = TenantRole.VIEWER

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"
    _assert_nothing_spent(wired)


def test_the_operator_flag_off_answers_404(wired, monkeypatch):
    """Stage 1 — the KI API looks non-existent (§1.3)."""
    _admit(wired)
    monkeypatch.setattr(settings, "ai_features_enabled", False)

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 404
    _assert_nothing_spent(wired)


def test_the_tenant_toggle_off_answers_403_disabled_for_tenant(wired):
    """Stage 2 — the garden has KI switched off."""
    _admit(wired)
    wired.state.tenant = _tenant(ai_enabled=False)

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "AI_DISABLED_FOR_TENANT"
    assert resp.json()["message"] == "ai.disabled_for_tenant"
    _assert_nothing_spent(wired)


QUESTION_ONLY = {"question": "What is VPD?"}


@pytest.mark.parametrize("state", ["never_asked", "revoked"])
@pytest.mark.parametrize("body", [BODY, QUESTION_ONLY], ids=["with_context", "question_only"])
def test_without_the_question_consent_nothing_reaches_the_llm(wired, state: str, body: dict):
    """Stage 3 — the free text leaves the installation under a tenant and an account.

    ``ai_tenant_data_access`` granted does not stand in for it: that consent
    covers plant values, not the question.
    """
    _grant(wired, AI_TENANT_DATA_ACCESS)
    if state == "revoked":
        wired.consent_repo.set(USER, AI_KNOWLEDGE_QUESTION, granted=False)

    resp = wired.client.post(ASK, json=body)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"
    assert resp.json()["details"][0]["purpose"] == AI_KNOWLEDGE_QUESTION
    assert resp.json()["details"][0]["field"] == "consent"  # unchanged, the purpose is additive
    assert (USER, AI_KNOWLEDGE_QUESTION) in wired.consent_repo.reads
    _assert_nothing_spent(wired)


def test_a_question_without_context_needs_only_the_question_consent(wired):
    """No plant value leaves, so ``ai_tenant_data_access`` is neither needed nor asked."""
    _grant(wired, AI_KNOWLEDGE_QUESTION)

    resp = wired.client.post(ASK, json=QUESTION_ONLY)

    assert resp.status_code == 200, resp.text
    assert wired.adapter.ask.await_args.kwargs["context"] is None
    assert (USER, AI_TENANT_DATA_ACCESS) not in wired.consent_repo.reads
    assert wired.audit_repo.create.call_args.args[0].uses_tenant_data is False


@pytest.mark.parametrize("state", ["never_asked", "revoked"])
def test_plant_context_never_leaves_under_the_question_consent_alone(wired, state: str):
    """Tenant data needs ``ai_tenant_data_access`` on top — refused before the LLM."""
    _grant(wired, AI_KNOWLEDGE_QUESTION)
    if state == "revoked":
        wired.consent_repo.set(USER, AI_TENANT_DATA_ACCESS, granted=False)

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"
    assert resp.json()["details"][0]["purpose"] == AI_TENANT_DATA_ACCESS
    assert (USER, AI_TENANT_DATA_ACCESS) in wired.consent_repo.reads
    _assert_nothing_spent(wired)


@pytest.mark.parametrize(
    ("field", "value"),
    [("species", "Ocimum basilicum"), ("phase", "seedling"), ("substrate", "coco"), ("ec", 0.0), ("ph", 6.2)],
)
def test_a_single_plant_value_is_plant_context(wired, field: str, value):
    """Any one value counts — not only a full context; ``ec: 0`` is a value too."""
    _grant(wired, AI_KNOWLEDGE_QUESTION)

    resp = wired.client.post(ASK, json={**QUESTION_ONLY, "context": {field: value}})

    assert resp.status_code == 403
    assert resp.json()["details"][0]["purpose"] == AI_TENANT_DATA_ACCESS
    _assert_nothing_spent(wired)


def test_a_cloud_provider_additionally_needs_the_cloud_consent(wired):
    _admit(wired)
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
    _admit(wired)
    monkeypatch.setattr(settings, "ai_budget_user_calls_per_day", 1)
    assert wired.client.post(ASK, json=BODY).status_code == 200

    refused = wired.client.post(ASK, json=BODY)

    assert refused.status_code == 429, refused.text
    assert refused.json()["error_code"] == "AI_BUDGET_EXCEEDED"
    assert refused.json()["details"][0]["code"] == "user_calls"
    assert 1 <= int(refused.headers["Retry-After"]) <= 86_400
    assert wired.adapter.ask.await_count == 1, "the refused call reached the LLM"


def test_a_valkey_outage_refuses_the_call_with_503(wired, monkeypatch):
    _admit(wired)
    monkeypatch.setattr(deps, "_get_redis_client", lambda: DownValkey())

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 503
    assert resp.json()["error_code"] == "AI_BUDGET_UNAVAILABLE"
    wired.adapter.ask.assert_not_awaited()


def test_light_mode_grants_no_exemption_from_the_consent(wired, monkeypatch):
    """The mode flag does not switch the consent check off.

    What this pins, and only this: with ``KAMERPLANTER_MODE=light`` and no consent
    record the route still refuses before the LLM — a light-mode shortcut around
    ``ai_knowledge_question`` (as REQ-027 grants elsewhere) would fail here while
    ``test_without_the_question_consent…[never_asked]`` stayed green.

    Not measured here: that a light-mode installation *cannot* obtain the consent.
    That follows from the mounting — the privacy router, through which consents
    are granted, is included only when ``kamerplanter_mode == "full"``
    (``app/api/v1/router.py``) — and is fixed at import time, so this test (whose
    tenant context is an override, not the light-mode principal) does not drive it.
    The light-mode knowledge question is ``POST /api/v1/public/ai/ask``.
    """
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")

    resp = wired.client.post(ASK, json=QUESTION_ONLY)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "CONSENT_REQUIRED"
    _assert_nothing_spent(wired)


# ── bounded input ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("species", "x" * 10_000),
        ("phase", "x" * 10_000),
        ("substrate", "x" * 10_000),
        ("ec", 1e9),
        ("ec", -1),
        ("ph", 15),
        ("ph", -0.1),
    ],
    ids=["species-10k", "phase-10k", "substrate-10k", "ec-huge", "ec-negative", "ph-15", "ph-negative"],
)
def test_an_unbounded_context_value_is_refused_before_the_llm(wired, field: str, value):
    """SEC-002: the 2 000-character bound on the question must not be bypassable
    through the context, which ends up in the same prompt."""
    _admit(wired)

    resp = wired.client.post(ASK, json={**BODY, "context": {field: value}})

    assert resp.status_code == 422, resp.text
    _assert_nothing_spent(wired)


def test_a_realistic_context_is_accepted(wired):
    """The control: the longest seeded scientific name is under 80 characters."""
    _admit(wired)
    context = {"species": "x" * 100, "phase": "flowering", "substrate": "coco", "ec": 20, "ph": 14}

    assert wired.client.post(ASK, json={**BODY, "context": context}).status_code == 200


@pytest.mark.parametrize(("top_k", "status"), [(10, 200), (11, 422)])
def test_top_k_is_bounded_like_the_sibling_routes(wired, top_k: int, status: int):
    _admit(wired)

    assert wired.client.post(ASK, json={**BODY, "top_k": top_k}).status_code == status


def test_an_empty_context_is_no_tenant_data(wired):
    """I-3: ``context: {}`` carries no plant value — it is sent as no context,
    audited as ``uses_tenant_data=False`` and needs only the question consent."""
    _grant(wired, AI_KNOWLEDGE_QUESTION)

    resp = wired.client.post(ASK, json={"question": "What is VPD?", "context": {}})

    assert resp.status_code == 200, resp.text
    assert wired.adapter.ask.await_args.kwargs["context"] is None
    assert wired.audit_repo.create.call_args.args[0].uses_tenant_data is False


# ── admitted ────────────────────────────────────────────────────────


def test_an_admitted_question_is_answered_and_charged_once(wired):
    _admit(wired)

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
    # No platform provider: the answer is labelled local Ollama.
    assert (body["provider_type"], body["uses_cloud_provider"]) == ("ollama", False)


@pytest.mark.parametrize(
    ("provider_type", "requires_consent", "uses_cloud"),
    [("anthropic", False, True), ("ollama", True, True), ("ollama", False, False)],
)
def test_the_answer_carries_the_platform_cloud_label(wired, provider_type, requires_consent, uses_cloud):
    """The Knowledge Service answers with its own model, so the label is the
    platform's system default provider — the glossary rule (REQ-035 §6) — not
    the asking tenant's records, which stay local here."""
    _admit(wired)
    wired.providers.get_system_default.return_value = AiProviderConfig(
        _key="p-system",
        tenant_key=None,
        provider_type=provider_type,
        display_name="Platform",
        model_name="m",
        requires_consent=requires_consent,
    )

    resp = wired.client.post(ASK, json=BODY)

    assert resp.status_code == 200, resp.text
    assert resp.json()["provider_type"] == provider_type
    assert resp.json()["uses_cloud_provider"] is uses_cloud


def test_an_unreachable_knowledge_service_is_a_502_and_audited(wired):
    _admit(wired)
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


def test_the_production_app_mounts_the_tenant_ask():
    """The OpenAPI document of the mounted app — not the router objects, whose
    nesting a flat scan of ``app.routes`` does not see.

    No negative assertion on ``/api/v1/knowledge/ask`` here: under the test
    defaults ``KNOWLEDGE_SERVICE_ENABLED`` is off, so the knowledge router is not
    mounted in this app and its absence would prove nothing. The router itself is
    driven in ``test_the_tenantless_ask_route_is_gone_and_search_stays``.
    """
    from app.main import app as production_app

    paths = production_app.openapi()["paths"]
    assert "post" in paths["/api/v1/t/{tenant_slug}/ai/knowledge/ask"]
