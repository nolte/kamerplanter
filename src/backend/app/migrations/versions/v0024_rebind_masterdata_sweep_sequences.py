"""v0024 — rebind the WP-8 master-data-sweep species onto their precise phase sequence (#565).

WP-8 gave the outdoor perennials/biennials that declared ``dormancy_required`` without a
phase model — and the previously model-less perennial herbs — a proper cyclic lifecycle in
``lifecycles_outdoor.yaml``, each bound to a template whose phase set includes a real
dormancy phase. Fresh installs pick that binding up from the seed. This migration repairs
EXISTING installs, where these species were left on the generic Phase-1 binding
(``evergreen_foliage_perennial`` via v0022) or on the annual ``indoor_default`` blanket
(the biennial onion), by re-pointing each ``has_phase_sequence`` edge onto the precise
WP-8 sequence — or creating the edge if the species never had one.

The species→sequence mapping is frozen in :data:`_TARGET_SEQUENCE` (immutable migration
contract, M-7): it mirrors the ``phase_sequence`` fields the WP-8 seed sets, but is copied
here so a later seed edit cannot silently change an already-applied migration's behaviour.

Idempotent (M-3): an edge already on the target sequence is skipped, so a re-run is a
no-op. Additive: only an edge's ``_to`` moves (or a single edge is created); no phase,
plant, or history is touched. Dry-run (M-5) computes the plan and writes nothing.
Irreversible (M-6): the prior target is not retained.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: Frozen WP-8 species → target phase-sequence name. Mirrors ``lifecycles_outdoor.yaml``.
_TARGET_SEQUENCE: dict[str, str] = {
    "Anemone hupehensis": "perennial_standard",
    "Astilbe chinensis": "perennial_standard",
    "Clematis spp.": "perennial_standard",
    "Delphinium elatum": "perennial_standard",
    "Echinacea purpurea": "perennial_standard",
    "Cornus mas": "perennial_fruit_early",
    "Asparagus officinalis": "perennial_early_harvest",
    "Allium sativum": "perennial_harvest_veg",
    "Mentha piperita": "perennial_harvest_veg",
    "Allium cepa": "biennial_vernalization",
    "Buxus sempervirens": "evergreen_subshrub_rest",
    "Lavandula angustifolia": "evergreen_subshrub_rest",
    "Salvia rosmarinus": "evergreen_subshrub_rest",
    "Salvia officinalis": "evergreen_subshrub_rest",
    "Thymus vulgaris": "evergreen_subshrub_rest",
}


class RebindMasterdataSweepSequencesMigration(Migration):
    version = "0024"
    name = "rebind_masterdata_sweep_sequences"
    description = "Re-point has_phase_sequence edges of the WP-8 sweep species onto their precise sequence (#565)."
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

        ``rebinds`` = ``[{edge_key, to_id}]`` for existing edges pointing at the
        wrong sequence; ``inserts`` = ``[{from_id, to_id}]`` for WP-8 species that
        have no ``has_phase_sequence`` edge yet.
        """
        seq_key_by_name = {s.get("name"): s["_key"] for s in self._scan(db, col.PHASE_SEQUENCES)}
        species_key_by_name = {s.get("scientific_name"): s["_key"] for s in self._scan(db, col.SPECIES)}

        edges_by_from: dict[str, list[dict[str, Any]]] = {}
        for edge in self._scan(db, col.HAS_PHASE_SEQUENCE):
            edges_by_from.setdefault(edge.get("_from", ""), []).append(edge)

        rebinds: list[dict[str, str]] = []
        inserts: list[dict[str, str]] = []

        for scientific_name, target_name in _TARGET_SEQUENCE.items():
            species_key = species_key_by_name.get(scientific_name)
            target_key = seq_key_by_name.get(target_name)
            # Skip cleanly when the species or the (WP-8-seeded) sequence is absent.
            if not species_key or not target_key:
                continue
            from_id = f"{col.SPECIES}/{species_key}"
            target_id = f"{col.PHASE_SEQUENCES}/{target_key}"
            existing = edges_by_from.get(from_id, [])
            if not existing:
                inserts.append({"from_id": from_id, "to_id": target_id})
                continue
            for edge in existing:
                if edge.get("_to") != target_id:
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
            "rebind_masterdata_sweep_sequences",
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


migration = RebindMasterdataSweepSequencesMigration()
