from typing import Any

from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, DocumentInsertError

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.engines.erasure_engine import TOMBSTONE_FULLMATCH_REGEX
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

    def create_with_key(self, erasure: ErasureRequest, key: str) -> ErasureRequest:
        """Insert *erasure* under the given document key (#1767 SEC-003).

        The immediate erasure entry keys its request deterministically per
        subject, so two callers that both found no open request cannot create
        two: the second insert fails on the primary key (``1210``, or ``1200``
        while the first insert is uncommitted) and surfaces as
        :class:`DuplicateError` / :class:`WriteConflictError`.
        """
        data = self._insert_payload(erasure)
        data["_key"] = key
        try:
            result = self.collection.insert(data, return_new=True)
        except DocumentInsertError as e:
            mapped = self._mapped_insert_error(e, self._collection_name, data)
            if mapped is not None:
                raise mapped from e
            raise
        created = ErasureRequest(**self._from_doc(result["new"]))
        if erasure.user_key:
            self.create_edge(
                col.REQUESTED_ERASURE,
                f"{col.USERS}/{erasure.user_key}",
                f"{col.ERASURE_REQUESTS}/{key}",
            )
        return created

    def list_by_user(self, user_key: UserKey) -> list[ErasureRequest]:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
          SORT DATE_TIMESTAMP(doc.requested_at) DESC
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
        """Return the user's open erasure request, if any.

        ``partially_completed`` counts as open (#1645 operator decision): the
        daily beat re-selects it and still owes it a run, so a second request
        for the same account would only schedule a duplicate of that duty.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
            AND doc.status IN ['scheduled', 'in_progress', 'partially_completed']
          SORT DATE_TIMESTAMP(doc.requested_at) ASC, doc._key ASC
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

        Both are compared as instants (#1784, see
        :mod:`app.data_access.arango.query_builder`). An ``updated_at`` that is
        missing **or unreadable** counts as stale: ``DATE_TIMESTAMP`` yields
        ``null`` for both, and ``null <= n`` is true — the same answer the
        explicit ``== null`` arm gives, on purpose.
        """
        query = """
        FOR doc IN @@collection
          FILTER DATE_TIMESTAMP(doc.hard_delete_scheduled_at) != null
            AND DATE_TIMESTAMP(doc.hard_delete_scheduled_at) <= DATE_TIMESTAMP(@now)
            AND (
              doc.status IN ['scheduled', 'partially_completed']
              OR (
                doc.status == 'in_progress'
                AND (
                  doc.updated_at == null
                  OR DATE_TIMESTAMP(doc.updated_at) <= DATE_TIMESTAMP(@stale_before)
                )
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

    def claim_for_run(self, key: str, *, now_iso: str, stale_before_iso: str) -> ErasureRequest | None:
        """Atomically claim an open request for one erasure run (#1767 SEC-003).

        Filter and write are one AQL ``UPDATE`` on one document: ArangoDB
        serialises writes per document, so of two concurrent claims one sees the
        other's ``in_progress`` (and is filtered out) or fails with a write-write
        conflict (``1200``). Both read as *not claimed*: the other run owns it.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
            AND doc.status != 'completed'
            AND (
              doc.status != 'in_progress'
              OR doc.updated_at == null
              OR DATE_TIMESTAMP(doc.updated_at) <= DATE_TIMESTAMP(@stale_before)
            )
          UPDATE doc WITH { status: 'in_progress', last_attempt_at: @now, updated_at: @now } IN @@collection
          RETURN NEW
        """
        try:
            cursor = self._db.aql.execute(
                query,
                bind_vars={
                    "@collection": col.ERASURE_REQUESTS,
                    "key": key,
                    "now": now_iso,
                    "stale_before": stale_before_iso,
                },
            )
            docs = list(cursor)
        except AQLQueryExecuteError as exc:
            if exc.error_code == 1200:  # write-write conflict: a concurrent claim holds the document
                return None
            raise
        if not docs:
            return None
        return ErasureRequest(**self._from_doc(docs[0]))

    #: The purge predicate, shared by every statement below so they cannot drift.
    #: ``completed_at`` is compared as an **instant** (``DATE_TIMESTAMP``), not as
    #: a string: ArangoDB orders strings by ICU collation, under which
    #: ``…:00.5Z`` sorts *before* ``…:00+00:00`` — a completion half a second
    #: after the cutoff was purged (#1773 review GDPR-009, measured). An
    #: unparsable value yields ``null``, which AQL orders below every number, so
    #: it is excluded explicitly rather than read as "long ago".
    _PURGE_DUE = """
          FILTER doc.status == 'completed'
            AND DATE_TIMESTAMP(doc.completed_at) != null
            AND DATE_TIMESTAMP(doc.completed_at) < DATE_TIMESTAMP(@cutoff)
    """
    #: Only a record whose ``user_key`` is already the tombstone is proof of a
    #: finished erasure (#1773 review GDPR-006): the erasure transaction rewrites
    #: the key. A ``completed`` record still naming its subject may be the only
    #: trace of an Art. 17 duty that was never fulfilled.
    _IS_TOMBSTONED = "REGEX_TEST(TO_STRING(doc.user_key), @tombstone)"

    def delete_completed_before(self, cutoff_iso: str) -> int:
        """Hard-delete completed, tombstoned requests past the NFR-011 R-06 period, edges first (#1772).

        Two statements, because AQL forbids reading a collection after
        modifying it in the same query: the ``requested_erasure`` edges into
        the selected requests are removed first, then the requests. The two
        selections cannot diverge between the statements: a request completing
        meanwhile carries ``completed_at = now``, never a time before a cutoff
        a year back, and a ``user_key`` becomes a tombstone only inside the
        erasure transaction, never back. Both carry the tombstone filter — the
        edge statement too, or a held record would lose its edge.
        """
        bind_vars: dict[str, Any] = {
            "@collection": col.ERASURE_REQUESTS,
            "cutoff": cutoff_iso,
            "tombstone": TOMBSTONE_FULLMATCH_REGEX,
        }
        edges_query = f"""
        FOR doc IN @@collection
          {self._PURGE_DUE}
          FILTER {self._IS_TOMBSTONED}
          FOR edge IN @@edges
            FILTER edge._to == doc._id
            REMOVE edge IN @@edges
        """
        self._db.aql.execute(edges_query, bind_vars={**bind_vars, "@edges": col.REQUESTED_ERASURE})
        docs_query = f"""
        FOR doc IN @@collection
          {self._PURGE_DUE}
          FILTER {self._IS_TOMBSTONED}
          REMOVE doc IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(docs_query, bind_vars=bind_vars)
        return len(list(cursor))

    def count_completed_without_tombstone_before(self, cutoff_iso: str) -> int:
        """Count the requests the purge holds back: due, but ``user_key`` is no tombstone (GDPR-006)."""
        query = f"""
        FOR doc IN @@collection
          {self._PURGE_DUE}
          FILTER !{self._IS_TOMBSTONED}
          COLLECT WITH COUNT INTO held
          RETURN held
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.ERASURE_REQUESTS,
                "cutoff": cutoff_iso,
                "tombstone": TOMBSTONE_FULLMATCH_REGEX,
            },
        )
        return int(next(iter(cursor), 0))
