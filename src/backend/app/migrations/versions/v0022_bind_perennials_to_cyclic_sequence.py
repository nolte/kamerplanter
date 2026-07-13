"""v0022 — bind Path-A perennials to a cyclic phase sequence (#565, WP-1/E2).

Before #565 every indoor species — perennials included — was blanket-linked to the
annual ``indoor_default`` PhaseSequence, which has NO terminal phase and NO cycle
restart: the perennial's REQ-003 cycle was therefore inert (it ran once and stopped;
the strawberry symptom of #541). The seed now routes perennials onto a cyclic
sequence for fresh installs; this migration repairs EXISTING installs by re-pointing
each ``has_phase_sequence`` edge that still targets ``indoor_default`` for an
effectively-perennial species onto the matching repeating perennial sequence:

* runner-propagated stauden (strawberry, ``Fragaria x ananassa``) → ``perennial_runner``
  (E4: once-only ``establishment`` + yearly ``sprouting`` restart, dormancy terminal);
* every other polycarpic perennial → ``evergreen_foliage_perennial``.

Monocarpic and non-perennial species are left on ``indoor_default`` (the former need
the clonal-pup template, a later-phase sweep). The classification is the single shared
:func:`resolve_perennial_sequence_name` used by the seed, so seed and migration cannot
drift (ADR-006 E2).

Idempotent (M-3): once an edge points at the perennial sequence it no longer targets
``indoor_default`` and is skipped, so a re-run is a no-op. Additive — only the edge's
``_to`` moves; no phase, plant or history is touched. Dry-run (M-5) computes the plan
and writes nothing. Irreversible (M-6): the prior blanket target is not retained.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.perennial_binding import INDOOR_DEFAULT_SEQUENCE, resolve_perennial_sequence_name

logger = structlog.get_logger()


class BindPerennialsToCyclicSequenceMigration(Migration):
    version = "0022"
    name = "bind_perennials_to_cyclic_sequence"
    description = "Re-point indoor_default edges of perennial species onto a cyclic phase sequence (#565)."
    reversible = False

    # ── read helpers (AQL-only, no-op-safe on an empty/fresh database) ────────

    def _scan(self, db: StandardDatabase, collection: str) -> list[dict[str, Any]]:
        """Return every document of ``collection`` (missing collection → empty list)."""
        if not db.has_collection(collection):
            return []
        return list(db.aql.execute(f"FOR d IN {collection} RETURN d"))

    # ── planning (pure, dry-run-safe) ─────────────────────────────────────────

    def _plan(self, db: StandardDatabase) -> list[dict[str, str]]:
        """Return ``[{edge_key, to_id}]`` for every indoor_default edge to re-point.

        Joins the ``has_phase_sequence`` edges to the species' scientific name and its
        lifecycle cycle/flowering attributes, then applies the shared classifier. Only
        edges that currently target ``indoor_default`` and resolve to a *different*
        perennial sequence are planned.
        """
        sequences = self._scan(db, col.PHASE_SEQUENCES)
        seq_key_by_name = {s.get("name"): s["_key"] for s in sequences}
        seq_name_by_id = {f"{col.PHASE_SEQUENCES}/{s['_key']}": s.get("name") for s in sequences}
        indoor_key = seq_key_by_name.get(INDOOR_DEFAULT_SEQUENCE)
        if not indoor_key:
            return []
        indoor_id = f"{col.PHASE_SEQUENCES}/{indoor_key}"

        species_name_by_key = {s["_key"]: s.get("scientific_name", "") for s in self._scan(db, col.SPECIES)}
        lifecycle_by_species: dict[str, dict[str, Any]] = {}
        for lc in self._scan(db, col.LIFECYCLE_CONFIGS):
            species_key = lc.get("species_key")
            if species_key:
                lifecycle_by_species[species_key] = lc

        plan: list[dict[str, str]] = []
        for edge in self._scan(db, col.HAS_PHASE_SEQUENCE):
            # Only edges still on the annual blanket are candidates (idempotency).
            if seq_name_by_id.get(edge.get("_to", "")) != INDOOR_DEFAULT_SEQUENCE:
                continue
            from_id = edge.get("_from") or ""
            species_key = from_id.split("/", 1)[1] if "/" in from_id else ""
            lifecycle = lifecycle_by_species.get(species_key)
            if lifecycle is None:
                continue
            target_name = resolve_perennial_sequence_name(
                species_name_by_key.get(species_key, ""),
                lifecycle.get("cycle_type"),
                lifecycle.get("flowering_strategy"),
            )
            if not target_name:
                continue
            target_key = seq_key_by_name.get(target_name)
            if not target_key:
                continue
            target_id = f"{col.PHASE_SEQUENCES}/{target_key}"
            if target_id == indoor_id:
                continue
            plan.append({"edge_key": edge["_key"], "to_id": target_id})
        return plan

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        plan = self._plan(db)
        scanned = len(plan)

        if not dry_run:
            for item in plan:
                db.aql.execute(
                    f"UPDATE {{_key: @key, _to: @to_id}} IN {col.HAS_PHASE_SEQUENCE}",
                    bind_vars={"key": item["edge_key"], "to_id": item["to_id"]},
                )

        logger.info("bind_perennials_to_cyclic_sequence", scanned=scanned, changed=scanned, dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else scanned,
            dry_run=dry_run,
            details={"rebound": scanned},
        )


migration = BindPerennialsToCyclicSequenceMigration()
