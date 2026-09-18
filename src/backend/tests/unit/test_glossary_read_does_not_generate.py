"""#1460 — the anonymous glossary read triggers no generation and no write.

``GET /api/v1/public/glossary/term/{slug}`` is the only route in the #1443
detector inventory an **unauthenticated** caller reaches. On a cache miss it
asked the Knowledge Service, persisted the answer in ArangoDB and Redis, and
wrote an AI audit record — so an anonymous caller chose when the installation
paid for an LLM call, and a safe method wrote three times.

The acceptance condition the issue names is measured here directly: **the LLM
double's call counter is zero on a miss**. A double that only records is the
right instrument for it — an assertion on the response body alone would be green
for a service that generated an answer and threw it away, which is worse than the
defect.

The counterparts are asserted alongside, because a read that answers nothing at
all would satisfy every "did not happen" assertion in this file: the curated
catalogue stays readable (the second acceptance condition), and
``generate_term`` still generates.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.interfaces.knowledge_service import AskResult, KnowledgeChunk
from app.domain.models.glossary_term import GlossaryTerm, GlossaryTermCacheEntry
from app.domain.services.glossary_service import GlossaryService


class _CountingKnowledgeService:
    """An LLM adapter that answers, and counts how often it was asked.

    The counter is the measurement #1460 asks for. ``ask`` returns a *usable*
    answer on purpose: a double that raised would make "no LLM call" and "the LLM
    call failed" indistinguishable in the assertions below.
    """

    def __init__(self) -> None:
        self.calls = 0

    async def ask(self, question: str, **kwargs: object) -> AskResult:
        self.calls += 1
        return AskResult(
            answer="A generated explanation.",
            sources=[
                KnowledgeChunk(
                    source_key="chunk-1",
                    source_type="care_rule",
                    title="VPD",
                    score=0.9,
                    language="de",
                )
            ],
            model_name="gemma3:12b",
            provider_type="ollama",
            kb_version="ks-1",
        )


class _CountingCacheRepo:
    """The ArangoDB cache, with every write counted and the hit configurable."""

    def __init__(self, hit: GlossaryTermCacheEntry | None = None) -> None:
        self.hit = hit
        self.upserts: list[GlossaryTermCacheEntry] = []

    def find_valid(self, slug: str, language: str, expertise_level: str) -> GlossaryTermCacheEntry | None:
        return self.hit

    def upsert(self, entry: GlossaryTermCacheEntry) -> GlossaryTermCacheEntry:
        self.upserts.append(entry)
        return entry


def _term() -> GlossaryTerm:
    return GlossaryTerm(
        slug="vpd",
        labels={"de": "VPD", "en": "VPD"},
        long_labels={"de": "Wasserdampfdruck-Defizit", "en": "Vapor Pressure Deficit"},
        category="umwelt",
        related_term_slugs=[],
        fallback_text={
            "de": "Das Dampfdruckdefizit beschreibt, wie trocken die Luft für die Pflanze ist.",
            "en": "Vapour pressure deficit describes how dry the air feels to the plant.",
        },
        rag_query_template="Erklaere '{label_de}' fuer einen {expertise_level} Freund.",
    )


def _term_repo(term: GlossaryTerm | None = None) -> MagicMock:
    repo = MagicMock()
    resolved = term if term is not None else _term()
    repo.resolve_slug.return_value = resolved.slug
    repo.get_by_slug.return_value = resolved
    repo.list_active.return_value = [resolved]
    return repo


def _service(
    adapter: _CountingKnowledgeService, cache: _CountingCacheRepo, audit: MagicMock
) -> tuple[GlossaryService, MagicMock]:
    redis = MagicMock()
    redis.get.return_value = None
    return (
        GlossaryService(
            term_repo=_term_repo(),
            cache_repo=cache,
            knowledge_adapter=adapter,  # type: ignore[arg-type]
            audit_logger=audit,
            redis_client=redis,
        ),
        redis,
    )


@pytest.fixture(autouse=True)
def _enable_ai_flag(monkeypatch: pytest.MonkeyPatch):
    """The stage-1 operator flag is on, because the interesting claim needs it.

    ``ai_features_enabled`` defaults to ``False`` (#684), and with it off the read
    served the curated fallback and called no LLM *already*. Every assertion in
    this file would then be green against the unfixed code — the vacuum this
    fixture removes.
    """
    from app.config.settings import settings

    monkeypatch.setattr(settings, "ai_features_enabled", True)


@pytest.fixture
def parts() -> tuple[GlossaryService, _CountingKnowledgeService, _CountingCacheRepo, MagicMock, MagicMock]:
    adapter = _CountingKnowledgeService()
    cache = _CountingCacheRepo()
    audit = MagicMock()
    service, redis = _service(adapter, cache, audit)
    return service, adapter, cache, audit, redis


# ── the acceptance condition ─────────────────────────────────────────────────


def test_a_cache_miss_calls_no_llm_and_writes_nothing(parts) -> None:
    """The counter is zero, and so is every write the miss used to perform."""
    service, adapter, cache, audit, redis = parts

    answer = service.get_term("vpd", language="de", expertise_level="beginner")

    assert adapter.calls == 0, "the anonymous read reached the Knowledge Service"
    assert cache.upserts == [], "the anonymous read wrote a cache row"
    redis.set.assert_not_called()
    audit.record.assert_not_called()
    # And it still answered — with the curated editorial text, flagged as such.
    assert answer.is_fallback is True
    assert answer.slug == "vpd"
    assert "Dampfdruckdefizit" in answer.answer_text
    assert answer.uses_cloud_provider is False


def test_repeated_misses_stay_at_zero(parts) -> None:
    """The shape of the finding: cost per *request*, not one cost in total."""
    service, adapter, cache, _audit, _redis = parts

    for level in ("beginner", "intermediate", "expert"):
        service.get_term("vpd", language="de", expertise_level=level)
        service.get_term("vpd", language="en", expertise_level=level)

    assert adapter.calls == 0
    assert cache.upserts == []


def test_a_cache_hit_is_served_and_still_writes_nothing() -> None:
    """The other read branch. It used to write an audit row on every hit too."""
    cached = GlossaryTermCacheEntry(
        term_slug="vpd",
        language="de",
        expertise_level="beginner",
        answer_text="Cached VPD answer.",
        kb_version="ks-1",
        is_fallback=False,
        valid_until=datetime.now(UTC) + timedelta(days=1),
    )
    adapter = _CountingKnowledgeService()
    cache = _CountingCacheRepo(hit=cached)
    audit = MagicMock()
    service, redis = _service(adapter, cache, audit)

    answer = service.get_term("vpd")

    assert answer.answer_text == "Cached VPD answer."
    assert answer.is_fallback is False
    assert adapter.calls == 0
    assert cache.upserts == []
    audit.record.assert_not_called()
    redis.set.assert_not_called()


# ── the catalogue stays readable (the issue's second acceptance condition) ────


def test_a_catalogue_slug_answers_200_and_an_unknown_one_404(parts) -> None:
    service, adapter, _cache, _audit, _redis = parts

    assert service.get_term("vpd").slug == "vpd"

    service._terms.resolve_slug.return_value = None  # type: ignore[attr-defined]
    with pytest.raises(NotFoundError):
        service.get_term("not-in-the-catalogue")
    assert adapter.calls == 0, "even the 404 path must not reach the LLM"


# ── the control: generation did not simply disappear ─────────────────────────


async def test_generate_term_still_calls_the_llm_and_caches(parts) -> None:
    """Without this the assertions above are satisfied by a broken service."""
    service, adapter, cache, audit, redis = parts

    answer = await service.generate_term("vpd", language="de", expertise_level="beginner")

    assert adapter.calls == 1
    assert len(cache.upserts) == 1
    assert cache.upserts[0].answer_text == "A generated explanation."
    audit.record.assert_called_once()
    redis.set.assert_called_once()
    assert answer.is_fallback is False


async def test_generate_term_is_idempotent_while_the_cache_is_valid() -> None:
    """A second request is not a second LLM call — the warm-up relies on it."""
    cached = GlossaryTermCacheEntry(
        term_slug="vpd",
        language="de",
        expertise_level="beginner",
        answer_text="Cached VPD answer.",
        kb_version="ks-1",
        is_fallback=False,
        valid_until=datetime.now(UTC) + timedelta(days=1),
    )
    adapter = _CountingKnowledgeService()
    cache = _CountingCacheRepo(hit=cached)
    service, _redis = _service(adapter, cache, MagicMock())

    answer = await service.generate_term("vpd")

    assert adapter.calls == 0
    assert cache.upserts == []
    assert answer.answer_text == "Cached VPD answer."


# ── the warm-up task is what refills the cache now ───────────────────────────


def test_the_warm_up_generates_every_catalogue_variant(monkeypatch: pytest.MonkeyPatch) -> None:
    """One LLM call per term and variant, off the request path (§4.3).

    The variants matter: the read can be asked for any (language, expertise)
    pair, and one the warm-up skipped would be a permanent editorial fallback for
    that audience, since nothing else generates any more.
    """
    from app.tasks import glossary_tasks

    service = MagicMock()
    service.catalogue_slugs.return_value = ["vpd", "gdd"]
    service.generate_term = AsyncMock(return_value=None)
    monkeypatch.setattr(glossary_tasks, "get_glossary_service", lambda: service)

    result = glossary_tasks.warm_glossary_cache()

    assert result["terms"] == 2
    assert result["warmed"] == 2 * len(glossary_tasks._VARIANTS)
    assert result["errors"] == 0
    asked = {
        (call.args[0], call.kwargs["language"], call.kwargs["expertise_level"])
        for call in service.generate_term.await_args_list
    }
    assert asked == {(slug, language, level) for slug in ("vpd", "gdd") for language, level in glossary_tasks._VARIANTS}


def test_the_warm_up_survives_one_failing_term(monkeypatch: pytest.MonkeyPatch) -> None:
    """A Knowledge-Service outage part-way through is a degraded, not a lost, run."""
    from app.tasks import glossary_tasks

    service = MagicMock()
    service.catalogue_slugs.return_value = ["vpd", "gdd"]

    async def _generate(slug: str, **kwargs: object) -> None:
        if slug == "vpd":
            raise RuntimeError("knowledge service unavailable")

    service.generate_term = AsyncMock(side_effect=_generate)
    monkeypatch.setattr(glossary_tasks, "get_glossary_service", lambda: service)

    result = glossary_tasks.warm_glossary_cache()

    variants = len(glossary_tasks._VARIANTS)
    assert result["errors"] == variants
    assert result["warmed"] == variants, "the second term was skipped along with the first"


def test_the_warm_up_does_nothing_with_the_ai_flag_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """There is no RAG stack to ask, and the curated fallback already answers."""
    from app.config.settings import settings
    from app.tasks import glossary_tasks

    monkeypatch.setattr(settings, "ai_features_enabled", False)
    service = MagicMock()
    monkeypatch.setattr(glossary_tasks, "get_glossary_service", lambda: service)

    result = glossary_tasks.warm_glossary_cache()

    assert result == {"status": "skipped", "warmed": 0, "errors": 0}
    service.catalogue_slugs.assert_not_called()
