"""REQ-031 §4.3 / §5.3 — unit tests for ``AiAssistantService`` orchestration.

Covers the light-mode ``context=null`` guarantee, graceful degradation to
rule-based tips on a Knowledge-Service outage, and the DSGVO conversation delete.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from app.common.enums import TenantRole
from app.data_access.external.knowledge_service_adapter import KnowledgeServiceUnavailableError
from app.domain.interfaces.knowledge_service import AskResult
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ai_assistant_service import AiAssistantService


def _ctx() -> TenantContext:
    return TenantContext(tenant_key="home", tenant_slug="home", user_key="anna", role=TenantRole.GROWER)


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


def test_get_tips_degrades_to_rule_based_on_outage() -> None:
    adapter = MagicMock()
    adapter.ask = AsyncMock(side_effect=KnowledgeServiceUnavailableError("down"))
    service = _service(adapter)
    service._tip_cache.find_valid.return_value = []

    tips = service.get_tips(_ctx(), context_type="planting_run", context_key="run-1")

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
