"""v0087 — drop the never-written ``tenant_key`` from every location and slot (#2107, MT-010).

``Location.tenant_key`` and ``Slot.tenant_key`` were declared with a default of
``""`` and never written by any path, so every stored location and slot carries
``tenant_key: ""`` (and rows from a pre-v0004 volume the site's key, stamped once
by ``backfill_tenant_key``). ``""`` is the hybrid-catalogue marker for *global*;
a field that reads as global on a tenant's row is the hazard #706 and #1397 ran
into. The models no longer declare the field — the site is the only owner in the
chain (``location_ownership``) — and this migration removes the stored value so no
reader can rediscover it.

**Idempotent (M-3).** A row without the attribute is not touched; a second run
changes nothing.

**Dry run (M-5).** Counts the affected rows per collection and writes nothing.

**Not reversible (M-6).** Nothing reads the value; an empty string carries no
information, and the v0004 stamps are the site's key, recoverable from
``site_key`` (locations) and ``location_key`` (slots).
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: The field the two models no longer declare.
_FIELD = "tenant_key"

#: The collections whose model lost it.
_COLLECTIONS: tuple[str, ...] = (col.LOCATIONS, col.SLOTS)

_SCAN_QUERY = """
FOR d IN @@collection
  FILTER HAS(d, @field)
  RETURN d._key
"""

_STRIP_QUERY = """
FOR d IN @@collection
  FILTER HAS(d, @field)
  REPLACE d WITH UNSET(d, @field) IN @@collection
"""


class DropLocationSlotTenantKeyMigration(Migration):
    version = "0087"
    name = "drop_location_slot_tenant_key"
    description = (
        "Remove the never-written tenant_key attribute from every location and slot; their tenant is their "
        "site's (#2107, MT-010)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        per_collection: dict[str, int] = {}
        for name in _COLLECTIONS:
            if not db.has_collection(name):
                per_collection[name] = 0
                continue
            bind_vars: dict[str, Any] = {"@collection": name, "field": _FIELD}
            affected = list(cast(Cursor, db.aql.execute(_SCAN_QUERY, bind_vars=bind_vars)))
            per_collection[name] = len(affected)
            if affected and not dry_run:
                db.aql.execute(_STRIP_QUERY, bind_vars=bind_vars)
        total = sum(per_collection.values())
        logger.info("drop_location_slot_tenant_key", rows=total, dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=total,
            changed=0 if dry_run else total,
            dry_run=dry_run,
            details={f"{name}_with_tenant_key": count for name, count in per_collection.items()},
        )


migration = DropLocationSlotTenantKeyMigration()
