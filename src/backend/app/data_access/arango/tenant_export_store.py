"""ArangoDB side of the tenant export and import (REQ-056 §8, #2138).

Nothing here names a tenant-scoped collection: the collections, their parent chains
and the row predicate come off the tenant-erasure inventory
(:func:`~app.data_access.arango.tenant_erasure_executor.tenant_row_filter`), so an
export reads exactly what the deletion of the tenant would reach.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.tenant_erasure_executor import tenant_row_filter
from app.domain.interfaces.tenant_export_store import (
    ITenantDataStore,
    ITenantExportRequestRepository,
    ITenantImportRequestRepository,
)
from app.domain.models.tenant_erasure import TenantErasureEntry
from app.domain.models.tenant_export import TenantExportRequest, TenantImportRequest

logger = structlog.get_logger()

_PAGE = """
FOR doc IN @@collection
  FILTER {match} AND doc._key > @after
  SORT doc._key
  LIMIT @page
  RETURN doc
"""

_EDGES_TOUCHING = """
FOR edge IN @@collection
  FILTER edge._from IN @ids OR edge._to IN @ids
  RETURN edge
"""

#: A row is global when it carries no tenant's key (the hybrid-catalogue convention: ``""`` or absent).
_GLOBAL_KEYS = """
FOR doc IN @@collection
  FILTER doc._key IN @keys AND (doc.tenant_key == null OR doc.tenant_key == "")
  RETURN doc._key
"""

#: A pure catalogue's row exists or not — a legacy ``tenant_key`` stamp on it is not ownership.
_EXISTING_KEYS = """
FOR doc IN @@collection
  FILTER doc._key IN @keys
  RETURN doc._key
"""

_INSERT = "FOR doc IN @docs INSERT doc INTO @@collection RETURN NEW._key"

_REMOVE_KEYS = """
FOR doc IN @@collection
  FILTER doc._key IN @keys
  REMOVE doc IN @@collection
  COLLECT WITH COUNT INTO removed
  RETURN removed
"""

_REMOVE_EDGES_ONTO = """
FOR edge IN @@collection
  FILTER edge._from IN @ids OR edge._to IN @ids
  REMOVE edge IN @@collection
"""

_MEMBERSHIP_IDS = "FOR m IN @@collection FILTER m.tenant_key == @tenant_key RETURN m._id"

#: The highest applied migration; ``__``-prefixed documents are the runner's lock and seed markers.
_MIGRATION_LEVEL = """
FOR doc IN @@collection
  FILTER doc.version != null AND NOT STARTS_WITH(doc._key, "__")
  SORT doc.version DESC
  LIMIT 1
  RETURN doc.version
