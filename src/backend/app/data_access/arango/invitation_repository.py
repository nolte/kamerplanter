from datetime import UTC, datetime
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.common.enums import InvitationStatus, InvitationType
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.invitation_repository import IInvitationRepository
from app.domain.models.invitation import Invitation


class ArangoInvitationRepository(BaseArangoRepository[Invitation], IInvitationRepository):
    _model_cls = Invitation

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.INVITATIONS)

    def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        return self.find_one_by_field("token_hash", token_hash)

    def list_pending_email_invitations(self, email: str) -> list[Invitation]:
        """The pending ``email`` invitations issued for *email*, case-insensitively (REQ-023 §3.2d, #2132)."""
        cursor = self._db.aql.execute(
            """
            FOR inv IN @@collection
              FILTER inv.invitation_type == @type AND inv.status == @status
                AND LOWER(inv.email) == LOWER(@email)
              RETURN inv
            """,
            bind_vars={
                "@collection": col.INVITATIONS,
                "type": InvitationType.EMAIL.value,
                "status": InvitationStatus.PENDING.value,
                "email": email.strip(),
            },
        )
        return [Invitation(**self._from_doc(doc)) for doc in cast(Cursor, cursor)]

    def count_email_invitations_issued_since(self, invited_by_user_key: str, since_iso: str) -> int:
        """The issuer's ``email`` invitations created at or after *since_iso*, any status (#2162 review W-1)."""
        cursor = self._db.aql.execute(
            """
            FOR inv IN @@collection
              FILTER inv.invited_by_user_key == @issuer AND inv.invitation_type == @type
                AND DATE_TIMESTAMP(inv.created_at) >= DATE_TIMESTAMP(@since)
              COLLECT WITH COUNT INTO n
              RETURN n
            """,
            bind_vars={
                "@collection": col.INVITATIONS,
                "issuer": invited_by_user_key,
                "type": InvitationType.EMAIL.value,
                "since": since_iso,
            },
        )
        return int(next(iter(cast(Cursor, cursor)), 0))

    def create(self, invitation: Invitation) -> Invitation:
        created = super().create(invitation)
        # Create edge: tenant -> invitation
        tenant_id = f"{col.TENANTS}/{invitation.tenant_key}"
        invitation_id = f"{col.INVITATIONS}/{created.key}"
        self.create_edge(col.HAS_INVITATION, tenant_id, invitation_id)
        return created

    def update_fields(self, key: str, fields: dict) -> Invitation | None:
        """Merge ``fields`` into the stored invitation and rewrite it (#968 §2).

        **Renamed from ``update``.** The old name shadowed
        :meth:`BaseArangoRepository.update`, whose signature takes a full
        *model*, with one that takes an arbitrary ``dict``. That reads like
        the checked full-model path while accepting whatever keys it is
        handed, so a caller who forwarded request data would have performed
        mass assignment under a reassuring name. The name now says what the
        payload is, and the inherited full-model :meth:`update` is reachable
        again on this repository instead of being shadowed.

        **Caller obligation.** ``fields`` is applied key-by-key, so it must be
        built from named fields or a validated schema's ``model_dump()`` —
        never from a raw request body. ``model_copy(update=...)`` does not
        validate, so an unknown or ill-typed key survives this step; what
        catches an ill-typed *declared* field is the re-validation the
        inherited :meth:`update` performs on the merged model (#968).

        **Not the base class's merge.** This deliberately keeps its
        read-modify-write shape rather than delegating to
        :meth:`BaseArangoRepository.update_fields`: that method writes the
        dict straight through and is documented as unchecked, whereas this
        one materialises a full Invitation and therefore gets validated. The
        price is the base method's lost-update commutativity — two concurrent
        calls touching *disjoint* fields can clobber each other here. Swapping
        that trade is a decision of its own, not a side effect of a rename.

        Returns ``None`` when no invitation carries ``key``.
        """
        existing = self.get_by_key(key)
        if not existing:
            return None
        merged = existing.model_copy(update=fields)
        return super().update(key, merged)

    def delete(self, key: str) -> bool:
        invitation_id = f"{col.INVITATIONS}/{key}"
        self.delete_edges(col.HAS_INVITATION, invitation_id, direction="inbound")
        return super().delete(key)

    def list_by_tenant(
        self, tenant_key: str, *, offset: int | None = None, limit: int | None = None
    ) -> list[Invitation]:
        """A tenant's invitations, newest first; ``offset``/``limit`` read one window (MT-035, #2131)."""
        return self.find_by_field(
            "tenant_key",
            tenant_key,
            sort="created_at",
            sort_direction="DESC",
            offset=offset,
            limit=limit,
            tiebreak_key=True,
        )

    def mark_accepted_if_pending(self, key: str, fields: dict[str, Any]) -> Invitation | None:
        """Accept *key* only while it is ``pending``: one AQL ``UPDATE`` on one document (AK-IE-06)."""
        query = f"""
        FOR doc IN {col.INVITATIONS}
          FILTER doc._key == @key AND doc.status == @pending
          UPDATE doc WITH MERGE(@fields, {{ status: @accepted, updated_at: @now }}) IN {col.INVITATIONS}
          RETURN NEW
        """
        docs = list(
            self._db.aql.execute(
                query,
                bind_vars={
                    "key": key,
                    "fields": fields,
                    "pending": InvitationStatus.PENDING.value,
                    "accepted": InvitationStatus.ACCEPTED.value,
                    "now": datetime.now(UTC).isoformat(),
                },
            )
        )
        return Invitation(**self._from_doc(docs[0])) if docs else None

    def revoke_pending_for_tenant(self, tenant_key: str) -> int:
        """Revoke every pending invitation into *tenant_key* in one statement (REQ-025 AK-IE-06)."""
        query = f"""
        FOR doc IN {col.INVITATIONS}
          FILTER doc.tenant_key == @tenant_key AND doc.status == @pending
          UPDATE doc WITH {{ status: @revoked, updated_at: @now }} IN {col.INVITATIONS}
          COLLECT WITH COUNT INTO affected
          RETURN affected
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "tenant_key": tenant_key,
                "pending": InvitationStatus.PENDING.value,
                "revoked": InvitationStatus.REVOKED.value,
                "now": datetime.now(UTC).isoformat(),
            },
        )
        return int(next(cursor, 0))

    def cleanup_expired(self, *, now: datetime | None = None) -> int:
        """Flip every pending invitation past its ``expires_at`` to ``expired``.

        ``now`` defaults to the wall clock; the parameter exists so the cutoff can
        be pinned in a test. Compared as instants (see
        :mod:`app.data_access.arango.query_builder`); ``expires_at`` is required
        on :class:`Invitation`, so one that is missing or unreadable is treated
        as expired rather than left acceptable for good.
        """
        stamp = (now or datetime.now(UTC)).isoformat()
        query = f"""
        FOR doc IN {col.INVITATIONS}
          FILTER doc.status == @pending
            AND (
              DATE_TIMESTAMP(doc.expires_at) == null
              OR DATE_TIMESTAMP(doc.expires_at) < DATE_TIMESTAMP(@now)
            )
          UPDATE doc WITH {{ status: @expired, updated_at: @now }} IN {col.INVITATIONS}
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "pending": InvitationStatus.PENDING.value,
                "expired": InvitationStatus.EXPIRED.value,
                "now": stamp,
            },
        )
        return sum(1 for _ in cursor)

    def delete_expired_before(self, cutoff_iso: str) -> int:
        """Hard-delete every ``expired`` invitation past the cutoff, edges first (NFR-011 R-12, #1800).

        Two statements, like ``ArangoErasureRepository.delete_completed_before``
        (R-06): AQL forbids reading a collection after modifying it in the same
        query, so the ``has_invitation`` edges into the selected invitations are
        removed first, then the invitations. ``expires_at`` is required on
        :class:`Invitation`, so — like :meth:`cleanup_expired` — a missing or
        unreadable value is treated as already past the cutoff rather than
        excluded (the documented exception for an ``expires_at`` selector, #1784).
        """
        due = """
          FILTER doc.status == @expired
            AND (
              DATE_TIMESTAMP(doc.expires_at) == null
              OR DATE_TIMESTAMP(doc.expires_at) < DATE_TIMESTAMP(@cutoff)
            )
        """
        bind_vars = {
            "@collection": col.INVITATIONS,
            "expired": InvitationStatus.EXPIRED.value,
            "cutoff": cutoff_iso,
        }
        edges_query = f"""
        FOR doc IN @@collection
          {due}
          FOR edge IN @@edges
            FILTER edge._to == doc._id
            REMOVE edge IN @@edges
        """
        self._db.aql.execute(edges_query, bind_vars={**bind_vars, "@edges": col.HAS_INVITATION})
        docs_query = f"""
        FOR doc IN @@collection
          {due}
          REMOVE doc IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(docs_query, bind_vars=bind_vars)
        return len(list(cursor))
