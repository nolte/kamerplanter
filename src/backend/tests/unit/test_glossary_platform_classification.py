"""#2110 (MT-013) — the shared glossary cache is classified by the platform, not by the first tenant.

One cached answer per term/language/level is served to every tenant. Before
#2110 whether its generation counted as cloud processing — and so whether the
triggering member had to consent, and what label every later reader saw — was
read from the *requesting tenant's* default provider. The knowledge service
answers with its own model whoever asks (``/ask`` names no provider), so that
was a property of whoever came first, frozen into a cache for everybody.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.exceptions import ConsentRequiredError
from app.config.settings import settings
from app.domain.interfaces.knowledge_service import AskResult, KnowledgeChunk
from app.domain.models.ai_assistant import AiProviderConfig
from app.domain.models.glossary_term import GlossaryTerm
from app.domain.services.glossary_service import GlossaryService


@pytest.fixture(autouse=True)
def _ai_on(monkeypatch):
    monkeypatch.setattr(settings, "ai_features_enabled", True)


def _provider(tenant_key: str | None, provider_type: str) -> AiProviderConfig:
    return AiProviderConfig(
        _key=f"{tenant_key or 'system'}-{provider_type}",
        tenant_key=tenant_key,
        provider_type=provider_type,
        display_name=provider_type,
        model_name="m",
        requires_consent=provider_type != "ollama",
        is_default=True,
    )


class _Providers:
    """Tenant ``cloudy`` defaults to a cloud LLM, tenant ``local`` to Ollama."""

    def __init__(self, system: AiProviderConfig | None) -> None:
        self._system = system
        self._tenants = {"cloudy": _provider("cloudy", "anthropic"), "local": _provider("local", "ollama")}

    def get_default(self, tenant_key: str, provider_key: str | None) -> AiProviderConfig | None:
        return self._tenants.get(tenant_key, self._system)

    def get_system_default(self) -> AiProviderConfig | None:
        return self._system


class _Cache:
    def __init__(self) -> None:
        self.entry = None

    def find_valid(self, slug, language, level):
        return self.entry

    def upsert(self, entry):
        self.entry = entry
        return entry


def _service(*, system: AiProviderConfig | None, consent: MagicMock | None = None):
    term = GlossaryTerm(slug="vpd", labels={"de": "VPD", "en": "VPD"}, fallback_text={"de": "VPD.", "en": "VPD."})
    terms = MagicMock()
    terms.resolve_slug.return_value = "vpd"
    terms.get_by_slug.return_value = term
    adapter = MagicMock()
    adapter.ask = AsyncMock(
        return_value=AskResult(
            answer="VPD ist ...",
            model_name="m",
            sources=[KnowledgeChunk(source_key="k", source_type="rag", title="t", score=0.9, language="de")],
        )
    )
    consent = consent if consent is not None else MagicMock()
    service = GlossaryService(
        call_budget=MagicMock(),
        term_repo=terms,
        cache_repo=_Cache(),
        knowledge_adapter=adapter,
        audit_logger=MagicMock(),
        consent_guard=consent,
        provider_repo=_Providers(system),
        redis_client=None,
    )
    return service, consent, adapter


async def test_a_tenants_own_cloud_provider_does_not_label_the_shared_entry() -> None:
    service, consent, _ = _service(system=_provider(None, "ollama"))

    generated = await service.generate_term("vpd", tenant_key="cloudy", user_key="anna")
    read_elsewhere = service.get_term("vpd")

    assert generated.uses_cloud_provider is False
    assert read_elsewhere.uses_cloud_provider is False
    consent.require_consent.assert_not_called()


async def test_a_platform_cloud_provider_needs_the_consent_of_any_triggering_member() -> None:
    """A tenant whose own default is local may not trigger a cloud call unasked."""
    consent = MagicMock()
    consent.require_consent.side_effect = ConsentRequiredError("ai_cloud_processing")
    service, _, adapter = _service(system=_provider(None, "anthropic"), consent=consent)

    with pytest.raises(ConsentRequiredError):
        await service.generate_term("vpd", tenant_key="local", user_key="ben")
    adapter.ask.assert_not_awaited()


async def test_every_reader_sees_the_label_of_the_entry_not_their_own() -> None:
    service, _, _ = _service(system=_provider(None, "anthropic"))

    generated = await service.generate_term("vpd", tenant_key="cloudy", user_key="anna")
    served = service.get_term("vpd")

    assert generated.uses_cloud_provider is True
    assert served.uses_cloud_provider is True


async def test_the_platform_warm_up_is_classified_by_the_platform_and_asks_nobody() -> None:
    service, consent, _ = _service(system=_provider(None, "anthropic"))

    warmed = await service.generate_term("vpd")

    assert warmed.uses_cloud_provider is True
    consent.require_consent.assert_not_called()
    service._budget.charge.assert_not_called()  # noqa: SLF001 — the platform's own generation


async def test_a_tenant_generation_charges_the_callers_budget_on_a_miss_only() -> None:
    service, _, _ = _service(system=None)

    await service.generate_term("vpd", tenant_key="local", user_key="ben")
    await service.generate_term("vpd", tenant_key="local", user_key="ben")  # cache hit now

    service._budget.charge.assert_called_once_with(tenant_key="local", user_key="ben")  # noqa: SLF001
