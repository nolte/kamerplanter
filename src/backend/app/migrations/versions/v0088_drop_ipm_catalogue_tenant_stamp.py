"""v0088 — remove the v0004 default-tenant stamp from the IPM catalogues (MT-052, #2144).

Migration ``v0004`` (``backfill_tenant_key.py``) listed ``pests``, ``diseases`` and
``treatments`` among its *top-level* collections and stamped every row with an
empty ``tenant_key`` with the key of one default tenant — on a volume that held
IPM seed rows then, every one of them. The repairs that followed (``v0036``/``v0038``
species and cultivars, ``v0066`` four catalogues, ``v0070`` harvest indicators) never
covered these three.

Why removing the attribute is safe — and the whole of it
--------------------------------------------------------
Unlike the hybrid catalogues ``v0066`` repairs, the three IPM models declare **no**
``tenant_key`` at all (``Pest``, ``Disease``, ``Treatment``): no application path can
write one, so no row can be a tenant's own, and every stored value — the stamp or an
empty string — is a leftover. Nothing reads it today: the models drop it on load and
the tenant erasure exempts the three collections (``NOT_TENANT_SCOPED``) precisely
*because* a stamp there is not ownership. What the stamp still is: a tenant key on a
global row, which the next reader written against ``doc.tenant_key`` (an export, an
ownership predicate, a deletion by tenant) would take for ownership. The attribute
goes, as ``v0087`` did for locations and slots.

**Idempotent (M-3).** A row without the attribute is not touched; a second run
changes nothing.

**Dry run (M-5).** Counts the rows that carry the attribute, and how many of those
carry a non-empty stamp, per collection; writes nothing.

**Not reversible (M-6).** The default tenant's key is not ownership and nobody wants
it back; the empty string carries no information.
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

#: The field the three models never declared.
_FIELD = "tenant_key"

#: The IPM catalogues ``v0004`` stamped and no later migration repaired.
_COLLECTIONS: tuple[str, ...] = (col.PESTS, col.DISEASES, col.TREATMENTS)

_SCAN_QUERY = """
FOR d IN @@collection
  FILTER HAS(d, @field)
  COLLECT AGGREGATE carrying = COUNT(1), stamped = SUM(d[@field] != null AND d[@field] != "" ? 1 : 0)
  RETURN {carrying, stamped}
"""

_STRIP_QUERY = """
FOR d IN @@collection
  FILTER HAS(d, @field)
  REPLACE d WITH UNSET(d, @field) IN @@collection
"""


class DropIpmCatalogueTenantStampMigration(Migration):
    version = "0088"
    name = "drop_ipm_catalogue_tenant_stamp"
    description = (
        "Remove the v0004 default-tenant stamp (and any empty tenant_key) from pests, diseases and treatments; "
        "their models carry no tenant (MT-052, #2144)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        details: dict[str, int] = {}
        total = 0
        for name in _COLLECTIONS:
            if not db.has_collection(name):
                details[f"{name}_with_tenant_key"] = 0
                details[f"{name}_stamped"] = 0
                continue
            bind_vars: dict[str, Any] = {"@collection": name, "field": _FIELD}
            rows = list(cast(Cursor, db.aql.execute(_SCAN_QUERY, bind_vars=bind_vars)))
            carrying = int(rows[0]["carrying"]) if rows else 0
            stamped = int(rows[0]["stamped"] or 0) if rows else 0
            details[f"{name}_with_tenant_key"] = carrying
            details[f"{name}_stamped"] = stamped
            total += carrying
            if carrying and not dry_run:
                db.aql.execute(_STRIP_QUERY, bind_vars=bind_vars)
        logger.info("drop_ipm_catalogue_tenant_stamp", rows=total, dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=total,
            changed=0 if dry_run else total,
            dry_run=dry_run,
            details=details,
        )


migration = DropIpmCatalogueTenantStampMigration()
