from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.email_change_repository import IEmailChangeRepository
from app.domain.models.privacy import EmailChangeRequest, EmailChangeRequestKey


class ArangoEmailChangeRepository(BaseArangoRepository[EmailChangeRequest], IEmailChangeRepository):
    """ArangoDB persistence for REQ-025 email-change requests (Art. 16)."""

    _model_cls = EmailChangeRequest

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.EMAIL_CHANGE_REQUESTS)

    def create(self, change_request: EmailChangeRequest) -> EmailChangeRequest:
        created = super().create(change_request)
        if change_request.user_key and created.key:
            user_id = f"{col.USERS}/{change_request.user_key}"
            change_id = f"{col.EMAIL_CHANGE_REQUESTS}/{created.key}"
            self.create_edge(col.REQUESTED_EMAIL_CHANGE, user_id, change_id)
        return created

    def get_by_token_hash(self, token_hash: str) -> EmailChangeRequest | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.verification_token_hash == @token_hash
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.EMAIL_CHANGE_REQUESTS,
                "token_hash": token_hash,
            },
        )
        docs = list(cursor)
        if not docs:
            return None
        return EmailChangeRequest(**self._from_doc(docs[0]))

    def get_by_revert_token_hash(self, token_hash: str) -> EmailChangeRequest | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.revert_token_hash == @token_hash
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.EMAIL_CHANGE_REQUESTS,
                "token_hash": token_hash,
            },
        )
        docs = list(cursor)
        if not docs:
            return None
        return EmailChangeRequest(**self._from_doc(docs[0]))

    def find_revert_reservation(self, email: str, now_iso: str) -> EmailChangeRequest | None:
        """The confirmed change whose revert window still holds *email* for its previous owner (#1848).

        While the window is open the previous address is reserved: an account
        registered on it — which needs no mailbox access, registration is
        unverified — would otherwise make every revert answer "taken".
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.status == 'confirmed'
            AND LOWER(doc.previous_email) == LOWER(@email)
            AND DATE_TIMESTAMP(doc.revert_expires_at) > DATE_TIMESTAMP(@now)
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": col.EMAIL_CHANGE_REQUESTS, "email": email, "now": now_iso},
        )
        docs = list(cursor)
        return EmailChangeRequest(**self._from_doc(docs[0])) if docs else None

    def claim_status(self, key: EmailChangeRequestKey, from_status: str, to_status: str, now_iso: str) -> bool:
        """Compare-and-set on ``status`` in one AQL write (#1848).

        The confirmation and the revert read a request, check it, then write the
        account. Two of them racing on one request (or a revert racing the
        confirmation of another) each saw the status they needed; the claim makes
        exactly one of them win before the account is touched.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key AND doc.status == @from_status
          UPDATE doc WITH MERGE(
            { status: @to_status, updated_at: @now },
            @to_status == 'confirmed' ? { confirmed_at: @now } : {}
          ) IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.EMAIL_CHANGE_REQUESTS,
                "key": key,
                "from_status": from_status,
                "to_status": to_status,
                "now": now_iso,
            },
        )
        return any(True for _ in cursor)

    def record_confirmation(
        self,
        key: EmailChangeRequestKey,
        *,
        previous_email: str,
        revert_token_hash: str,
        revert_expires_at_iso: str,
        now_iso: str,
    ) -> bool:
        """Stamp the revert data onto a confirmed request, conditionally (#1848).

        A plain :meth:`update` would write ``status`` back as well and could turn
        a request a concurrent revert just superseded into a live one again.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key AND doc.status == 'confirmed'
          UPDATE doc WITH {
            previous_email: @previous_email,
            revert_token_hash: @revert_token_hash,
            revert_expires_at: @revert_expires_at,
            updated_at: @now
          } IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.EMAIL_CHANGE_REQUESTS,
                "key": key,
                "previous_email": previous_email,
                "revert_token_hash": revert_token_hash,
                "revert_expires_at": revert_expires_at_iso,
                "now": now_iso,
            },
        )
        return any(True for _ in cursor)

    def supersede_confirmed_after(self, user_key: UserKey, confirmed_after_iso: str, now_iso: str) -> int:
        """Close the revert windows of the account's changes confirmed after the instant (#1848).

        Compared as instants. A revert takes the account back to the state before
        its change; a change confirmed later — the attacker's own second hop —
        must not be able to undo that with its own revert token.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
            AND doc.status == 'confirmed'
            AND DATE_TIMESTAMP(doc.confirmed_at) > DATE_TIMESTAMP(@after)
          UPDATE doc WITH { status: 'superseded', updated_at: @now } IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.EMAIL_CHANGE_REQUESTS,
                "user_key": user_key,
                "after": confirmed_after_iso,
                "now": now_iso,
            },
        )
        return sum(1 for _ in cursor)

    def close_revert_windows(self, now_iso: str) -> int:
        """Drop the previous address and the revert token once the window closed (NFR-011 R-07, #1848).

        Compared as instants, like :meth:`expire_old`. A change with a revert token
        but an unreadable window is closed too — the conservative reading.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.revert_token_hash != null
            AND (
              DATE_TIMESTAMP(doc.revert_expires_at) == null
              OR DATE_TIMESTAMP(doc.revert_expires_at) < DATE_TIMESTAMP(@now)
            )
          UPDATE doc WITH {
            previous_email: null, revert_token_hash: null, revert_expires_at: null, updated_at: @now
          } IN @@collection OPTIONS { keepNull: true }
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.EMAIL_CHANGE_REQUESTS,
                "now": now_iso,
            },
        )
        return sum(1 for _ in cursor)

    def list_pending_for_user(self, user_key: UserKey) -> list[EmailChangeRequest]:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key AND doc.status == 'pending'
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.EMAIL_CHANGE_REQUESTS,
                "user_key": user_key,
            },
        )
        return [EmailChangeRequest(**self._from_doc(doc)) for doc in cursor]

    def expire_old(self, now_iso: str) -> int:
        """Flip every pending request past its ``expires_at`` to ``expired``.

        Compared as instants (see :mod:`app.data_access.arango.query_builder`).
        ``expires_at`` is required on :class:`EmailChangeRequest`; a request whose
        expiry is missing or unreadable is treated as expired, as the string
        comparison did for ``null``.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.status == 'pending'
            AND (
              DATE_TIMESTAMP(doc.expires_at) == null
              OR DATE_TIMESTAMP(doc.expires_at) < DATE_TIMESTAMP(@now)
            )
          UPDATE doc WITH { status: 'expired', updated_at: @now } IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.EMAIL_CHANGE_REQUESTS,
                "now": now_iso,
            },
        )
        return sum(1 for _ in cursor)

    def delete(self, key: EmailChangeRequestKey) -> bool:
        change_id = f"{col.EMAIL_CHANGE_REQUESTS}/{key}"
        query = (
            f"FOR e IN {col.REQUESTED_EMAIL_CHANGE} FILTER e._to == @change_id REMOVE e IN {col.REQUESTED_EMAIL_CHANGE}"
        )
        self._db.aql.execute(query, bind_vars={"change_id": change_id})
        return super().delete(key)

    #: Unconfirmed terminal states (NFR-011 R-07, #1800): never reached
    #: ``confirmed``, so the request served no further purpose once its
    #: ``expires_at`` passed. ``cancelled`` (#1841) is the owner taking the
    #: account back while the request was still ``pending`` — it never confirms
    #: either, so it shares R-07's clock, not R-07b's.
    _UNCONFIRMED_STATUSES = ["pending", "expired", "cancelled"]

    def delete_expired_unconfirmed(self, now_iso: str) -> int:
        """Hard-delete every unconfirmed request past its ``expires_at``, edges first (NFR-011 R-07, #1800).

        Until #1800 :meth:`expire_old` only flipped the status; ``new_email``
        (and every other field) outlived the account this many hours forever.
        Two statements, like ``ArangoErasureRepository.delete_completed_before``:
        AQL forbids reading a collection after modifying it in the same query, so
        the ``requested_email_change`` edges into the selected requests are
        removed first, then the requests. ``expires_at`` is a required field on
        :class:`EmailChangeRequest`, so — like :meth:`expire_old` — a missing or
        unreadable value is treated as already expired rather than excluded.
        """
        due = """
          FILTER doc.status IN @unconfirmed
            AND (
              DATE_TIMESTAMP(doc.expires_at) == null
              OR DATE_TIMESTAMP(doc.expires_at) < DATE_TIMESTAMP(@now)
            )
        """
        bind_vars = {
            "@collection": col.EMAIL_CHANGE_REQUESTS,
            "unconfirmed": self._UNCONFIRMED_STATUSES,
            "now": now_iso,
        }
        edges_query = f"""
        FOR doc IN @@collection
          {due}
          FOR edge IN @@edges
            FILTER edge._to == doc._id
            REMOVE edge IN @@edges
        """
        self._db.aql.execute(edges_query, bind_vars={**bind_vars, "@edges": col.REQUESTED_EMAIL_CHANGE})
        docs_query = f"""
        FOR doc IN @@collection
          {due}
          REMOVE doc IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(docs_query, bind_vars=bind_vars)
        return len(list(cursor))

    #: Confirmed terminal states (NFR-011 R-07b, #1800): every one of these
    #: reached ``confirmed`` at least once and therefore carries a ``confirmed_at``
    #: R-07b's window is measured from.
    _CONFIRMED_STATUSES = ["confirmed", "reverted", "superseded"]

    def delete_confirmed_past_revert_window(self, cutoff_iso: str) -> int:
        """Hard-delete the whole document of a confirmed change past its R-07a revert window (NFR-011 R-07b, #1800).

        ``cutoff_iso`` is ``now - RETENTION_EMAIL_CHANGE_REVERT_DAYS``
        (:meth:`RetentionService.email_change_document_purge_cutoff`), compared
        against ``confirmed_at`` — not the nullable ``revert_expires_at``
        :meth:`close_revert_windows` (R-07a) itself clears, so this does not
        depend on R-07a's own write having already run in the same beat cycle.
        Until #1800 R-07a only nulled ``previous_email`` / ``revert_token_hash`` /
        ``revert_expires_at``; the rest of the document (``new_email``,
        ``requested_at``, ``confirmed_at``, …) stayed forever.
        """
        due = """
          FILTER doc.status IN @confirmed
            AND DATE_TIMESTAMP(doc.confirmed_at) != null
            AND DATE_TIMESTAMP(doc.confirmed_at) < DATE_TIMESTAMP(@cutoff)
        """
        bind_vars = {
            "@collection": col.EMAIL_CHANGE_REQUESTS,
            "confirmed": self._CONFIRMED_STATUSES,
            "cutoff": cutoff_iso,
        }
        edges_query = f"""
        FOR doc IN @@collection
          {due}
          FOR edge IN @@edges
            FILTER edge._to == doc._id
            REMOVE edge IN @@edges
        """
        self._db.aql.execute(edges_query, bind_vars={**bind_vars, "@edges": col.REQUESTED_EMAIL_CHANGE})
        docs_query = f"""
        FOR doc IN @@collection
          {due}
          REMOVE doc IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(docs_query, bind_vars=bind_vars)
        return len(list(cursor))
