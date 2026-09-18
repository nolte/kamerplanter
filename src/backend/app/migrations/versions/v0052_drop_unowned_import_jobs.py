"""v0052 — delete import jobs that belong to no tenant (#1501, review SCR-001).

``ImportJob`` has carried ``tenant_key`` since it was written and **nothing ever
set it**: the router called ``ImportService.upload`` without ``uploaded_by`` and
there was no ``tenant_key`` parameter at all, so every staged job in this
collection was stamped ``""``. That inertness is why ``GET /import/jobs``,
``GET /import/jobs/{key}`` and ``DELETE /import/jobs/{key}`` had nothing to scope
by and were readable and destroyable by any authenticated member of any tenant.

#1501 makes the stamp real. This migration deals with what the stamp cannot fix
retroactively: the rows written before it.

**Why delete rather than backfill.** There is nothing to backfill *from*.
``uploaded_by`` was empty on exactly the same rows and for exactly the same
reason, so no stored field names the tenant — or even the user — a job belonged
to. Guessing one would attribute another tenant's uploaded CSV to whoever guessed
best, which is the failure this whole issue is about, committed deliberately.

**Why the rows are unreachable anyway, so deleting loses nothing.** After #1501:

* ``ImportService.get_job`` refuses an empty ``tenant_key`` outright — it is a
  caller with no resolvable tenant, not a wildcard — so ``""`` matches no caller's
  scope, including the empty one;
* ``list_jobs`` short-circuits an empty context to an empty page and the
  repository's ``is_tenant_scoped`` guard refuses an unbound list besides;
* ``POST /import/upload`` now requires ``require_active_tenant_role(GROWER)``, and
  a caller with no resolvable tenant arrives as the fail-safe ``VIEWER``, so **no
  new job can be stamped ``""``** and this collection cannot regrow the class.

A row that no caller can address, that no future write can recreate, and whose
only content is a parsed CSV awaiting a confirmation nobody can give, is not data
— it is residue holding personal data (`preview_rows` is the uploaded file's
content, NFR-011 / REQ-025). Deleting it is the answer retention gives anyway.

**Not reversible (M-6).** The documents are gone and there is no owner to restore
them to; a ``down`` that re-created them without a ``tenant_key`` would recreate
the defect. It declares ``reversible = False`` rather than faking an inverse.

**Idempotent (M-3).** A re-run finds no matching document and reports
``changed == 0``, and — per the paragraph above — nothing can create a new match.

**Measured before writing.** Against the kind installation on 2026-09-18:
``RETURN LENGTH(import_jobs)`` → ``0``, so this migration is a no-op *there*. It
exists for installations that have staged an import: the count is a property of
the deployment, not of the schema, and a migration that only runs where the
developer happened to have data is the "inert guard" shape twice over.

**On the version number.** This module was written as ``0051`` and renumbered to
``0052`` when #1523 (``v0051_rename_cec_key``) landed on ``develop`` first — the
collision ``app/migrations/README.md`` describes, resolved the way it prescribes:
whoever lands second rebases and renames *before* the merge, all four things at
once (module file, ``version`` string, unit-test module and its imports; this
migration has no integration test to rename). Safe because it has been applied
nowhere: M-7 pins an *applied* migration to its number and its checksum, and a
renumbering after that would be the thing M-7 forbids.

``discovery.validate_sequence`` enforces gapless numbering from ``0001`` (M-1) and
that check sits on the application's startup path, so a number cannot be reserved
ahead of a branch that has not landed — which is why the collision is resolved
after the fact rather than avoided in advance. #1505 takes ``0053`` behind this
one. v0047 and v0049 both record the same collision and the same resolution.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)


class DropUnownedImportJobsMigration(Migration):
    version = "0052"
    name = "drop_unowned_import_jobs"
    description = "Delete staged import jobs that carry no tenant_key (#1501)."
    reversible = False

    #: ``(j.tenant_key || "") == ""`` rather than ``j.tenant_key == ""``, so a
    #: document written before the field existed — which has no such attribute at
    #: all rather than an empty one — is matched too. Both spell the same thing:
    #: this job belongs to nobody.
    _SCAN_QUERY = f"""
    FOR j IN {col.IMPORT_JOBS}
      FILTER (j.tenant_key || "") == ""
      RETURN j._key
    """

    _TOTAL_QUERY = f"RETURN LENGTH({col.IMPORT_JOBS})"

    def _plan(self, db: StandardDatabase) -> tuple[int, list[str]]:
        """Return ``(scanned, keys to delete)`` without writing.

        Pure, so ``dry_run`` reports the numbers the real run would produce (M-5).
        A dry run that took its own path would describe a plan nobody executes.
        """
        if not db.has_collection(col.IMPORT_JOBS):
            return (0, [])
        scanned = int(next(iter(db.aql.execute(self._TOTAL_QUERY)), 0))
        keys = [str(k) for k in db.aql.execute(self._SCAN_QUERY)]
        return (scanned, keys)

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        scanned, keys = self._plan(db)

        if not dry_run and keys:
            jobs = db.collection(col.IMPORT_JOBS)
            for key in keys:
                # ``ignore_missing`` so a concurrent delete (a lead clearing their
                # own list while this runs) is not an error: the desired end state
                # is "the document is gone", and it is.
                jobs.delete({"_key": key}, ignore_missing=True)

        logger.info(
            "drop_unowned_import_jobs",
            scanned=scanned,
            unowned=len(keys),
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else len(keys),
            dry_run=dry_run,
            details={"unowned": len(keys), "keys": keys},
        )


migration = DropUnownedImportJobsMigration()
