from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.common.enums import InvitationStatus
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.invitation_repository import IInvitationRepository
from app.domain.models.invitation import Invitation

if TYPE_CHECKING:
    from arango.database import StandardDatabase


class ArangoInvitationRepository(IInvitationRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.INVITATIONS)

    def get_by_key(self, key: str) -> Invitation | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return Invitation(**doc) if doc else None

    def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.token_hash == @token_hash
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": col.INVITATIONS, "token_hash": token_hash},
        )
        docs = list(cursor)
        if not docs:
            return None
        return Invitation(**self._from_doc(docs[0]))

    def create(self, invitation: Invitation) -> Invitation:
        doc = BaseArangoRepository.create(self, invitation)
        inv = Invitation(**doc)
        # Create edge: tenant -> invitation
        tenant_id = f"{col.TENANTS}/{invitation.tenant_key}"
        invitation_id = f"{col.INVITATIONS}/{inv.key}"
        self.create_edge(col.HAS_INVITATION, tenant_id, invitation_id)
        return inv

    def update(self, key: str, data: dict) -> Invitation | None:
        existing = self.get_by_key(key)
        if not existing:
            return None
        update_data = existing.model_copy(update=data)
        doc = BaseArangoRepository.update(self, key, update_data)
        return Invitation(**doc)

    def delete(self, key: str) -> bool:
        invitation_id = f"{col.INVITATIONS}/{key}"
        # Clean up edge
        query = f"""
        FOR e IN {col.HAS_INVITATION}
          FILTER e._to == @inv_id
          REMOVE e IN {col.HAS_INVITATION}
        """
        self._db.aql.execute(query, bind_vars={"inv_id": invitation_id})
        return BaseArangoRepository.delete(self, key)

    def list_by_tenant(self, tenant_key: str) -> list[Invitation]:
        query = """
        FOR doc IN @@collection
          FILTER doc.tenant_key == @tenant_key
          SORT doc.created_at DESC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": col.INVITATIONS, "tenant_key": tenant_key},
        )
        return [Invitation(**self._from_doc(doc)) for doc in cursor]

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
