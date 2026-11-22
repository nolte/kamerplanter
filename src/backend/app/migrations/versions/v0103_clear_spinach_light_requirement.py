"""v0103 — clear the unsourced seeded ``light_requirement`` of spinach (#2516, E-10).

The Steckbrief of *Spinacia oleracea* used to classify the species as ``full_sun``,
although its only source (RHS, "Spinach: Grow your own") names "sun or partial
shade" with equal weight — the stage was an interpretation, not a sourced value.
Under the operator rule E-10 an unsourced agronomic value stays ``null``, so the
Steckbrief now carries ``DATEN FEHLEN`` and the seed ``plant_info_outdoor_2.yaml``
``light_requirement: null``.

That seed change alone does not reach an installation that was already seeded: the
plant-info seed writes species with the repository's partial update
(``exclude_none``), so a ``null`` in the YAML is simply absent from the patch and the
stored ``full_sun`` survives every later seed run. This migration converges EXISTING
installs onto the seed: it sets ``light_requirement`` to ``null`` on the scoped
species row.

The correction table :data:`_CORRECTIONS` is frozen here so a later seed edit cannot
change an already-applied migration's behaviour (immutable migration contract, M-7).

Scope guard: a row is only touched when it is a **global seed row** (``origin ==
"system"`` and no owning tenant) **and** still carries exactly the retired seed value
(``full_sun``). A tenant-owned spinach row, or a value a platform admin has since set
to something else, is never clobbered.

Idempotent (M-3): once the value is ``null`` the row no longer matches and a re-run is
a no-op. Additive in effect: one attribute of one row is reset; nothing else is
touched. Dry-run (M-5) computes the plan and writes nothing. Irreversible (M-6): the
retired value was unsourced, so restoring it would re-introduce the defect.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: Frozen ``scientific_name → retired seed value`` of ``light_requirement`` (#2516).
_CORRECTIONS: dict[str, str] = {
    "Spinacia oleracea": "full_sun",
}

#: Provenance value of a curated seed row (``DataOrigin.SYSTEM``), frozen here (M-7).
_SYSTEM_ORIGIN = "system"


class ClearSpinachLightRequirementMigration(Migration):
    version = "0103"
    name = "clear_spinach_light_requirement"
    description = "Reset the unsourced seeded light_requirement of Spinacia oleracea to null (#2516, E-10)."
    reversible = False

    # ── read helpers (AQL-only, no-op-safe on an empty/fresh database) ────────

    def _scan(self, db: StandardDatabase) -> list[dict[str, Any]]:
        """Return every species document (missing collection → empty list)."""
        if not db.has_collection(col.SPECIES):
            return []
        return list(cast(Cursor, db.aql.execute(f"FOR d IN {col.SPECIES} RETURN d")))

    # ── planning (pure, dry-run-safe) ─────────────────────────────────────────

    def _plan(self, db: StandardDatabase) -> list[str]:
        """Return the keys of the global seed rows that still carry a retired value."""
        keys: list[str] = []
        for doc in self._scan(db):
            retired = _CORRECTIONS.get(doc.get("scientific_name", ""))
            if retired is None:
                continue
            if doc.get("tenant_key") or doc.get("origin") != _SYSTEM_ORIGIN:
                continue  # tenant-owned or user-created — never ours to reset
            if doc.get("light_requirement") != retired:
                continue  # already null (idempotent) or deliberately changed since
            keys.append(doc["_key"])
        return keys

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        keys = self._plan(db)

        if not dry_run:
            for key in keys:
                db.aql.execute(
                    f"UPDATE {{_key: @key, light_requirement: null}} IN {col.SPECIES} OPTIONS {{keepNull: true}}",
                    bind_vars={"key": key},
                )

        logger.info("clear_spinach_light_requirement", cleared=len(keys), dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(keys),
            changed=0 if dry_run else len(keys),
            dry_run=dry_run,
            details={"cleared": len(keys)},
        )


migration = ClearSpinachLightRequirementMigration()
