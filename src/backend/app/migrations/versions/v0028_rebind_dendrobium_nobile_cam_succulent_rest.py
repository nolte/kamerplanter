"""v0028 — rebind Dendrobium nobile onto cam_succulent_rest (follow-up to #680).

The Steckbrief of *Dendrobium nobile* documents an obligate cool-dry winter rest as
the sole bloom trigger (``dormancy_required: true``). The seed, however, carried
``photosynthesis_type: c3``, so the attribute-driven resolver
(:func:`~app.migrations.perennial_binding.resolve_phase_sequence_name`) fell through to
Rule 5 and bound the species to ``evergreen_foliage_perennial`` — a cycle *without* a
winter rest (``dormancy_required: false``). That is a genuine lifecycle bug: the
rest phase that the bloom depends on was missing.

The companion seed fix sets ``photosynthesis_type: cam``, so fresh installs now fire
resolver Rule 3 (CAM) and bind to ``cam_succulent_rest`` (``dormancy_required: true``),
consistent with the CAM epiphyte orchids Cattleya hybrida / Phalaenopsis hybrida
(v0027). This migration converges EXISTING installs onto the same target: it re-points
the species' ``has_phase_sequence`` edge that still targets one of the generic blankets
(``evergreen_foliage_perennial`` — the pre-fix binding; defensively also
``indoor_default``) onto ``cam_succulent_rest``, or creates the edge when the species
has none yet.

The frozen :data:`_TARGET_SEQUENCE` mirrors the seed resolver's post-fix output but is
copied here so a later seed/resolver edit cannot silently change an already-applied
migration's behaviour (immutable migration contract, M-7).

Scope guard: an edge is only re-pointed when it currently targets one of the two
generic blankets — a species already bound to a *more precise* sequence (including a
prior ``cam_succulent_rest`` from a partial run) is never clobbered. Only Dendrobium
nobile is in scope; the accepted intra-sequence order compromise of ``cam_succulent_rest``
(flowering before winter_rest, while Dendrobium is biologically rest-before-flowering)
is out of scope — the decisive rest phase is present.

Idempotent (M-3): once the edge points at ``cam_succulent_rest`` it no longer targets a
blanket and is skipped, so a re-run is a no-op. Additive: only an edge's ``_to`` moves,
or a single edge is created; no phase, plant or history is touched. Dry-run (M-5)
computes the plan and writes nothing. Irreversible (M-6): the prior blanket target is
not retained.
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
#: ``evergreen_foliage_perennial`` is the pre-fix binding; ``indoor_default`` is a
#: defensive fallback for an even older install that never ran the v0022 sweep.
_BLANKET_SEQUENCES = frozenset({"indoor_default", "evergreen_foliage_perennial"})

#: Frozen species → fine-typed phase-sequence name. Mirrors the post-seed-fix output of
#: ``resolve_phase_sequence_name`` for Dendrobium nobile (CAM epiphyte orchid, Rule 3).
_TARGET_SEQUENCE: dict[str, str] = {
    "Dendrobium nobile": "cam_succulent_rest",
}


class RebindDendrobiumNobileCamSucculentRestMigration(Migration):
    version = "0028"
    name = "rebind_dendrobium_nobile_cam_succulent_rest"
    description = "Re-point Dendrobium nobile's generic-blanket edge onto cam_succulent_rest (#680)."
    reversible = False

    # ── read helpers (AQL-only, no-op-safe on an empty/fresh database) ────────

    def _scan(self, db: StandardDatabase, collection: str) -> list[dict[str, Any]]:
        """Return every document of ``collection`` (missing collection → empty list)."""
        if not db.has_collection(collection):
            return []
        return list(db.aql.execute(f"FOR d IN {collection} RETURN d"))

    # ── planning (pure, dry-run-safe) ─────────────────────────────────────────

    def _plan(self, db: StandardDatabase) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """Return ``(rebinds, inserts)``.

        ``rebinds`` = ``[{edge_key, to_id}]`` for existing edges that still target one of
        the two generic blankets; ``inserts`` = ``[{from_id, to_id}]`` for a scoped species
        that has no ``has_phase_sequence`` edge yet. A species already bound to a more
        precise sequence is left untouched.
        """
        sequences = self._scan(db, col.PHASE_SEQUENCES)
        seq_key_by_name = {s.get("name"): s["_key"] for s in sequences}
        seq_name_by_id = {f"{col.PHASE_SEQUENCES}/{s['_key']}": s.get("name") for s in sequences}
        species_key_by_name = {s.get("scientific_name"): s["_key"] for s in self._scan(db, col.SPECIES)}

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
                    continue  # already fine-typed (idempotent)
                # Scope guard: only move OFF a generic blanket, never a precise binding.
                if seq_name_by_id.get(current_to) in _BLANKET_SEQUENCES:
                    rebinds.append({"edge_key": edge["_key"], "to_id": target_id})

        return rebinds, inserts

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        rebinds, inserts = self._plan(db)
        changed = len(rebinds) + len(inserts)

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

        logger.info(
            "rebind_dendrobium_nobile_cam_succulent_rest",
            rebound=len(rebinds),
            created=len(inserts),
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=changed,
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            details={"rebound": len(rebinds), "created": len(inserts)},
        )


migration = RebindDendrobiumNobileCamSucculentRestMigration()
