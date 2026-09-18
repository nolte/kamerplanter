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


@pytest.fixture
def warm_up(monkeypatch: pytest.MonkeyPatch):
    """The warm-up task with a doubled service and an in-memory lock.

    The Redis client is stubbed rather than reached: the tier guard
    (`tests/support/db_guard.py`) refuses a live datastore from a unit test, and
    it caught exactly that the moment the single-run lock was added — the lock is
    real infrastructure and this tier does not get to touch it.
    """
    from app.common import dependencies
    from app.tasks import glossary_tasks

    redis = MagicMock()
    redis.set.return_value = True  # the lock is free
    monkeypatch.setattr(dependencies, "_get_redis_client", lambda: redis)

    service = MagicMock()
    service.catalogue_slugs.return_value = ["vpd", "gdd"]
    service.generate_term = AsyncMock(return_value=None)
    monkeypatch.setattr(glossary_tasks, "get_glossary_service", lambda: service)

    return glossary_tasks, service, redis


def test_the_warm_up_generates_every_catalogue_variant(warm_up) -> None:
    """One LLM call per term and variant, off the request path (§4.3).

    The variants matter: the read can be asked for any (language, expertise)
    pair, and one the warm-up skipped would be a permanent editorial fallback for
    that audience, since nothing else generates any more.
    """
    glossary_tasks, service, _redis = warm_up

    result = glossary_tasks.warm_glossary_cache()

    assert result["status"] == "ok"
    assert result["terms"] == 2
    assert result["warmed"] == 2 * len(glossary_tasks._VARIANTS)
    assert result["errors"] == 0
    asked = {
        (call.args[0], call.kwargs["language"], call.kwargs["expertise_level"])
        for call in service.generate_term.await_args_list
    }
    assert asked == {(slug, language, level) for slug in ("vpd", "gdd") for language, level in glossary_tasks._VARIANTS}


def test_the_warm_up_survives_scattered_failures(warm_up) -> None:
    """One bad term is not a broken service: the run continues and reports both.

    The failures are spread across terms on purpose — a *consecutive* run of them
    is the other case and is asserted separately below. The counter reset is what
    separates the two, and a test whose failures happened to be consecutive would
    measure the abort instead of the resilience.
    """
    glossary_tasks, service, _redis = warm_up
    service.catalogue_slugs.return_value = ["vpd", "gdd", "ec"]

    async def _generate(slug: str, *, language: str, expertise_level: str) -> None:
        if expertise_level == "expert":
            raise RuntimeError("knowledge service hiccup")

    service.generate_term = AsyncMock(side_effect=_generate)

    result = glossary_tasks.warm_glossary_cache()

    variants = len(glossary_tasks._VARIANTS)
    assert result["status"] == "ok", "scattered failures must not trip the abort"
    assert result["errors"] == 3 * 2, "one failure per (term, language) at the expert level"
    assert result["warmed"] == 3 * variants - 6


def test_the_warm_up_aborts_when_the_service_is_simply_down(warm_up) -> None:
    """Review SCR-008 — a dead Knowledge Service is not 192 individual failures.

    Without the abort, a service that is down spends the whole time budget
    producing the same error once per variant, and the operator reads a long log
    of identical warnings instead of one statement.
    """
    glossary_tasks, service, _redis = warm_up
    service.generate_term = AsyncMock(side_effect=RuntimeError("knowledge service unavailable"))

    result = glossary_tasks.warm_glossary_cache()

    assert result["status"] == "aborted"
    assert result["errors"] == glossary_tasks._MAX_CONSECUTIVE_FAILURES
    assert result["warmed"] == 0
    # It really stopped early rather than finishing and relabelling the result.
    assert service.generate_term.await_count == glossary_tasks._MAX_CONSECUTIVE_FAILURES
    assert service.generate_term.await_count < 2 * len(glossary_tasks._VARIANTS)


def test_the_warm_up_reports_what_it_warmed_when_the_budget_runs_out(warm_up) -> None:
    """The soft limit lands inside the loop, so the counts survive it."""
    from celery.exceptions import SoftTimeLimitExceeded

    glossary_tasks, service, _redis = warm_up
    calls = {"n": 0}

    async def _generate(slug: str, **kwargs: object) -> None:
        calls["n"] += 1
        if calls["n"] > 3:
            raise SoftTimeLimitExceeded

    service.generate_term = AsyncMock(side_effect=_generate)

    result = glossary_tasks.warm_glossary_cache()

    assert result["status"] == "timed_out"
    assert result["warmed"] == 3, "the run threw away what it had already done"
    assert result["errors"] == 0, "the budget is not a failure of the term it landed on"


def test_a_second_run_does_not_pay_for_the_catalogue_twice(warm_up) -> None:
    """Review SCR-008 — two reingests close together are one warm-up."""
    glossary_tasks, service, redis = warm_up
    redis.set.return_value = False  # another run holds the lock

    result = glossary_tasks.warm_glossary_cache()

    assert result == {"status": "locked", "warmed": 0, "errors": 0}
    service.generate_term.assert_not_awaited()
    service.catalogue_slugs.assert_not_called()


def test_the_lock_is_released_even_when_the_run_aborts(warm_up) -> None:
    """A held lock outliving its run would block every later reingest."""
    glossary_tasks, service, redis = warm_up
    service.generate_term = AsyncMock(side_effect=RuntimeError("down"))

    glossary_tasks.warm_glossary_cache()

    redis.delete.assert_called_once_with(glossary_tasks._RUN_LOCK_KEY)


