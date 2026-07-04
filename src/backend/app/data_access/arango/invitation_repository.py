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

    def update(self, key: str, data: dict) -> Invitation | None:
        existing = self.get_by_key(key)
        if not existing:
            return None
        update_data = existing.model_copy(update=data)
        return super().update(key, update_data)

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
