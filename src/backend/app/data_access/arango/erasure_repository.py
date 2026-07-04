from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.erasure_repository import IErasureRepository
from app.domain.models.privacy import ErasureRequest


class ArangoErasureRepository(BaseArangoRepository[ErasureRequest], IErasureRepository):
    """ArangoDB persistence for REQ-025 erasure requests (Art. 17)."""

    _model_cls = ErasureRequest

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.ERASURE_REQUESTS)

    def create(self, erasure: ErasureRequest) -> ErasureRequest:
        created = super().create(erasure)
        if erasure.user_key and created.key:
            user_id = f"{col.USERS}/{erasure.user_key}"
            erasure_id = f"{col.ERASURE_REQUESTS}/{created.key}"
            self.create_edge(col.REQUESTED_ERASURE, user_id, erasure_id)
        return created

    def list_by_user(self, user_key: UserKey) -> list[ErasureRequest]:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
          SORT doc.requested_at DESC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.ERASURE_REQUESTS,
                "user_key": user_key,
            },
        )
        return [ErasureRequest(**self._from_doc(doc)) for doc in cursor]

    def find_active_for_user(self, user_key: UserKey) -> ErasureRequest | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
            AND doc.status IN ['scheduled', 'in_progress']
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.ERASURE_REQUESTS,
                "user_key": user_key,
            },
        )
        docs = list(cursor)
        if not docs:
            return None
        return ErasureRequest(**self._from_doc(docs[0]))

    def list_due_for_hard_delete(self, now_iso: str, stale_before_iso: str) -> list[ErasureRequest]:
        """Return erasure requests due for hard-delete, including retries.

        Selects three states (SEC-001 — under-erasure fix):

        - ``scheduled`` — first hard-delete attempt after the 90-day grace.
        - ``partially_completed`` — a previous run failed a pre-ArangoDB phase
          (transient storage / pgvector error) and left the request for retry.
        - ``in_progress`` — a worker crashed mid-run before flipping the status.
          Re-picked only when **stale** (``updated_at <= stale_before``) so a run
          that is genuinely still executing is never processed twice.

        ``stale_before_iso`` is ``now - run_interval`` (the staleness guard). All
        candidates additionally require ``hard_delete_scheduled_at <= now``.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.hard_delete_scheduled_at != null
            AND doc.hard_delete_scheduled_at <= @now
            AND (
              doc.status IN ['scheduled', 'partially_completed']
              OR (
                doc.status == 'in_progress'
                AND (doc.updated_at == null OR doc.updated_at <= @stale_before)
              )
            )
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.ERASURE_REQUESTS,
                "now": now_iso,
                "stale_before": stale_before_iso,
            },
        )
        return [ErasureRequest(**self._from_doc(doc)) for doc in cursor]
