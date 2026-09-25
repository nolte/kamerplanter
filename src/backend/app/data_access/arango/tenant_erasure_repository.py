"""ArangoDB persistence of the tenant-deletion proof (#1769)."""

from __future__ import annotations

from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, DocumentInsertError

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.tenant_erasure_repository import ITenantErasureRepository
from app.domain.models.tenant_erasure import TenantErasureRecord


class ArangoTenantErasureRepository(BaseArangoRepository[TenantErasureRecord], ITenantErasureRepository):
    _model_cls = TenantErasureRecord

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.TENANT_ERASURE_RECORDS)

    def get(self, key: str) -> TenantErasureRecord | None:
        return self.get_by_key(key)

    def create_with_key(self, record: TenantErasureRecord, key: str) -> TenantErasureRecord:
        """Insert *record* under the per-tenant key; the second of two concurrent inserts fails."""
        data = self._insert_payload(record)
        data["_key"] = key
        try:
            result = self.collection.insert(data, return_new=True)
        except DocumentInsertError as e:
            mapped = self._mapped_insert_error(e, self._collection_name, data)
            if mapped is not None:
                raise mapped from e
            raise
        return TenantErasureRecord(**self._from_doc(result["new"]))

    def claim_for_run(self, key: str, *, now_iso: str, stale_before_iso: str) -> TenantErasureRecord | None:
        """Atomically claim an open record: one AQL ``UPDATE`` on one document.

        ArangoDB serialises writes per document, so of two concurrent claims one
        sees the other's ``in_progress`` (filtered out) or fails with a
        write-write conflict (``1200``); both read as *not claimed*.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
            AND doc.status != 'completed'
            AND (
              doc.status != 'in_progress'
              OR doc.last_attempt_at == null
              OR doc.updated_at == null
              OR DATE_TIMESTAMP(doc.updated_at) <= DATE_TIMESTAMP(@stale_before)
            )
          UPDATE doc WITH { status: 'in_progress', last_attempt_at: @now, updated_at: @now } IN @@collection
          RETURN NEW
        """
        try:
            docs = list(
                self._db.aql.execute(
                    query,
                    bind_vars={
                        "@collection": col.TENANT_ERASURE_RECORDS,
                        "key": key,
                        "now": now_iso,
                        "stale_before": stale_before_iso,
                    },
                )
            )
        except AQLQueryExecuteError as exc:
            if exc.error_code == 1200:  # a concurrent claim holds the document
                return None
            raise
        if not docs:
            return None
        return TenantErasureRecord(**self._from_doc(docs[0]))

    def list_due(self, *, stale_before_iso: str) -> list[TenantErasureRecord]:
        query = """
        FOR doc IN @@collection
          FILTER doc.status == 'partially_completed'
            OR (
              doc.status == 'in_progress'
              AND (doc.updated_at == null OR DATE_TIMESTAMP(doc.updated_at) <= DATE_TIMESTAMP(@stale_before))
            )
          SORT doc.requested_at ASC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": col.TENANT_ERASURE_RECORDS, "stale_before": stale_before_iso},
        )
        return [TenantErasureRecord(**self._from_doc(doc)) for doc in cursor]
