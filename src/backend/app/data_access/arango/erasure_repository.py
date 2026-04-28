from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.erasure_repository import IErasureRepository
from app.domain.models.privacy import ErasureRequest, ErasureRequestKey


class ArangoErasureRepository(IErasureRepository, BaseArangoRepository):
    """ArangoDB persistence for REQ-025 erasure requests (Art. 17)."""

    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.ERASURE_REQUESTS)

    def create(self, erasure: ErasureRequest) -> ErasureRequest:
        doc = BaseArangoRepository.create(self, erasure)
        created = ErasureRequest(**doc)
        if erasure.user_key and created.key:
            user_id = f"{col.USERS}/{erasure.user_key}"
            erasure_id = f"{col.ERASURE_REQUESTS}/{created.key}"
            self.create_edge(col.REQUESTED_ERASURE, user_id, erasure_id)
        return created

    def get_by_key(self, key: ErasureRequestKey) -> ErasureRequest | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return ErasureRequest(**doc) if doc else None

    def update(self, key: ErasureRequestKey, erasure: ErasureRequest) -> ErasureRequest:
        doc = BaseArangoRepository.update(self, key, erasure)
        return ErasureRequest(**doc)

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

    def list_due_for_hard_delete(self, now_iso: str) -> list[ErasureRequest]:
        query = """
        FOR doc IN @@collection
          FILTER doc.status == 'scheduled'
            AND doc.hard_delete_scheduled_at != null
            AND doc.hard_delete_scheduled_at <= @now
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.ERASURE_REQUESTS,
                "now": now_iso,
            },
        )
        return [ErasureRequest(**self._from_doc(doc)) for doc in cursor]
