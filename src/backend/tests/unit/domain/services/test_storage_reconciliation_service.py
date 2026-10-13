"""#1834 — what the reconciliation reports and logs, and how it fails.

The deletion behaviour is measured against a real ArangoDB and the real local-fs
adapter in ``tests/integration/test_storage_reconciliation.py``; this module pins
what needs no database: the report carries counts only, and an unanswered
catalogue question aborts the run instead of reading as "nothing holds it".
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta

import pytest
import structlog

from app.common.exceptions import NotFoundError
from app.domain.engines.storage.reconciliation_keys import holder_candidates, is_reconcilable
from app.domain.models.storage import ObjectMetadata
from app.domain.services.storage_reconciliation_service import StorageReconciliationService

NOW = datetime(2026, 10, 2, tzinfo=UTC)
SECRET_TENANT = "tenant-secret-9f3"
KEY = f"t/{SECRET_TENANT}/diary/2026/01/01ARZ3NDEKTSV4RRFFQ69G5FAV.jpg"


class _Store:
    """The three adapter calls the service uses, over a fixed key list."""

    def __init__(self, keys, *, age_hours=72, fail_delete=False):
        self.keys = list(keys)
        self.age = age_hours
        self.fail_delete = fail_delete
        self.deleted: list[str] = []

    async def list_objects(self, prefix, page_token=None):
        return {"keys": [k for k in self.keys if k.startswith(prefix)], "next_page_token": None}

    async def head_object(self, key):
        if key not in self.keys:
            raise NotFoundError("storage object", key)
        modified = NOW - timedelta(hours=self.age)
        return ObjectMetadata(
            key=key,
            size_bytes=10,
            content_type=None,
            etag="",
            last_modified=str(modified.timestamp()),
            user_metadata={},
        )

    async def delete_object(self, key):
        if self.fail_delete:
            raise OSError(f"cannot delete {key}")
        self.keys.remove(key)
        self.deleted.append(key)


class _Repo:
    def __init__(self, held=(), *, fail=False):
        self.held = set(held)
        self.fail = fail

    def held_storage_keys(self, storage_keys):
        if self.fail:
            raise RuntimeError("database unavailable")
        return {k for k in storage_keys if k in self.held}


def _service(store, repo, *, delete=True, cursor=None, max_orphan_fraction=0.5):
    return StorageReconciliationService(
        storage=store,
        attachment_repo=repo,
        min_age=timedelta(hours=24),
        delete_enabled=delete,
        max_objects_per_run=1000,
        max_orphan_fraction=max_orphan_fraction,
        cursor_store=cursor,
        clock=lambda: NOW,
    )


@pytest.mark.asyncio
async def test_the_report_and_the_logs_carry_no_key_tenant_or_path():
    store = _Store([KEY], fail_delete=True)
    with structlog.testing.capture_logs() as logs:
        report = await _service(store, _Repo()).run()

    rendered = repr(report.as_dict()) + repr(logs)
    assert SECRET_TENANT not in rendered
    assert KEY not in rendered
    assert "diary" not in rendered
    assert report.failed == 1


@pytest.mark.asyncio
async def test_an_unanswerable_catalogue_aborts_the_run_and_deletes_nothing():
    store = _Store([KEY])
    with pytest.raises(RuntimeError):
        await _service(store, _Repo(fail=True)).run()
    assert store.deleted == []


@pytest.mark.asyncio
async def test_report_only_counts_what_it_would_delete_and_deletes_nothing():
    store = _Store([KEY])
    report = (await _service(store, _Repo(), delete=False).run()).as_dict()
    assert (report["would_delete"], report["deleted"], report["report_only"]) == (1, 0, True)
    assert store.deleted == []


@pytest.mark.asyncio
async def test_an_object_without_a_readable_age_is_kept():
    class Undated(_Store):
        async def head_object(self, key):
            meta = await super().head_object(key)
            return dataclasses.replace(meta, last_modified=None)

    store = Undated([KEY])
    report = await _service(store, _Repo()).run()
    assert report.undated == 1
    assert store.deleted == []


def test_a_rendition_maps_to_every_original_it_could_have_been_rendered_from():
    rendition = "t/x/diary/2026/01/ULID_t512.webp"
    assert {"t/x/diary/2026/01/ULID.jpg", "t/x/diary/2026/01/ULID.png", rendition} <= holder_candidates(rendition)
    assert holder_candidates("t/x/diary/2026/01/ULID.jpg") == {"t/x/diary/2026/01/ULID.jpg"}


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("t/x/diary/a.jpg", True),
        ("privacy/exports/someone/1.json", False),
        ("t/x/diary/", False),
        ("tmp/stray.jpg", False),
    ],
)
def test_only_tenant_objects_are_judged(key, expected):
    assert is_reconcilable(key) is expected


def _many(count):
    return [f"t/{SECRET_TENANT}/diary/2026/01/{n:026d}.jpg" for n in range(count)]


@pytest.mark.asyncio
async def test_a_catalogue_that_answers_empty_trips_the_brake_and_deletes_nothing():
    """A wrong database over this bucket: every object looks unheld and no query fails."""
    store = _Store(_many(40))
    report = await _service(store, _Repo(held=())).run()

    assert report.brake_tripped is True
    assert report.eligible == 40
    assert report.deleted == 0
    assert store.deleted == []


@pytest.mark.asyncio
async def test_a_plausible_orphan_share_is_deleted_without_tripping_the_brake():
    keys = _many(40)
    store = _Store(keys)
    report = await _service(store, _Repo(held=keys[:30])).run()  # 10 of 40 orphaned

    assert report.brake_tripped is False
    assert sorted(store.deleted) == sorted(keys[30:])


@pytest.mark.asyncio
async def test_a_small_page_is_not_judged_by_its_orphan_share():
    store = _Store(_many(3))
    report = await _service(store, _Repo()).run()

    assert report.brake_tripped is False
    assert report.deleted == 3


@pytest.mark.asyncio
async def test_an_absurd_modification_time_keeps_the_object_instead_of_aborting_the_run():
    class Absurd(_Store):
        async def head_object(self, key):
            meta = await super().head_object(key)
            return dataclasses.replace(meta, last_modified="1e300")

    store = Absurd([KEY])
    report = await _service(store, _Repo()).run()
    assert report.undated == 1
    assert store.deleted == []


class _Cursor:
    def __init__(self, token=None):
        self.token, self.cleared = token, False

    def get(self):
        return self.token

    def set(self, token):
        self.token = token

    def clear(self):
        self.token, self.cleared = None, True


@pytest.mark.asyncio
async def test_a_resume_token_the_backend_rejects_is_dropped_so_the_next_run_starts_over():
    class Rejecting(_Store):
        async def list_objects(self, prefix, page_token=None):
            if page_token is not None:
                raise ValueError("InvalidContinuationToken")
            return await super().list_objects(prefix, page_token)

    cursor = _Cursor("stale")
    with pytest.raises(ValueError):
        await _service(Rejecting([KEY]), _Repo(), cursor=cursor).run()
    assert cursor.cleared is True


@pytest.mark.parametrize(
    "key",
    ["t/x/a\\b.jpg", "t/x//b.jpg", "t/x/./b.jpg", "t/x/../y/b.jpg"],
)
def test_a_key_the_local_adapter_would_resolve_elsewhere_is_never_judged(key):
    assert is_reconcilable(key) is False
