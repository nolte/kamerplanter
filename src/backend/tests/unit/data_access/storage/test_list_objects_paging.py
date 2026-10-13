"""#1834 — both adapters list ``t/`` in bounded, ordered, resumable pages.

The reconciliation walks every object of every tenant. Before this the local-fs
adapter returned its whole tree in one list (``rglob`` + sort) and the S3 adapter's
continuation was never exercised against the real client's response shape.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from botocore.stub import Stubber

from app.data_access.storage import local_fs_adapter
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.storage.s3_adapter import S3StorageAdapter


async def _stream(data: bytes) -> AsyncIterator[bytes]:
    yield data


def _local(tmp_path) -> LocalFsStorageAdapter:
    return LocalFsStorageAdapter(
        root=str(tmp_path),
        public_base_url="http://localhost",
        signing_secret="unit-test-secret",
        max_object_size_bytes=1024 * 1024,
    )


async def _all_pages(adapter, prefix: str) -> list[list[str]]:
    pages, token = [], None
    while True:
        page = await adapter.list_objects(prefix, token)
        pages.append(page["keys"])
        token = page["next_page_token"]
        if token is None:
            return pages


@pytest.mark.asyncio
async def test_local_listing_is_paged_and_in_bucket_order(tmp_path, monkeypatch):
    monkeypatch.setattr(local_fs_adapter, "LIST_PAGE_SIZE", 2)
    adapter = _local(tmp_path)
    # ``a0`` sorts after ``a/b`` in a bucket listing ('0' > '/'), ``a-1`` before it:
    # a per-directory sort of files-then-subdirectories would get this wrong.
    keys = ["t/a-1.jpg", "t/a/b.jpg", "t/a0.jpg", "t/a/c/d.jpg", "t/z.jpg"]
    for key in keys:
        await adapter.put_object(key, _stream(b"x"), "image/jpeg")

    pages = await _all_pages(adapter, "t/")

    assert [len(page) for page in pages] == [2, 2, 1]
    assert [key for page in pages for key in page] == sorted(keys)


@pytest.mark.asyncio
async def test_local_listing_resumes_after_a_token_and_skips_sidecar_files(tmp_path, monkeypatch):
    monkeypatch.setattr(local_fs_adapter, "LIST_PAGE_SIZE", 10)
    adapter = _local(tmp_path)
    for key in ["t/a/1.jpg", "t/b/2.jpg", "t/c/3.jpg", "other/4.jpg"]:
        await adapter.put_object(key, _stream(b"x"), "image/jpeg")

    resumed = await adapter.list_objects("t/", "t/b/2.jpg")

    assert resumed["keys"] == ["t/c/3.jpg"], "resume is strictly after the token and inside the prefix"
    assert resumed["next_page_token"] is None


@pytest.mark.asyncio
async def test_local_listing_of_an_empty_root_is_empty(tmp_path):
    assert await _local(tmp_path).list_objects("t/") == {"keys": [], "next_page_token": None}


@pytest.mark.asyncio
async def test_s3_listing_follows_the_continuation_token():
    adapter = S3StorageAdapter(
        endpoint_url="https://s3.eu-central-1.amazonaws.com",
        region="eu-central-1",
        bucket="bk",
        access_key_id="x",
        secret_access_key="y",
    )
    client = adapter._get_client()
    stub_time = datetime(2026, 1, 1, tzinfo=UTC)
    with Stubber(client) as stubber:
        stubber.add_response(
            "list_objects_v2",
            {
                "IsTruncated": True,
                "NextContinuationToken": "tok-2",
                "Contents": [{"Key": "t/a.jpg", "LastModified": stub_time, "Size": 1}],
            },
            {"Bucket": "bk", "Prefix": "t/"},
        )
        stubber.add_response(
            "list_objects_v2",
            {"IsTruncated": False, "Contents": [{"Key": "t/b.jpg", "LastModified": stub_time, "Size": 1}]},
            {"Bucket": "bk", "Prefix": "t/", "ContinuationToken": "tok-2"},
        )
        pages = await _all_pages(adapter, "t/")

    assert pages == [["t/a.jpg"], ["t/b.jpg"]]


@pytest.mark.asyncio
async def test_local_listing_does_not_list_symlinks(tmp_path):
    """A listed link would be unlinked *through* by the delete that follows it."""
    adapter = _local(tmp_path)
    await adapter.put_object("t/a/real.jpg", _stream(b"x"), "image/jpeg")
    (tmp_path / "t" / "a" / "link.jpg").symlink_to(tmp_path / "t" / "a" / "real.jpg")

    assert (await adapter.list_objects("t/"))["keys"] == ["t/a/real.jpg"]
