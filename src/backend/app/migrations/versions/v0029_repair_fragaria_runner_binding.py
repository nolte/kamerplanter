"""v0029 — repair the strawberry runner binding v0022 missed, and its allelopathy sign.

Two follow-ups for *Fragaria x ananassa* that earlier passes left on existing installs:

1. **Phase-sequence binding.** v0022 (#565) was meant to move runner-propagated stauden
   (strawberry is the flagship) off the annual ``indoor_default`` blanket onto the cyclic
   ``perennial_runner`` template. On installs where the strawberry's ``lifecycle_config``
   did not yet carry ``cycle_type: perennial`` at the moment v0022 ran, its
   :func:`~app.migrations.perennial_binding.resolve_perennial_sequence_name` classifier
   returned ``None`` (its ``cycle_type != perennial`` guard fires *before* the runner
   check), so the edge was skipped and stayed on ``indoor_default`` — the app then shows
   the annual Cannabis-style ``…flushing → ripening`` flow instead of the 7-phase
   establishment→sprouting-restart→…→dormancy staude cycle. v0027 fine-typed the
   CAM/monocarp/photoperiodic/palm-fern-geophyte cohorts but not the runner cohort, so
   the gap survived. This migration re-points the edge that still targets a generic
   blanket onto ``perennial_runner`` (or creates it when the species has none).

2. **Allelopathy sign.** The seed carried ``allelopathy_score: 0.1`` for strawberry, but
   the Steckbrief documents a *negative* autotoxicity (phenolic-acid replant problem /
   Bodenmüdigkeit; §1.1). The companion seed fix sets ``-0.4``; this migration converges
   existing installs by correcting the exact stored error value ``0.1 → -0.4``.

The frozen constants mirror the post-fix seed output but are copied here so a later
seed/resolver edit cannot silently change an already-applied migration's behaviour
(immutable migration contract, M-7).

Scope guard: an edge is only re-pointed when it currently targets one of the two generic
blankets — a species already on a more precise sequence (incl. a prior ``perennial_runner``
from a partial run) is never clobbered. The allelopathy fix only fires when the stored
value is exactly the documented error ``0.1`` (both endpoints pinned), so a deliberate
third value is left untouched.

Idempotent (M-3): once the edge points at ``perennial_runner`` and the score is ``-0.4``,
neither branch matches, so a re-run is a no-op. Additive: only the edge's ``_to`` moves
(or one edge is created) and one scalar field is corrected; no phase, plant or history is
touched. Dry-run (M-5) computes the plan and writes nothing. Irreversible (M-6): neither
the prior blanket target nor the prior score is retained.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: The two generic blanket sequences an edge may be re-pointed *from* (scope guard).
_BLANKET_SEQUENCES = frozenset({"indoor_default", "evergreen_foliage_perennial"})

#: Frozen species → phase-sequence name. Mirrors ``resolve_phase_sequence_name`` output
#: for the runner cohort (strawberry, #541).
_TARGET_SEQUENCE: dict[str, str] = {
    "Fragaria x ananassa": "perennial_runner",
}

#: Frozen allelopathy corrections: species → (stored error value, corrected value). Both
#: endpoints pinned so the fix can neither re-fire nor swallow an unrelated future value.
_ALLELOPATHY_FIX: dict[str, tuple[float, float]] = {
    "Fragaria x ananassa": (0.1, -0.4),
}

#: Float tolerance for matching the pinned stored error value.
_EPS = 1e-9


class RepairFragariaRunnerBindingMigration(Migration):
    version = "0029"
    name = "repair_fragaria_runner_binding"
    description = "Re-point strawberry's blanket edge onto perennial_runner and fix its allelopathy sign (#541/#680)."
    reversible = False

    # ── read helpers (AQL-only, no-op-safe on an empty/fresh database) ────────

    def _scan(self, db: StandardDatabase, collection: str) -> list[dict[str, Any]]:
        """Return every document of ``collection`` (missing collection → empty list)."""
        if not db.has_collection(collection):
            return []
        return list(db.aql.execute(f"FOR d IN {collection} RETURN d"))

    # ── planning (pure, dry-run-safe) ─────────────────────────────────────────

    def _plan(self, db: StandardDatabase) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, Any]]]:
        """Return ``(rebinds, inserts, attr_fixes)``.

        ``rebinds`` = ``[{edge_key, to_id}]`` for edges still on a generic blanket;
        ``inserts`` = ``[{from_id, to_id}]`` for a scoped species with no edge yet;
        ``attr_fixes`` = ``[{species_key, allelopathy_score}]`` for species whose stored
        allelopathy score equals the pinned error value.
        """
        species_docs = self._scan(db, col.SPECIES)
        species_key_by_name = {s.get("scientific_name"): s["_key"] for s in species_docs}
        species_by_name = {s.get("scientific_name"): s for s in species_docs}

        sequences = self._scan(db, col.PHASE_SEQUENCES)
        seq_key_by_name = {s.get("name"): s["_key"] for s in sequences}
        seq_name_by_id = {f"{col.PHASE_SEQUENCES}/{s['_key']}": s.get("name") for s in sequences}

        edges_by_from: dict[str, list[dict[str, Any]]] = {}
        for edge in self._scan(db, col.HAS_PHASE_SEQUENCE):
            edges_by_from.setdefault(edge.get("_from", ""), []).append(edge)

        rebinds: list[dict[str, str]] = []
        inserts: list[dict[str, str]] = []

        for scientific_name, target_name in _TARGET_SEQUENCE.items():
            species_key = species_key_by_name.get(scientific_name)
            target_key = seq_key_by_name.get(target_name)
            # Skip cleanly when the species or the target sequence is absent (unseeded).
            if not species_key or not target_key:
                continue
            from_id = f"{col.SPECIES}/{species_key}"
            target_id = f"{col.PHASE_SEQUENCES}/{target_key}"
            existing = edges_by_from.get(from_id, [])
            if not existing:
                inserts.append({"from_id": from_id, "to_id": target_id})
                continue
            for edge in existing:
                current_to = edge.get("_to", "")
                if current_to == target_id:
                    continue  # already bound (idempotent)
                # Scope guard: only move OFF a generic blanket, never a precise binding.
                if seq_name_by_id.get(current_to) in _BLANKET_SEQUENCES:
                    rebinds.append({"edge_key": edge["_key"], "to_id": target_id})

        attr_fixes: list[dict[str, Any]] = []
        for scientific_name, (error_value, corrected_value) in _ALLELOPATHY_FIX.items():
            species = species_by_name.get(scientific_name)
            if species is None:
                continue
            current = species.get("allelopathy_score")
            if current is not None and abs(float(current) - error_value) < _EPS:
                attr_fixes.append({"species_key": species["_key"], "allelopathy_score": corrected_value})

        return rebinds, inserts, attr_fixes

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        rebinds, inserts, attr_fixes = self._plan(db)
        changed = len(rebinds) + len(inserts) + len(attr_fixes)

        if not dry_run:
            for item in rebinds:
                db.aql.execute(
                    f"UPDATE {{_key: @key, _to: @to_id}} IN {col.HAS_PHASE_SEQUENCE}",
                    bind_vars={"key": item["edge_key"], "to_id": item["to_id"]},
                )
            for item in inserts:
                db.aql.execute(
                    f"INSERT {{_from: @from_id, _to: @to_id}} INTO {col.HAS_PHASE_SEQUENCE}",
                    bind_vars={"from_id": item["from_id"], "to_id": item["to_id"]},
                )
            for item in attr_fixes:
                db.aql.execute(
                    f"UPDATE {{_key: @key, allelopathy_score: @score}} IN {col.SPECIES}",
                    bind_vars={"key": item["species_key"], "score": item["allelopathy_score"]},
                )

        logger.info(
            "repair_fragaria_runner_binding",
            rebound=len(rebinds),
            created=len(inserts),
            allelopathy_fixed=len(attr_fixes),
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=changed,
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            details={"rebound": len(rebinds), "created": len(inserts), "allelopathy_fixed": len(attr_fixes)},
        )


migration = RepairFragariaRunnerBindingMigration()
