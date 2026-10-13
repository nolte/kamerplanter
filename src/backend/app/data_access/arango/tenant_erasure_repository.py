"""ArangoDB persistence of the tenant-deletion proof (#1769)."""

from __future__ import annotations

from typing import Any

from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, DocumentInsertError

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.tenant_erasure_repository import ITenantErasureRepository
from app.domain.models.tenant_erasure import TenantErasureRecord


class ArangoTenantErasureRepository(BaseArangoRepository[TenantErasureRecord], ITenantErasureRepository):
    _model_cls = TenantErasureRecord
    #: Each record names the one tenant it erases. The erasure beat reads
    #: through :meth:`list_due` and by key; a base list read without a
    #: ``tenant_key`` (or ``all_tenants=True``) raises (MT-023, #2119).
    is_tenant_scoped = True

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

    def heartbeat(
        self, key: str, *, claimed_at_iso: str, now_iso: str, parent_keys: dict[str, list[str]] | None = None
    ) -> bool:
        """Refresh ``updated_at`` (and optionally ``parent_keys``) while the run's claim still stands.

        One AQL ``UPDATE`` on one document, conditional on the claim stamp
        (``last_attempt_at``) the run wrote: a claim another worker took over
        changed that stamp, so this finds nothing and returns ``False``. A
        write-write conflict (``1200``) means that claim is landing right now —
        also ``False``.
        """
        changes: dict[str, object] = {"updated_at": now_iso}
        if parent_keys is not None:
            changes["parent_keys"] = parent_keys
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
            AND doc.status == 'in_progress'
            AND doc.last_attempt_at == @claimed_at
          UPDATE doc WITH @changes IN @@collection OPTIONS { mergeObjects: false }
          RETURN NEW._key
        """
        try:
            refreshed = list(
                self._db.aql.execute(
                    query,
                    bind_vars={
                        "@collection": col.TENANT_ERASURE_RECORDS,
                        "key": key,
                        "claimed_at": claimed_at_iso,
                        "changes": changes,
                    },
                )
            )
        except AQLQueryExecuteError as exc:
            if exc.error_code == 1200:
                return False
            raise
        return bool(refreshed)

    def update_fields_while_claimed(
        self, key: str, *, claimed_at_iso: str, fields: dict[str, Any]
    ) -> TenantErasureRecord | None:
        """Merge *fields* (and ``updated_at``) in one conditional AQL ``UPDATE``; ``None`` when the claim is gone.

        The condition is :meth:`heartbeat`'s — ``in_progress`` and ``last_attempt_at`` still the
        run's own claim stamp — so a run that lost its claim cannot overwrite the record the
        run holding it now owns. ``fields`` is built by ``TenantService`` from a literal
        allow-list, never from a request. A write-write conflict (``1200``) reads as *claim gone*.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
            AND doc.status == 'in_progress'
            AND doc.last_attempt_at == @claimed_at
          UPDATE doc WITH @changes IN @@collection OPTIONS { mergeObjects: false }
          RETURN NEW
        """
        changes = {**fields, "updated_at": self._now()}
        try:
            docs = list(
                self._db.aql.execute(
                    query,
                    bind_vars={
                        "@collection": col.TENANT_ERASURE_RECORDS,
                        "key": key,
                        "claimed_at": claimed_at_iso,
                        "changes": changes,
                    },
                )
            )
        except AQLQueryExecuteError as exc:
            if exc.error_code == 1200:
                return None
            raise
        return TenantErasureRecord(**self._from_doc(docs[0])) if docs else None

    def delete_unclaimed(self, key: str) -> bool:
        """Remove the record only while no run has claimed it: one AQL ``REMOVE`` on one document.

        The mirror of :meth:`claim_for_run`'s first claim, which sets
        ``last_attempt_at``. A write-write conflict (``1200``) means a claim is
        landing on the document right now; it reads as *not removed*.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
            AND doc.origin == 'account_erasure'
            AND doc.status == 'in_progress'
            AND doc.last_attempt_at == null
            AND (doc.attempt_count == null OR doc.attempt_count == 0)
          REMOVE doc IN @@collection
          RETURN OLD._key
        """
        try:
            removed = list(
                self._db.aql.execute(query, bind_vars={"@collection": col.TENANT_ERASURE_RECORDS, "key": key})
            )
        except AQLQueryExecuteError as exc:
            if exc.error_code == 1200:
                return False
            raise
        return bool(removed)

    def delete_scheduled(self, key: str) -> bool:
        """Remove the record only while it is ``scheduled``: one AQL ``REMOVE`` on one document (#2123).

        The mirror of :meth:`claim_for_run`, which flips a due ``scheduled`` record to
        ``in_progress`` in one ``UPDATE``: ArangoDB serialises the two on the document,
        so either the claim finds no record or this finds it ``in_progress``. A
        write-write conflict (``1200``) means the claim is landing now — *not removed*.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
            AND doc.status == 'scheduled'
            AND doc.last_attempt_at == null
          REMOVE doc IN @@collection
          RETURN OLD._key
        """
        try:
            removed = list(
                self._db.aql.execute(query, bind_vars={"@collection": col.TENANT_ERASURE_RECORDS, "key": key})
            )
        except AQLQueryExecuteError as exc:
            if exc.error_code == 1200:
                return False
            raise
        return bool(removed)

    def list_due(
        self, *, stale_before_iso: str, scheduled_due_before_iso: str | None = None
    ) -> list[TenantErasureRecord]:
        query = """
        FOR doc IN @@collection
          FILTER doc.status == 'partially_completed'
            OR (
              doc.status == 'in_progress'
              AND (doc.updated_at == null OR DATE_TIMESTAMP(doc.updated_at) <= DATE_TIMESTAMP(@stale_before))
            )
            OR (
              @due_before != null
              AND doc.status == 'scheduled'
              AND doc.scheduled_for != null
              AND DATE_TIMESTAMP(doc.scheduled_for) <= DATE_TIMESTAMP(@due_before)
            )
          SORT DATE_TIMESTAMP(doc.requested_at) ASC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.TENANT_ERASURE_RECORDS,
                "stale_before": stale_before_iso,
                "due_before": scheduled_due_before_iso,
            },
        )
        return [TenantErasureRecord(**self._from_doc(doc)) for doc in cursor]
