"""REQ-010 — ArangoDB repository for ``pest_image_contributions``.

All queries are tenant-scoped and fully parametrized (``bind_vars`` only, no
f-string interpolation) so a tenant can never read or delete another tenant's
contributed pest images.
"""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.pest_image_repository import IPestImageRepository
from app.domain.models.pest_image import PestImageContribution


class ArangoPestImageRepository(IPestImageRepository, BaseArangoRepository):
    """ArangoDB-backed repository for ``pest_image_contributions``."""

    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.PEST_IMAGE_CONTRIBUTIONS)

    def create(self, contribution: PestImageContribution) -> PestImageContribution:
        doc = BaseArangoRepository.create(self, contribution)
        return PestImageContribution(**doc)

    def get(self, key: str, tenant_key: str) -> PestImageContribution | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        if doc is None or doc.get("tenant_key") != tenant_key:
            return None
        return PestImageContribution(**doc)

    def list_for_pest(self, tenant_key: str, pest_key: str) -> list[PestImageContribution]:
        query = """
        FOR c IN @@collection
          FILTER c.tenant_key == @tenant_key AND c.pest_key == @pest_key
          SORT c.created_at DESC
          RETURN c
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "pest_key": pest_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PestImageContribution(**self._from_doc(doc)) for doc in cursor]

    def list_for_tenant(self, tenant_key: str) -> list[PestImageContribution]:
        query = """
        FOR c IN @@collection
          FILTER c.tenant_key == @tenant_key
          SORT c.created_at DESC
          RETURN c
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PestImageContribution(**self._from_doc(doc)) for doc in cursor]

    def delete(self, key: str, tenant_key: str) -> bool:
        existing = self.get(key, tenant_key)
        if existing is None:
            return False
        return BaseArangoRepository.delete(self, key)
