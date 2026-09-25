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


def _leaks(logs: list[dict[str, Any]]) -> list[str]:
    return [
        f"{event.get('event')}.{field}" for event in logs for field, value in event.items() if USER_KEY in str(value)
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

    @pytest.mark.parametrize("key", ["t/tenant-1/plant_photo/01HX.jpg", "t/tenant-1/", "privacy/exports/", "other"])
    def test_every_other_key_passes_unchanged(self, key: str) -> None:
        assert loggable_storage_key(key) == key


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

    async def test_storage_put_and_copy_of_an_export_bundle_name_nobody(self) -> None:
        adapter = _s3()
        other = DataExportEngine.bundle_object_key(USER_KEY, "exp-78")

        with structlog.testing.capture_logs() as logs:
            await adapter.put_object(BUNDLE_KEY, _stream(), "application/json")
            await adapter.copy_object(BUNDLE_KEY, other)

        assert {"storage_put_object", "storage_copy_object"} <= {event["event"] for event in logs}
        assert _leaks(logs) == []
