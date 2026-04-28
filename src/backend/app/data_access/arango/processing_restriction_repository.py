from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.processing_restriction_repository import (
    IProcessingRestrictionRepository,
)
from app.domain.models.privacy import (
    ProcessingRestriction,
    ProcessingRestrictionKey,
)


class ArangoProcessingRestrictionRepository(IProcessingRestrictionRepository, BaseArangoRepository):
    """ArangoDB persistence for REQ-025 processing restrictions (Art. 18 / 21)."""

    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.PROCESSING_RESTRICTIONS)

    def create(self, restriction: ProcessingRestriction) -> ProcessingRestriction:
        doc = BaseArangoRepository.create(self, restriction)
        created = ProcessingRestriction(**doc)
        if restriction.user_key and created.key:
            user_id = f"{col.USERS}/{restriction.user_key}"
            restriction_id = f"{col.PROCESSING_RESTRICTIONS}/{created.key}"
            self.create_edge(col.HAS_RESTRICTION, user_id, restriction_id)
        return created

    def get_by_key(self, key: ProcessingRestrictionKey) -> ProcessingRestriction | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return ProcessingRestriction(**doc) if doc else None

    def get_by_user_and_scope(
        self,
        user_key: UserKey,
        scope: str,
    ) -> ProcessingRestriction | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key AND doc.scope == @scope
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.PROCESSING_RESTRICTIONS,
                "user_key": user_key,
                "scope": scope,
            },
        )
        docs = list(cursor)
        if not docs:
            return None
        return ProcessingRestriction(**self._from_doc(docs[0]))

    def update(
        self,
        key: ProcessingRestrictionKey,
        restriction: ProcessingRestriction,
    ) -> ProcessingRestriction:
        doc = BaseArangoRepository.update(self, key, restriction)
        return ProcessingRestriction(**doc)

    def list_by_user(self, user_key: UserKey) -> list[ProcessingRestriction]:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
          SORT doc.created_at DESC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.PROCESSING_RESTRICTIONS,
                "user_key": user_key,
            },
        )
        return [ProcessingRestriction(**self._from_doc(doc)) for doc in cursor]

    def list_active_by_user(self, user_key: UserKey) -> list[ProcessingRestriction]:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key AND doc.lifted_at == null
          SORT doc.created_at DESC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.PROCESSING_RESTRICTIONS,
                "user_key": user_key,
            },
        )
        return [ProcessingRestriction(**self._from_doc(doc)) for doc in cursor]

    def delete(self, key: ProcessingRestrictionKey) -> bool:
        restriction_id = f"{col.PROCESSING_RESTRICTIONS}/{key}"
        query = f"FOR e IN {col.HAS_RESTRICTION} FILTER e._to == @restriction_id REMOVE e IN {col.HAS_RESTRICTION}"
        self._db.aql.execute(query, bind_vars={"restriction_id": restriction_id})
        return BaseArangoRepository.delete(self, key)
