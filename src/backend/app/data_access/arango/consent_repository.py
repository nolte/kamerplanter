from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.consent_repository import IConsentRepository
from app.domain.models.privacy import ConsentRecord, ConsentRecordKey


class ArangoConsentRepository(BaseArangoRepository[ConsentRecord], IConsentRepository):
    """ArangoDB persistence for REQ-025 consent records."""

    _model_cls = ConsentRecord

    #: Full-replace null semantics for ``consent_records`` (#1516).
    #:
    #: ``PrivacyService.grant_consent`` re-grants a revoked consent by nulling
    #: ``revoked_at`` (and by writing the request's ``ip_address``/``user_agent``,
    #: which are ``None`` when the caller has none). In the inherited merge mode
    #: all three were dropped, so the record kept the timestamp of its revocation
    #: next to ``granted=True`` and kept the IP of the *previous* grant — a
    #: personal datum the new grant did not supply (REQ-025).
    #:
    #: **Every writer starts from the stored record**, so none can lose a field it
    #: never mentioned (measured 2026-09-18 over all four call sites; nothing else
    #: writes ``consent_records`` — the retention/anonymisation beat task touches
    #: ``refresh_tokens`` only):
    #:
    #: * ``grant_consent`` / ``revoke_consent`` — ``get_by_user_and_purpose`` then
    #:   attribute assignment on the loaded :class:`ConsentRecord`
    #: * their two ``create`` branches — inserts, not updates
    _update_is_full_replace = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.CONSENT_RECORDS)

    def create(self, consent: ConsentRecord) -> ConsentRecord:
        created = super().create(consent)
        if consent.user_key and created.key:
            user_id = f"{col.USERS}/{consent.user_key}"
            consent_id = f"{col.CONSENT_RECORDS}/{created.key}"
            self.create_edge(col.HAS_CONSENT, user_id, consent_id)
        return created

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
        return super().delete(key)

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
