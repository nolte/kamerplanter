"""#1666 finding 3 — ``get_object`` must stream, not buffer the object and slice it.

Both adapters used to read the whole object into memory and then yield slices
of it: an ``AsyncIterator`` in the signature, a full in-memory copy underneath.
For the Art. 15 download that is a complete copy of an account held in the
worker per request. The tests below measure what was actually read from the
backend by the time a consumer has taken one chunk.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.data_access.storage import local_fs_adapter, s3_adapter
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.storage.s3_adapter import S3StorageAdapter

KEY = "t/t-1/exports/bundle.json"


@pytest.mark.asyncio
class TestLocalFsStreams:
    async def test_bytes_not_yet_consumed_are_read_from_disk_not_memory(self, tmp_path):
        """Truncate the file after the first chunk: a buffered copy would still yield it all."""
        chunk = local_fs_adapter._CHUNK_SIZE
        adapter = LocalFsStorageAdapter(
            root=str(tmp_path),
            public_base_url="http://localhost/api/v1/storage/token",
            signing_secret="test-secret-please-change",
            max_object_size_bytes=10 * chunk,
        )
        path = tmp_path / KEY
        path.parent.mkdir(parents=True)
        path.write_bytes(b"x" * (3 * chunk))

        stream = await adapter.get_object(KEY)
        first = await anext(stream)
        with path.open("r+b") as handle:
            handle.truncate(len(first))
        rest = [part async for part in stream]

        assert len(first) == chunk
        assert sum(len(part) for part in rest) == 0

    async def test_a_missing_object_is_reported_before_streaming(self, tmp_path):
        adapter = LocalFsStorageAdapter(
            root=str(tmp_path),
            public_base_url="http://localhost/api/v1/storage/token",
            signing_secret="test-secret-please-change",
            max_object_size_bytes=1024,
        )
        with pytest.raises(NotFoundError):
            await adapter.get_object(KEY)


class _Body:
    """A botocore ``StreamingBody`` stand-in recording how it was read."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos = 0
        self.reads: list[int | None] = []
        self.closed = False

    def read(self, amt: int | None = None) -> bytes:
        self.reads.append(amt)
        end = len(self._data) if amt is None else self._pos + amt
        part = self._data[self._pos : end]
        self._pos += len(part)
        return part

    def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
class TestS3Streams:
    def _adapter(self, body: _Body) -> S3StorageAdapter:
        adapter = S3StorageAdapter(
            endpoint_url="http://localhost:9000",
            region="eu-central-1",
            bucket="bk",
            access_key_id="x",
            secret_access_key="y",
            use_path_style=True,
        )
        client: Any = MagicMock()
        client.exceptions.NoSuchKey = type("NoSuchKey", (Exception,), {})
        client.get_object.return_value = {"Body": body}
        adapter._client = client
        return adapter

    async def test_the_body_is_read_chunk_by_chunk_and_closed(self):
        chunk = s3_adapter._CHUNK_SIZE
        body = _Body(b"y" * (2 * chunk + 10))
        adapter = self._adapter(body)

        stream = await adapter.get_object(KEY)
        first = await anext(stream)

        assert len(first) == chunk
        assert body.reads == [chunk], "one chunk consumed must mean one chunk read"

        rest = b"".join([part async for part in stream])
        assert len(first) + len(rest) == 2 * chunk + 10
        assert None not in body.reads, "a whole-body read() is the buffering this replaces"
        assert body.closed
