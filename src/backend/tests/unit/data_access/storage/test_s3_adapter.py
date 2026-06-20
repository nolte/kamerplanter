"""NFR-013 §4.2 — S3 adapter constructor, capabilities and pre-sign specifics.

Migrated from ``tests/unit/data_access/external/test_s3_storage_adapter.py``.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.storage.s3_adapter import S3StorageAdapter
from app.domain.models.storage import S3_DEFAULT_CAPABILITIES


class TestS3StorageAdapterConstructor:
    def test_force_tls_blocks_plain_http_endpoints_outside_localhost(self):
        with pytest.raises(ValueError, match="STORAGE_S3_FORCE_TLS"):
            S3StorageAdapter(
                endpoint_url="http://s3.example.com",
                region="eu-central-1",
                bucket="bk",
                access_key_id="x",
                secret_access_key="y",
                force_tls=True,
            )

    def test_force_tls_allows_plain_http_for_localhost_minio(self):
        adapter = S3StorageAdapter(
            endpoint_url="http://localhost:9000",
            region="eu-central-1",
            bucket="bk",
            access_key_id="x",
            secret_access_key="y",
            use_path_style=True,
            force_tls=True,
        )
        assert adapter.capabilities is S3_DEFAULT_CAPABILITIES

    def test_force_tls_can_be_opted_out(self):
        adapter = S3StorageAdapter(
            endpoint_url="http://internal.minio:9000",
            region="eu-central-1",
            bucket="bk",
            access_key_id="x",
            secret_access_key="y",
            force_tls=False,
        )
        assert adapter.capabilities.supports_presigned_upload is True


class TestCapabilities:
    def test_default_capabilities_advertise_full_s3_feature_set(self):
        caps = S3_DEFAULT_CAPABILITIES
        assert caps.supports_presigned_upload is True
        assert caps.supports_presigned_download is True
        assert caps.supports_server_side_copy is True
        assert caps.supports_server_side_encryption is True
        assert caps.supports_versioning is True
        assert caps.supports_lifecycle_rules is True
        assert caps.max_object_size_bytes == 5 * 1024 * 1024 * 1024
        assert caps.requires_per_user_oauth is False


class TestPresignUrls:
    def _adapter(self) -> S3StorageAdapter:
        return S3StorageAdapter(
            endpoint_url="",
            region="eu-central-1",
            bucket="bk",
            access_key_id="testing",
            secret_access_key="testing",
        )

    def test_presign_download_url_is_signed(self):
        url = self._adapter().presign_download_url("t-1/diary/a.jpg", ttl_seconds=300)
        assert "t-1/diary/a.jpg" in url
        assert "X-Amz-Signature" in url or "Signature" in url

    def test_presign_upload_url_is_signed(self):
        url = self._adapter().presign_upload_url("t-1/diary/b.jpg", "image/jpeg", ttl_seconds=300)
        assert "t-1/diary/b.jpg" in url


class TestEraserHooks:
    def _adapter(self) -> S3StorageAdapter:
        return S3StorageAdapter(
            endpoint_url="https://s3.eu-central-1.amazonaws.com",
            region="eu-central-1",
            bucket="bk",
            access_key_id="x",
            secret_access_key="y",
        )

    @pytest.mark.asyncio
    async def test_delete_for_user_returns_zero_without_repo(self):
        assert await self._adapter().delete_for_user("t-1", "u-1", "all") == 0

    @pytest.mark.asyncio
    async def test_strip_exif_for_user_returns_zero_without_repo(self):
        assert await self._adapter().strip_exif_for_user("t-1", "u-1", "all") == 0

    @pytest.mark.asyncio
    async def test_strip_exif_skips_heic_but_counts_it(self):
        """SEC-005 — HEIC is not put back and is logged as skipped."""
        import structlog

        att_heic = MagicMock()
        att_heic.storage_key = "t-1/diary/photo.heic"
        att_heic.mime_type = "image/heic"
        repo = MagicMock()
        repo.find_by_user.return_value = [att_heic]

        adapter = S3StorageAdapter(
            endpoint_url="https://s3.eu-central-1.amazonaws.com",
            region="eu-central-1",
            bucket="bk",
            access_key_id="x",
            secret_access_key="y",
            attachment_repo=repo,
        )
        adapter._get_sync = MagicMock(side_effect=AssertionError("HEIC must not be read"))
        adapter._put_sync = MagicMock(side_effect=AssertionError("HEIC must not be written"))

        with structlog.testing.capture_logs() as logs:
            rewritten = await adapter.strip_exif_for_user("t-1", "u-1", "all")

        assert rewritten == 0
        events = {log["event"] for log in logs}
        assert "exif_strip_unsupported_format" in events


class TestDeletePrefixGuard:
    """SEC-004 — over-broad delete prefixes are rejected before listing."""

    def _adapter(self) -> S3StorageAdapter:
        return S3StorageAdapter(
            endpoint_url="https://s3.eu-central-1.amazonaws.com",
            region="eu-central-1",
            bucket="bk",
            access_key_id="x",
            secret_access_key="y",
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad", ["", "t", "t/", "t//"])
    async def test_delete_prefix_rejects_over_broad(self, bad):
        adapter = self._adapter()
        client = MagicMock()
        adapter._client = client
        with pytest.raises(ValueError):
            await adapter.delete_prefix(bad)
        # The S3 paginator must never be touched for a rejected prefix.
        client.get_paginator.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_prefix_passes_scoped_prefix_to_s3(self):
        adapter = self._adapter()
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [{"Contents": [{"Key": "t/aaa/diary/x.jpg"}]}]
        client.get_paginator.return_value = paginator
        adapter._client = client

        deleted = await adapter.delete_prefix("t/aaa/")

        assert deleted == 1
        # The tenant-scoped trailing slash is preserved in the S3 listing.
        assert paginator.paginate.call_args.kwargs["Prefix"] == "t/aaa/"


class TestKmsEncryption:
    def test_encryption_args_set_when_kms_key_present(self):
        adapter = S3StorageAdapter(
            endpoint_url="",
            region="eu-central-1",
            bucket="bk",
            access_key_id="x",
            secret_access_key="y",
            kms_key_id="arn:aws:kms:eu-central-1:123:key/abc",
        )
        args = adapter._encryption_args()
        assert args["ServerSideEncryption"] == "aws:kms"
        assert args["SSEKMSKeyId"].endswith("abc")

    def test_no_encryption_args_without_kms_key(self):
        adapter = S3StorageAdapter(
            endpoint_url="",
            region="eu-central-1",
            bucket="bk",
            access_key_id="x",
            secret_access_key="y",
        )
        assert adapter._encryption_args() == {}
