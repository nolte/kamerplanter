"""v0025 — enforce normalized-name uniqueness on ``species`` (Issue #624, SEC-003).

The deferred uniqueness follow-up promised by v0010 / ``species_repository`` finally
lands here. v0010 (REQ-048 Stufe 1) backfilled ``scientific_name_normalized`` and
reconciled the then-existing normalization duplicates, but left the persistent index
**non-unique** on purpose — a unique index cannot be created while duplicates exist,
and ``ensure_collections`` runs at startup *before* the migration runner. So the DB
never actually enforced the dedup key, and the two create paths that bypassed the
atomic UPSERT (import, seed) could keep minting normalization duplicates (× vs x,
casing, whitespace). Issue #624 closes both gaps: this PR routes *every* create path
through ``upsert_by_normalized_scientific_name`` AND this migration promotes the index
to unique so the database is the final backstop.

Two ordered jobs, both idempotent:

1. **Reconcile residual duplicates.** Any normalization-duplicate group that
   accumulated on a volume after v0010 ran (via the pre-#624 bypassing create paths)
   is merged onto one survivor, repointing every reference (companion
   ``compatible_with``/``incompatible_with`` edges, ``descended_from`` lineage, plant
   instances, cultivars, ``ExternalMapping``s, tasks, …) with no orphan left behind.
   The reconcile logic is not re-implemented: it delegates to the battle-tested,
   fully-covered v0010 reconciliation (``_v0010.up``), which is itself idempotent —
   on an already-clean volume it finds no groups and does nothing. Survivor selection
   keeps the record carrying live plants and adopts the richer metadata; the
   server-managed ``origin`` provenance is never reset (REQ-048 R3 / #624 note).

2. **Promote the index to unique.** ``scientific_name_normalized`` is a distinct
   index definition when unique vs non-unique, so promotion = create the unique index
   (now safe: step 1 guarantees no duplicates remain) and drop the redundant
   non-unique bootstrap index. After this the DB rejects a second insert of an
   existing normalized key at the storage layer, closing the last TOCTOU window.

Idempotent (M-3): a re-run finds no duplicate groups (step 1 no-op) and the unique
index already present with no non-unique sibling (step 2 no-op) → ``changed == 0``.
Dry-run (M-5): step 1 is previewed via v0010's dry-run and no index is touched.
Irreversible (M-6): step 1 deletes loser documents and step 2 drops the non-unique
index that predates this migration (bootstrap created it), so there is no honest
inverse.

NOTE (merge): this version number (``0026``) is provisional — it is the next free
slot above the current develop head (``0025``). If a parallel lane lands another
``0025`` first, RENUMBER this module (and its test) to the next free contiguous slot
before merge; the discovery layer enforces gapless numbering (M-1).
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.versions.v0010_backfill_scientific_name_normalized import migration as _v0010

logger = structlog.get_logger()

#: Fields of the canonical dedup index this migration promotes to unique.
_INDEX_FIELDS: list[str] = ["scientific_name_normalized"]


class PromoteScientificNameNormalizedUniqueMigration(Migration):
    version = "0026"
    name = "promote_scientific_name_normalized_unique"
    description = (
        "Reconcile residual scientific_name_normalized duplicates and promote the "
        "index to unique so the DB enforces species dedup on every create path (#624)."
    )
    reversible = False

    def _persistent_normalized_indexes(self, species_col: Any) -> list[dict[str, Any]]:
        """Return the persistent index dicts on ``scientific_name_normalized``.

        ``collection.indexes()`` yields one dict per index (``type``/``fields``/
        ``unique``/``id``); a unique and a non-unique index on the same field are two
        distinct definitions, so this can legitimately return both during promotion.
        """
        return [
            idx
            for idx in species_col.indexes()
            if isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == _INDEX_FIELDS
        ]

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        # 1. Reconcile any residual duplicate groups (idempotent, no-op when clean).
        dedup = _v0010.up(db, dry_run=dry_run)

        species_col = db.collection(col.SPECIES)
        indexes = self._persistent_normalized_indexes(species_col)
        has_unique = any(idx.get("unique") for idx in indexes)
        non_unique = [idx for idx in indexes if not idx.get("unique")]

        if dry_run:
            logger.info(
                "promote_scientific_name_normalized_unique_dry_run",
                dedup_changed=dedup.changed,
                index_already_unique=has_unique,
                non_unique_indexes=len(non_unique),
            )
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=dedup.scanned,
                changed=0,
                dry_run=True,
                details={
                    "dedup": dedup.details,
                    "index_already_unique": has_unique,
                    "will_create_unique_index": not has_unique,
                    "will_drop_non_unique_indexes": len(non_unique),
                },
            )

        # 2. Promote: create the unique index (safe now — no duplicates remain) and
        #    drop the redundant non-unique bootstrap index.
        index_changes = 0
        if not has_unique:
            species_col.add_persistent_index(fields=_INDEX_FIELDS, unique=True)
            index_changes += 1
        for idx in self._persistent_normalized_indexes(species_col):
            if not idx.get("unique"):
                species_col.delete_index(idx["id"], ignore_missing=True)
                index_changes += 1

        changed = dedup.changed + index_changes
        logger.info(
            "promote_scientific_name_normalized_unique_applied",
            dedup_changed=dedup.changed,
            index_changes=index_changes,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=dedup.scanned,
            changed=changed,
            dry_run=False,
            details={
                "dedup": dedup.details,
                "index_changes": index_changes,
                "unique_index_enforced": True,
            },
        )


migration = PromoteScientificNameNormalizedUniqueMigration()
