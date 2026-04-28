from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.email_change_repository import IEmailChangeRepository
from app.domain.models.privacy import EmailChangeRequest, EmailChangeRequestKey


class ArangoEmailChangeRepository(IEmailChangeRepository, BaseArangoRepository):
    """ArangoDB persistence for REQ-025 email-change requests (Art. 16)."""

    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.EMAIL_CHANGE_REQUESTS)

    def create(self, change_request: EmailChangeRequest) -> EmailChangeRequest:
        doc = BaseArangoRepository.create(self, change_request)
        created = EmailChangeRequest(**doc)
        if change_request.user_key and created.key:
            user_id = f"{col.USERS}/{change_request.user_key}"
            change_id = f"{col.EMAIL_CHANGE_REQUESTS}/{created.key}"
            self.create_edge(col.REQUESTED_EMAIL_CHANGE, user_id, change_id)
        return created

    def get_by_key(self, key: EmailChangeRequestKey) -> EmailChangeRequest | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return EmailChangeRequest(**doc) if doc else None

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

    def update(
        self,
        key: EmailChangeRequestKey,
        change_request: EmailChangeRequest,
    ) -> EmailChangeRequest:
        doc = BaseArangoRepository.update(self, key, change_request)
        return EmailChangeRequest(**doc)

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
        query = """
        FOR doc IN @@collection
          FILTER doc.status == 'pending' AND doc.expires_at < @now
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
        return BaseArangoRepository.delete(self, key)
