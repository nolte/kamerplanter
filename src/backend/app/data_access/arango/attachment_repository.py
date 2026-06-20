"""NFR-013 §2.2 — ArangoDB repository for the ``attachments`` collection."""

from datetime import UTC, date, datetime
from typing import Any

from arango.database import StandardDatabase

from app.common.enums import AttachmentCategory
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.attachment_repository import UNSET, IAttachmentRepository, _Unset
from app.domain.models.attachment import Attachment

# REQ-025 §3.1 — value written to ``created_by`` when a user is erased but the
# attachment must stay attached to the tenant record (Scope
# ``user_diary_attachments``). Must match the spec marker exactly (AK-OS-02).
ANONYMIZED_MARKER = "_anonymized"


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

    def update_metadata(
        self,
        key: str,
        tenant_key: str,
        *,
        caption: str | None | _Unset = UNSET,
        taken_on: date | None | _Unset = UNSET,
    ) -> Attachment | None:
        """REQ-034 §2.1 v1.2 — patch ``caption`` / ``taken_on`` (tenant-scoped, AQL).

        True PATCH: only the explicitly-passed fields are written. The patch doc
        is assembled in Python and bound as a single ``@patch`` object so the AQL
        stays fully parametrized (no f-string interpolation) and an explicit
        ``None`` is preserved (it would otherwise be impossible to *clear* a
        field with ArangoDB's default ``mergeObjects``/``keepNull`` semantics).
        """
        patch: dict[str, Any] = {}
        if not isinstance(caption, _Unset):
            patch["caption"] = caption
        if not isinstance(taken_on, _Unset):
            # AQL has no native date type — store the ISO date string, matching
            # how Pydantic serialises ``date`` everywhere else in the catalog.
            patch["taken_on"] = taken_on.isoformat() if isinstance(taken_on, date) else None
        if not patch:
            # Nothing to change — return the current document (tenant-scoped).
            return self.get(key, tenant_key)

        patch["updated_at"] = datetime.now(UTC).isoformat()
        query = """
        FOR att IN @@collection
          FILTER att._key == @key AND att.tenant_key == @tenant_key
          UPDATE att WITH @patch IN @@collection
            OPTIONS { keepNull: true }
          RETURN NEW
        """
        bind_vars = {
            "@collection": self._collection_name,
            "key": key,
            "tenant_key": tenant_key,
            "patch": patch,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        doc = next(cursor, None)
        if doc is None:
            return None
        return Attachment(**self._from_doc(doc))

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

    def anonymize_user_metadata(
        self,
        tenant_key: str,
        user_key: str,
        categories: list[AttachmentCategory] | None = None,
    ) -> int:
        """REQ-025 Phase 0 — set ``created_by = '_anonymized'`` (tenant-scoped, AQL).

        Only touches documents that still carry the user's ``created_by`` (so a
        re-run after a partial failure is idempotent and stays a no-op once
        everything is anonymised). Returns the number of documents updated.
        """
        category_values = [c.value for c in categories] if categories else None
        query = """
        FOR att IN @@collection
          FILTER att.tenant_key == @tenant_key AND att.created_by == @user_key
          FILTER @categories == null OR att.category IN @categories
          UPDATE att WITH { created_by: @marker } IN @@collection
          COLLECT WITH COUNT INTO updated
          RETURN updated
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "user_key": user_key,
            "categories": category_values,
            "marker": ANONYMIZED_MARKER,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return int(next(cursor, 0) or 0)

    def delete_all_for_tenant(self, tenant_key: str) -> int:
        """REQ-024/-025 — delete every attachment metadata document of a tenant."""
        query = """
        FOR att IN @@collection
          FILTER att.tenant_key == @tenant_key
          REMOVE att IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return int(next(cursor, 0) or 0)

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
