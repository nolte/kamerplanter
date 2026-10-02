"""#1773 — the storage adapters log object keys without the account key in them.

The export bundle is stored at ``privacy/exports/<user_key>/<export_key>.json``
(``DataExportEngine.bundle_object_key``). Both adapters logged the raw key on
every put / delete / copy, so each Art. 15 export — and its removal during an
erasure — wrote the account key into a log stream that has no retention rule
(NFR-011). The adapters now log ``loggable_storage_key(key)``: the account
segment masked, the export key kept for correlation, every other key unchanged.

The adapter tests drive the real ``delete_object`` / ``put_object`` / ``copy_object``
(local fs against ``tmp_path``; S3 against a mocked boto3 client, the approach
``test_s3_adapter`` uses) and read what structlog receives.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import structlog.testing

from app.common.log_privacy import log_tenant
from app.config.settings import settings
from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from app.data_access.storage.s3_adapter import S3StorageAdapter
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.storage.export_bundle_key import (
    EXPORT_BUNDLE_NAMESPACE,
    REDACTED_SUBJECT_SEGMENT,
    loggable_storage_key,
)

#: Distinctive, so a substring hit cannot be a coincidence.
USER_KEY = "subject-2d9f40"
EXPORT_KEY = "exp-77"
BUNDLE_KEY = DataExportEngine.bundle_object_key(USER_KEY, EXPORT_KEY)
#: #1966: an attachment key — the object every delete path touches.
TENANT_KEY = "tenant-1966-owner-garden"
ATTACHMENT_KEY = f"t/{TENANT_KEY}/plant_photo/2026/10/01HZX3K9ABCDEFGHJKMNPQRSTV.jpg"


@pytest.fixture(autouse=True)
def _log_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


def _leaks(logs: list[dict[str, Any]], *needles: str) -> list[str]:
    return [
        f"{event.get('event')}.{field}"
        for event in logs
        for field, value in event.items()
        if any(needle in str(value) for needle in (needles or (USER_KEY,)))
    ]


async def _stream(data: bytes = b"{}") -> AsyncIterator[bytes]:
    yield data


class TestLoggableStorageKey:
    def test_the_bundle_key_loses_its_account_segment_and_keeps_the_export_key(self) -> None:
        logged = loggable_storage_key(BUNDLE_KEY)

        assert USER_KEY not in logged
        assert logged == f"{EXPORT_BUNDLE_NAMESPACE}{REDACTED_SUBJECT_SEGMENT}/{EXPORT_KEY}.json"

    def test_the_builder_and_the_redaction_share_one_shape(self) -> None:
        """If the builder's shape moved, the redaction would silently stop matching it."""
        for user_key in ("u-1", "8271634", "subject-with-dashes"):
            assert user_key not in loggable_storage_key(DataExportEngine.bundle_object_key(user_key, "e-1"))

    @pytest.mark.parametrize(
        "key",
        [f"privacy/exports/{USER_KEY}/", f"privacy/exports/{USER_KEY}", f"/privacy/exports/{USER_KEY}/x.json"],
    )
    def test_prefixes_and_a_leading_slash_are_masked_too(self, key: str) -> None:
        assert USER_KEY not in loggable_storage_key(key)

    @pytest.mark.parametrize("key", ["privacy/exports/", "t/", "other", "text/plain", "x/t/tenant-1/a.jpg"])
    def test_every_other_key_passes_unchanged(self, key: str) -> None:
        assert loggable_storage_key(key) == key

    def test_an_attachment_key_loses_its_tenant_segment_and_keeps_category_date_ulid_and_extension(self) -> None:
        """#1966: ``t/<tenant>/…`` named the tenant — and for a personal tenant its owner — on every delete line."""
        logged = loggable_storage_key(ATTACHMENT_KEY)

        assert TENANT_KEY not in logged
        assert logged == f"t/{log_tenant(TENANT_KEY)}/plant_photo/2026/10/01HZX3K9ABCDEFGHJKMNPQRSTV.jpg"

    @pytest.mark.parametrize("key", [f"t/{TENANT_KEY}/", f"t/{TENANT_KEY}", f"/t/{TENANT_KEY}/plant_photo/"])
    def test_a_tenant_prefix_and_a_leading_slash_are_masked_too(self, key: str) -> None:
        assert TENANT_KEY not in loggable_storage_key(key)

    def test_the_reference_is_the_one_the_service_lines_carry(self) -> None:
        assert f"t/{log_tenant(TENANT_KEY)}/" in loggable_storage_key(f"t/{TENANT_KEY}/")

    def test_without_a_log_salt_the_tenant_is_still_not_named(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "log_pseudonym_salt", "")

        assert TENANT_KEY not in loggable_storage_key(ATTACHMENT_KEY)


def _local(tmp_path: Path) -> LocalFsStorageAdapter:
    return LocalFsStorageAdapter(
        root=str(tmp_path),
        public_base_url="http://localhost/api/v1/storage/token",
        signing_secret="test-secret-please-change",
        max_object_size_bytes=1024 * 1024,
    )