"""


class ArangoTenantDataStore(ITenantDataStore):
    """Reads a tenant's rows page by page and writes an import's rows in bounded transactions."""

    #: Ids per ``edges_touching`` query: large enough to be few queries, small enough for the bind payload.
    ID_CHUNK = 1000

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def migration_level(self) -> str | None:
        if not self._db.has_collection(col.SCHEMA_MIGRATIONS):
            return None
        level = next(
            iter(
                cast(Cursor, self._db.aql.execute(_MIGRATION_LEVEL, bind_vars={"@collection": col.SCHEMA_MIGRATIONS}))
            ),
            None,
        )
        return str(level) if level is not None else None

    def tenant_document(self, tenant_key: str) -> dict[str, Any] | None:
        doc = cast(dict[str, Any] | None, self._db.collection(col.TENANTS).get(tenant_key))
        return dict(doc) if doc else None

    def _collections(self) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], self._db.collections())

    def collection_names(self) -> set[str]:
        return {c["name"] for c in self._collections() if not c["system"] and c["type"] != "edge"}

    def edge_collection_names(self) -> list[str]:
        return sorted(c["name"] for c in self._collections() if not c["system"] and c["type"] == "edge")

    def iter_tenant_rows(
        self, entry: TenantErasureEntry, *, tenant_key: str, parent_keys: dict[str, list[str]], page_size: int
    ) -> Iterator[list[dict[str, Any]]]:
        if not tenant_key:
            # ``doc.tenant_key == ""`` matches every global catalogue row.
            raise ValueError("an export needs a tenant key")
        match, binds = tenant_row_filter(entry, parent_keys, col.TENANTS)
        after = ""
        while True:
            bind_vars: dict[str, Any] = {
                "@collection": entry.collection,
                "tenant_key": tenant_key,
                "after": after,
                "page": page_size,
                **binds,
            }
            page = list(cast(Cursor, self._db.aql.execute(_PAGE.format(match=match), bind_vars=bind_vars)))
            if not page:
                return
            yield [dict(doc) for doc in page]
            after = str(page[-1]["_key"])

    def edges_touching(self, edge_collection: str, ids: list[str]) -> list[dict[str, Any]]:
        found: dict[str, dict[str, Any]] = {}
        for start in range(0, len(ids), self.ID_CHUNK):
            chunk = ids[start : start + self.ID_CHUNK]
            for edge in cast(
                Cursor, self._db.aql.execute(_EDGES_TOUCHING, bind_vars={"@collection": edge_collection, "ids": chunk})
            ):
                found[str(edge["_key"])] = dict(edge)
        return [found[key] for key in sorted(found)]

    def existing_global_keys(self, collection: str, keys: list[str], *, any_row: bool = False) -> set[str]:
        if not keys or not self._db.has_collection(collection):
            return set()
        existing: set[str] = set()
        for start in range(0, len(keys), self.ID_CHUNK):
            bind_vars: dict[str, Any] = {"@collection": collection, "keys": keys[start : start + self.ID_CHUNK]}
            if any_row:
                cursor = cast(Cursor, self._db.aql.execute(_EXISTING_KEYS, bind_vars=bind_vars))
            else:
                cursor = cast(Cursor, self._db.aql.execute(_GLOBAL_KEYS, bind_vars=bind_vars))
            existing.update(str(key) for key in cursor)
        return existing

    def insert_documents(self, collection: str, documents: list[dict[str, Any]]) -> list[str]:
        if not documents:
            return []
        transaction = self._db.begin_transaction(write=[collection], allow_implicit=False)
        try:
            written = [
                str(key)
                for key in cast(
                    Cursor, transaction.aql.execute(_INSERT, bind_vars={"@collection": collection, "docs": documents})
                )
            ]
            transaction.commit_transaction()
        except BaseException:
            try:
                transaction.abort_transaction()
            except Exception as exc:  # noqa: BLE001 - the primary error is the one to raise
                logger.warning("tenant_import.transaction_abort_failed", error_type=type(exc).__name__)
            raise
        return written

    def remove_documents(self, collection: str, keys: list[str]) -> int:
        removed = 0
        for start in range(0, len(keys), self.ID_CHUNK):
            chunk = keys[start : start + self.ID_CHUNK]
            removed += int(
                next(
                    iter(
                        cast(
                            Cursor,
                            self._db.aql.execute(_REMOVE_KEYS, bind_vars={"@collection": collection, "keys": chunk}),
                        )
                    ),
                    0,
                )
            )
        return removed

    def remove_tenant_shell(self, *, tenant_key: str) -> None:
        if not tenant_key:
            raise ValueError("a rollback needs the founded tenant's key")
        ids: list[str] = [
            str(member_id)
            for member_id in cast(
                Cursor,
                self._db.aql.execute(
                    _MEMBERSHIP_IDS, bind_vars={"@collection": col.MEMBERSHIPS, "tenant_key": tenant_key}
                ),
            )
        ]
        ids.append(f"{col.TENANTS}/{tenant_key}")
        for edge_collection in self.edge_collection_names():
            for start in range(0, len(ids), self.ID_CHUNK):
                cast(
                    Cursor,
                    self._db.aql.execute(
                        _REMOVE_EDGES_ONTO,
                        bind_vars={"@collection": edge_collection, "ids": ids[start : start + self.ID_CHUNK]},
                    ),
                )
        member_ids: list[str] = ids[:-1]
        member_keys: list[str] = []
        for member_id in member_ids:
            text: str = member_id
            member_keys.append(text.partition("/")[2])
        self.remove_documents(col.MEMBERSHIPS, member_keys)
        self.remove_documents(col.TENANTS, [tenant_key])


class ArangoTenantExportRequestRepository(BaseArangoRepository[TenantExportRequest], ITenantExportRequestRepository):
    """``tenant_export_requests`` — every read names the tenant or the request key."""

    _model_cls = TenantExportRequest
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.TENANT_EXPORT_REQUESTS)

    def get(self, key: str) -> TenantExportRequest | None:
        return self.get_by_key(key)

    def list_by_tenant(
        self, *, tenant_key: str, requested_by_user_key: str, offset: int, limit: int
    ) -> list[TenantExportRequest]:
        self._require_tenant_key(tenant_key, "list_by_tenant")
        query = """
        FOR doc IN @@collection
          FILTER doc.tenant_key == @tenant_key AND doc.requested_by_user_key == @requester
          SORT DATE_TIMESTAMP(doc.requested_at) DESC, doc._key DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        bind_vars: dict[str, Any] = {
            "@collection": col.TENANT_EXPORT_REQUESTS,
            "tenant_key": tenant_key,
            "requester": requested_by_user_key,
            "offset": offset,
            "limit": limit,
        }
        cursor = cast(Cursor, self._db.aql.execute(query, bind_vars=bind_vars))
        return [TenantExportRequest(**self._from_doc(doc)) for doc in cursor]

    def count_requested_since(self, *, tenant_key: str, since: datetime) -> int:
        self._require_tenant_key(tenant_key, "count_requested_since")
        query = """
        FOR doc IN @@collection
          FILTER doc.tenant_key == @tenant_key AND DATE_TIMESTAMP(doc.requested_at) >= DATE_TIMESTAMP(@since)
          COLLECT WITH COUNT INTO n
          RETURN n
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                query,
                bind_vars={
                    "@collection": col.TENANT_EXPORT_REQUESTS,
                    "tenant_key": tenant_key,
                    "since": since.isoformat(),
                },
            ),
        )
        return int(next(iter(cursor), 0))

    def active_keys(self, *, tenant_key: str) -> list[str]:
        self._require_tenant_key(tenant_key, "active_keys")
        query = """
        FOR doc IN @@collection
          FILTER doc.tenant_key == @tenant_key AND doc.status IN ["pending", "running"]
          SORT DATE_TIMESTAMP(doc.requested_at), doc._key
          RETURN doc._key
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                query, bind_vars={"@collection": col.TENANT_EXPORT_REQUESTS, "tenant_key": tenant_key}
            ),
        )
        return [str(key) for key in cursor]

    def claim(self, key: str, now: datetime) -> TenantExportRequest | None:
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key AND doc.status == "pending"
          UPDATE doc WITH { status: "running", started_at: @now, updated_at: @now } IN @@collection
          RETURN NEW
        """
        docs = list(
            cast(
                Cursor,
                self._db.aql.execute(
                    query, bind_vars={"@collection": col.TENANT_EXPORT_REQUESTS, "key": key, "now": now.isoformat()}
                ),
            )
        )
        return TenantExportRequest(**self._from_doc(docs[0])) if docs else None

    def update_fields(self, key: str, fields: dict[str, Any]) -> TenantExportRequest | None:  # type: ignore[override]
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
          UPDATE doc WITH @fields IN @@collection OPTIONS { keepNull: false, mergeObjects: false }
          RETURN NEW
        """
        docs = list(
            cast(
                Cursor,
                self._db.aql.execute(
                    query,
                    bind_vars={"@collection": col.TENANT_EXPORT_REQUESTS, "key": key, "fields": _serialisable(fields)},
                ),
            )
        )
        return TenantExportRequest(**self._from_doc(docs[0])) if docs else None

    def list_expiry_due(self, now: datetime) -> list[TenantExportRequest]:
        query = """
        FOR doc IN @@collection
          FILTER doc.status == "completed" AND doc.expires_at != null
            AND DATE_TIMESTAMP(doc.expires_at) <= DATE_TIMESTAMP(@now)
          LIMIT 500
          RETURN doc
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(query, bind_vars={"@collection": col.TENANT_EXPORT_REQUESTS, "now": now.isoformat()}),
        )
        return [TenantExportRequest(**self._from_doc(doc)) for doc in cursor]

    def list_stale_active(self, before: datetime) -> list[TenantExportRequest]:
        query = """
        FOR doc IN @@collection
          FILTER doc.status IN ["pending", "running"]
            AND DATE_TIMESTAMP(doc.updated_at || doc.requested_at) <= DATE_TIMESTAMP(@before)
          SORT DATE_TIMESTAMP(doc.updated_at || doc.requested_at), doc._key
          LIMIT 500
          RETURN doc
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                query, bind_vars={"@collection": col.TENANT_EXPORT_REQUESTS, "before": before.isoformat()}
            ),
        )
        return [TenantExportRequest(**self._from_doc(doc)) for doc in cursor]

    def delete_finished_before(self, before: datetime) -> int:
        query = """
        FOR doc IN @@collection
          FILTER doc.status IN ["failed", "expired"]
            AND DATE_TIMESTAMP(doc.updated_at || doc.requested_at) <= DATE_TIMESTAMP(@before)
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO n
          RETURN n
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                query, bind_vars={"@collection": col.TENANT_EXPORT_REQUESTS, "before": before.isoformat()}
            ),
        )
        return int(next(iter(cursor), 0))


class ArangoTenantImportRequestRepository(BaseArangoRepository[TenantImportRequest], ITenantImportRequestRepository):
    """``tenant_import_requests`` — global; read by key only."""

    _model_cls = TenantImportRequest

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.TENANT_IMPORT_REQUESTS)

    def get(self, key: str) -> TenantImportRequest | None:
        return self.get_by_key(key)

    def claim(self, key: str, now: datetime) -> TenantImportRequest | None:
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key AND doc.status == "pending"
          UPDATE doc WITH { status: "validating", updated_at: @now } IN @@collection
          RETURN NEW
        """
        docs = list(
            cast(
                Cursor,
                self._db.aql.execute(
                    query, bind_vars={"@collection": col.TENANT_IMPORT_REQUESTS, "key": key, "now": now.isoformat()}
                ),
            )
        )
        return TenantImportRequest(**self._from_doc(docs[0])) if docs else None

    def update_fields(self, key: str, fields: dict[str, Any]) -> TenantImportRequest | None:  # type: ignore[override]
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
          UPDATE doc WITH @fields IN @@collection OPTIONS { keepNull: false, mergeObjects: false }
          RETURN NEW
        """
        docs = list(
            cast(
                Cursor,
                self._db.aql.execute(
                    query,
                    bind_vars={"@collection": col.TENANT_IMPORT_REQUESTS, "key": key, "fields": _serialisable(fields)},
                ),
            )
        )
        return TenantImportRequest(**self._from_doc(docs[0])) if docs else None

    def list_stale_active(self, before: datetime) -> list[TenantImportRequest]:
        # ``cleanup_pending`` at any age: its tenant is known to hold rows the next sweep must erase.
        query = """
        FOR doc IN @@collection
          FILTER doc.status == "cleanup_pending"
            OR (doc.status IN ["pending", "validating", "running"]
                AND DATE_TIMESTAMP(doc.updated_at || doc.requested_at) <= DATE_TIMESTAMP(@before))
          SORT DATE_TIMESTAMP(doc.updated_at || doc.requested_at), doc._key
          LIMIT 100
          RETURN doc
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                query, bind_vars={"@collection": col.TENANT_IMPORT_REQUESTS, "before": before.isoformat()}
            ),
        )
        return [TenantImportRequest(**self._from_doc(doc)) for doc in cursor]

    def delete_finished_before(self, before: datetime) -> int:
        query = """
        FOR doc IN @@collection
          FILTER doc.status IN ["completed", "failed"]
            AND DATE_TIMESTAMP(doc.updated_at || doc.requested_at) <= DATE_TIMESTAMP(@before)
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO n
          RETURN n
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                query, bind_vars={"@collection": col.TENANT_IMPORT_REQUESTS, "before": before.isoformat()}
            ),
        )
        return int(next(iter(cursor), 0))


def _serialisable(fields: dict[str, Any]) -> dict[str, Any]:
    """``datetime`` values as ISO strings, the way every repository stores instants."""
    return {name: _stored(value) for name, value in fields.items()}


def _stored(value: Any) -> Any:
    if isinstance(value, datetime):
        instant: datetime = value
        return instant.isoformat()
    return value
