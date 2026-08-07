from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.common.enums import InvitationStatus
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

    def list_by_tenant(self, tenant_key: str) -> list[Invitation]:
        return self.find_by_field("tenant_key", tenant_key, sort="created_at", sort_direction="DESC")

    def cleanup_expired(self) -> int:
        now = datetime.now(UTC).isoformat()
        query = f"""
        FOR doc IN {col.INVITATIONS}
          FILTER doc.status == @pending AND doc.expires_at < @now
          UPDATE doc WITH {{ status: @expired, updated_at: @now }} IN {col.INVITATIONS}
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "pending": InvitationStatus.PENDING.value,
                "expired": InvitationStatus.EXPIRED.value,
                "now": now,
            },
        )
        return sum(1 for _ in cursor)

    def delete_all_for_tenant(self, tenant_key: str) -> int:
        query = f"""
        FOR doc IN {col.INVITATIONS}
          FILTER doc.tenant_key == @tenant_key
          LET inv_id = CONCAT("{col.INVITATIONS}/", doc._key)
          LET del_edge = (
            FOR e IN {col.HAS_INVITATION} FILTER e._to == inv_id REMOVE e IN {col.HAS_INVITATION}
          )
          REMOVE doc IN {col.INVITATIONS}
          RETURN 1
        """
        cursor = self._db.aql.execute(query, bind_vars={"tenant_key": tenant_key})
        return sum(1 for _ in cursor)
