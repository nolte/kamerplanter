"""REQ-029 §2 — ArangoDB repository for identification requests."""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.identification_repository import IIdentificationRepository
from app.domain.models.identification import IdentificationRequest


class ArangoIdentificationRepository(BaseArangoRepository[IdentificationRequest], IIdentificationRepository):
    """ArangoDB-backed repository for ``identification_requests``."""

    _model_cls = IdentificationRequest

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.IDENTIFICATION_REQUESTS)

    def get(self, key: str, tenant_key: str) -> IdentificationRequest | None:
        request = super().get_by_key(key)
        if request is None or request.tenant_key != tenant_key:
            return None
        return request

    def set_selected_rank(
        self,
        key: str,
        tenant_key: str,
        selected_rank: int,
    ) -> IdentificationRequest | None:
        query = """
        FOR req IN @@collection
          FILTER req._key == @key AND req.tenant_key == @tenant_key
          UPDATE req WITH {
            selected_result_rank: @rank,
            updated_at: @now
          } IN @@collection
          RETURN NEW
        """
        bind_vars = {
            "@collection": self._collection_name,
            "key": key,
            "tenant_key": tenant_key,
            "rank": selected_rank,
            "now": self._now(),
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        updated = next(cursor, None)
        if updated is None:
            return None
        return IdentificationRequest(**self._from_doc(updated))

    def set_plant_instance_key(
        self,
        key: str,
        tenant_key: str,
        plant_instance_key: str,
    ) -> IdentificationRequest | None:
        """Link the identification request to the plant instance created from it (#630).

        The ``tenant_key`` filter is part of the parametrized ``FILTER`` (never an
        f-string) so a caller can only ever mutate a record in its own tenant.
        Returns ``None`` when no matching record exists in this tenant.
        """
        query = """
        FOR req IN @@collection
          FILTER req._key == @key AND req.tenant_key == @tenant_key
          UPDATE req WITH {
            plant_instance_key: @plant_instance_key,
            updated_at: @now
          } IN @@collection
          RETURN NEW
        """
        bind_vars = {
            "@collection": self._collection_name,
            "key": key,
            "tenant_key": tenant_key,
            "plant_instance_key": plant_instance_key,
            "now": self._now(),
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        updated = next(cursor, None)
        if updated is None:
            return None
        return IdentificationRequest(**self._from_doc(updated))

    def list_for_user(
        self,
        tenant_key: str,
        user_key: str,
        limit: int = 20,
    ) -> list[IdentificationRequest]:
        query = """
        FOR req IN @@collection
          FILTER req.tenant_key == @tenant_key AND req.user_key == @user_key
          SORT req.created_at DESC
          LIMIT @limit
          RETURN req
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "user_key": user_key,
            "limit": limit,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [IdentificationRequest(**self._from_doc(doc)) for doc in cursor]
