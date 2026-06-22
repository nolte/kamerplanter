"""REQ-010 — ArangoDB repository for ``pest_image_contributions``.

All queries are tenant-scoped and fully parametrized (``bind_vars`` only, no
f-string interpolation) so a tenant can never read or delete another tenant's
contributed pest images.
"""

from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.common.enums import PestImageStatus
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

    def get_by_key(self, key: str) -> PestImageContribution | None:  # type: ignore[override]
        """Resolve a contribution irrespective of tenant (moderation / global content)."""
        doc = BaseArangoRepository.get_by_key(self, key)
        if doc is None:
            return None
        return PestImageContribution(**doc)

    def list_for_pest(
        self, tenant_key: str, pest_key: str, *, include_inactive: bool = False
    ) -> list[PestImageContribution]:
        # ``is_active != false`` keeps legacy documents (no field) visible by
        # treating a missing flag as active. Only an explicit ``false`` hides a
        # deselected image from the default gallery.
        query = """
        FOR c IN @@collection
          FILTER c.tenant_key == @tenant_key AND c.pest_key == @pest_key
          FILTER @include_inactive OR c.is_active != false
          SORT c.created_at DESC
          RETURN c
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "pest_key": pest_key,
            "include_inactive": include_inactive,
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

    def list_for_user(self, user_key: str) -> list[PestImageContribution]:
        query = """
        FOR c IN @@collection
          FILTER c.contributed_by == @user_key
          SORT c.created_at DESC
          RETURN c
        """
        bind_vars = {
            "@collection": self._collection_name,
            "user_key": user_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PestImageContribution(**self._from_doc(doc)) for doc in cursor]

    def list_all_for_pest(self, pest_key: str) -> list[PestImageContribution]:
        query = """
        FOR c IN @@collection
          FILTER c.pest_key == @pest_key
          SORT c.created_at DESC
          RETURN c
        """
        bind_vars = {
            "@collection": self._collection_name,
            "pest_key": pest_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PestImageContribution(**self._from_doc(doc)) for doc in cursor]

    def list_promoted_for_pest(self, pest_key: str, *, include_inactive: bool = False) -> list[PestImageContribution]:
        query = """
        FOR c IN @@collection
          FILTER c.pest_key == @pest_key AND c.status == @status
          FILTER @include_inactive OR c.is_active != false
          SORT c.created_at DESC
          RETURN c
        """
        bind_vars = {
            "@collection": self._collection_name,
            "pest_key": pest_key,
            "status": PestImageStatus.PROMOTED.value,
            "include_inactive": include_inactive,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PestImageContribution(**self._from_doc(doc)) for doc in cursor]

    def set_status(self, key: str, status: PestImageStatus, promoted_by: str | None) -> PestImageContribution | None:
        existing = self.get_by_key(key)
        if existing is None:
            return None
        if status == PestImageStatus.PROMOTED:
            promoted_at: datetime | None = datetime.now(UTC)
        else:
            promoted_at = None
            promoted_by = None
        updated = existing.model_copy(update={"status": status, "promoted_at": promoted_at, "promoted_by": promoted_by})
        doc = BaseArangoRepository.update(self, key, updated)
        return PestImageContribution(**doc)

    def set_active(self, key: str, is_active: bool) -> PestImageContribution | None:
        existing = self.get_by_key(key)
        if existing is None:
            return None
        updated = existing.model_copy(update={"is_active": is_active})
        doc = BaseArangoRepository.update(self, key, updated)
        return PestImageContribution(**doc)

    def delete(self, key: str, tenant_key: str) -> bool:
        existing = self.get(key, tenant_key)
        if existing is None:
            return False
        return BaseArangoRepository.delete(self, key)

    def delete_for_tenant(self, tenant_key: str) -> int:
        query = """
        FOR c IN @@collection
          FILTER c.tenant_key == @tenant_key
          REMOVE c IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        result = list(cursor)
        return int(result[0]) if result else 0
