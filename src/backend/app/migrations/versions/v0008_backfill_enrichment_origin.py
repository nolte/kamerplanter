"""v0008_backfill_enrichment_origin — stamp ``origin = enrichment`` on species that
were enriched before provenance existed.

The ``origin`` provenance marker (``DataOrigin``) was added to species *after* the
external-source enrichment engine already ran against existing data.  Predecessor
migration ``v0006`` back-filled every ``origin``-less record as ``system`` (seed
set) or ``tenant`` (user data) — but it had no signal for *enrichment*, so a
species that was **enriched in the past** was stamped ``system``/``tenant`` and its
origin chip shows the wrong provenance (REQ-011, UI-NFR-018).

This migration reconstructs the ``enrichment`` provenance from the only persistent
marker the engine leaves behind: an ``external_mappings`` document
(``internal_collection == "species"``, ``internal_key == species._key``).  A mapping
alone is *not* proof that data was written — the engine records a mapping even when
every external field was rejected because the local value was already populated
(``accepted == False``).  The precise marker that mirrors the live flip in
``EnrichmentEngine._apply_enrichment`` is therefore a mapping carrying **at least
one** field with ``accepted == True``.

The flip is guarded exactly like the live engine (``enrichment_engine.py``): only a
record whose current ``origin`` is ``system`` is promoted to ``enrichment``.  A
``tenant`` (or ``import``) record is never touched — this preserves the
anti-lockout guarantee (v0006): a user must never lose edit/delete rights to their
own master data.

Idempotent (M-3): only ``system`` species are candidates, so once promoted to
``enrichment`` a re-run is a no-op (``changed == 0``).  Dry-run (M-5): the report is
computed without writing.  Irreversible (M-6): the pre-migration state carried no
``enrichment`` provenance signal, so there is no honest inverse — a plain revert
would wrongly re-lock genuinely-enriched seed records.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.common.enums import DataOrigin
from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()


def _has_accepted_field(field_mappings: object) -> bool:
    """True when at least one field mapping was actually accepted (data written).

    Mirrors ``applied_any`` in :meth:`EnrichmentEngine._apply_enrichment`: only an
    ``accepted`` field means external data landed on the species, which is the
    condition under which the live engine promotes ``origin`` to ``enrichment``.
    """
    if not isinstance(field_mappings, dict):
        return False
    return any(isinstance(fm, dict) and fm.get("accepted") for fm in field_mappings.values())


class BackfillEnrichmentOriginMigration(Migration):
    version = "0008"
    name = "backfill_enrichment_origin"
    description = "Stamp origin=enrichment on species enriched before provenance existed (system-origin only)."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        # 1. Species that carry a genuine enrichment marker (an external mapping
        #    with at least one accepted field). Set-dedupes multiple mappings
        #    (one per external source) for the same species.
        enriched_keys: set[str] = set()
        for row in db.aql.execute(
            f"FOR em IN {col.EXTERNAL_MAPPINGS} "
            f"FILTER em.internal_collection == @species "
            f"RETURN {{internal_key: em.internal_key, field_mappings: em.field_mappings}}",
            bind_vars={"species": col.SPECIES},
        ):
            if _has_accepted_field(row.get("field_mappings")):
                enriched_keys.add(row["internal_key"])

        # 2. Of those, only the ones still stamped ``system`` are promoted;
        #    ``tenant``/``import`` are left untouched (anti-lockout). Filtering on
        #    ``system`` also makes the migration idempotent — a re-run finds none.
        to_flip: list[str] = []
        if enriched_keys:
            for key in db.aql.execute(
                f"FOR d IN {col.SPECIES} FILTER d._key IN @keys AND d.origin == @system RETURN d._key",
                bind_vars={"keys": sorted(enriched_keys), "system": DataOrigin.SYSTEM.value},
            ):
                to_flip.append(key)

        scanned = len(enriched_keys)
        details = {"enriched_species": scanned, "flipped": len(to_flip)}

        if dry_run:
            logger.info("backfill_enrichment_origin_dry_run", scanned=scanned, to_flip=len(to_flip))
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=True,
                details=details,
            )

        changed = 0
        if to_flip:
            db.aql.execute(
                "FOR k IN @keys UPDATE {_key: k, origin: @origin} IN @@collection",
                bind_vars={
                    "keys": to_flip,
                    "origin": DataOrigin.ENRICHMENT.value,
                    "@collection": col.SPECIES,
                },
            )
            changed = len(to_flip)

        logger.info("backfill_enrichment_origin_applied", scanned=scanned, changed=changed)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=False,
            details={**details, "flipped": changed},
        )


migration = BackfillEnrichmentOriginMigration()