def _s3() -> S3StorageAdapter:
    adapter = S3StorageAdapter(
        endpoint_url="http://localhost:9000",
        region="eu-central-1",
        bucket="bk",
        access_key_id="x",
        secret_access_key="y",
        use_path_style=True,
        force_tls=False,
    )
    client = MagicMock()
    client.put_object.return_value = {"ETag": '"etag"'}
    adapter._client = client
    return adapter


@pytest.mark.asyncio
class TestLocalFsAdapterLogs:
    async def test_storage_delete_object_of_an_export_bundle_names_nobody(self, tmp_path: Path) -> None:
        adapter = _local(tmp_path)
        await adapter.put_object(BUNDLE_KEY, _stream(), "application/json")

        with structlog.testing.capture_logs() as logs:
            await adapter.delete_object(BUNDLE_KEY)

        deleted = next(event for event in logs if event["event"] == "storage_delete_object")
        assert deleted["key"] == loggable_storage_key(BUNDLE_KEY)
        assert _leaks(logs) == []

    async def test_every_delete_path_names_no_tenant(self, tmp_path: Path) -> None:
        """#1966: ``storage_delete_object`` / ``storage_delete_prefix`` / put / copy carry ``t/<tenant>/…`` keys."""
        adapter = _local(tmp_path)
        other = ATTACHMENT_KEY.replace(".jpg", ".png")
        await adapter.put_object(ATTACHMENT_KEY, _stream(), "image/jpeg")

        with structlog.testing.capture_logs() as logs:
            await adapter.copy_object(ATTACHMENT_KEY, other)
            await adapter.delete_object(ATTACHMENT_KEY)
            await adapter.delete_prefix(f"t/{TENANT_KEY}/")
            await adapter.put_object(ATTACHMENT_KEY, _stream(), "image/jpeg")

        events = {event["event"] for event in logs}
        assert {"storage_delete_object", "storage_delete_prefix", "storage_copy_object", "storage_put_object"} <= events
        assert _leaks(logs, TENANT_KEY) == []
        deleted = next(event for event in logs if event["event"] == "storage_delete_object")
        assert deleted["key"] == f"t/{log_tenant(TENANT_KEY)}/plant_photo/2026/10/01HZX3K9ABCDEFGHJKMNPQRSTV.jpg"

    async def test_storage_put_and_copy_of_an_export_bundle_name_nobody(self, tmp_path: Path) -> None:
        adapter = _local(tmp_path)
        other = DataExportEngine.bundle_object_key(USER_KEY, "exp-78")

        with structlog.testing.capture_logs() as logs:
            await adapter.put_object(BUNDLE_KEY, _stream(), "application/json")
            await adapter.copy_object(BUNDLE_KEY, other)

        assert {"storage_put_object", "storage_copy_object"} <= {event["event"] for event in logs}
        assert _leaks(logs) == []


@pytest.mark.asyncio
class TestS3AdapterLogs:
    async def test_storage_delete_object_of_an_export_bundle_names_nobody(self) -> None:
        adapter = _s3()

        with structlog.testing.capture_logs() as logs:
            await adapter.delete_object(BUNDLE_KEY)

        adapter._client.delete_object.assert_called_once_with(Bucket="bk", Key=BUNDLE_KEY)
        deleted = next(event for event in logs if event["event"] == "storage_delete_object")
        assert deleted["key"] == loggable_storage_key(BUNDLE_KEY)
        assert _leaks(logs) == []

    async def test_every_delete_path_names_no_tenant(self) -> None:
        adapter = _s3()
        adapter._client.list_objects_v2.return_value = {"Contents": [], "IsTruncated": False}

        with structlog.testing.capture_logs() as logs:
            await adapter.delete_object(ATTACHMENT_KEY)
            await adapter.delete_prefix(f"t/{TENANT_KEY}/")

        adapter._client.delete_object.assert_called_once_with(Bucket="bk", Key=ATTACHMENT_KEY)
        assert {"storage_delete_object", "storage_delete_prefix"} <= {event["event"] for event in logs}
        assert _leaks(logs, TENANT_KEY) == []
        deleted = next(event for event in logs if event["event"] == "storage_delete_object")
        assert deleted["key"] == f"t/{log_tenant(TENANT_KEY)}/plant_photo/2026/10/01HZX3K9ABCDEFGHJKMNPQRSTV.jpg"

    async def test_storage_put_and_copy_of_an_export_bundle_name_nobody(self) -> None:
        adapter = _s3()
        other = DataExportEngine.bundle_object_key(USER_KEY, "exp-78")

        with structlog.testing.capture_logs() as logs:
            await adapter.put_object(BUNDLE_KEY, _stream(), "application/json")
            await adapter.copy_object(BUNDLE_KEY, other)

        assert {"storage_put_object", "storage_copy_object"} <= {event["event"] for event in logs}
        assert _leaks(logs) == []
