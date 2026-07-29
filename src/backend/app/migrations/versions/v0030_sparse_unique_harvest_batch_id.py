"""v0030 — make ``harvest_batches.batch_id`` uniqueness sparse (#740).

Bug #740: ``harvest_batches`` carried ``add_persistent_index(fields=["batch_id"],
unique=True)`` (non-sparse), while ``HarvestBatch.batch_id`` was an *optional*
user-facing lot label defaulting to ``""``. Every create path that omitted the
label persisted ``batch_id == ""``, so the FIRST unlabelled batch inserted fine
but the SECOND collided on the empty key — ArangoDB error 1210 surfacing as a 409
``DUPLICATE_ENTRY``. Users could therefore only ever create a single batch without
a lot ID, even though the UI calls the field an "optionale Kennung".

The code fix (a) normalises blank ``batch_id`` inputs to ``None`` in the model and
(b) recreates the bootstrap index as ``unique=True, sparse=True`` so null/absent
labels are excluded from the constraint while real IDs stay unique. This migration
repairs existing volumes.

Two ordered jobs, both idempotent:

1. **Null out blank labels.** Every ``harvest_batches`` document whose ``batch_id``
   is ``""`` (or a whitespace-only string) is set to ``null`` via a single batched
   AQL UPDATE. Documents already carrying ``null`` or a real label are untouched.
   ``scanned`` counts the blank rows found; ``changed`` counts those rewritten.

2. **Promote the index to sparse.** The persistent index on ``["batch_id"]`` is a
   distinct definition when sparse vs non-sparse, so promotion = ensure the
   unique+sparse index exists (safe now — step 1 removed the colliding empty keys)
   and drop any redundant non-sparse index on the same field. Index introspection
   mirrors v0026: ``indexes()`` filtered by ``type``/``fields``, ``sparse`` flag
   compared, ``delete_index(..., ignore_missing=True)``.

Idempotent (M-3): a re-run finds no blank ``batch_id`` (step 1 no-op) and the
unique+sparse index already present with no non-sparse sibling (step 2 no-op) →
``changed == 0``. Dry-run (M-5): both jobs are previewed and nothing is written.
Irreversible (M-6): step 1 discards the original ``""`` sentinel (indistinguishable
from a legitimately-blank label afterwards) and step 2 drops the non-sparse
bootstrap index that predates this migration, so there is no honest inverse.

NOTE (merge): this version number (``0030``) is provisional — it is the next free
slot above the current develop head (``0029``). If a parallel lane lands another
``0030`` first, RENUMBER this module (and its test) to the next free contiguous slot
before merge; the discovery layer enforces gapless numbering (M-1).
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: Fields of the batch_id index this migration promotes to unique+sparse.
_INDEX_FIELDS: list[str] = ["batch_id"]


class SparseUniqueHarvestBatchIdMigration(Migration):
    version = "0030"
    name = "sparse_unique_harvest_batch_id"
    description = (
        "Null out blank harvest_batches.batch_id values and make the unique index "
        "sparse so multiple unlabelled batches no longer collide (#740)."
    )
    reversible = False

    # ── read helpers (no-op-safe on an empty/fresh database) ──────────────────

    def _blank_batch_ids(self, db: StandardDatabase) -> list[str]:
        """Keys of every harvest batch whose batch_id is blank (read-only, M-5-safe).

        Matches both the historical ``""`` sentinel and whitespace-only labels that
        should never have persisted as a value.
        """
        if not db.has_collection(col.HARVEST_BATCHES):
            return []
        return list(
            db.aql.execute(
                "FOR doc IN @@collection FILTER doc.batch_id != null AND TRIM(doc.batch_id) == '' RETURN doc._key",
                bind_vars={"@collection": col.HARVEST_BATCHES},
            )
        )

    def _persistent_batch_id_indexes(self, batches_col: Any) -> list[dict[str, Any]]:
        """Return the persistent index dicts on ``batch_id``.

        ``collection.indexes()`` yields one dict per index (``type``/``fields``/
        ``unique``/``sparse``/``id``); a sparse and a non-sparse index on the same
        field are two distinct definitions, so this can legitimately return both
        during promotion.
        """
        return [
            idx
            for idx in batches_col.indexes()
            if isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == _INDEX_FIELDS
        ]

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        blank_keys = self._blank_batch_ids(db)
        scanned = len(blank_keys)

        batches_col = db.collection(col.HARVEST_BATCHES)
        indexes = self._persistent_batch_id_indexes(batches_col)
        has_sparse_unique = any(idx.get("unique") and idx.get("sparse") for idx in indexes)
        redundant = [idx for idx in indexes if not (idx.get("unique") and idx.get("sparse"))]

        if dry_run:
            logger.info(
                "sparse_unique_harvest_batch_id_dry_run",
                blank_batch_ids=scanned,
                index_already_sparse_unique=has_sparse_unique,
                redundant_indexes=len(redundant),
            )
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=True,
                details={
                    "blank_batch_ids": scanned,
                    "index_already_sparse_unique": has_sparse_unique,
                    "will_create_sparse_unique_index": not has_sparse_unique,
                    "will_drop_redundant_indexes": len(redundant),
                },
            )

        # 1. Null out blank batch_id sentinels in a single batched UPDATE.
        if blank_keys:
            db.aql.execute(
                "FOR key IN @keys UPDATE {_key: key, batch_id: null} IN @@collection",
                bind_vars={"keys": blank_keys, "@collection": col.HARVEST_BATCHES},
            )

        # 2. Promote: ensure the unique+sparse index and drop any non-sparse sibling.
        index_changes = 0
        if not has_sparse_unique:
            batches_col.add_persistent_index(fields=_INDEX_FIELDS, unique=True, sparse=True)
            index_changes += 1
        for idx in self._persistent_batch_id_indexes(batches_col):
            if not (idx.get("unique") and idx.get("sparse")):
                batches_col.delete_index(idx["id"], ignore_missing=True)
                index_changes += 1

        changed = len(blank_keys) + index_changes
        logger.info(
            "sparse_unique_harvest_batch_id_applied",
            nulled_batch_ids=len(blank_keys),
            index_changes=index_changes,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=False,
            details={
                "nulled_batch_ids": len(blank_keys),
                "index_changes": index_changes,
                "sparse_unique_index_enforced": True,
            },
        )


migration = SparseUniqueHarvestBatchIdMigration()
