"""v0041 — move the species dedup key from global to per-tenant (#1162).

``v0026`` promoted a **global** unique index on ``scientific_name_normalized``:
one row per taxon across the whole installation. That made a tenant's create run
silently onto another tenant's private row — the UPSERT matched, returned the
foreign document, and reported success for a species the caller can never see.

The key becomes ``(tenant_key, scientific_name_normalized)``. A tenant may hold
its own row for a taxon another tenant also holds; the system context
(``tenant_key == ""``) still yields exactly one row per taxon in the shared
catalogue, which is what REQ-048 Stufe 1 was really protecting.

**The old index must be dropped, not merely superseded.** Leaving it in place
would keep the *stricter* global constraint active and make the compound index
cosmetic — the change would look applied and behave exactly as before. That is the
one failure this migration exists to avoid, and it is why the drop is the step
that decides success rather than an afterthought.

**Order matters.** The compound index is created *first* and the legacy one
dropped only afterwards. The reverse order would leave a window with no
uniqueness constraint at all, and a concurrent create in that window could insert
the very duplicate both indexes exist to prevent.

**No data moves.** A globally-unique set is by construction unique per tenant too,
so no row can violate the new index and nothing needs de-duplicating. That is why
this migration only touches indexes — the asymmetry is worth stating, because the
reverse change (per-tenant → global) could not be written this way.

Idempotent (M-3): a re-run finds the compound index present and the legacy one
gone, and reports ``changed == 0``.

Irreversible (M-6) in practice: rows created under the per-tenant key may collide
under the global one, so going back would require deleting somebody's species.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.collections import (
    LEGACY_GLOBAL_NAME_INDEX_FIELDS,
    SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS,
)
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)


class TenantScopedSpeciesDedupIndexMigration(Migration):
    version = "0041"
    name = "tenant_scoped_species_dedup_index"
    description = "Replace the global species dedup index with (tenant_key, scientific_name_normalized) (#1162)."
    reversible = False

    def _indexes(self, db: StandardDatabase) -> list[dict[str, Any]]:
        if not db.has_collection(col.SPECIES):
            return []
        return [idx for idx in db.collection(col.SPECIES).indexes() if isinstance(idx, dict)]

    def _plan(self, db: StandardDatabase) -> tuple[bool, list[str]]:
        """Return ``(needs_compound, legacy_index_ids)``.

        Pure and dry-run-safe. A missing collection yields "nothing to do" rather
        than an error, so a fresh install boots.
        """
        indexes = self._indexes(db)
        has_compound = any(
            idx.get("type") == "persistent"
            and idx.get("fields") == SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS
            and idx.get("unique")
            for idx in indexes
        )
        legacy_ids = [
            str(idx["id"])
            for idx in indexes
            if idx.get("type") == "persistent" and idx.get("fields") == LEGACY_GLOBAL_NAME_INDEX_FIELDS and "id" in idx
        ]
        needs_compound = db.has_collection(col.SPECIES) and not has_compound
        return needs_compound, legacy_ids

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        needs_compound, legacy_ids = self._plan(db)
        changed = int(needs_compound) + len(legacy_ids)

        if not dry_run and db.has_collection(col.SPECIES):
            species = db.collection(col.SPECIES)
            if needs_compound:
                # First: the replacement constraint. Dropping the old one before
                # this exists would open a window with no uniqueness at all.
                species.add_persistent_index(fields=SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS, unique=True)
            for index_id in legacy_ids:
                # Then: retire the global one. Without this the old, stricter
                # constraint stays in force and the whole change is inert.
                species.delete_index(index_id, ignore_missing=True)

        logger.info(
            "tenant_scoped_species_dedup_index",
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


#: Module-level instance the discovery loader binds (framework contract).
migration = TenantScopedSpeciesDedupIndexMigration()
