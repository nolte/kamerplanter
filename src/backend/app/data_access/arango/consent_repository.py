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
    #: never mentioned (measured 2026-09-18 over all four call sites):
    #:
    #: * ``grant_consent`` / ``revoke_consent`` — ``get_by_user_and_purpose`` then
    #:   attribute assignment on the loaded :class:`ConsentRecord`
    #: * their two ``create`` branches — inserts, not updates
    #:
    #: ``mark_ip_anonymized`` (#1800, R-04a) is a direct field write, not a full
    #: replace — it never reads the record back, so this flag does not apply to it.
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

    def list_unanonymized_ips_before(self, cutoff_iso: str) -> list[tuple[str, str]]:
        """``(key, ip_address)`` of every consent record granted before the cutoff whose IP is still plain.

        NFR-011 R-04a.

        Mirrors ``RefreshTokenRepository.list_unanonymized_ips_before`` (R-03).
        ``granted_at`` is compared as an instant (#1784); a record whose grant
        time cannot be read **is** selected — anonymising is the minimising
        action, so an IP of unknown age is anonymised rather than kept in full
        (the same rule R-03's review GDPR-001 established).
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.ip_address != null
            AND doc.ip_anonymized_at == null
            AND (
              DATE_TIMESTAMP(doc.granted_at) == null
              OR DATE_TIMESTAMP(doc.granted_at) < DATE_TIMESTAMP(@cutoff)
            )
          RETURN { _key: doc._key, ip_address: doc.ip_address }
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.CONSENT_RECORDS,
                "cutoff": cutoff_iso,
            },
        )
        return [(row["_key"], row["ip_address"]) for row in cursor]

    def mark_ip_anonymized(
        self, key: ConsentRecordKey, previous_ip: str, anonymized_ip: str, anonymized_at_iso: str
    ) -> bool:
        """Replace a consent record's IP with its anonymised form, conditionally (NFR-011 R-04a, #1800).

        Guarded on ``ip_address == @previous_ip AND ip_anonymized_at == null``
        (#1800 security review, SEC-003): an unconditional
        ``collection.update`` would let a concurrent re-grant's fresh IP be
        overwritten by a stale hash and marked anonymised, leaving the fresh
        address unreachable by this task (it only selects
        ``ip_anonymized_at == null``).
        """
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key AND doc.ip_address == @previous_ip AND doc.ip_anonymized_at == null
          UPDATE doc WITH { ip_address: @anonymized_ip, ip_anonymized_at: @anonymized_at } IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.CONSENT_RECORDS,
                "key": key,
                "previous_ip": previous_ip,
                "anonymized_ip": anonymized_ip,
                "anonymized_at": anonymized_at_iso,
            },
        )
        return any(True for _ in cursor)

    def delete_revoked_before(self, cutoff_iso: str) -> int:
        """Hard-delete every consent record revoked before the cutoff, edges first (NFR-011 R-04, #1800).

        Two statements, like ``ArangoErasureRepository.delete_completed_before``
        (R-06): AQL forbids reading a collection after modifying it in the same
        query, so the ``has_consent`` edges into the selected records are removed
        first, then the records. ``revoked_at`` is compared as an instant and
        excluded when unreadable (#1784): this is a destructive selector, and a
        consent never revoked (the ordinary state of an active grant) must not
        be purged on the strength of a missing timestamp.
        """
        due = """
          FILTER doc.revoked_at != null
            AND DATE_TIMESTAMP(doc.revoked_at) != null
            AND DATE_TIMESTAMP(doc.revoked_at) < DATE_TIMESTAMP(@cutoff)
        """
        bind_vars = {"@collection": col.CONSENT_RECORDS, "cutoff": cutoff_iso}
        edges_query = f"""
        FOR doc IN @@collection
          {due}
          FOR edge IN @@edges
            FILTER edge._to == doc._id
            REMOVE edge IN @@edges
        """
        self._db.aql.execute(edges_query, bind_vars={**bind_vars, "@edges": col.HAS_CONSENT})
        docs_query = f"""
        FOR doc IN @@collection
          {due}
          REMOVE doc IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(docs_query, bind_vars=bind_vars)
        return len(list(cursor))

    def revoke_all_unrevoked(self, user_key: UserKey, now_iso: str) -> int:
        """Mark every consent record of *user_key* with no ``revoked_at`` as revoked *now* (NFR-011 R-04, #1800).

        Runs at account erasure, before Phase 2.5 pseudonymises the row. See
        the interface docstring for why an unrevoked record must not survive
        pseudonymisation with ``revoked_at`` still null.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key AND doc.revoked_at == null
          UPDATE doc WITH { granted: false, revoked_at: @now, updated_at: @now } IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": col.CONSENT_RECORDS, "user_key": user_key, "now": now_iso},
        )
        return sum(1 for _ in cursor)
