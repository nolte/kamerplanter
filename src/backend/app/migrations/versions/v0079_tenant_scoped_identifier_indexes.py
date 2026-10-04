"""v0079 — scope instance_id, batch_id and slot_id to their owner instead of every tenant (#2065).

Three unique indexes on tenant-owned collections were collection-wide. Measured on
ArangoDB 3.12.8 through the real routes:

* ``plant_instances.instance_id`` — the second tenant to onboard a species got
  ``200 completed`` with both plants skipped (``onb-<species_key>-<n>`` was taken), and
  ``POST /t/{slug}/plant-instances`` with an id another tenant used answered ``409
  DUPLICATE_ENTRY … instance_id='BASIL-001' already exists``;
* ``harvest_batches.batch_id`` — the same ``409`` for a lot label;
* ``slots.slot_id`` — the same ``409`` for a slot label such as ``TENT01_A1``.

Each refusal denied the label and told the caller that another tenant holds it.

The keys become ``(tenant_key, instance_id)``, ``(tenant_key, batch_id)`` (sparse, as
the label index has been since v0030) and ``(location_key, slot_id)`` — a slot has no
tenant of its own, its location belongs to exactly one
(:data:`~app.data_access.arango.collections.SLOT_ID_INDEX_FIELDS`).

**Order, per collection.** The compound index is created first — ``ensure_collections``
already does so on every boot; this version creates it itself when it is missing so the
drop never depends on the boot order — and only then is the legacy index dropped,
through :func:`~app.migrations.support.legacy_indexes.retire_legacy_index`, which sees
``persistent`` and pre-June ``hash`` indexes alike and never drops a legacy index
without a different unique index of the replacement shape. There is no window without
a constraint.

**Never without the replacement.** When any collection's replacement is still missing
after the creation step, the run reports ``precondition_unmet``: the runner leaves this
version pending and a later boot retries it. A collection already done stays done; the
re-run finds nothing left to drop there.

**No data moves.** A set unique on a field is unique on any superset of the fields, so
no existing row can violate a compound index. The sparse batch index skips a row whose
``tenant_key`` or ``batch_id`` is ``null``; the old sparse index skipped only a ``null``
``batch_id``, and ``HarvestBatch`` always stores a ``tenant_key`` string.

Idempotent (M-3): a re-run finds every compound present and no legacy index →
``changed == 0``. Dry-run (M-5) reports the plan and touches no index. Irreversible
(M-6): once two tenants share a label, the collection-wide index can no longer be
created without renaming somebody's plant, slot or lot.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog
from arango.collection import StandardCollection
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_indexes import IndexShape, retire_legacy_index

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class _Target:
    """One collection: the collection-wide index it retires and the scoped one replacing it."""

    collection: str
    legacy: IndexShape
    replacement: IndexShape


#: The three constraints #2065 retires, with their replacements as ``ensure_collections``
#: creates them.
TARGETS: tuple[_Target, ...] = (
    _Target(
        collection=col.PLANT_INSTANCES,
        legacy=IndexShape(fields=tuple(col.LEGACY_PLANT_INSTANCE_ID_INDEX_FIELDS), unique=True),
        replacement=IndexShape(fields=tuple(col.PLANT_INSTANCE_ID_INDEX_FIELDS), unique=True),
    ),
    _Target(
        collection=col.HARVEST_BATCHES,
        legacy=IndexShape(fields=tuple(col.LEGACY_HARVEST_BATCH_ID_INDEX_FIELDS), unique=True, sparse=True),
        replacement=IndexShape(fields=tuple(col.HARVEST_BATCH_ID_INDEX_FIELDS), unique=True, sparse=True),
    ),
    _Target(
        collection=col.SLOTS,
        legacy=IndexShape(fields=tuple(col.LEGACY_SLOT_ID_INDEX_FIELDS), unique=True),
        replacement=IndexShape(fields=tuple(col.SLOT_ID_INDEX_FIELDS), unique=True),
    ),
)


def _has_replacement(collection: StandardCollection, target: _Target) -> bool:
    """Whether the scoped unique index exists (``persistent`` or ``hash``)."""
    rows = collection.indexes()
    return isinstance(rows, list) and any(isinstance(idx, dict) and target.replacement.matches(idx) for idx in rows)


def _create_replacement(collection: StandardCollection, target: _Target) -> None:
    """Create the scoped unique index; a separate step so the gate after it is testable."""
    collection.add_persistent_index(
        fields=list(target.replacement.fields), unique=True, sparse=target.replacement.sparse
    )


class TenantScopedIdentifierIndexesMigration(Migration):
    version = "0079"
    name = "tenant_scoped_identifier_indexes"
    description = (
        "Replace the collection-wide unique indexes on plant_instances(instance_id), "
        "harvest_batches(batch_id) and slots(slot_id) with (tenant_key, instance_id), "
        "(tenant_key, batch_id) and (location_key, slot_id), retiring each legacy index "
        "whether it is typed persistent or hash (#2065)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        scanned = 0
        changed = 0
        any_refused = False
        per_collection: dict[str, dict[str, Any]] = {}
        for target in TARGETS:
            if not db.has_collection(target.collection):
                continue
            collection = db.collection(target.collection)

            needs_compound = not _has_replacement(collection, target)
            compound_created = False
            if needs_compound and not dry_run:
                # First the replacement constraint; dropping the old one before it
                # exists would leave a window with no uniqueness at all. Counted from
                # the re-read, not from the call having been made.
                _create_replacement(collection, target)
                compound_created = _has_replacement(collection, target)

            outcome = retire_legacy_index(
                collection, legacy=target.legacy, replacement=target.replacement, dry_run=dry_run
            )
            # A dry run does not create the replacement, so the selector sees none; the
            # real run would have created it first — that is the plan, not a refusal.
            refused = outcome.refused and not (dry_run and needs_compound)
            any_refused = any_refused or refused

            details: dict[str, Any] = {
                **outcome.details(),
                "refused_without_replacement": refused,
                "compound_created": compound_created,
            }
            if dry_run:
                details["compound_to_create"] = needs_compound
            per_collection[target.collection] = details
            scanned += len(outcome.legacy_ids) + int(needs_compound)
            changed += 0 if dry_run else int(compound_created) + outcome.dropped

        if any_refused:
            logger.warning("tenant_scoped_identifier_indexes_refused", dry_run=dry_run, collections=per_collection)
        else:
            logger.info("tenant_scoped_identifier_indexes", dry_run=dry_run, collections=per_collection)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=dry_run,
            precondition_unmet=any_refused,
            details={"collections": per_collection},
        )


migration = TenantScopedIdentifierIndexesMigration()
