"""NFR-013 §7.3 / AC-07 — object-storage migration tool.

Verifies the ``StorageMigrator`` round-trips every object between two adapters,
that ``--dry-run`` writes nothing, and that ``--checksum-verify`` recomputes
SHA-256 on the target. Uses real ``local-fs`` adapters and a real moto S3 to
prove the migration is adapter-agnostic.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from app.data_access.storage.local_fs_adapter import LocalFsStorageAdapter
from scripts.storage.migrate import MigrationReport, StorageMigrator, main

MAX_SIZE = 25 * 1024 * 1024
SECRET = "test-secret-please-change"


async def _stream(data: bytes) -> AsyncIterator[bytes]:
    yield data


async def _collect(adapter, key: str) -> bytes:
    out = bytearray()
    async for chunk in await adapter.get_object(key):
        out.extend(chunk)
    return bytes(out)


def _local_adapter(root) -> LocalFsStorageAdapter:
    return LocalFsStorageAdapter(
        root=str(root),
        public_base_url="http://localhost:8000/api/v1/storage/token",
        signing_secret=SECRET,
        max_object_size_bytes=MAX_SIZE,
    )


@pytest.mark.asyncio
class TestStorageMigrator:
    async def test_dry_run_writes_nothing(self, tmp_path):
        source = _local_adapter(tmp_path / "src")
        target = _local_adapter(tmp_path / "dst")
        await source.put_object("t-1/diary/a.jpg", _stream(b"img-a"), "image/jpeg")
        await source.put_object("t-1/ipm/b.png", _stream(b"img-b"), "image/png")

        migrator = StorageMigrator(
            source,
            target,
            backend_from="local-fs",
            backend_to="local-fs",
            dry_run=True,
        )
        report = await migrator.run()

        assert report.total == 2
        assert report.copied == 0
        assert report.skipped == 2
        # Nothing landed on the target.
        assert (await target.list_objects("t-1"))["keys"] == []

    async def test_round_trip_local_to_local_with_checksum_verify(self, tmp_path):
        source = _local_adapter(tmp_path / "src")
        target = _local_adapter(tmp_path / "dst")
        payloads = {
            "t-1/diary/a.jpg": b"alpha-bytes",
            "t-1/harvest/2026/04/c.webp": b"charlie-bytes",
            "t-2/plant/2026/04/d.jpg": b"delta-bytes",
        }
        for key, data in payloads.items():
            await source.put_object(key, _stream(data), "image/jpeg")

        migrator = StorageMigrator(
            source,
            target,
            backend_from="local-fs",
            backend_to="local-fs",
            checksum_verify=True,
        )
        report = await migrator.run()

        assert report.total == 3
        assert report.copied == 3
        assert report.verified == 3
        assert report.failures == []
        for key, data in payloads.items():
            assert await _collect(target, key) == data

    async def test_round_trip_local_to_s3_with_checksum_verify(self, tmp_path):
        moto = pytest.importorskip("moto")
        import boto3

        from app.data_access.storage.s3_adapter import S3StorageAdapter

        source = _local_adapter(tmp_path / "src")
        await source.put_object("t-1/diary/a.jpg", _stream(b"alpha"), "image/jpeg")
        await source.put_object("t-1/plant/b.png", _stream(b"bravo"), "image/png")

        with moto.mock_aws():
            boto3.client("s3", region_name="eu-central-1").create_bucket(
                Bucket="migrate-target",
                CreateBucketConfiguration={"LocationConstraint": "eu-central-1"},
            )
            target = S3StorageAdapter(
                endpoint_url="",
                region="eu-central-1",
                bucket="migrate-target",
                access_key_id="testing",
                secret_access_key="testing",
            )
            migrator = StorageMigrator(
                source,
                target,
                backend_from="local-fs",
                backend_to="s3",
                checksum_verify=True,
            )
            report = await migrator.run()

            assert report.copied == 2
            assert report.verified == 2
            assert report.failures == []
            assert await _collect(target, "t-1/diary/a.jpg") == b"alpha"


class TestMigrateCli:
    def test_refuses_same_backend_without_target_bucket(self):
        # s3 → s3 without --target-bucket is a no-op footgun → exit code 2.
        rc = main(["--from", "s3", "--to", "s3"])
        assert rc == 2


class TestMigrationReport:
    def test_report_ok_flag_reflects_failures(self):
        report = MigrationReport(
            backend_from="local-fs",
            backend_to="s3",
            dry_run=False,
            checksum_verify=True,
        )
        assert report.as_dict()["ok"] is True
        report.failures.append("k: boom")
        assert report.as_dict()["ok"] is False
