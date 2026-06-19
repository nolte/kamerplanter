"""NFR-013 AC-10 — shared adapter test set.

ONE parametrized suite that runs identically against the ``local-fs`` adapter
(``tmp_path``) and the ``s3`` adapter (``moto`` in-memory S3). Any new method
added to ``IObjectStorageAdapter`` should be exercised here so both backends
stay behaviorally interchangeable (NFR-013 §4.2).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from app.common.exceptions import NotFoundError
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.storage.s3_adapter import S3StorageAdapter

MAX_SIZE = 25 * 1024 * 1024


async def _stream(data: bytes) -> AsyncIterator[bytes]:
    """Yield ``data`` in two chunks to exercise multi-chunk reads."""
    mid = len(data) // 2
    yield data[:mid]
    yield data[mid:]


async def _collect(adapter, key: str) -> bytes:
    out = bytearray()
    async for chunk in await adapter.get_object(key):
        out.extend(chunk)
    return bytes(out)


@pytest.fixture(params=["local-fs", "s3"])
def adapter(request, tmp_path):
    """Yield a fresh storage adapter for each backend."""
    if request.param == "local-fs":
        yield LocalFsStorageAdapter(
            root=str(tmp_path),
            public_base_url="http://localhost:8000/api/v1/storage/token",
            signing_secret="test-secret-please-change",
            max_object_size_bytes=MAX_SIZE,
        )
        return

    moto = pytest.importorskip("moto")
    import boto3

    with moto.mock_aws():
        boto3.client("s3", region_name="eu-central-1").create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-central-1"},
        )
        yield S3StorageAdapter(
            endpoint_url="",
            region="eu-central-1",
            bucket="test-bucket",
            access_key_id="testing",
            secret_access_key="testing",
        )


class TestSharedAdapterContract:
    """NFR-013 §4.2 — backend-neutral behavior."""

    @pytest.mark.asyncio
    async def test_put_get_round_trip_preserves_bytes(self, adapter):
        data = b"hello \x00\x01\x02 binary world" * 100
        ref = await adapter.put_object("t-1/diary/a.bin", _stream(data), "application/octet-stream")
        assert ref.key == "t-1/diary/a.bin"
        assert ref.size_bytes == len(data)
        assert ref.etag

        result = await _collect(adapter, "t-1/diary/a.bin")
        assert result == data

    @pytest.mark.asyncio
    async def test_head_object_returns_size_and_mime(self, adapter):
        data = b"x" * 512
        await adapter.put_object("t-1/diary/b.jpg", _stream(data), "image/jpeg")
        meta = await adapter.head_object("t-1/diary/b.jpg")
        assert meta.key == "t-1/diary/b.jpg"
        assert meta.size_bytes == 512
        assert meta.content_type == "image/jpeg"

    @pytest.mark.asyncio
    async def test_head_object_missing_raises_not_found(self, adapter):
        with pytest.raises(NotFoundError):
            await adapter.head_object("t-1/diary/missing.bin")

    @pytest.mark.asyncio
    async def test_get_object_missing_raises_not_found(self, adapter):
        with pytest.raises(NotFoundError):
            await _collect(adapter, "t-1/diary/missing.bin")

    @pytest.mark.asyncio
    async def test_delete_object_is_idempotent(self, adapter):
        await adapter.put_object("t-1/diary/c.bin", _stream(b"data"), "application/octet-stream")
        await adapter.delete_object("t-1/diary/c.bin")
        # Deleting again must not raise.
        await adapter.delete_object("t-1/diary/c.bin")
        with pytest.raises(NotFoundError):
            await adapter.head_object("t-1/diary/c.bin")

    @pytest.mark.asyncio
    async def test_delete_prefix_counts_and_is_tenant_isolated(self, adapter):
        await adapter.put_object("t-1/diary/x1.bin", _stream(b"1"), "application/octet-stream")
        await adapter.put_object("t-1/diary/x2.bin", _stream(b"2"), "application/octet-stream")
        await adapter.put_object("t-1/ipm/y1.bin", _stream(b"3"), "application/octet-stream")
        await adapter.put_object("t-2/diary/z1.bin", _stream(b"4"), "application/octet-stream")

        deleted = await adapter.delete_prefix("t-1/diary")
        assert deleted == 2

        # Sibling prefix and other tenant must be untouched.
        assert (await adapter.head_object("t-1/ipm/y1.bin")).size_bytes == 1
        assert (await adapter.head_object("t-2/diary/z1.bin")).size_bytes == 1
        with pytest.raises(NotFoundError):
            await adapter.head_object("t-1/diary/x1.bin")

    @pytest.mark.asyncio
    async def test_delete_prefix_missing_returns_zero(self, adapter):
        assert await adapter.delete_prefix("t-9/nothing") == 0

    @pytest.mark.asyncio
    async def test_list_objects_filters_by_prefix(self, adapter):
        await adapter.put_object("t-1/diary/l1.bin", _stream(b"1"), "application/octet-stream")
        await adapter.put_object("t-1/diary/l2.bin", _stream(b"2"), "application/octet-stream")
        await adapter.put_object("t-1/ipm/l3.bin", _stream(b"3"), "application/octet-stream")

        result = await adapter.list_objects("t-1/diary")
        assert set(result["keys"]) == {"t-1/diary/l1.bin", "t-1/diary/l2.bin"}
        assert "next_page_token" in result

    @pytest.mark.asyncio
    async def test_copy_object_duplicates_bytes(self, adapter):
        data = b"copy me" * 50
        await adapter.put_object("t-1/diary/src.bin", _stream(data), "application/octet-stream")
        await adapter.copy_object("t-1/diary/src.bin", "t-1/diary/dst.bin")

        assert await _collect(adapter, "t-1/diary/dst.bin") == data
        # Source remains intact.
        assert await _collect(adapter, "t-1/diary/src.bin") == data

    @pytest.mark.asyncio
    async def test_capabilities_flags_are_present(self, adapter):
        caps = adapter.capabilities
        assert isinstance(caps.supports_presigned_upload, bool)
        assert isinstance(caps.supports_server_side_copy, bool)
        assert caps.max_object_size_bytes > 0

    @pytest.mark.asyncio
    async def test_health_check_reports_ready(self, adapter):
        result = await adapter.health_check()
        assert result["ready"] is True
        assert result["backend"] in ("local-fs", "s3")

    @pytest.mark.asyncio
    async def test_erasure_hooks_return_zero_without_repo(self, adapter):
        assert await adapter.delete_for_user("t-1", "u-1", "all") == 0
        assert await adapter.strip_exif_for_user("t-1", "u-1", "all") == 0
