"""NFR-013 S3StorageAdapter scaffolding tests.

The adapter is a stub today — methods raise ``NotImplementedError`` but
the constructor, capabilities and the W-007 hooks already behave like
contract-conformant code.
"""

import pytest

from app.data_access.external.s3_storage_adapter import (
    S3_DEFAULT_CAPABILITIES,
    S3StorageAdapter,
)


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


class TestEraserHooks:
    """REQ-025 W-007 hooks — stubbed but contract-conformant."""

    def _adapter(self) -> S3StorageAdapter:
        return S3StorageAdapter(
            endpoint_url="https://s3.eu-central-1.amazonaws.com",
            region="eu-central-1",
            bucket="bk",
            access_key_id="x",
            secret_access_key="y",
        )

    @pytest.mark.asyncio
    async def test_delete_for_user_returns_zero_until_repo_wired(self):
        adapter = self._adapter()
        assert await adapter.delete_for_user("t-1", "u-1", "user_personal") == 0

    @pytest.mark.asyncio
    async def test_strip_exif_for_user_returns_zero_until_repo_wired(self):
        adapter = self._adapter()
        assert await adapter.strip_exif_for_user("t-1", "u-1", "user_personal") == 0


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_returns_scaffold_status(self):
        adapter = S3StorageAdapter(
            endpoint_url="https://s3.eu-central-1.amazonaws.com",
            region="eu-central-1",
            bucket="bk",
            access_key_id="x",
            secret_access_key="y",
        )
        result = await adapter.health_check()
        assert result["backend"] == "s3"
        assert result["bucket"] == "bk"
        assert result["ready"] is False
        assert "scaffolding" in result["reason"]
