"""#2630 — owed object releases in ``storage_release_retries``.

A row is ``{tenant_key, object_keys, attempts, created_at, last_attempt_at}`` keyed by a hash of the object's main
key, so a second failure for the same object merges into one row. No personal data: storage keys name the tenant
namespace and a content hash. The tenant deletion removes a tenant's rows (``TenantErasureEngine.INVENTORY``).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.interfaces.storage_release_retry_repository import (
    IStorageReleaseRetryRepository,
    StorageReleaseRetry,
)

_RECORD = """
UPSERT { _key: @key }
INSERT { _key: @key, tenant_key: @tenant_key, object_keys: @object_keys, attempts: 0, created_at: @now,
         last_attempt_at: null }
UPDATE { object_keys: UNION_DISTINCT(OLD.object_keys, @object_keys) }
IN @@retries
"""

_DUE = """
FOR r IN @@retries
  SORT DATE_TIMESTAMP(r.created_at), r._key
  LIMIT @limit
  RETURN r
"""

_FAILED_AGAIN = """
FOR r IN @@retries
  FILTER r._key == @key
  UPDATE r WITH { attempts: r.attempts + 1, last_attempt_at: @now } IN @@retries
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _row_key(main_object_key: str) -> str:
    return hashlib.sha256(main_object_key.encode()).hexdigest()[:40]


def _owed_from(row: dict[str, Any]) -> StorageReleaseRetry:
    return StorageReleaseRetry(
        key=str(row["_key"]),
        tenant_key=str(row.get("tenant_key") or ""),
        object_keys=tuple(str(key) for key in row.get("object_keys") or []),
        attempts=int(row.get("attempts") or 0),
        created_at=str(row.get("created_at") or ""),
    )


class ArangoStorageReleaseRetryRepository(IStorageReleaseRetryRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def owe_release(self, *, tenant_key: str, object_keys: list[str]) -> None:
        if not object_keys:
            return
        self._db.aql.execute(
            _RECORD,
            bind_vars={
                "@retries": col.STORAGE_RELEASE_RETRIES,
                "key": _row_key(object_keys[0]),
                "tenant_key": tenant_key,
                "object_keys": object_keys,
                "now": _now(),
            },
        )

    def due(self, limit: int) -> list[StorageReleaseRetry]:
        if not self._db.has_collection(col.STORAGE_RELEASE_RETRIES):
            return []  # a database before ``ensure_collections`` owes nothing
        bind_vars: dict[str, Any] = {"@retries": col.STORAGE_RELEASE_RETRIES, "limit": limit}
        cursor = cast(Cursor, self._db.aql.execute(_DUE, bind_vars=bind_vars))
        return [_owed_from(row) for row in cursor]

    def settle_release(self, key: str) -> None:
        self._db.collection(col.STORAGE_RELEASE_RETRIES).delete(key, ignore_missing=True)

    def release_failed_again(self, key: str) -> None:
        self._db.aql.execute(
            _FAILED_AGAIN, bind_vars={"@retries": col.STORAGE_RELEASE_RETRIES, "key": key, "now": _now()}
        )
