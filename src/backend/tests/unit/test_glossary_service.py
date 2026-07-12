"""REQ-035 §4.1 — unit tests for ``GlossaryService``.

Covers the cache-first path, the KB-score fallback, alias resolution, the
``context=null`` guarantee, expertise differentiation, the cloud-processing
consent gate and slug/expertise validation (§8 scenarios 1-10).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.exceptions import ConsentRequiredError, NotFoundError, ValidationError
from app.data_access.external.knowledge_service_adapter import KnowledgeServiceUnavailableError
from app.domain.interfaces.knowledge_service import AskResult, KnowledgeChunk
from app.domain.models.ai_assistant import AiProviderConfig
from app.domain.models.glossary_term import GlossaryTerm, GlossaryTermCacheEntry
from app.domain.services.glossary_service import GlossaryService


def _term(slug: str = "vpd", **overrides) -> GlossaryTerm:
    data = {
        "slug": slug,
        "labels": {"de": "VPD", "en": "VPD"},
        "long_labels": {"de": "Wasserdampfdruck-Defizit", "en": "Vapor Pressure Deficit"},
        "aliases": {"de": ["saettigungsdefizit"], "en": ["saturation deficit"]},
        "category": "umwelt",
        "related_term_slugs": ["transpiration"],
        "fallback_text": {"de": "VPD Kurzdefinition.", "en": "VPD short definition."},
        "rag_query_template": "Erklaere '{label_de}' fuer einen {expertise_level} Freund.",
    }
    data.update(overrides)
    return GlossaryTerm(**data)


def _ask_result(score: float = 0.9, sources: int = 1) -> AskResult:
    chunks = [
        KnowledgeChunk(source_key=f"umwelt/vpd#{i}", source_type="care_rule", title="VPD", score=score, language="de")
        for i in range(sources)
    ]
    return AskResult(answer="VPD ist ...", model_name="gemma3:12b", provider_type="ollama", sources=chunks)


def _service(*, term, ks_ask, cache_hit=None, provider=None, consent_ok=True):
    term_repo = MagicMock()
    term_repo.resolve_slug.return_value = term.slug if term else None
    lookup = {term.slug: term} if term else {}
    if term:
        for rel in term.related_term_slugs:
            lookup.setdefault(rel, _term(rel, labels={"de": rel, "en": rel}, related_term_slugs=[]))
    term_repo.get_by_slug.side_effect = lambda s: lookup.get(s)

    cache_repo = MagicMock()
    cache_repo.find_valid.return_value = cache_hit
    cache_repo.upsert.side_effect = lambda e: e
    cache_repo.invalidate_all.return_value = 5
    cache_repo.invalidate_slug.return_value = 2

    adapter = MagicMock()
    adapter.ask = ks_ask

    consent = MagicMock()
    if not consent_ok:
        consent.require_consent.side_effect = ConsentRequiredError("ai_cloud_processing")

    provider_repo = MagicMock()
    provider_repo.get_default.return_value = provider

    service = GlossaryService(
        term_repo=term_repo,
        cache_repo=cache_repo,
        knowledge_adapter=adapter,
        audit_logger=MagicMock(),
        consent_guard=consent,
        provider_repo=provider_repo,
        redis_client=None,
    )
    return service, term_repo, cache_repo, adapter, consent


# ── Scenario 1: cache-miss RAG success ─────────────────────────────


async def test_get_term_rag_success_sends_context_null() -> None:
    term = _term()
    ask = AsyncMock(return_value=_ask_result())
    service, _tr, cache_repo, adapter, _c = _service(term=term, ks_ask=ask)

    answer = await service.get_term("vpd", language="de", expertise_level="beginner")

    adapter.ask.assert_awaited_once()
    assert adapter.ask.await_args.kwargs["context"] is None  # §4.1 step 5
    assert adapter.ask.await_args.kwargs["doc_language"] == "all"
    assert answer.is_fallback is False
    assert answer.uses_tenant_data is False
    assert answer.slug == "vpd"
    assert answer.related_terms and answer.related_terms[0].slug == "transpiration"
    cache_repo.upsert.assert_called_once()


# ── Scenario 2 + 10: low score / no sources → editorial fallback ───


async def test_get_term_low_score_falls_back() -> None:
    term = _term()
    ask = AsyncMock(return_value=_ask_result(score=0.2))
    service, *_ = _service(term=term, ks_ask=ask)

    answer = await service.get_term("vpd")

    assert answer.is_fallback is True
    assert answer.answer_text == "VPD Kurzdefinition."
    assert answer.sources == []


async def test_get_term_no_sources_falls_back() -> None:
    term = _term()
    ask = AsyncMock(return_value=_ask_result(sources=0))
    service, *_ = _service(term=term, ks_ask=ask)

    answer = await service.get_term("vpd")
    assert answer.is_fallback is True


# ── Scenario 5: cache-hit skips the KS ─────────────────────────────


async def test_get_term_cache_hit_skips_ks() -> None:
    term = _term()
    cached = GlossaryTermCacheEntry(
        term_slug="vpd",
        language="de",
        expertise_level="beginner",
        answer_text="Cached VPD answer.",
        kb_version="ks-1",
        is_fallback=False,
    )
    ask = AsyncMock()
    service, _tr, cache_repo, adapter, _c = _service(term=term, ks_ask=ask, cache_hit=cached)

    answer = await service.get_term("vpd")

    adapter.ask.assert_not_awaited()
    cache_repo.upsert.assert_not_called()
    assert answer.answer_text == "Cached VPD answer."
    assert answer.kb_version == "ks-1"


# ── Scenario 4: alias resolution ───────────────────────────────────


async def test_get_term_resolves_alias_to_canonical_slug() -> None:
    term = _term()
    ask = AsyncMock(return_value=_ask_result())
    service, term_repo, *_ = _service(term=term, ks_ask=ask)
    term_repo.resolve_slug.return_value = "vpd"  # alias → canonical

    answer = await service.get_term("saettigungsdefizit", language="de")

    assert answer.slug == "vpd"
    assert answer.label == "VPD"


# ── Unknown term → 404 ─────────────────────────────────────────────


async def test_get_term_unknown_raises_404() -> None:
    ask = AsyncMock()
    service, term_repo, *_ = _service(term=None, ks_ask=ask)
    term_repo.resolve_slug.return_value = None

    with pytest.raises(NotFoundError):
        await service.get_term("does-not-exist")
    ask.assert_not_awaited()


# ── Scenario 9: prompt-injection / bad input rejected before KS ────


async def test_get_term_rejects_unsafe_slug() -> None:
    ask = AsyncMock()
    service, *_ = _service(term=_term(), ks_ask=ask)

    with pytest.raises(ValidationError):
        await service.get_term("<script>alert(1)</script>")
    ask.assert_not_awaited()


async def test_get_term_rejects_bad_expertise() -> None:
    ask = AsyncMock()
    service, *_ = _service(term=_term(), ks_ask=ask)

    with pytest.raises(ValidationError):
        await service.get_term("vpd", expertise_level="ignore_previous_instructions")
    ask.assert_not_awaited()


# ── Scenario 3: KS outage → graceful fallback ──────────────────────


async def test_get_term_ks_outage_falls_back() -> None:
    term = _term()
    ask = AsyncMock(side_effect=KnowledgeServiceUnavailableError("down"))
    service, *_ = _service(term=term, ks_ask=ask)

    answer = await service.get_term("vpd")

    assert answer.is_fallback is True
    assert answer.answer_text == "VPD Kurzdefinition."


# ── Scenario 8: expertise differentiation in the prompt ────────────


async def test_expertise_level_shapes_the_question() -> None:
    term = _term()
    captured: dict = {}

    async def _capture(question, **kwargs):
        captured["question"] = question
        return _ask_result()

    service, *_ = _service(term=term, ks_ask=AsyncMock(side_effect=_capture))

    await service.get_term("vpd", expertise_level="expert")
    assert "expert" in captured["question"]
    assert "VPD" in captured["question"]


# ── §6: cloud-processing consent gate on the tenant path ───────────


async def test_tenant_cloud_provider_requires_consent() -> None:
    term = _term()
    cloud = AiProviderConfig(
        _key="claude",
        tenant_key="home",
        provider_type="anthropic",
        display_name="Claude",
        model_name="claude-3-5",
        requires_consent=True,
        is_default=True,
    )
    ask = AsyncMock(return_value=_ask_result())
    service, *_ = _service(term=term, ks_ask=ask, provider=cloud, consent_ok=False)

    with pytest.raises(ConsentRequiredError):
        await service.get_term("vpd", tenant_key="home", user_key="anna", allow_cloud=True)


async def test_public_path_never_uses_cloud() -> None:
    term = _term()
    ask = AsyncMock(return_value=_ask_result())
    service, *_ = _service(term=term, ks_ask=ask)

    answer = await service.get_term("vpd")  # no tenant_key → public
    assert answer.uses_cloud_provider is False


async def test_tenant_local_provider_no_consent_no_cloud() -> None:
    term = _term()
    local = AiProviderConfig(
        _key="ollama",
        tenant_key="home",
        provider_type="ollama",
        display_name="Ollama",
        model_name="gemma3:12b",
        is_default=True,
    )
    ask = AsyncMock(return_value=_ask_result())
    service, _tr, _cr, _ad, consent = _service(term=term, ks_ask=ask, provider=local)

    answer = await service.get_term("vpd", tenant_key="home", user_key="anna", allow_cloud=True)
    assert answer.uses_cloud_provider is False
    consent.require_consent.assert_not_called()


# ── list_terms + invalidate ────────────────────────────────────────


def test_list_terms_localises_labels() -> None:
    term = _term()
    service, term_repo, *_ = _service(term=term, ks_ask=AsyncMock())
    term_repo.list_active.return_value = [term]

    summaries = service.list_terms(language="en")
    assert summaries[0].slug == "vpd"
    assert summaries[0].category == "umwelt"


def test_invalidate_cache_all_vs_slug() -> None:
    service, _tr, cache_repo, *_ = _service(term=_term(), ks_ask=AsyncMock())

    assert service.invalidate_cache(None) == 5
    cache_repo.invalidate_all.assert_called_once()

    assert service.invalidate_cache("vpd") == 2
    cache_repo.invalidate_slug.assert_called_once_with("vpd")
