#!/usr/bin/env python3
"""NFR-013 §7.3 — object-storage migration tool.

Migrates every binary object from one storage backend to another by streaming
``list_objects`` → ``get_object`` → ``put_object``. Supported moves (AC-07):

  --from local-fs --to s3                 # initial migration before provider switch
  --from s3       --to local-fs           # rollback / light-mode switch
  --from s3       --to s3 --target-bucket # provider switch (same backend type)

Flags:

  --dry-run          list the operations without writing anything
  --checksum-verify  recompute SHA-256 of every migrated object on the target
                     and compare against the source (100 % verification, AC-07)
  --prefix           restrict the migration to a key prefix (e.g. one tenant)

The heavy lifting lives in :class:`StorageMigrator` so the Celery task
(``app.tasks.storage_tasks.migrate_storage``) can reuse it with progress and
audit logging. Run from the backend root:

    python -m scripts.storage.migrate --from local-fs --to s3 --checksum-verify
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import sys
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter

logger = structlog.get_logger()

_SUPPORTED_BACKENDS = ("local-fs", "s3")


@dataclass
class MigrationReport:
    """Outcome of a migration run."""

    backend_from: str
    backend_to: str
    dry_run: bool
    checksum_verify: bool
    total: int = 0
    copied: int = 0
    skipped: int = 0
    verified: int = 0
    failures: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "backend_from": self.backend_from,
            "backend_to": self.backend_to,
            "dry_run": self.dry_run,
            "checksum_verify": self.checksum_verify,
            "total": self.total,
            "copied": self.copied,
            "skipped": self.skipped,
            "verified": self.verified,
            "failures": self.failures,
            "ok": not self.failures,
        }


async def _collect(stream: AsyncIterator[bytes]) -> bytes:
    out = bytearray()
    async for chunk in stream:
        out.extend(chunk)
    return bytes(out)


async def _one_chunk(data: bytes) -> AsyncIterator[bytes]:
    yield data


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class StorageMigrator:
    """Streams every object from a source adapter to a target adapter."""

    def __init__(
        self,
        source: IObjectStorageAdapter,
        target: IObjectStorageAdapter,
        *,
        backend_from: str,
        backend_to: str,
        dry_run: bool = False,
        checksum_verify: bool = False,
    ) -> None:
        self._source = source
        self._target = target
        self._backend_from = backend_from
        self._backend_to = backend_to
        self._dry_run = dry_run
        self._checksum_verify = checksum_verify

    async def _iter_keys(self, prefix: str) -> AsyncIterator[str]:
        """Yield every source key under ``prefix`` across all pages."""
        page_token: str | None = None
        while True:
            page = await self._source.list_objects(prefix, page_token)
            for key in page.get("keys", []):
                yield key
            page_token = page.get("next_page_token")
            if not page_token:
                break

    async def run(self, prefix: str = "") -> MigrationReport:
        """Execute the migration and return a structured report."""
        report = MigrationReport(
            backend_from=self._backend_from,
            backend_to=self._backend_to,
            dry_run=self._dry_run,
            checksum_verify=self._checksum_verify,
        )
        async for key in self._iter_keys(prefix):
            report.total += 1
            try:
                await self._migrate_one(key, report)
            except Exception as exc:  # noqa: BLE001 — record + continue, never abort the run
                report.failures.append(f"{key}: {exc}")
                logger.error("storage_migrate_object_failed", key=key, error=str(exc))
        logger.info("storage_migrate_completed", **report.as_dict())
        return report

    async def _migrate_one(self, key: str, report: MigrationReport) -> None:
        if self._dry_run:
            # List the operation, write nothing (AC-07 dry-run contract).
            logger.info(
                "storage_migrate_dry_run",
                key=key,
                backend_from=self._backend_from,
                backend_to=self._backend_to,
            )
            report.skipped += 1
            return

        data = await _collect(await self._source.get_object(key))
        metadata = await self._source.head_object(key)
        mime_type = metadata.content_type or "application/octet-stream"
        await self._target.put_object(key, _one_chunk(data), mime_type, metadata=None)
        report.copied += 1

        if self._checksum_verify:
            source_hash = _sha256(data)
            target_data = await _collect(await self._target.get_object(key))
            target_hash = _sha256(target_data)
            if source_hash != target_hash:
                raise ValueError(f"checksum mismatch (source={source_hash[:12]} target={target_hash[:12]})")
            report.verified += 1


def build_adapter(backend_key: str, *, target_bucket: str | None = None) -> IObjectStorageAdapter:
    """Build a configured adapter for ``backend_key`` from settings.

    ``target_bucket`` overrides the S3 bucket so an ``s3 → s3`` provider switch
    can write into a different bucket while reading from the configured one.
    """
    from app.data_access.storage.registry import StorageAdapterRegistry

    if backend_key not in _SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported backend '{backend_key}'. Supported: {_SUPPORTED_BACKENDS}")

    if backend_key == "s3" and target_bucket:
        from app.config.settings import settings
        from app.data_access.storage.s3_adapter import S3StorageAdapter

        return S3StorageAdapter(
            endpoint_url=settings.storage_s3_endpoint_url,
            region=settings.storage_s3_region,
            bucket=target_bucket,
            access_key_id=settings.storage_s3_access_key_id,
            secret_access_key=settings.storage_s3_secret_access_key,
            use_path_style=settings.storage_s3_use_path_style,
            kms_key_id=settings.storage_s3_kms_key_id or None,
            force_tls=settings.storage_s3_force_tls,
        )

    return StorageAdapterRegistry.get_for_backend(backend_key)


async def migrate(
    *,
    backend_from: str,
    backend_to: str,
    target_bucket: str | None = None,
    prefix: str = "",
    dry_run: bool = False,
    checksum_verify: bool = False,
) -> MigrationReport:
    """High-level entry point used by both the CLI and the Celery task."""
    source = build_adapter(backend_from)
    target = build_adapter(backend_to, target_bucket=target_bucket)
    migrator = StorageMigrator(
        source,
        target,
        backend_from=backend_from,
        backend_to=backend_to,
        dry_run=dry_run,
        checksum_verify=checksum_verify,
    )
    return await migrator.run(prefix=prefix)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scripts.storage.migrate",
        description="Migrate object-storage binaries between backends (NFR-013 §7.3).",
    )
    parser.add_argument("--from", dest="backend_from", required=True, choices=_SUPPORTED_BACKENDS)
    parser.add_argument("--to", dest="backend_to", required=True, choices=_SUPPORTED_BACKENDS)
    parser.add_argument("--target-bucket", dest="target_bucket", default=None)
    parser.add_argument("--prefix", dest="prefix", default="")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true")
    parser.add_argument("--checksum-verify", dest="checksum_verify", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if args.backend_from == args.backend_to and not args.target_bucket:
        print(
            "Refusing to migrate a backend onto itself without --target-bucket.",
            file=sys.stderr,
        )
        return 2

    report = asyncio.run(
        migrate(
            backend_from=args.backend_from,
            backend_to=args.backend_to,
            target_bucket=args.target_bucket,
            prefix=args.prefix,
            dry_run=args.dry_run,
            checksum_verify=args.checksum_verify,
        )
    )
    result = report.as_dict()
    print(  # noqa: T201 — CLI summary output is intentional
        f"migrate {result['backend_from']} → {result['backend_to']}: "
        f"total={result['total']} copied={result['copied']} skipped={result['skipped']} "
        f"verified={result['verified']} failures={len(result['failures'])} "
        f"dry_run={result['dry_run']} ok={result['ok']}"
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
