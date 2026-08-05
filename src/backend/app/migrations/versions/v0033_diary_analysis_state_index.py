"""v0033 — add the persistent ``(tenant_key, analysis_state, analysis_requested_at)``
index to ``plant_diary_entries`` on existing volumes (REQ-050 §5, #921).

REQ-050 gives every diary entry an analysis state. Two reads lean on it:
``list_pending_diary_analyses`` (§4.1), which fetches a tenant's waiting entries
oldest-first, and the analysis-state filter of the tenant-wide diary overview
(§2.5.2) — by the requirement's own admission the most frequent access there is
"what is finished by now?". Without an index both are a full scan over every
diary entry of the tenant.

Fresh databases get the identical index from ``ensure_collections`` bootstrap
(``collections.py``); this migration brings *existing* volumes to the same shape.
It is structural only — **no document is rewritten**. REQ-050 §5 states outright
that existing entries stay valid without a data migration, and the model carries
``analysis_state`` with the default ``none`` (AK-26).

**The field order is the whole point, and a query can miss it.** ArangoDB uses a
persistent index only from its leading attribute onwards, so:

* ``FILTER doc.tenant_key == @t AND doc.analysis_state == @s
  SORT doc.analysis_requested_at ASC`` — fully covered, sort included;
* the same query with ``doc.analysis_state IN @states`` — still covered (the
  optimiser turns the ``IN`` into index ranges), though the sort may be applied
  afterwards across the ranges;
* a filter on ``analysis_state`` **without** ``tenant_key`` — not covered at all,
  and also a cross-tenant read, so it must not exist in the first place;
* ``analysis_lease_expires_at`` (the stale-lease predicate of ``include_stale``)
  is deliberately *not* in the index: it only ever narrows the small
  ``in_progress`` range and would push ``analysis_requested_at`` out of sort
  position.

**Reading state ``none`` needs an ``IN [..., null]``, not an ``==``.** A document
written before REQ-050 carries no ``analysis_state`` attribute; in AQL a missing
attribute compares equal to ``null``, never to the string ``"none"``. A filter
``doc.analysis_state == 'none'`` therefore silently skips exactly the entries
AK-26 says must read as ``none``. The correct, still index-using form is
``FILTER doc.analysis_state IN @states`` with ``["none", null]`` bound for that
state.

Idempotent (M-3): the target index is looked up first — when a persistent index
on the exact field list already exists (bootstrapped fresh DB or a prior run) the
migration is a no-op (``changed == 0``). Dry-run (M-5): existence is inspected
without creating anything. Irreversible (M-6): dropping an index that may predate
this migration (bootstrap also creates it) would not honestly restore the
pre-migration state, so no inverse is offered.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: Field list of the target index. Ordering is significant — see the module
#: docstring; it mirrors the bootstrap index in ``collections.py``.
_TARGET_FIELDS: list[str] = ["tenant_key", "analysis_state", "analysis_requested_at"]


def _has_analysis_state_index(indexes: object) -> bool:
    """True when a persistent index on :data:`_TARGET_FIELDS` already exists.

    ``collection.indexes()`` returns a list of index dicts (``type``/``fields``).
    The comparison is on the exact field *sequence*, not on the set: an index over
    the same three attributes in another order would not serve the tenant-scoped,
    ``requested_at``-sorted read and must not be mistaken for this one.
    """
    if not isinstance(indexes, list):
        return False
    return any(
        isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == _TARGET_FIELDS
        for idx in indexes
    )


class DiaryAnalysisStateIndexMigration(Migration):
    version = "0033"
    name = "diary_analysis_state_index"
    description = (
        "Add the persistent (tenant_key, analysis_state, analysis_requested_at) index to "
        "plant_diary_entries on existing volumes so the REQ-050 work queue and the "
        "analysis-state filter of the diary overview are not collection scans."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.PLANT_DIARY_ENTRIES):
            # A volume without the collection has nothing to index; bootstrap
            # creates collection and index together.
            logger.info("diary_analysis_state_index_skipped", reason="collection_absent")
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=0,
                changed=0,
                dry_run=dry_run,
                details={"index_fields": _TARGET_FIELDS, "collection_absent": True},
            )

        collection = db.collection(col.PLANT_DIARY_ENTRIES)
        already_present = _has_analysis_state_index(collection.indexes())

        # ``scanned`` counts the one target index definition inspected; ``changed``
        # is 1 only when this run actually creates it. No document is touched.
        details = {"index_fields": _TARGET_FIELDS, "already_present": already_present}

        if dry_run:
            logger.info("diary_analysis_state_index_dry_run", already_present=already_present)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=1,
                changed=0,
                dry_run=True,
                details={**details, "will_create": not already_present},
            )

        changed = 0
        if not already_present:
            collection.add_persistent_index(fields=_TARGET_FIELDS, unique=False)
            changed = 1

        logger.info("diary_analysis_state_index_applied", changed=changed, already_present=already_present)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=1,
            changed=changed,
            dry_run=False,
            details={**details, "created": bool(changed)},
        )


migration = DiaryAnalysisStateIndexMigration()
