from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.consent_repository import IConsentRepository
from app.domain.models.privacy import ConsentRecord, ConsentRecordKey


class ArangoConsentRepository(IConsentRepository, BaseArangoRepository):
    """ArangoDB persistence for REQ-025 consent records."""

    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.CONSENT_RECORDS)

    def create(self, consent: ConsentRecord) -> ConsentRecord:
        doc = BaseArangoRepository.create(self, consent)
        created = ConsentRecord(**doc)
        if consent.user_key and created.key:
            user_id = f"{col.USERS}/{consent.user_key}"
            consent_id = f"{col.CONSENT_RECORDS}/{created.key}"
            self.create_edge(col.HAS_CONSENT, user_id, consent_id)
        return created

    def get_by_key(self, key: ConsentRecordKey) -> ConsentRecord | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return ConsentRecord(**doc) if doc else None

    def get_by_user_and_purpose(
        self,
        user_key: UserKey,
        purpose: str,
    ) -> ConsentRecord | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key AND doc.purpose == @purpose
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.CONSENT_RECORDS,
                "user_key": user_key,
                "purpose": purpose,
            },
        )
        docs = list(cursor)
        if not docs:
            return None
        return ConsentRecord(**self._from_doc(docs[0]))

    def update(self, key: ConsentRecordKey, consent: ConsentRecord) -> ConsentRecord:
        doc = BaseArangoRepository.update(self, key, consent)
        return ConsentRecord(**doc)

    def list_by_user(self, user_key: UserKey) -> list[ConsentRecord]:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
          SORT doc.purpose ASC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.CONSENT_RECORDS,
                "user_key": user_key,
            },
        )
        return [ConsentRecord(**self._from_doc(doc)) for doc in cursor]

    def delete(self, key: ConsentRecordKey) -> bool:
        consent_id = f"{col.CONSENT_RECORDS}/{key}"
        query = f"FOR e IN {col.HAS_CONSENT} FILTER e._to == @consent_id REMOVE e IN {col.HAS_CONSENT}"
        self._db.aql.execute(query, bind_vars={"consent_id": consent_id})
        return BaseArangoRepository.delete(self, key)

    def delete_all_for_user(self, user_key: UserKey) -> int:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
          REMOVE doc IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.CONSENT_RECORDS,
                "user_key": user_key,
            },
        )
        return sum(1 for _ in cursor)
