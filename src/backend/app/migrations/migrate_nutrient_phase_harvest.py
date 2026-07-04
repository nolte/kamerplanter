"""Retire the abolished ``harvest`` phase on legacy nutrient-plan phase entries (#306).

Issue #306 removed ``PhaseName.HARVEST`` from the enum (feeding-harvest phases
became ``ripening``, the 0-0-0 flush became ``flushing``). No data migration
shipped with it, so ArangoDB volumes seeded before #306 still hold
``nutrient_plan_phase_entries`` documents with ``phase_name == "harvest"``.
Reading those documents strictly validates the retired enum value and raises a
``ValidationError``, which crashes the whole startup seed before it can repair
itself. This migration reclassifies the stale documents in place, following the
enum comment (``enums.py``): feeding harvest → ``ripening``, 0-0-0 flush →
``flushing``.

It is:

- **idempotent** — only documents still typed ``harvest`` are touched, so a
  re-run is a safe no-op (nothing else is scanned into a write);
- **non-destructive** — it only rewrites ``phase_name``, never deletes a
  document, and the field stays user-editable afterwards;
- **reportable & logged** — every reclassification is logged via structlog and
  the returned report summarises the change counts.

Run from the backend root::

    python -m app.migrations.migrate_nutrient_phase_harvest            # apply
    python -m app.migrations.migrate_nutrient_phase_harvest --dry-run  # report only
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.common.enums import PhaseName
from app.data_access.arango import collections as col

logger = structlog.get_logger()

_HARVEST_VALUE = "harvest"
_RIPENING_VALUE = PhaseName.RIPENING.value
_FLUSHING_VALUE = PhaseName.FLUSHING.value


@dataclass
class HarvestPhaseMigrationReport:
    """Summary of the retired-``harvest``-phase reclassification run."""

    scanned: int = 0
    reclassified: int = 0
    to_ripening: int = 0
    to_flushing: int = 0
    changed_keys: list[str] = field(default_factory=list)
    dry_run: bool = False


def _is_flush(npk_ratio: Any) -> bool:
    """True when the NPK ratio is absent or all-zero (a 0-0-0 flush phase)."""
    if not npk_ratio:
        return True
    try:
        return all(float(value) == 0.0 for value in npk_ratio)
    except (TypeError, ValueError) as exc:
        # Malformed npk_ratio — treat as feeding (ripening) rather than guessing a flush.
        logger.debug("nutrient_phase_harvest_malformed_npk", npk_ratio=npk_ratio, error=str(exc))
        return False


def migrate_nutrient_phase_harvest(db: StandardDatabase, *, dry_run: bool = False) -> HarvestPhaseMigrationReport:
    """Reclassify retired ``harvest`` phase entries to ``ripening`` or ``flushing``."""
    report = HarvestPhaseMigrationReport(dry_run=dry_run)

    cursor = db.aql.execute(
        f"FOR doc IN {col.NUTRIENT_PLAN_PHASE_ENTRIES} "
        "FILTER doc.phase_name == @harvest "
        "RETURN { _key: doc._key, npk_ratio: doc.npk_ratio }",
        bind_vars={"harvest": _HARVEST_VALUE},
    )

    for doc in cursor:
        report.scanned += 1
        key = doc.get("_key")
        new_phase = _FLUSHING_VALUE if _is_flush(doc.get("npk_ratio")) else _RIPENING_VALUE

        report.reclassified += 1
        report.changed_keys.append(key)
        if new_phase == _FLUSHING_VALUE:
            report.to_flushing += 1
        else:
            report.to_ripening += 1

        logger.info(
            "nutrient_phase_harvest_reclassify",
            key=key,
            old_phase=_HARVEST_VALUE,
            new_phase=new_phase,
            dry_run=dry_run,
        )

        if not dry_run:
            db.aql.execute(
                f"UPDATE @key WITH {{ phase_name: @new_phase }} IN {col.NUTRIENT_PLAN_PHASE_ENTRIES}",
                bind_vars={"key": key, "new_phase": new_phase},
            )

    logger.info(
        "nutrient_phase_harvest_migration_complete",
        scanned=report.scanned,
        reclassified=report.reclassified,
        to_ripening=report.to_ripening,
        to_flushing=report.to_flushing,
        dry_run=dry_run,
    )
    return report


def run_migrate_nutrient_phase_harvest(*, dry_run: bool = False) -> HarvestPhaseMigrationReport:
    """Entrypoint: resolve the DB connection and run the migration."""
    from app.common.dependencies import get_db

    return migrate_nutrient_phase_harvest(get_db(), dry_run=dry_run)


if __name__ == "__main__":
    run_migrate_nutrient_phase_harvest(dry_run="--dry-run" in sys.argv)
