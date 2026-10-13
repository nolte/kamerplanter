"""v0091 — every tenant points at a plan (REQ-056 §7.1, AK-16, #2142).

Until #2142 every limit read its own setting and a tenant had no plan. A tenant now
carries ``plan_key`` (never inside the schemaless ``settings``, audit MT-056), and the
quotas it is held to are resolved through that plan (``EntitlementService``). This
version stamps ``plan_key = "standard"`` on every stored tenant that carries none - in
every state, the platform tenant included.

The plan document itself is not written here: the fatal seed job ``plans``
(``app/migrations/seed_plans.py``) creates it from ``plans.yaml`` right after the
migrations, under the same lock, on every boot - ``standard``, every limit ``null`` =
the instance setting, ``is_default: true``. Between the two steps a tenant on a plan
that is not stored yet resolves to exactly those limits anyway (the entitlement
service's fallback for a missing plan is the default plan, then the instance settings).

Because ``standard`` resolves every dimension to the instance setting, no limit an
installation enforces today changes (REQ-056 AK-17): the same code, status and
threshold for every refusal, including any limit an operator set by environment
variable.

**Idempotent (M-3).** A tenant with a ``plan_key`` no longer matches; a second run
changes nothing.

**Dry run (M-5).** Counts the tenants without a plan; writes nothing.

**Not reversible (M-6).** Nothing to undo that matters: an older image ignores the
``plan_key`` attribute and the ``plans`` collection. A ``down`` would only discard the
plan a platform admin may have assigned since.
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

#: The plan every tenant without one gets (``app.domain.models.plan.DEFAULT_PLAN_KEY`` at the time of writing;
#: frozen here so a later rename of the constant does not change what this applied version did).
DEFAULT_PLAN_KEY = "standard"

_COUNT_QUERY = """
FOR doc IN @@collection
  FILTER doc.plan_key == null
  COLLECT WITH COUNT INTO n
  RETURN n
"""

_STAMP_QUERY = """
FOR doc IN @@collection
  FILTER doc.plan_key == null
  UPDATE doc WITH { plan_key: @plan_key } IN @@collection
  COLLECT WITH COUNT INTO n
  RETURN n
"""


class TenantPlanKeyMigration(Migration):
    version = "0091"
    name = "tenant_plan_key"
    description = "Stamp plan_key='standard' on every tenant without one (#2142)."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        tenants = 0
        if db.has_collection(col.TENANTS):
            binds: dict[str, Any] = {"@collection": col.TENANTS}
            if not dry_run:
                binds["plan_key"] = DEFAULT_PLAN_KEY
            cursor = cast(Cursor, db.aql.execute(_COUNT_QUERY if dry_run else _STAMP_QUERY, bind_vars=binds))
            tenants = int(next(iter(cursor), 0))
        logger.info("tenant_plan_key", dry_run=dry_run, tenants=tenants)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=tenants,
            changed=0 if dry_run else tenants,
            dry_run=dry_run,
            details={"tenants_without_plan": tenants},
        )


migration = TenantPlanKeyMigration()
