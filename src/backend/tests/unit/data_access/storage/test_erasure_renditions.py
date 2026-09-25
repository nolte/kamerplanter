"""#1760 — the Art. 17 storage hard-delete removes an image's renditions too.

``delete_for_user`` is the Phase 0 ``hard_delete`` hook. It used to delete each
attachment's original object only; the WebP renditions the thumbnail task writes
next to it (``<stem>_t{128,512,1280}.webp``) stayed in object storage with no
record pointing at them once the ArangoDB plan removed the attachment.

The renditions here are written by the production task body
(:func:`app.tasks.storage_tasks._generate`) from a real JPEG, so the test holds
the erasure against the keys the product actually writes, not against a key
format restated in the test. Both adapters run the same scenario.
"""

from __future__ import annotations

import io
from collections.abc import AsyncIterator
from dataclasses import dataclass
from unittest.mock import patch

import pytest
from PIL import Image

from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.storage.s3_adapter import S3StorageAdapter
from app.tasks import storage_tasks

TENANT = "t-1"
USER = "u-1"


@dataclass
class _Attachment:
    key: str
    storage_key: str
    mime_type: str


class _AttachmentRepo:
    """Just the two reads the thumbnail task and the erasure hook make."""

    def __init__(self, attachments: list[_Attachment]) -> None:
        self._attachments = attachments

    def get(self, attachment_id: str, tenant_key: str) -> _Attachment | None:
        return next((a for a in self._attachments if a.key == attachment_id), None)

    def find_by_user(self, tenant_key, user_key, categories=None):  # type: ignore[no-untyped-def]
        return list(self._attachments)


class _FakeS3Client:
    """In-memory stand-in for the boto3 calls the adapter makes."""

    class exceptions:  # noqa: N801 — mirrors boto3's attribute name
        class NoSuchKey(Exception):  # noqa: N818 — mirrors boto3's class name
            pass

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_object(self, *, Bucket, Key, Body, **_kwargs):  # type: ignore[no-untyped-def]  # noqa: N803
        self.objects[Key] = Body
        return {"ETag": '"x"'}

    def get_object(self, *, Bucket, Key):  # type: ignore[no-untyped-def]  # noqa: N803
        if Key not in self.objects:
            raise self.exceptions.NoSuchKey(Key)
        return {"Body": io.BytesIO(self.objects[Key])}

    def delete_object(self, *, Bucket, Key):  # type: ignore[no-untyped-def]  # noqa: N803
        self.objects.pop(Key, None)


def _jpeg() -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (1600, 1200), (40, 120, 60)).save(out, format="JPEG")
    return out.getvalue()


async def _stream(data: bytes) -> AsyncIterator[bytes]:
    yield data


def _local(tmp_path, repo: _AttachmentRepo):  # type: ignore[no-untyped-def]
    adapter = LocalFsStorageAdapter(
        root=str(tmp_path),
        public_base_url="http://x",
        signing_secret="unit-test-secret",
        max_object_size_bytes=25 * 1024 * 1024,
        attachment_repo=repo,
    )

    async def keys() -> list[str]:
        return sorted((await adapter.list_objects(f"t/{TENANT}/"))["keys"])

    return adapter, keys


def _s3(tmp_path, repo: _AttachmentRepo):  # type: ignore[no-untyped-def]
    adapter = S3StorageAdapter(
        endpoint_url="https://s3.eu-central-1.amazonaws.com",
        region="eu-central-1",
        bucket="bk",
        access_key_id="x",
        secret_access_key="y",
        attachment_repo=repo,
    )
    client = _FakeS3Client()
    adapter._get_client = lambda: client  # type: ignore[method-assign]

    async def keys() -> list[str]:
        return sorted(client.objects)

    return adapter, keys


@pytest.mark.asyncio
@pytest.mark.parametrize("build", [_local, _s3], ids=["local_fs", "s3"])
async def test_delete_for_user_removes_the_renditions_the_thumbnail_task_wrote(tmp_path, build):
    photo = _Attachment(key="a1", storage_key=f"t/{TENANT}/pest_reference/2026/09/01J.jpg", mime_type="image/jpeg")
    document = _Attachment(
        key="a2", storage_key=f"t/{TENANT}/pest_reference/2026/09/01K.pdf", mime_type="application/pdf"
    )
    repo = _AttachmentRepo([photo, document])
    adapter, keys = build(tmp_path, repo)
    await adapter.put_object(photo.storage_key, _stream(_jpeg()), photo.mime_type)
    await adapter.put_object(document.storage_key, _stream(b"%PDF-1.4"), document.mime_type)

    with (
        patch.object(storage_tasks, "get_object_storage", return_value=adapter),
        patch.object(storage_tasks, "get_attachment_repo", return_value=repo),
    ):
        outcome = await storage_tasks._generate(photo.key, TENANT)
    assert outcome["generated"] == 3
    before = await keys()
    assert len(before) == 5, before  # two originals + three renditions of the photo

    deleted = await adapter.delete_for_user(TENANT, USER, "all")

    assert await keys() == []
    # The count stays "attachments erased", not "objects erased".
    assert deleted == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("build", [_local, _s3], ids=["local_fs", "s3"])
async def test_delete_for_user_tolerates_renditions_that_were_never_generated(tmp_path, build):
    """The thumbnail task is asynchronous; an erasure can overtake it."""
    photo = _Attachment(key="a1", storage_key=f"t/{TENANT}/diary/2026/09/01J.png", mime_type="image/png")
    repo = _AttachmentRepo([photo])
    adapter, keys = build(tmp_path, repo)
    await adapter.put_object(photo.storage_key, _stream(b"png"), photo.mime_type)

    assert await adapter.delete_for_user(TENANT, USER, "all") == 1
    assert await keys() == []
