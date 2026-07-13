"""v0023_document_instance_cultivation_cycle — additive per-instance cycle field.

ADR-006 E1 / E7 (#565 Phase 2). Phase 2 introduces the per-instance cultivation
decision ``PlantInstance.cultivation_cycle_type: CycleType | None`` and the single
``resolve_effective_cycle`` cascade (instance → species cultivation_cycle_type →
species botanical cycle_type). Per ADR-006 E7(1) the field is **additive and
None-defaultable**: ArangoDB is schemaless (ADR-001), so existing plant instances
need **no backfill** — an absent field reads as ``None`` = "same as the species",
which is exactly the pre-Phase-2 behaviour.

This migration therefore performs **no data transformation**; it exists to document
the schema evolution in the tracked, ordered migration ledger (ADR-005 / NFR-016)
and to record how many live plant instances inherit the species default. It is a
pure read: it scans ``plant_instances`` and reports the count, changing nothing. A
re-run is a no-op (M-3, ``is_noop``); dry-run and normal run are identical (M-5);
there is nothing to reverse (M-6, ``reversible = False``). The Weg-A → Weg-B
lifecycle backfill of E2/E4/E7(2) is a separate concern already handled by v0022.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()


class DocumentInstanceCultivationCycleMigration(Migration):
    version = "0023"
    name = "document_instance_cultivation_cycle"
    description = (
        "Document the additive per-instance PlantInstance.cultivation_cycle_type override (ADR-006 E1); "
        "schemaless, no backfill — absent = 'same as the species'."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        # Pure read: count live instances that inherit the species default (no field
        # set). Nothing is written in either dry-run or normal mode.
        instances = list(db.aql.execute(f"FOR d IN {col.PLANT_INSTANCES} RETURN d.cultivation_cycle_type"))
        total = len(instances)
        inheriting = sum(1 for value in instances if value is None)

        logger.info(
            "document_instance_cultivation_cycle",
            total=total,
            inheriting_species_default=inheriting,
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=total,
            changed=0,  # additive field, schemaless — nothing to transform (E7)
            dry_run=dry_run,
            details={"inheriting_species_default": inheriting},
        )


migration = DocumentInstanceCultivationCycleMigration()
