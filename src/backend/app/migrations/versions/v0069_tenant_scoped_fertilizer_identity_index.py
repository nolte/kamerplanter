"""v0069 — move the fertilizer identity index from collection-wide to per-tenant (#2000).

The unique index ``fertilizers(product_name, brand)`` was collection-wide. Two
consequences, both cross-tenant:

* The seed loaders matched a seed product over every tenant's rows; a tenant's own
  product with a seed's ``(product_name, brand)`` was found, rewritten from the seed
  model as global and overwritten. The loaders now match global rows only — and with
  the old index a global seed row could not be created beside the tenant's, so the
  product would have been denied to every tenant instead (the cultivar situation of
  #1090).
* A tenant creating a product another tenant holds privately got a ``409``: the
  constraint told it that the other tenant owns such a product, and refused it the
  name.

The key becomes ``(tenant_key, product_name, brand)`` — the decision ``species`` took
in #1162 (``v0041``), and the same shape. The shared catalogue (``tenant_key == ""``)
still holds exactly one row per pair; each tenant holds at most one of its own.

**The old index is dropped, not merely superseded** — left in place it keeps the
stricter constraint in force and the compound index is cosmetic. **Order:** the
compound index is created first (``ensure_collections`` already does so on every boot)
and the legacy one dropped afterwards, so there is no window without a constraint.

**No data moves.** A set unique on ``(product_name, brand)`` is unique on any superset
of those fields, so no row can violate the new index.

Idempotent (M-3): a re-run finds the compound index present and the legacy one gone
and reports ``changed == 0``. Dry-run (M-5) reports the plan and touches no index.
Irreversible (M-6): once a tenant holds a product named like a global one, the
collection-wide index can no longer be created without deleting somebody's product.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.collections import (
    FERTILIZER_IDENTITY_INDEX_FIELDS,
    LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS,
    has_unique_index,
)
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)


class TenantScopedFertilizerIdentityIndexMigration(Migration):
    version = "0069"
    name = "tenant_scoped_fertilizer_identity_index"
    description = (
        "Replace the collection-wide fertilizers(product_name, brand) unique index with "
        "(tenant_key, product_name, brand) (#2000)."
    )
    reversible = False

    @staticmethod
    def _plan(db: StandardDatabase) -> tuple[bool, list[str]]:
        """``(needs_compound, legacy_index_ids)`` — read-only, so dry-run safe."""
        if not db.has_collection(col.FERTILIZERS):
            return False, []
        fertilizers = db.collection(col.FERTILIZERS)
        legacy_ids = [
            str(idx["id"])
            for idx in fertilizers.indexes()
            if isinstance(idx, dict)
            and idx.get("type") == "persistent"
            and idx.get("fields") == LEGACY_GLOBAL_FERTILIZER_INDEX_FIELDS
            and "id" in idx
        ]
        has_compound = has_unique_index(fertilizers, FERTILIZER_IDENTITY_INDEX_FIELDS)
        return not has_compound, legacy_ids

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        needs_compound, legacy_ids = self._plan(db)
        changed = int(needs_compound) + len(legacy_ids)

        if not dry_run and changed:
            fertilizers = db.collection(col.FERTILIZERS)
            if needs_compound:
                # First the replacement constraint; dropping the old one before it
                # exists would leave a window with no uniqueness at all.
                fertilizers.add_persistent_index(fields=FERTILIZER_IDENTITY_INDEX_FIELDS, unique=True)
            for index_id in legacy_ids:
                fertilizers.delete_index(index_id, ignore_missing=True)

        logger.info(
            "tenant_scoped_fertilizer_identity_index",
            compound_created=needs_compound,
            legacy_dropped=len(legacy_ids),
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=changed,
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            details={"compound_created": needs_compound, "legacy_dropped": len(legacy_ids)},
        )


migration = TenantScopedFertilizerIdentityIndexMigration()
