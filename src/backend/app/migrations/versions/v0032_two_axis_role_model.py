"""v0032 — migrate memberships to the REQ-049 two-axis role model.

``TenantRole.ADMIN`` was retired. It had come to mean two unrelated things —
"may delete domain records" and "administers the tenant" — and in roughly 30 of
45 permission-table rows it was only ever the former. REQ-049 splits that into a
ranked domain role (viewer / grower / **lead**) and additive administrative
scopes (``management``, ``technical``).

The mapping is lossless and rights-preserving:

| stored | becomes |
|---|---|
| ``role: "admin"`` | ``role: "lead"``, ``admin_scopes: ["management", "technical"]`` |
| ``role: "grower"`` | ``role: "grower"``, ``admin_scopes: []`` |
| ``role: "viewer"`` | ``role: "viewer"``, ``admin_scopes: []`` |

An ``admin`` could do everything a ``lead`` with both scopes can do, and nothing
more — so nobody gains or loses access at the moment this runs. The deliberate
behaviour change REQ-049 §6 announces (a grower can no longer delete) lives in
the enforcement layer, not here: this migration only moves the stored values so
the code that reads them can stop meaning two things at once.

**The ``platform`` tenant is migrated like every other.** Its membership is what
marks a platform admin (REQ-049 §2.5), and ``is_platform_admin`` moved to
``lead`` with it. Excluding it here would leave the installation with no
platform admin at all — the failure would surface as an inexplicable ``403`` on
the admin panel rather than as a migration error.

Three ordered jobs, all idempotent:

1. **Rename the domain role.** Every membership with ``role == "admin"`` becomes
   ``"lead"``. Values already migrated, and the two roles that keep their name,
   are not touched.
2. **Backfill ``admin_scopes``.** Memberships that lack the attribute get one:
   both scopes for those that were ``admin`` (matched *before* job 1 renames
   them, so the two jobs run as a single AQL pass per document), an empty list
   otherwise. A membership that already carries the attribute is left alone —
   re-running must not restore scopes an operator has since removed.
3. **Add the INV-1 index.** A non-unique persistent index on
   ``["tenant_key", "admin_scopes[*]"]`` so counting a tenant's remaining
   ``management`` holders — which every member removal does — is not a full
   collection scan. Bootstrap creates the same index on a fresh database; this
   job exists for volumes that predate it.

Idempotent (M-3): a re-run finds no ``admin`` role left, no membership without
``admin_scopes``, and the index already present → ``changed == 0``.
Dry-run (M-5): all three jobs are previewed and nothing is written.
Irreversible (M-6): the ``admin`` value it replaces no longer exists in
:class:`~app.common.enums.TenantRole`, so a down-migration could not write a
value the application can read back. The inverse is a fresh migration, not a
rollback.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: The retired value this migration replaces. Spelled literally rather than via
#: ``TenantRole`` — the enum member is gone, which is the whole point.
_RETIRED_ROLE = "admin"
_REPLACEMENT_ROLE = "lead"

#: Scopes an ex-``admin`` receives. Together they are exactly what that value
#: used to convey, which is what makes the mapping rights-preserving.
_FULL_SCOPES = ["management", "technical"]

#: Index that makes the INV-1 guard cheap.
_INDEX_FIELDS: list[str] = ["tenant_key", "admin_scopes[*]"]


class TwoAxisRoleModelMigration(Migration):
    version = "0032"
    name = "two_axis_role_model"
    description = (
        "Map the retired membership role 'admin' onto REQ-049's two axes: role 'lead' plus "
        "both administrative scopes, backfill admin_scopes on every other membership, and "
        "index the scopes so the last-manager guard does not scan the collection."
    )
    reversible = False

    # ── read helpers (no-op-safe on a fresh/empty database) ───────────────────

    def _count_retired_role(self, db: StandardDatabase) -> int:
        if not db.has_collection(col.MEMBERSHIPS):
            return 0
        cursor = db.aql.execute(
            "FOR doc IN @@collection FILTER doc.role == @role COLLECT WITH COUNT INTO cnt RETURN cnt",
            bind_vars={"@collection": col.MEMBERSHIPS, "role": _RETIRED_ROLE},
        )
        return int(next(cursor, 0))

    def _count_missing_scopes(self, db: StandardDatabase) -> int:
        if not db.has_collection(col.MEMBERSHIPS):
            return 0
        cursor = db.aql.execute(
            "FOR doc IN @@collection FILTER doc.admin_scopes == null COLLECT WITH COUNT INTO cnt RETURN cnt",
            bind_vars={"@collection": col.MEMBERSHIPS},
        )
        return int(next(cursor, 0))

    def _has_scope_index(self, db: StandardDatabase) -> bool:
        if not db.has_collection(col.MEMBERSHIPS):
            return False
        return any(
            isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == _INDEX_FIELDS
            for idx in db.collection(col.MEMBERSHIPS).indexes()
        )

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        retired = self._count_retired_role(db)
        missing_scopes = self._count_missing_scopes(db)
        index_present = self._has_scope_index(db)
        scanned = retired + missing_scopes

        if dry_run:
            details: dict[str, Any] = {
                "memberships_with_retired_admin_role": retired,
                "memberships_without_admin_scopes": missing_scopes,
                "scope_index_already_present": index_present,
                "will_create_scope_index": not index_present,
            }
            logger.info("two_axis_role_model_dry_run", scanned=scanned, details=details)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=True,
                details=details,
            )

        changed = 0

        if db.has_collection(col.MEMBERSHIPS):
            # Jobs 1 + 2 in one pass: the scope backfill has to see the *old*
            # role value to know whether the membership was an admin, so
            # renaming first would lose that information.
            cursor = db.aql.execute(
                """
                FOR doc IN @@collection
                  LET was_admin = doc.role == @retired
                  LET needs_role = was_admin
                  LET needs_scopes = doc.admin_scopes == null
                  FILTER needs_role OR needs_scopes
                  UPDATE doc WITH {
                    role: needs_role ? @replacement : doc.role,
                    admin_scopes: needs_scopes ? (was_admin ? @full_scopes : []) : doc.admin_scopes
                  } IN @@collection
                  COLLECT WITH COUNT INTO cnt
                  RETURN cnt
                """,
                bind_vars={
                    "@collection": col.MEMBERSHIPS,
                    "retired": _RETIRED_ROLE,
                    "replacement": _REPLACEMENT_ROLE,
                    "full_scopes": _FULL_SCOPES,
                },
            )
            changed += int(next(cursor, 0))

            # Job 3: the index the INV-1 guard leans on.
            if not index_present:
                db.collection(col.MEMBERSHIPS).add_persistent_index(fields=_INDEX_FIELDS, unique=False)
                changed += 1

        details = {
            "memberships_with_retired_admin_role": retired,
            "memberships_without_admin_scopes": missing_scopes,
            "scope_index_created": not index_present,
        }
        logger.info("two_axis_role_model_applied", scanned=scanned, changed=changed, details=details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=False,
            details=details,
        )


migration = TwoAxisRoleModelMigration()
