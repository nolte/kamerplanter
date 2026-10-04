"""#2108 — the thumbnail task gives up on permanent failures, and dispatch is claimed once per window."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from celery.exceptions import Retry
from redis.exceptions import ConnectionError as RedisConnectionError

from app.common.enums import AttachmentCategory
from app.common.exceptions import ImagePixelLimitError
from app.data_access.external.rendition_dispatch_claims import (
    DISPATCH_WINDOW_SECONDS,
    MemoryRenditionDispatchClaims,
    RedisRenditionDispatchClaims,
)
from app.domain.models.attachment import Attachment
from app.tasks import storage_tasks


def _attachment(**overrides: object) -> Attachment:
    values: dict[str, object] = {
        "key": "att1",
        "tenant_key": "t-1",
        "mime_type": "image/jpeg",
        "byte_size": 10,
        "sha256": "0" * 64,
        "original_filename": "a.jpg",
        "created_by": "u-1",
        "category": AttachmentCategory.DIARY,
        "storage_key": "t/t-1/diary/2026/10/01JABCDEFGHJKMNPQRSTVWXYZ0.jpg",
    }
    values.update(overrides)
    return Attachment(**values)


class _Repo:
    def __init__(self) -> None:
        self.marked: list[tuple[str, str]] = []

    def get(self, key: str, tenant_key: str) -> Attachment:
        return _attachment()

    def mark_renditions_failed(self, tenant_key: str, storage_key: str) -> int:
        self.marked.append((tenant_key, storage_key))
        return 1


class TestPermanentFailure:
    def test_a_pixel_bomb_is_marked_failed_and_not_retried(self) -> None:
        repo = _Repo()

        async def _bomb(attachment_id: str, tenant_key: str) -> dict:
            raise ImagePixelLimitError(40_000_000)

        with (
            patch.object(storage_tasks, "_generate", _bomb),
            patch.object(storage_tasks, "get_attachment_repo", return_value=repo),
            patch.object(storage_tasks.generate_thumbnails, "retry") as retry,
        ):
            result = storage_tasks.generate_thumbnails.run("att1", "t-1")

        assert result["reason"] == "renditions_failed"
        retry.assert_not_called()
        assert repo.marked == [("t-1", _attachment().storage_key)]

    def test_a_transient_failure_is_retried_and_not_marked(self) -> None:
        repo = _Repo()

        async def _flaky(attachment_id: str, tenant_key: str) -> dict:
            raise OSError("storage briefly unavailable")

        with (
            patch.object(storage_tasks, "_generate", _flaky),
            patch.object(storage_tasks, "get_attachment_repo", return_value=repo),
            # Outside a worker Celery's ``retry`` re-raises the cause; stand in for the worker.
            patch.object(storage_tasks.generate_thumbnails, "retry", side_effect=Retry()) as retry,
            pytest.raises(Retry),
        ):
            storage_tasks.generate_thumbnails.run("att1", "t-1")

        retry.assert_called_once()
        assert repo.marked == []

    def test_the_last_failed_retry_marks_the_attachment(self) -> None:
        repo = _Repo()

        async def _flaky(attachment_id: str, tenant_key: str) -> dict:
            raise OSError("storage still unavailable")

        task = storage_tasks.generate_thumbnails
        task.push_request(retries=task.max_retries)
        try:
            with (
                patch.object(storage_tasks, "_generate", _flaky),
                patch.object(storage_tasks, "get_attachment_repo", return_value=repo),
            ):
                result = task.run("att1", "t-1")
        finally:
            task.pop_request()

        assert result["reason"] == "renditions_failed"
        assert repo.marked == [("t-1", _attachment().storage_key)]


class TestRequestThumbnails:
    def test_one_dispatch_per_window(self) -> None:
        claims = MemoryRenditionDispatchClaims()
        with patch.object(storage_tasks.generate_thumbnails, "delay") as delay:
            answers = [storage_tasks.request_thumbnails(_attachment(), claims) for _ in range(5)]

        assert answers == [True] * 5
        delay.assert_called_once_with("att1", "t-1")

    def test_failed_renditions_and_unrendered_types_dispatch_nothing(self) -> None:
        claims = MemoryRenditionDispatchClaims()
        with patch.object(storage_tasks.generate_thumbnails, "delay") as delay:
            failed = storage_tasks.request_thumbnails(_attachment(renditions_failed=True), claims)
            pdf = storage_tasks.request_thumbnails(_attachment(mime_type="application/pdf"), claims)

        assert (failed, pdf) == (False, False)
        delay.assert_not_called()


class _FakeRedis:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.keys: dict[str, int | None] = {}

    def set(self, name: str, value: str, ex: int | None = None, nx: bool = False) -> object:
        if self.fail:
            raise RedisConnectionError("valkey down")
        if nx and name in self.keys:
            return None
        self.keys[name] = ex
        return True


class TestRedisClaims:
    def test_the_claim_is_set_nx_with_the_window_as_ttl(self) -> None:
        redis = _FakeRedis()
        claims = RedisRenditionDispatchClaims(redis, fallback=MemoryRenditionDispatchClaims())

        assert [claims.claim("att1"), claims.claim("att1"), claims.claim("att2")] == [True, False, True]
        assert redis.keys == {
            "kp:thumb:dispatch:att1": DISPATCH_WINDOW_SECONDS,
            "kp:thumb:dispatch:att2": DISPATCH_WINDOW_SECONDS,
        }

    def test_a_valkey_outage_degrades_to_the_in_process_tier_not_to_always(self) -> None:
        claims = RedisRenditionDispatchClaims(_FakeRedis(fail=True), fallback=MemoryRenditionDispatchClaims())

        assert [claims.claim("att1"), claims.claim("att1")] == [True, False]

    def test_the_attachment_service_provider_wires_the_valkey_claim(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.common import dependencies

        redis = _FakeRedis()
        monkeypatch.setattr(dependencies, "_get_redis_client", lambda: redis)
        monkeypatch.setattr(dependencies, "get_object_storage", lambda: object())
        monkeypatch.setattr(dependencies, "get_attachment_repo", lambda: object())

        service = dependencies.get_attachment_service()

        assert isinstance(service._rendition_claims, RedisRenditionDispatchClaims)
        assert service._rendition_claims.claim("att9") is True
        assert "kp:thumb:dispatch:att9" in redis.keys
