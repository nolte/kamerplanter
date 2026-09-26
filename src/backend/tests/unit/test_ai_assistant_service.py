"""REQ-031 §4.3 / §5.3 — unit tests for ``AiAssistantService`` orchestration.

Covers the light-mode ``context=null`` guarantee, graceful degradation to
rule-based tips on a Knowledge-Service outage, and the DSGVO conversation delete.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import AiDisabledError, ConsentRequiredError
from app.data_access.external.knowledge_service_adapter import KnowledgeServiceUnavailableError
from app.domain.guards.consent_guard import AI_CLOUD_PROCESSING
from app.domain.interfaces.knowledge_service import AskResult
from app.domain.models.ai_assistant import AiProviderConfig
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ai_assistant_service import AiAssistantService


def _ctx() -> TenantContext:
    return TenantContext(tenant_key="home", tenant_slug="home", user_key="anna", role=TenantRole.GROWER)


def _cloud_provider() -> AiProviderConfig:
    return AiProviderConfig(
        _key="claude",
        tenant_key="home",
        provider_type="anthropic",
        display_name="Claude",
        model_name="claude-3-5",
        requires_consent=True,
        is_default=True,
    )


def _local_provider() -> AiProviderConfig:
    return AiProviderConfig(
        _key="ollama",
        tenant_key="home",
        provider_type="ollama",
        display_name="Ollama",
        model_name="gemma3:12b",
    )


class _OwnRuns:
    def get_by_key(self, key):
        return SimpleNamespace(key=key, tenant_key="home")


def _service(knowledge_adapter):
    consent_guard = MagicMock()
    consent_guard.require_consent.return_value = None
    provider_repo = MagicMock()
    provider_repo.get_default.return_value = None  # local Ollama default
    return AiAssistantService(
        knowledge_adapter=knowledge_adapter,
        consent_guard=consent_guard,
        audit_logger=MagicMock(),
        tip_cache_repo=MagicMock(),
        conversation_repo=MagicMock(),
        provider_repo=provider_repo,
        # The context run is the tenant's own (#1872 C9 resolves it before tips are stored).
        planting_run_repo=_OwnRuns(),
    )


async def test_public_ask_sends_context_null() -> None:
    adapter = MagicMock()
    adapter.ask = AsyncMock(return_value=AskResult(answer="VPD explained.", model_name="gemma3:12b"))
    service = _service(adapter)

    response = await service.ask_public("What is VPD?", language="en")

    adapter.ask.assert_awaited_once()
    # The public path must never send tenant context to the KS (§5.3).
    assert adapter.ask.await_args.kwargs["context"] is None
    assert response.uses_tenant_data is False
    assert response.uses_cloud_provider is False


async def test_public_ask_degrades_on_outage() -> None:
    adapter = MagicMock()
    adapter.ask = AsyncMock(side_effect=KnowledgeServiceUnavailableError("down"))
    service = _service(adapter)

    response = await service.ask_public("What is VPD?", language="de")

    # A KS outage yields a graceful message, not a 5xx.
    assert response.uses_tenant_data is False
    assert "nicht erreichbar" in response.answer_text


def test_refresh_tips_degrades_to_rule_based_on_outage() -> None:
    """Generation moved to ``refresh_tips`` (#1461); the degradation is unchanged."""
    adapter = MagicMock()
    adapter.ask = AsyncMock(side_effect=KnowledgeServiceUnavailableError("down"))
    service = _service(adapter)
    service._tip_cache.find_valid.return_value = []

    tips = service.refresh_tips(_ctx(), context_type="planting_run", context_key="run-1")

    assert len(tips) >= 1
    assert all(t.model_name == "rule-based-fallback" for t in tips)


def test_delete_conversation_rejects_foreign_tenant() -> None:
    adapter = MagicMock()
    service = _service(adapter)
    conv = MagicMock()
    conv.tenant_key = "other-tenant"
    service._conversations.get_by_key.return_value = conv

    assert service.delete_conversation(_ctx(), "conv-1") is False
    service._conversations.delete.assert_not_called()


# ── SEC-001: cloud-processing consent + fail-closed provider gate ──────────


def _ask_ok() -> AsyncMock:
    return AsyncMock(return_value=AskResult(answer="Because VPD is high.", model_name="claude-3-5"))


def test_cloud_provider_without_consent_raises_403() -> None:
    adapter = MagicMock()
    adapter.ask = _ask_ok()
    service = _service(adapter)
    service._tip_cache.find_valid.return_value = []
    service._providers.get_default.return_value = _cloud_provider()

    # Consent granted for tenant-data-access but NOT for cloud processing.
    def _require(_user_key, purpose):
        if purpose == AI_CLOUD_PROCESSING:
            raise ConsentRequiredError(purpose)

    service._consent.require_consent.side_effect = _require

    with pytest.raises(ConsentRequiredError):
        service.refresh_tips(_ctx(), context_type="planting_run", context_key="run-1", allow_cloud=True)

    # The LLM must not be reached without the cloud consent.
    adapter.ask.assert_not_awaited()


def test_cloud_provider_with_consent_calls_llm() -> None:
    adapter = MagicMock()
    adapter.ask = _ask_ok()
    service = _service(adapter)
    service._tip_cache.find_valid.return_value = []
    service._tip_cache.create.side_effect = lambda card: card
    service._providers.get_default.return_value = _cloud_provider()

    tips = service.refresh_tips(_ctx(), context_type="planting_run", context_key="run-1", allow_cloud=True)

    adapter.ask.assert_awaited_once()
    service._consent.require_consent.assert_any_call("anna", AI_CLOUD_PROCESSING)
    assert len(tips) == 1


def test_cloud_disabled_flag_fails_closed_to_local_ollama() -> None:
    adapter = MagicMock()
    adapter.ask = _ask_ok()
    service = _service(adapter)
    service._tip_cache.find_valid.return_value = []
    service._tip_cache.create.side_effect = lambda card: card
    service._providers.get_default.return_value = _cloud_provider()
    service._providers.list_for_tenant.return_value = [_cloud_provider(), _local_provider()]

    tips = service.refresh_tips(_ctx(), context_type="planting_run", context_key="run-1", allow_cloud=False)

    # Downgraded to local Ollama: no cloud consent demanded, request still served.
    adapter.ask.assert_awaited_once()
    cloud_calls = [c for c in service._consent.require_consent.call_args_list if c.args[1] == AI_CLOUD_PROCESSING]
    assert cloud_calls == []
    assert tips[0].provider_key == "ollama"


def test_cloud_disabled_without_local_provider_raises_ai_disabled() -> None:
    adapter = MagicMock()
    adapter.ask = _ask_ok()
    service = _service(adapter)
    service._tip_cache.find_valid.return_value = []
    service._providers.get_default.return_value = _cloud_provider()
    service._providers.list_for_tenant.return_value = [_cloud_provider()]  # no local fallback

    with pytest.raises(AiDisabledError):
        service.refresh_tips(_ctx(), context_type="planting_run", context_key="run-1", allow_cloud=False)
    adapter.ask.assert_not_awaited()


# ── SEC-002: conversation ownership (IDOR) ─────────────────────────────────


def _foreign_conversation() -> MagicMock:
    conv = MagicMock()
    conv.tenant_key = "home"  # same tenant …
    conv.user_key = "bob"  # … but a different user
    conv.key = "conv-a"
    return conv


def test_get_conversation_rejects_foreign_user_same_tenant() -> None:
    service = _service(MagicMock())
    service._conversations.get_by_key.return_value = _foreign_conversation()

    assert service.get_conversation(_ctx(), "conv-a") is None


def test_delete_conversation_rejects_foreign_user_same_tenant() -> None:
    service = _service(MagicMock())
    service._conversations.get_by_key.return_value = _foreign_conversation()

    assert service.delete_conversation(_ctx(), "conv-a") is False
    service._conversations.delete.assert_not_called()


async def test_stream_chat_rejects_injection_into_foreign_conversation() -> None:
    adapter = MagicMock()
    adapter.ask = AsyncMock()
    service = _service(adapter)
    service._conversations.get_by_key.return_value = _foreign_conversation()

    frames = [frame async for frame in service.stream_chat(_ctx(), conversation_key="conv-a", message="hi")]

    # No LLM call, no persistence — only a not-found error frame.
    adapter.ask.assert_not_awaited()
    service._conversations.update.assert_not_called()
    assert any("conversation_not_found" in frame for frame in frames)


# ── #1461 — the tip reads generate nothing and write nothing ──────────────────


def test_get_tips_on_a_miss_answers_empty_without_touching_the_llm() -> None:
    """Entry 6 of the #1443 inventory: the read generated and persisted a card.

    The LLM adapter is the witness, not the repository: an empty answer with a
    call to ``ask`` would mean the generation ran and its result was dropped,
    which is a worse outcome than the defect. Both are asserted.
    """
    adapter = MagicMock()
    adapter.ask = AsyncMock(return_value=AskResult(answer="anything", model_name="m"))
    service = _service(adapter)
    service._tip_cache.find_valid.return_value = []

    tips = service.get_tips(_ctx(), context_type="planting_run", context_key="run-1")

    assert tips == []
    adapter.ask.assert_not_called()
    service._tip_cache.create.assert_not_called()
    service._tip_cache.invalidate_context.assert_not_called()
    service._audit.record.assert_not_called()


def test_get_daily_tip_on_a_miss_answers_none_without_touching_the_llm() -> None:
    """Entry 5, and the more expensive of the two — the dashboard calls it per load."""
    adapter = MagicMock()
    adapter.ask = AsyncMock(return_value=AskResult(answer="anything", model_name="m"))
    service = _service(adapter)
    service._tip_cache.find_valid.return_value = []

    assert service.get_daily_tip(_ctx()) is None
    adapter.ask.assert_not_called()
    service._tip_cache.create.assert_not_called()
    service._audit.record.assert_not_called()


def test_get_tips_still_answers_with_what_is_stored() -> None:
    """The control: a read that answers nothing at all would pass the two above."""
    from app.domain.models.ai_assistant import AiTipCard

    stored = AiTipCard(
        _key="tip-1",
        tenant_key="home",
        context_type="planting_run",
        context_key="run-1",
        tip_type="care",
        priority="medium",
        title="Water it",
        body="Water it today.",
    )
    service = _service(MagicMock())
    service._tip_cache.find_valid.return_value = [stored]

    assert service.get_tips(_ctx(), context_type="planting_run", context_key="run-1") == [stored]
    assert service.get_daily_tip(_ctx()) is stored


def test_refresh_daily_tip_is_idempotent_for_the_day() -> None:
    """A second click is not a second LLM call."""
    from app.domain.models.ai_assistant import AiTipCard

    stored = AiTipCard(
        _key="tip-1",
        tenant_key="home",
        context_type="daily",
        context_key="2026-09-17",
        tip_type="optimization",
        priority="low",
        title="Today",
        body="Do this.",
    )
    adapter = MagicMock()
    adapter.ask = AsyncMock(return_value=AskResult(answer="anything", model_name="m"))
    service = _service(adapter)
    service._tip_cache.find_valid.return_value = [stored]

    assert service.refresh_daily_tip(_ctx()) is stored
    adapter.ask.assert_not_called()
    service._tip_cache.create.assert_not_called()


def test_refresh_tips_still_generates_and_persists() -> None:
    """The control for the write half: generation did not simply disappear."""
    adapter = MagicMock()
    adapter.ask = AsyncMock(return_value=AskResult(answer="Water it today.", model_name="gemma3:12b"))
    service = _service(adapter)
    service._tip_cache.find_valid.return_value = []

    service.refresh_tips(_ctx(), context_type="planting_run", context_key="run-1")

    adapter.ask.assert_awaited_once()
    service._tip_cache.invalidate_context.assert_called_once()
    service._tip_cache.create.assert_called_once()
    service._audit.record.assert_called_once()


# ── action_url is not an open href (review SCR-012) ──────────────────────────


def test_action_url_accepts_a_site_relative_path() -> None:
    from app.domain.models.ai_assistant import AiTipCard

    card = AiTipCard(tenant_key="home", title="t", body="b", action_url="/pflanzen/p-1")

    assert card.action_url == "/pflanzen/p-1"


@pytest.mark.parametrize(
    "value",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "https://evil.example/phish",
        # Protocol-relative: it starts with "/" and is an ABSOLUTE link, which is
        # precisely what a naive "must start with /" check waves through.
        "//evil.example/phish",
    ],
)
def test_action_url_refuses_anything_that_leaves_the_app(value: str) -> None:
    """The field is rendered straight into an ``href`` on a button the user is
    invited to press, and it is persisted — so a row written by a future producer
    or by hand must not be able to carry a script URL.

    Nothing writes ``action_url`` today (measured 2026-09-18), which is why this
    is a boundary constraint rather than a repair: the point is that the next
    producer cannot introduce the hole without this test going red.
    """
    import pydantic

    from app.domain.models.ai_assistant import AiTipCard

    with pytest.raises(pydantic.ValidationError):
        AiTipCard(tenant_key="home", title="t", body="b", action_url=value)


def test_an_empty_action_url_is_simply_absent() -> None:
    """``""`` is "no link", not a link to the site root."""
    from app.domain.models.ai_assistant import AiTipCard

    assert AiTipCard(tenant_key="home", title="t", body="b", action_url="").action_url is None
