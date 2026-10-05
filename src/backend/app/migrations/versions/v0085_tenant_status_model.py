"""v0085 — a tenant's ``is_active`` bool becomes the ``status`` lifecycle state (#2123, MT-027).

REQ-024 AK-65 / AK-52: a tenant is ``active | suspended | pending_deletion |
orphaned | deleted``. ``Tenant.is_active`` is no longer stored — it is derived
from ``status`` (only ``active`` resolves, #2105) — so every stored tenant needs
the state its old flag meant:

* ``is_active == false`` → ``suspended`` (the platform admin's switch, AK-56);
* a tenant whose deletion is already open (a ``tenant_erasure_records`` row
  that is not ``completed``) → ``deleted``: it was accepted under the immediate
  contract of #1792, its memberships are frozen and a run holds or retries it —
  there is nothing left to cancel;
* everything else → ``active`` (a missing flag always counted as active).

The ``is_active`` field is removed from every tenant document in the same
statement, so no reader can mistake a stale flag for the state.

**Idempotent (M-3).** A document that carries ``status`` and no ``is_active``
no longer matches; a second run changes nothing.

**Dry run (M-5).** Counts the documents per target state and writes nothing.

**Not reversible (M-6).** ``pending_deletion`` / ``orphaned`` have no bool to go
back to, and writing ``is_active: true`` for them would hand a tenant whose
deletion is scheduled back to its members. A rollback of the application keeps
the documents readable (the old model defaults a missing ``is_active`` to
``true``) — which is exactly that hand-back, so roll back only with no tenant in
a non-active state (the dry run's ``details`` say how many there are).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, cast

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: The retired field (``Tenant.is_active`` until #2123), bound into every query as ``@retired``.
RETIRED_FIELD = "is_active"

#: A tenant still to migrate: no state yet, or the retired flag still stored.
_MATCH = "FILTER doc.status == null OR HAS(doc, @retired)"

#: The state each document gets; the open-erasure lookup only when the records collection exists.
_TARGET = """
LET open_erasure = @has_records AND LENGTH(
  FOR r IN @@records FILTER r._key == CONCAT('ter_', doc._key) AND r.status != 'completed' LIMIT 1 RETURN 1
) > 0
LET target = doc.status != null ? doc.status : (
  open_erasure ? 'deleted' : (doc[@retired] == false ? 'suspended' : 'active')
)
"""

_COUNT_QUERY = f"""
FOR doc IN @@collection
  {_MATCH}
  {_TARGET}
  COLLECT state = target WITH COUNT INTO n
  RETURN {{state, n}}
"""

_MIGRATE_QUERY = f"""
FOR doc IN @@collection
  {_MATCH}
  {_TARGET}
  REPLACE doc WITH MERGE(UNSET(doc, @retired), {{status: target}}) IN @@collection
  COLLECT state = target WITH COUNT INTO n
  RETURN {{state, n}}
"""


class TenantStatusModelMigration(Migration):
    version = "0085"
    name = "tenant_status_model"
    description = (
        "Replace the tenant is_active bool by the status lifecycle state "
        "(active | suspended | pending_deletion | orphaned | deleted) and drop is_active (#2123)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.TENANTS):
            return MigrationReport(version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run)
        has_records = db.has_collection(col.TENANT_ERASURE_RECORDS)
        binds: dict[str, Any] = {
            "@collection": col.TENANTS,
            # The bind is required by the query text; an absent collection is never read (``has_records``).
            "@records": col.TENANT_ERASURE_RECORDS if has_records else col.TENANTS,
            "has_records": has_records,
            "retired": RETIRED_FIELD,
        }
        cursor = db.aql.execute(_COUNT_QUERY if dry_run else _MIGRATE_QUERY, bind_vars=binds)
        by_state = {row["state"]: row["n"] for row in cast(Iterable[dict[str, Any]], cursor)}
        rows = sum(by_state.values())
        logger.info("tenant_status_model", dry_run=dry_run, tenants=rows, **by_state)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=rows,
            changed=0 if dry_run else rows,
            dry_run=dry_run,
            details={f"tenants_{state}": n for state, n in sorted(by_state.items())},
        )


migration = TenantStatusModelMigration()
