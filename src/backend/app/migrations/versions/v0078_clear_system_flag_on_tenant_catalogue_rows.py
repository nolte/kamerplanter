"""v0078 — clear ``is_system`` on tenant-owned activities and workflow templates (#2027 follow-up).

``is_system`` marks a row the seed ships, and a seed row is global
(``tenant_key == ""``). A row carrying a tenant's key is that tenant's, yet some
carry the flag:

* ``POST /api/v1/t/{slug}/tasks/workflows`` accepted ``is_system`` until the
  #2027 review removed it from ``WorkflowTemplateCreate``;
* ``v0004`` stamped the then-global seed workflow templates with a default tenant,
  and ``v0066`` resets only the stamps it can prove — a seed since renamed or
  dropped from the YAML keeps its stamp and its flag.

No code path writes a tenant-owned activity (the catalogue routes are
platform-admin only and write global rows), so a flagged one is legacy or
hand-written data; it is cleared by the same rule.

On such a row the flag locks the owner out of its own data (every write path
refuses an ``is_system`` row) and, until the same change, kept the row through the
tenant erasure. ``ArangoActivityRepository.get_system_activities`` reads
``is_system`` without a tenant filter, so a flagged tenant activity was also listed
to every other tenant.

This migration sets ``is_system`` to ``false`` on every row of ``activities`` and
``workflow_templates`` whose ``tenant_key`` is non-empty. The ``tenant_key`` itself is
not touched: the row stays the tenant's — turning it global would hand a tenant's
data to everyone, and the stamp of a renamed seed is not provable as a stamp
(see ``v0066``). Global rows (``tenant_key`` empty or absent) keep their flag.

**Idempotent (M-3).** A cleared row no longer matches; a second run changes nothing.

**Dry run (M-5).** Counts the rows per collection and writes nothing.

**Not reversible (M-6).** Which rows carried the flag is not recorded, and the
flag on a tenant's row is the defect being repaired.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: The two hybrid catalogues whose rows carry ``is_system`` next to a ``tenant_key``.
COLLECTIONS: tuple[str, ...] = (col.ACTIVITIES, col.WORKFLOW_TEMPLATES)

#: A tenant-owned row (non-empty ``tenant_key``) that still carries the seed flag.
_TENANT_ROW_WITH_FLAG = "FILTER doc.tenant_key != null AND doc.tenant_key != '' AND doc.is_system == true"

_COUNT_QUERY = f"FOR doc IN @@collection {_TENANT_ROW_WITH_FLAG} COLLECT WITH COUNT INTO n RETURN n"
_CLEAR_QUERY = (
    f"FOR doc IN @@collection {_TENANT_ROW_WITH_FLAG} "
    "UPDATE doc WITH {is_system: false} IN @@collection "
    "COLLECT WITH COUNT INTO n RETURN n"
)


class ClearSystemFlagOnTenantCatalogueRowsMigration(Migration):
    version = "0078"
    name = "clear_system_flag_on_tenant_catalogue_rows"
    description = (
        "Set is_system to false on activities and workflow_templates rows that carry a non-empty "
        "tenant_key; only a global seed row is a system row (#2027 follow-up)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        per_collection: dict[str, int] = {}
        for collection in COLLECTIONS:
            if not db.has_collection(collection):
                continue
            query = _COUNT_QUERY if dry_run else _CLEAR_QUERY
            per_collection[collection] = next(iter(db.aql.execute(query, bind_vars={"@collection": collection})), 0)

        total = sum(per_collection.values())
        logger.info("clear_system_flag_on_tenant_catalogue_rows", dry_run=dry_run, rows=total, **per_collection)
        details: dict[str, Any] = dict(per_collection)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=total,
            changed=0 if dry_run else total,
            dry_run=dry_run,
            details=details,
        )


migration = ClearSystemFlagOnTenantCatalogueRowsMigration()
