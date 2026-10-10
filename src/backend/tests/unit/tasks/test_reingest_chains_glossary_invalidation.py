"""#2169 — a finished knowledge-base reingest refreshes the glossary cache.

REQ-035 §4.3 says ``glossary.invalidate_after_reingest`` runs "after
``ai.knowledge_service_ingest`` (chained)"; nothing chained it (MT-051, #2144).
Because that task is also the only thing that queues ``glossary.warm_cache``, the
warm-up never ran: every cached answer outlived its 7-day TTL once and every term
then stayed on its editorial fallback.

Two links are pinned here, both through the worker path (``Task.apply()``):

1. the reingest queues the invalidation when — and only when — the Knowledge
   Service reports a finished reingest;
2. the invalidation clears the Redis hot tier too. The read path and the warm-up
   ask Redis first, so an ArangoDB-only invalidation would leave the warm-up
   finding every variant "cached" and regenerating none. The hot entry is written
   and read back through :class:`GlossaryService` itself, not through a key
   spelled out in this test.
"""

from __future__ import annotations

import fnmatch
from unittest.mock import MagicMock, patch

import pytest

from app.config.settings import settings
from app.domain.models.glossary_term import GlossaryTermCacheEntry
from app.domain.services.glossary_service import GlossaryService
from app.tasks import ai_tasks, celery_app
from app.tasks.glossary_tasks import invalidate_after_reingest, warm_glossary_cache


class _FakeRedis:
    """The slice of redis-py the glossary hot cache uses: get/set/scan_iter/delete."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def set(self, key: str, value: str, ex: int | None = None, nx: bool = False) -> bool:
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    def scan_iter(self, match: str = "*"):
        return iter([key for key in list(self.store) if fnmatch.fnmatchcase(key, match)])

    def delete(self, *keys: str) -> int:
        return sum(1 for key in keys if self.store.pop(key, None) is not None)


def _ingest_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


@pytest.mark.parametrize(
    ("payload", "chained"),
    [
        ({"status": "ok", "files": 12, "chunks": 340}, True),
        # The Knowledge Service found nothing to index: the KB did not change.
        ({"status": "skipped", "reason": "no_yaml_files"}, False),
    ],
)
def test_a_finished_reingest_queues_the_glossary_invalidation(
    monkeypatch: pytest.MonkeyPatch, payload: dict, chained: bool
) -> None:
    monkeypatch.setattr(settings, "knowledge_service_enabled", True)

    with (
        patch("httpx.post", return_value=_ingest_response(payload)) as post,
        patch.object(invalidate_after_reingest, "delay") as invalidate,
    ):
        result = ai_tasks.knowledge_service_ingest.apply()

    assert result.successful(), result.result
    assert result.result == payload
    post.assert_called_once()
    assert invalidate.call_count == (1 if chained else 0)


def test_a_disabled_knowledge_service_queues_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "knowledge_service_enabled", False)

    with patch("httpx.post") as post, patch.object(invalidate_after_reingest, "delay") as invalidate:
        result = ai_tasks.knowledge_service_ingest.apply()

    assert result.result["status"] == "skipped"
    post.assert_not_called()
    invalidate.assert_not_called()


def _service(redis: _FakeRedis) -> GlossaryService:
    cache_repo = MagicMock()
    cache_repo.upsert.side_effect = lambda entry: entry
    return GlossaryService(
        call_budget=MagicMock(),
        term_repo=MagicMock(),
        cache_repo=cache_repo,
        knowledge_adapter=MagicMock(),
        audit_logger=MagicMock(),
        redis_client=redis,
    )


def test_the_invalidation_clears_the_redis_hot_tier_the_reader_consults_first() -> None:
    redis = _FakeRedis()
    service = _service(redis)
    for slug, language, level in [("vpd", "de", "beginner"), ("ec", "en", "expert")]:
        service._store_cache(
            GlossaryTermCacheEntry(term_slug=slug, language=language, expertise_level=level, answer_text="old kb")
        )
    # A neighbour under the glossary prefix that is not a cached answer (the warm-up mutex).
    redis.set("glossary:warm_cache:running", "1")
    assert service._load_cache("vpd", "de", "beginner") is not None  # precondition: a hot hit

    repo = MagicMock()
    repo.invalidate_all.return_value = 2
    with (
        patch("app.tasks.glossary_tasks.get_db"),
        patch("app.tasks.glossary_tasks.ArangoGlossaryTermCacheRepository", return_value=repo),
        patch("app.common.dependencies._get_redis_client", return_value=redis),
        patch.object(warm_glossary_cache, "delay") as warm,
    ):
        result = celery_app.tasks["glossary.invalidate_after_reingest"].apply()

    assert result.successful(), result.result
    assert result.result == 2
    repo.invalidate_all.assert_called_once_with()
    warm.assert_called_once_with()
    # The ArangoDB tier is the repository's (doubled above); the hot tier must be empty
    # as the service reads it, or the warm-up regenerates nothing.
    service._cache.find_valid.return_value = None
    assert service._load_cache("vpd", "de", "beginner") is None
    assert service._load_cache("ec", "en", "expert") is None
    assert redis.get("glossary:warm_cache:running") == "1"


def test_the_invalidation_survives_a_missing_redis() -> None:
    repo = MagicMock()
    repo.invalidate_all.return_value = 0
    with (
        patch("app.tasks.glossary_tasks.get_db"),
        patch("app.tasks.glossary_tasks.ArangoGlossaryTermCacheRepository", return_value=repo),
        patch("app.common.dependencies._get_redis_client", side_effect=RuntimeError("no valkey")),
        patch.object(warm_glossary_cache, "delay") as warm,
    ):
        result = celery_app.tasks["glossary.invalidate_after_reingest"].apply()

    assert result.successful(), result.result
    warm.assert_called_once_with()
