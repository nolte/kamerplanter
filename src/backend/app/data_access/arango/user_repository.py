from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.user import User


class ArangoUserRepository(IUserRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.USERS)

    def get_by_key(self, key: UserKey) -> User | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return User(**doc) if doc else None

    def get_by_email(self, email: str) -> User | None:
        query = "FOR doc IN @@collection FILTER LOWER(doc.email) == LOWER(@email) LIMIT 1 RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.USERS, "email": email})
        docs = list(cursor)
        if not docs:
            return None
        return User(**self._from_doc(docs[0]))

    def create(self, user: User) -> User:
        doc = BaseArangoRepository.create(self, user)
        return User(**doc)

    def update(self, key: UserKey, user: User) -> User:
        doc = BaseArangoRepository.update(self, key, user)
        return User(**doc)

    def delete(self, key: UserKey) -> bool:
        user_id = f"{col.USERS}/{key}"
        # Delete auth provider edges + docs
        self.delete_edges(col.HAS_AUTH_PROVIDER, user_id)
        query = f"FOR doc IN {col.AUTH_PROVIDERS} FILTER doc.user_key == @key REMOVE doc IN {col.AUTH_PROVIDERS}"
        self._db.aql.execute(query, bind_vars={"key": key})
        # Delete refresh tokens
        query = f"FOR doc IN {col.REFRESH_TOKENS} FILTER doc.user_key == @key REMOVE doc IN {col.REFRESH_TOKENS}"
        self._db.aql.execute(query, bind_vars={"key": key})
        # Delete session edges
        self.delete_edges(col.HAS_SESSION, user_id)
        return BaseArangoRepository.delete(self, key)

    def get_unverified_before(self, cutoff_iso: str) -> list[User]:
        query = """
        FOR doc IN @@collection
          FILTER doc.email_verified == false AND doc.created_at < @cutoff
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.USERS, "cutoff": cutoff_iso})
        return [User(**self._from_doc(doc)) for doc in cursor]