def test_a_missing_redis_does_not_block_the_warm_up(monkeypatch: pytest.MonkeyPatch, warm_up) -> None:
    """The lock is an optimisation; refusing to warm over it would be worse."""
    from app.common import dependencies

    glossary_tasks, service, _redis = warm_up
    monkeypatch.setattr(dependencies, "_get_redis_client", lambda: (_ for _ in ()).throw(RuntimeError("no redis")))

    result = glossary_tasks.warm_glossary_cache()

    assert result["status"] == "ok"
    assert result["warmed"] == 2 * len(glossary_tasks._VARIANTS)


def test_the_lock_carries_a_ttl(warm_up) -> None:
    """Without it, a worker killed mid-run wedges every future reingest."""
    glossary_tasks, _service, redis = warm_up

    glossary_tasks.warm_glossary_cache()

    _args, kwargs = redis.set.call_args
    assert kwargs["nx"] is True
    assert kwargs["ex"] == glossary_tasks._HARD_TIME_LIMIT_SECONDS


def test_the_task_declares_both_time_limits() -> None:
    """Review SCR-008 — an unbounded run holds a worker and stops the queue."""
    from app.tasks.glossary_tasks import warm_glossary_cache

    assert warm_glossary_cache.soft_time_limit
    assert warm_glossary_cache.time_limit
    assert warm_glossary_cache.soft_time_limit < warm_glossary_cache.time_limit, (
        "the soft limit must land first, or the loop never gets to report its counts"
    )


def test_the_warm_up_does_nothing_with_the_ai_flag_off(monkeypatch: pytest.MonkeyPatch, warm_up) -> None:
    """There is no RAG stack to ask, and the curated fallback already answers."""
    from app.config.settings import settings

    glossary_tasks, service, redis = warm_up
    monkeypatch.setattr(settings, "ai_features_enabled", False)

    result = glossary_tasks.warm_glossary_cache()

    assert result == {"status": "skipped", "warmed": 0, "errors": 0}
    service.catalogue_slugs.assert_not_called()
    # And it does not take the lock it has no use for.
    redis.set.assert_not_called()


# ── the operator kill switch gates the OUTPUT, not only the generation ───────


def test_the_flag_off_serves_the_curated_text_over_a_warm_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Review SCR-004, and the assertion the router tests could not make.

    ``tests/api/test_glossary_endpoints.py::*_flag_off_serves_fallback`` drives
    the *route* with a doubled service whose return value is already
    ``is_fallback=True`` — it measures that the router forwards an answer, not
    that the service produces the right one with the flag off. Here the service is
    real and the cache is **warm**, which is the case that separates "the switch
    stops generation" from "the switch stops AI text reaching a user".

    Without this, throwing the kill switch would take up to the seven-day cache
    TTL to have any visible effect, while the user-facing documentation says the
    term "stays explainable without any AI/RAG stack" — meaning the curated text.
    """
    from app.config.settings import settings

    cached = GlossaryTermCacheEntry(
        term_slug="vpd",
        language="de",
        expertise_level="beginner",
        answer_text="A cached RAG answer written before the switch was thrown.",
        kb_version="ks-1",
        is_fallback=False,
        valid_until=datetime.now(UTC) + timedelta(days=1),
    )
    adapter = _CountingKnowledgeService()
    cache = _CountingCacheRepo(hit=cached)
    service, redis = _service(adapter, cache, MagicMock())

    monkeypatch.setattr(settings, "ai_features_enabled", False)
    answer = service.get_term("vpd")

    assert answer.is_fallback is True
    assert "Dampfdruckdefizit" in answer.answer_text
    assert answer.answer_text != cached.answer_text
    assert adapter.calls == 0
    assert cache.upserts == []
    # Not even read: consulting the cache and discarding the result would be the
    # same outcome with a worse reason, and the Redis hop is pure cost.
    redis.get.assert_not_called()


def test_the_flag_on_still_serves_the_warm_cache() -> None:
    """The control. Without it the assertion above is satisfied by a service that
    has stopped reading its cache at all."""
    cached = GlossaryTermCacheEntry(
        term_slug="vpd",
        language="de",
        expertise_level="beginner",
        answer_text="A cached RAG answer.",
        kb_version="ks-1",
        is_fallback=False,
        valid_until=datetime.now(UTC) + timedelta(days=1),
    )
    service, _redis = _service(_CountingKnowledgeService(), _CountingCacheRepo(hit=cached), MagicMock())

    answer = service.get_term("vpd")

    assert answer.is_fallback is False
    assert answer.answer_text == "A cached RAG answer."


# ── one vocabulary, three consumers (review SCR-005) ─────────────────────────


def test_the_variant_space_has_exactly_one_source():
    """The model's literals are the source; the service and the task derive.

    Three copies existed. Each stayed internally consistent while they could
    disagree with each other, and the disagreement is invisible: adding a language
    to the model would leave the warm-up covering the old set, so every read in the
    new language would answer a curated fallback forever and nothing would fail.

    Asserted as an equality against the published literals rather than against a
    hand-written list, so this test cannot itself become the fourth copy.
    """
    from typing import get_args

    from app.domain.models.glossary_term import ExpertiseLevel, Language
    from app.domain.services import glossary_service
    from app.tasks import glossary_tasks

    languages, levels = set(get_args(Language)), set(get_args(ExpertiseLevel))

    assert languages == glossary_service._VALID_LANGUAGES
    assert levels == glossary_service._VALID_LEVELS
    assert {language for language, _ in glossary_tasks._VARIANTS} == languages
    assert {level for _, level in glossary_tasks._VARIANTS} == levels
    assert len(glossary_tasks._VARIANTS) == len(languages) * len(levels)


def test_the_variant_space_is_not_empty():
    """The control: `get_args` on a non-Literal returns `()` and every assertion
    above would pass over empty sets."""
    from app.tasks import glossary_tasks

    assert len(glossary_tasks._VARIANTS) >= 6
