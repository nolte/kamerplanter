"""v0099 — the irrigation-zone indexes on existing volumes (REQ-053 WP 7.1, #2467; P-5).

Two indexes, both structural — **no document is read for its content or written**:

* ``irrigation_zones (tenant_key, site_key)`` — the zone list of a site (``GET /sites/{key}/irrigation-zones``)
  and the water-source unlink of the plan batch filter on both; ``tenant_key`` leads because the zone carries it
  (E-01, ``test_tenant_unique_indexes_are_scoped`` style even though this one is not unique).
* ``zone_covers`` unique on ``_to`` — a bed is in at most one zone (§14.1). The services keep that already
  (every writer removes the bed's old edge in the same transaction); the index makes a race between two
  writers fail at the database instead of leaving a bed in two zones.

Fresh volumes get the same indexes from ``ensure_collections``
(:data:`~app.data_access.arango.collections.IRRIGATION_ZONE_SITE_INDEX_FIELDS`,
:data:`~app.data_access.arango.collections.ZONE_COVERS_TARGET_INDEX_FIELDS`); this migration brings a volume
that predates WP 7.1 to that shape.

**Who owns the unique index.** One function: :func:`~app.data_access.arango.collections.ensure_unique_index_when_clean`
— the shape v0070 (#2001) set for the seed identity indexes. ``ensure_collections`` runs at startup *before* the
migration runner (``app/main.py``) and calls it, so on a clean volume the index exists before this version runs and
this half is a no-op; on a volume with two edges to one bed the creation is refused (``1210``), absorbed, and the
boot continues to this migration. Here the dry run counts the beds with more than one edge
(``duplicate_targets``), and a real run calls the same function again: created when clean, otherwise **blocked** —
logged with the count, reported, never an edge deleted and never a failed boot (a raising migration is fatal at
startup). Every later boot retries. No code path wrote ``zone_covers`` before WP 7.1, so ``0`` is expected; P-5
reads the dry-run report before the prod run (plan §8).

Idempotent (M-3): an index on exactly the target fields (``indexes_on``, persistent or a pre-June ``hash``; for
``_to`` additionally unique) makes that half a no-op. Dry-run (M-5) inspects without creating. Irreversible (M-6):
the bootstrap creates both indexes on every boot, so dropping them would not restore the pre-migration state.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_unique_index_when_clean, has_unique_index
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_indexes import indexes_on

logger = structlog.get_logger(__name__)

#: Frozen here so a later change of the bootstrap constants does not change what this version did.
#: Equal to ``collections.IRRIGATION_ZONE_SITE_INDEX_FIELDS`` / ``ZONE_COVERS_TARGET_INDEX_FIELDS`` (unit test).
ZONE_SITE_FIELDS: tuple[str, ...] = ("tenant_key", "site_key")
COVERS_TARGET_FIELDS: tuple[str, ...] = ("_to",)

_DUPLICATE_TARGETS = """
RETURN LENGTH(
    FOR e IN @@covers
        COLLECT target = e._to WITH COUNT INTO edges
        FILTER edges > 1
        RETURN 1
)
"""


class IrrigationZoneIndexesMigration(Migration):
    version = "0099"
    name = "irrigation_zone_indexes"
    description = (
        "Add the irrigation_zones (tenant_key, site_key) index and the unique zone_covers._to index on existing "
        "volumes, so a site's zones are read by index and a bed is in at most one zone (REQ-053 WP 7.1)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        details: dict[str, Any] = {
            "zone_site_fields": list(ZONE_SITE_FIELDS),
            "covers_target_fields": list(COVERS_TARGET_FIELDS),
        }
        zones_present = bool(db.has_collection(col.IRRIGATION_ZONES))
        covers_present = bool(db.has_collection(col.ZONE_COVERS))
        details["collections_absent"] = sorted(
            name
            for name, present in ((col.IRRIGATION_ZONES, zones_present), (col.ZONE_COVERS, covers_present))
            if not present
        )

        zone_index = bool(indexes_on(db.collection(col.IRRIGATION_ZONES), ZONE_SITE_FIELDS)) if zones_present else True
        covers_index = (
            has_unique_index(db.collection(col.ZONE_COVERS), list(COVERS_TARGET_FIELDS)) if covers_present else True
        )
        duplicates = self._duplicate_targets(db) if covers_present and not covers_index else 0
        details.update(
            {
                "zone_site_index_present": zone_index,
                "covers_target_index_present": covers_index,
                "duplicate_targets": duplicates,
            }
        )
        scanned = int(zones_present) + int(covers_present)

        if dry_run:
            logger.info(
                "irrigation_zone_indexes_dry_run",
                zone_site_index_present=zone_index,
                covers_target_index_present=covers_index,
                duplicate_targets=duplicates,
            )
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=True,
                details={
                    **details,
                    "will_create": [
                        name
                        for name, present in (("zone_site", zone_index), ("covers_target", covers_index))
                        if not present
                    ],
                },
            )

        changed = 0
        blocked = False
        if not zone_index:
            db.collection(col.IRRIGATION_ZONES).add_persistent_index(
                fields=list(ZONE_SITE_FIELDS), unique=False, in_background=True
            )
            changed += 1
        if not covers_index:
            if ensure_unique_index_when_clean(db.collection(col.ZONE_COVERS), list(COVERS_TARGET_FIELDS)):
                changed += 1
            else:
                blocked = True
                logger.warning(
                    "irrigation_zone_cover_index_blocked_by_duplicates",
                    duplicate_targets=duplicates,
                    hint="a bed has more than one zone_covers edge; resolve by hand, every boot retries",
                )
        details["covers_target_blocked"] = blocked

        logger.info("irrigation_zone_indexes_applied", changed=changed)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=False,
            details={**details, "created": changed},
        )

    @staticmethod
    def _duplicate_targets(db: StandardDatabase) -> int:
        cursor = cast("Cursor", db.aql.execute(_DUPLICATE_TARGETS, bind_vars={"@covers": col.ZONE_COVERS}))
        return int(next(iter(cursor), 0) or 0)


migration = IrrigationZoneIndexesMigration()
