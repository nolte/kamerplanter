"""NFR-013 §2.2 — ArangoDB repository for the ``attachments`` collection."""

from arango.database import StandardDatabase

from app.common.enums import AttachmentCategory
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.attachment_repository import IAttachmentRepository
from app.domain.models.attachment import Attachment


class ArangoAttachmentRepository(IAttachmentRepository, BaseArangoRepository):
    """ArangoDB-backed repository for ``attachments``."""

    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.ATTACHMENTS)

    def create(self, attachment: Attachment) -> Attachment:
        doc = BaseArangoRepository.create(self, attachment)
        return Attachment(**doc)

    def get(self, key: str, tenant_key: str) -> Attachment | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        if doc is None or doc.get("tenant_key") != tenant_key:
            return None
        return Attachment(**doc)

    def delete(self, key: str, tenant_key: str) -> bool:
        existing = self.get(key, tenant_key)
        if existing is None:
            return False
        return BaseArangoRepository.delete(self, key)

    def find_by_user(
        self,
        tenant_key: str,
        user_key: str,
        categories: list[AttachmentCategory] | None = None,
    ) -> list[Attachment]:
        category_values = [c.value for c in categories] if categories else None
        query = """
        FOR att IN @@collection
          FILTER att.tenant_key == @tenant_key AND att.created_by == @user_key
          FILTER @categories == null OR att.category IN @categories
          SORT att.created_at DESC
          RETURN att
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "user_key": user_key,
            "categories": category_values,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Attachment(**self._from_doc(doc)) for doc in cursor]

    def find_by_sha256(self, tenant_key: str, sha256: str) -> Attachment | None:
        query = """
        FOR att IN @@collection
          FILTER att.tenant_key == @tenant_key AND att.sha256 == @sha256
          LIMIT 1
          RETURN att
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "sha256": sha256,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        doc = next(cursor, None)
        if doc is None:
            return None
        return Attachment(**self._from_doc(doc))

    def count_by_tenant(self, tenant_key: str) -> int:
        query = """
        RETURN LENGTH(
          FOR att IN @@collection
            FILTER att.tenant_key == @tenant_key
            RETURN 1
        )
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return next(cursor, 0)

    def sum_bytes_by_tenant(self, tenant_key: str) -> int:
        query = """
        RETURN SUM(
          FOR att IN @@collection
            FILTER att.tenant_key == @tenant_key
            RETURN att.byte_size
        )
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return int(next(cursor, 0) or 0)

    def list_by_tenant(
        self,
        tenant_key: str,
        category: AttachmentCategory | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Attachment], int]:
        category_value = category.value if category else None
        query = """
        FOR att IN @@collection
          FILTER att.tenant_key == @tenant_key
          FILTER @category == null OR att.category == @category
          SORT att.created_at DESC
          LIMIT @offset, @limit
          RETURN att
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "category": category_value,
            "offset": offset,
            "limit": limit,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [Attachment(**self._from_doc(doc)) for doc in cursor]

        count_query = """
        RETURN LENGTH(
          FOR att IN @@collection
            FILTER att.tenant_key == @tenant_key
            FILTER @category == null OR att.category == @category
            RETURN 1
        )
        """
        count_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "category": category_value,
        }
        count_cursor = self._db.aql.execute(count_query, bind_vars=count_vars)
        total = int(next(count_cursor, 0) or 0)
        return items, total
