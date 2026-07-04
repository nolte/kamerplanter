"""Backfill ``fertilizer_type = "calmag"`` on legacy CalMag products (DOM-6).

Historically CalMag supplements were stored as ``supplement`` (or another type)
and only recognised by fragile substring name matching. AP-10 introduces the
structured ``FertilizerType.CALMAG`` value; this migration reclassifies existing
documents whose *normalized* product name matches a known CalMag pattern
("Cal-Mag", "CaliMagic", "Calcium/Magnesium", …).

It is:

- **idempotent** — documents already typed ``calmag`` are skipped, so re-running
  is a safe no-op (only documents that actually change are written);
- **non-destructive** — it only sets the type, never deletes a product, and the
  field stays user-editable afterwards;
- **reportable & logged** — every reclassification is logged via structlog and
  the returned report summarises the change count.

Run from the backend root::

    python -m app.migrations.migrate_fertilizer_calmag_type            # apply
    python -m app.migrations.migrate_fertilizer_calmag_type --dry-run  # report only
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

import structlog
from arango.database import StandardDatabase

from app.common.enums import FertilizerType
from app.data_access.arango import collections as col
from app.domain.engines.fertilizer_classification import matches_calmag_name

logger = structlog.get_logger()

_CALMAG_VALUE = FertilizerType.CALMAG.value


@dataclass
class CalmagMigrationReport:
    """Summary of the CalMag reclassification run."""

    scanned: int = 0
    reclassified: int = 0
    changed_keys: list[str] = field(default_factory=list)
    dry_run: bool = False


def migrate_fertilizer_calmag_type(db: StandardDatabase, *, dry_run: bool = False) -> CalmagMigrationReport:
    """Set ``fertilizer_type = "calmag"`` for name-matched legacy products."""
    report = CalmagMigrationReport(dry_run=dry_run)

    cursor = db.aql.execute(
        f"FOR doc IN {col.FERTILIZERS} RETURN {{ _key: doc._key, "
        "product_name: doc.product_name, fertilizer_type: doc.fertilizer_type }}"
    )

    for doc in cursor:
        report.scanned += 1
        key = doc.get("_key")
        name = doc.get("product_name") or ""
        current_type = doc.get("fertilizer_type")

        if current_type == _CALMAG_VALUE:
            continue
        if not matches_calmag_name(name):
            continue

        report.reclassified += 1
        report.changed_keys.append(key)
        logger.info(
            "fertilizer_calmag_reclassify",
            key=key,
            product_name=name,
            old_type=current_type,
            new_type=_CALMAG_VALUE,
            dry_run=dry_run,
        )

        if not dry_run:
            db.aql.execute(
                f"UPDATE @key WITH {{ fertilizer_type: @new_type }} IN {col.FERTILIZERS}",
                bind_vars={"key": key, "new_type": _CALMAG_VALUE},
            )

    logger.info(
        "fertilizer_calmag_migration_complete",
        scanned=report.scanned,
        reclassified=report.reclassified,
        dry_run=dry_run,
    )
    return report


def run_migrate_fertilizer_calmag_type(*, dry_run: bool = False) -> CalmagMigrationReport:
    """Entrypoint: resolve the DB connection and run the migration."""
    from app.common.dependencies import get_db

    return migrate_fertilizer_calmag_type(get_db(), dry_run=dry_run)


if __name__ == "__main__":
    run_migrate_fertilizer_calmag_type(dry_run="--dry-run" in sys.argv)
