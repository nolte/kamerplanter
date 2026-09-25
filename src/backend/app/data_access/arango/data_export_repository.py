from typing import Any

from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.data_export_repository import IDataExportRepository
from app.domain.models.privacy import DataExportRequest, DataExportRequestKey


class ArangoDataExportRepository(BaseArangoRepository[DataExportRequest], IDataExportRepository):
    """ArangoDB persistence for REQ-025 data-export requests."""

    _model_cls = DataExportRequest

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.DATA_EXPORT_REQUESTS)

    def create(self, export_request: DataExportRequest) -> DataExportRequest:
        created = super().create(export_request)
        if export_request.user_key and created.key:
            user_id = f"{col.USERS}/{export_request.user_key}"
            export_id = f"{col.DATA_EXPORT_REQUESTS}/{created.key}"
            self.create_edge(col.REQUESTED_EXPORT, user_id, export_id)
        return created

    def increment_download_count(self, key: DataExportRequestKey) -> DataExportRequest:
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
          UPDATE doc WITH { download_count: (doc.download_count || 0) + 1 } IN @@collection
          RETURN NEW
        """
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.DATA_EXPORT_REQUESTS, "key": key})
        docs = list(cursor)
        if not docs:
            from app.common.exceptions import NotFoundError

            raise NotFoundError("DataExportRequest", key)
        return DataExportRequest(**self._from_doc(docs[0]))

    def list_by_user(self, user_key: UserKey) -> list[DataExportRequest]:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
          SORT doc.requested_at DESC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.DATA_EXPORT_REQUESTS,
                "user_key": user_key,
            },
        )
        return [DataExportRequest(**self._from_doc(doc)) for doc in cursor]

    def list_active_by_user(self, user_key: UserKey) -> list[DataExportRequest]:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key AND doc.status IN ['pending', 'processing']
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.DATA_EXPORT_REQUESTS,
                "user_key": user_key,
            },
        )
        return [DataExportRequest(**self._from_doc(doc)) for doc in cursor]

    def delete(self, key: DataExportRequestKey) -> bool:
        export_id = f"{col.DATA_EXPORT_REQUESTS}/{key}"
        query = f"FOR e IN {col.REQUESTED_EXPORT} FILTER e._to == @export_id REMOVE e IN {col.REQUESTED_EXPORT}"
        self._db.aql.execute(query, bind_vars={"export_id": export_id})
        return super().delete(key)

    def list_expiry_due(self, now_iso: str) -> list[DataExportRequest]:
        """Exports due for the NFR-011 R-05 bundle delete; read-only (#1767 GDPR-005).

        Until #1767 this was ``expire_old``, which flipped ``status=expired``
        in the same query that found the records. A bundle delete that then
        failed left an ``expired`` record pointing at a file that still
        existed, and no later run selected it again (the filter wanted
        ``completed``). The second arm re-selects exactly those records.
        """
        query = """
        FOR doc IN @@collection
          FILTER (doc.status == 'completed' AND doc.expires_at != null AND doc.expires_at < @now)
            OR (doc.status == 'expired' AND doc.file_path != null)
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.DATA_EXPORT_REQUESTS,
                "now": now_iso,
            },
        )
        return [DataExportRequest(**self._from_doc(doc)) for doc in cursor]

    def list_stale_pending(self, cutoff_iso: str) -> list[DataExportRequest]:
        """Return pending exports requested before ``cutoff_iso``.

        Re-dispatch candidates for ``retention.redispatch_stale_pending_exports``.
        ``LIMIT 100`` caps the batch against a pathological backlog — the task
        runs hourly and drains the rest on the next tick.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.status == "pending"
          FILTER doc.requested_at != null AND doc.requested_at < @cutoff
          SORT doc.requested_at ASC
          LIMIT 100
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.DATA_EXPORT_REQUESTS,
                "cutoff": cutoff_iso,
            },
        )
        return [DataExportRequest(**self._from_doc(doc)) for doc in cursor]

    def complete_if_processing(self, key: str, fields: dict[str, Any]) -> DataExportRequest | None:
        """Conditional completion write (#1767 review SEC-A); ``None`` when no longer ``processing``."""
        data = {name: value for name, value in fields.items() if not name.startswith("_")}
        data["updated_at"] = self._now()
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key AND doc.status == 'processing'
          UPDATE doc WITH @fields IN @@collection OPTIONS { keepNull: true }
          RETURN NEW
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": col.DATA_EXPORT_REQUESTS, "key": key, "fields": data},
        )
        docs = list(cursor)
        if not docs:
            return None
        return DataExportRequest(**self._from_doc(docs[0]))

    def fail_open_for_user(self, user_key: str, reason: str) -> int:
        """Close the user's in-flight exports as ``failed`` (#1767 review SEC-A)."""
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key AND doc.status IN ['pending', 'processing']
          UPDATE doc WITH { status: 'failed', error_message: @reason, updated_at: @now } IN @@collection
          COLLECT WITH COUNT INTO closed
          RETURN closed
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.DATA_EXPORT_REQUESTS,
                "user_key": user_key,
                "reason": reason,
                "now": self._now(),
            },
        )
        return next(iter(cursor), 0)

    def start_processing(
        self, key: str, *, from_statuses: list[str], fields: dict[str, Any]
    ) -> DataExportRequest | None:
        """Conditional ``→ processing`` write (#1767 review); ``None`` when the status moved on."""
        data = {name: value for name, value in fields.items() if not name.startswith("_")}
        data["status"] = "processing"
        data["updated_at"] = self._now()
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key AND doc.status IN @from_statuses
          UPDATE doc WITH @fields IN @@collection OPTIONS { keepNull: true }
          RETURN NEW
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.DATA_EXPORT_REQUESTS,
                "key": key,
                "from_statuses": from_statuses,
                "fields": data,
            },
        )
        docs = list(cursor)
        if not docs:
            return None
        return DataExportRequest(**self._from_doc(docs[0]))
