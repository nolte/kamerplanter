"""NFR-013 §4.2 — local-fs adapter specifics (token URLs, path safety, capabilities)."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

import pytest

from app.data_access.storage.local_fs_adapter import (
    LocalFsStorageAdapter,
    _sanitize_key,
    verify_token,
)

SECRET = "unit-test-secret"
MAX_SIZE = 25 * 1024 * 1024


def _adapter(tmp_path) -> LocalFsStorageAdapter:
    return LocalFsStorageAdapter(
        root=str(tmp_path),
        public_base_url="http://localhost:8000/api/v1/storage/token",
        signing_secret=SECRET,
        max_object_size_bytes=MAX_SIZE,
    )


async def _stream(data: bytes) -> AsyncIterator[bytes]:
    yield data


class TestKeySanitization:
    @pytest.mark.parametrize("bad_key", ["", "   ", "../escape", "a/../../b", "\\..\\x"])
    def test_rejects_unsafe_keys(self, bad_key):
        with pytest.raises(ValueError):
            _sanitize_key(bad_key)

    def test_normalizes_leading_slash_and_backslash(self):
        # A leading slash is stripped to a safe relative key, not rejected.
        assert _sanitize_key("/t-1/diary/a.bin").as_posix() == "t-1/diary/a.bin"
        assert _sanitize_key("/etc/passwd").as_posix() == "etc/passwd"
        assert _sanitize_key("t-1\\diary\\a.bin").as_posix() == "t-1/diary/a.bin"

    @pytest.mark.asyncio
    async def test_put_rejects_traversal_key(self, tmp_path):
        adapter = _adapter(tmp_path)
        with pytest.raises(ValueError):
            await adapter.put_object("../outside.bin", _stream(b"x"), "application/octet-stream")


class TestCapabilities:
    def test_local_fs_disables_presign_and_server_side_copy(self, tmp_path):
        caps = _adapter(tmp_path).capabilities
        assert caps.supports_presigned_upload is False
        assert caps.supports_presigned_download is False
        assert caps.supports_server_side_copy is False
        assert caps.supports_server_side_encryption is False
        assert caps.max_object_size_bytes == MAX_SIZE
        assert caps.requires_per_user_oauth is False


class TestSignedTokenUrls:
    def test_presign_download_url_is_verifiable(self, tmp_path):
        adapter = _adapter(tmp_path)
        url = adapter.presign_download_url("t-1/diary/a.jpg", ttl_seconds=300, response_disposition="inline")
        assert url.startswith("http://localhost:8000/api/v1/storage/token/")
        token = url.rsplit("/", 1)[1]
        payload = adapter.verify_token(token)
        assert payload is not None
        assert payload["op"] == "download"
        assert payload["key"] == "t-1/diary/a.jpg"
        assert payload["disposition"] == "inline"

    def test_presign_upload_url_embeds_constraints(self, tmp_path):
        adapter = _adapter(tmp_path)
        url = adapter.presign_upload_url("t-1/diary/b.jpg", "image/jpeg", ttl_seconds=300)
        token = url.rsplit("/", 1)[1]
        payload = adapter.verify_token(token)
        assert payload is not None
        assert payload["op"] == "upload"
        assert payload["mime_type"] == "image/jpeg"
        assert payload["max_size"] == MAX_SIZE

    def test_module_level_verify_token_matches(self, tmp_path):
        adapter = _adapter(tmp_path)
        url = adapter.presign_download_url("t-1/diary/c.jpg")
        token = url.rsplit("/", 1)[1]
        assert verify_token(token, SECRET) is not None
        assert verify_token(token, "wrong-secret") is None

    def test_tampered_token_is_rejected(self, tmp_path):
        adapter = _adapter(tmp_path)
        url = adapter.presign_download_url("t-1/diary/d.jpg")
        token = url.rsplit("/", 1)[1]
        body, sig = token.split(".", 1)
        tampered = f"{body}.{'A' * len(sig)}"
        assert adapter.verify_token(tampered) is None

    def test_expired_token_is_rejected(self, tmp_path):
        adapter = _adapter(tmp_path)
        token = adapter._make_token({"op": "download", "key": "k", "exp": int(time.time()) - 10})
        assert adapter.verify_token(token) is None

    def test_garbage_token_is_rejected(self, tmp_path):
        adapter = _adapter(tmp_path)
        assert adapter.verify_token("not-a-token") is None
        assert adapter.verify_token("") is None


class TestConstructorValidation:
    def test_empty_signing_secret_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="signing secret"):
            LocalFsStorageAdapter(
                root=str(tmp_path),
                public_base_url="http://x",
                signing_secret="",
                max_object_size_bytes=MAX_SIZE,
            )


class TestEraserHooksWithRepo:
    """delete_for_user / strip_exif_for_user with a fake attachment repo."""

    class _FakeAttachment:
        def __init__(self, storage_key: str, mime_type: str) -> None:
            self.storage_key = storage_key
            self.mime_type = mime_type

    class _FakeRepo:
        def __init__(self, attachments) -> None:
            self._attachments = attachments

        def find_by_user(self, tenant_key, user_key, categories=None):
            return self._attachments

    @pytest.mark.asyncio
    async def test_delete_for_user_deletes_user_objects(self, tmp_path):
        attachments = [
            self._FakeAttachment("t-1/diary/u1.jpg", "image/jpeg"),
            self._FakeAttachment("t-1/diary/u2.png", "image/png"),
        ]
        adapter = LocalFsStorageAdapter(
            root=str(tmp_path),
            public_base_url="http://x",
            signing_secret=SECRET,
            max_object_size_bytes=MAX_SIZE,
            attachment_repo=self._FakeRepo(attachments),
        )
        for att in attachments:
            await adapter.put_object(att.storage_key, _stream(b"img"), att.mime_type)

        deleted = await adapter.delete_for_user("t-1", "u-1", "all")
        assert deleted == 2
        result = await adapter.list_objects("t-1")
        assert result["keys"] == []

    @pytest.mark.asyncio
    async def test_strip_exif_rewrites_images_only(self, tmp_path):
        attachments = [
            self._FakeAttachment("t-1/diary/i.jpg", "image/jpeg"),
            self._FakeAttachment("t-1/export/doc.zip", "application/zip"),
        ]
        adapter = LocalFsStorageAdapter(
            root=str(tmp_path),
            public_base_url="http://x",
            signing_secret=SECRET,
            max_object_size_bytes=MAX_SIZE,
            attachment_repo=self._FakeRepo(attachments),
        )
        for att in attachments:
            await adapter.put_object(att.storage_key, _stream(b"payload"), att.mime_type)

        rewritten = await adapter.strip_exif_for_user("t-1", "u-1", "all")
        assert rewritten == 1
