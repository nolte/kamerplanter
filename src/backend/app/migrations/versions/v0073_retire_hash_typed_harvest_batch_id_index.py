"""v0073 — drop the hash-typed non-sparse ``harvest_batches.batch_id`` index v0030 missed (#2034).

``v0030`` (#740) made ``batch_id`` uniqueness sparse: it ensures a unique+sparse
index and drops the non-sparse unique one, so many unlabelled batches (``batch_id``
``null``) no longer collide. It found the old index with ``type == "persistent"``.
A volume first booted before 2026-06-07 created that index with ``add_hash_index``
(``516bcd832^:…/collections.py:1159``), and ArangoDB 3.12 reports it as
``type: "hash"`` — so v0030 left it in place. Measured on 3.12.8: after v0030 the
second unlabelled batch is still refused with ``[ERR 1210] unique constraint
violated - in index … of type hash over 'batch_id'``. #740 stayed open on exactly
those volumes while v0030 reported success.

v0030 is shipped, so its class is frozen (M-7); this version is the correction.
It drops every unique **non-sparse** index on exactly ``["batch_id"]``, ``hash`` or
``persistent``, through the shared selector
(:mod:`app.migrations.support.legacy_indexes`). A non-unique index on the field
(no code has created one) is left alone.

**Never without the replacement.** The drop happens only while the unique+sparse
index on ``batch_id`` exists — ``ensure_collections`` creates it before any
migration runs. If it is missing, nothing is dropped and the run reports
``precondition_unmet`` with the counts, so the runner leaves this version (and every
later one) pending and a later boot retries it.

Idempotent (M-3): a re-run finds no legacy index → ``changed == 0``. Dry-run (M-5)
counts and drops nothing. Irreversible (M-6): the dropped index is the constraint
#740 retired.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_indexes import IndexShape, retire_legacy_index

logger = structlog.get_logger(__name__)

#: The constraint #740 retired: unique over every ``batch_id``, ``null`` included.
LEGACY_BATCH_ID_INDEX = IndexShape(fields=("batch_id",), unique=True, sparse=False)

#: Its replacement, as ``ensure_collections`` and v0030 create it.
SPARSE_BATCH_ID_INDEX = IndexShape(fields=("batch_id",), unique=True, sparse=True)


class RetireHashTypedHarvestBatchIdIndexMigration(Migration):
    version = "0073"
    name = "retire_hash_typed_harvest_batch_id_index"
    description = (
        "Drop the non-sparse unique harvest_batches.batch_id index of type hash that v0030 "
        "missed, once the unique+sparse replacement exists (#2034)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.HARVEST_BATCHES):
            return MigrationReport(version=self.version, name=self.name, dry_run=dry_run)
        outcome = retire_legacy_index(
            db.collection(col.HARVEST_BATCHES),
            legacy=LEGACY_BATCH_ID_INDEX,
            replacement=SPARSE_BATCH_ID_INDEX,
            dry_run=dry_run,
        )
        if outcome.refused:
            logger.warning("retire_hash_typed_harvest_batch_id_index_refused", **outcome.details())
        else:
            logger.info("retire_hash_typed_harvest_batch_id_index", dry_run=dry_run, **outcome.details())
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(outcome.legacy_ids),
            changed=outcome.dropped,
            dry_run=dry_run,
            precondition_unmet=outcome.refused,
            details=outcome.details(),
        )


migration = RetireHashTypedHarvestBatchIdIndexMigration()
