from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.data_export_repository import IDataExportRepository
from app.domain.models.privacy import DataExportRequest, DataExportRequestKey


class ArangoDataExportRepository(IDataExportRepository, BaseArangoRepository):
    """ArangoDB persistence for REQ-025 data-export requests."""

    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.DATA_EXPORT_REQUESTS)

    def create(self, export_request: DataExportRequest) -> DataExportRequest:
        doc = BaseArangoRepository.create(self, export_request)
        created = DataExportRequest(**doc)
        if export_request.user_key and created.key:
            user_id = f"{col.USERS}/{export_request.user_key}"
            export_id = f"{col.DATA_EXPORT_REQUESTS}/{created.key}"
            self.create_edge(col.REQUESTED_EXPORT, user_id, export_id)
        return created

    def get_by_key(self, key: DataExportRequestKey) -> DataExportRequest | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return DataExportRequest(**doc) if doc else None

    def update(
        self,
        key: DataExportRequestKey,
        export_request: DataExportRequest,
    ) -> DataExportRequest:
        doc = BaseArangoRepository.update(self, key, export_request)
        return DataExportRequest(**doc)

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
        return BaseArangoRepository.delete(self, key)

    def expire_old(self, now_iso: str) -> int:
        """Flip completed exports past their 72-hour expiry to ``status=expired``.

        NFR-011 R-05 — called by the daily Celery retention task.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.status == 'completed' AND doc.expires_at != null AND doc.expires_at < @now
          UPDATE doc WITH { status: 'expired' } IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.DATA_EXPORT_REQUESTS,
                "now": now_iso,
            },
        )
        return sum(1 for _ in cursor)

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
