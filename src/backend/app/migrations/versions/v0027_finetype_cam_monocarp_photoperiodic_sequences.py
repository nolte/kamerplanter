"""v0027 — fine-type the CAM/monocarpic/photoperiodic/palm-fern-geophyte cohorts (#616).

Epic #565 Phase 1 (#601 / v0022) moved the ~90 path-A perennials onto the generic
cyclic ``evergreen_foliage_perennial`` template, but deliberately left the CAM
succulents, monocarpic bromeliads, photoperiodic ornamentals and palm/fern/geophyte
cohorts on the generic ``evergreen_foliage_perennial`` / annual ``indoor_default``
blankets. This migration gives EXISTING installs the biologically precise sequences
seeded in ``phase_sequences.yaml`` (REQ-003 D9–D12, audit #576): it re-points each
``has_phase_sequence`` edge that still targets one of the two generic blankets
(``indoor_default`` / ``evergreen_foliage_perennial``) onto the fine-typed target —
or creates the edge when the species has none yet.

Fresh installs pick the same binding up from the attribute-driven seed resolver
(:func:`~app.migrations.perennial_binding.resolve_phase_sequence_name`); the frozen
:data:`_TARGET_SEQUENCE` mirrors that resolver's output for these cohorts but is
copied here so a later seed/resolver edit cannot silently change an already-applied
migration's behaviour (immutable migration contract, M-7).

Scope guard: an edge is only re-pointed when it currently targets one of the two
generic blankets — a species already bound to a *more precise* sequence (e.g. the WP-8
outdoor perennials on ``perennial_standard``/``evergreen_subshrub_rest`` from v0024) is
never clobbered. Cannabis (annual, short-day) is intentionally NOT re-typed: its
harvest-terminated ``indoor_default`` flow must not become a no-harvest ornamental cycle.

Idempotent (M-3): once an edge points at its fine-typed target it no longer targets a
blanket and is skipped, so a re-run is a no-op. Additive: only an edge's ``_to`` moves,
or a single edge is created; no phase, plant or history is touched. Dry-run (M-5)
computes the plan and writes nothing. Irreversible (M-6): the prior blanket target is
not retained.

NOTE (provisional version): ``v0024`` is the last version on ``develop`` at authoring
time; parallel lanes may also claim ``0025``. RENUMBER on merge if ``0025`` is taken
(rename the file, the ``version`` attribute and the test module in lockstep).
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

#: Frozen species → fine-typed phase-sequence name (audit #576 gap list, REQ-003 D9–D12).
#: Mirrors ``resolve_phase_sequence_name`` for these cohorts. WP-8 outdoor species (v0024)
#: and Cannabis are intentionally excluded.
_TARGET_SEQUENCE: dict[str, str] = {
    # -- D9a: CAM succulents with a cool-dry winter rest (20) --
    "Aloe vera": "cam_succulent_rest",
    "Cattleya hybrida": "cam_succulent_rest",
    "Ceropegia woodii": "cam_succulent_rest",
    "Crassula ovata": "cam_succulent_rest",
    "Curio rowleyanus": "cam_succulent_rest",
    "Dracaena angolensis": "cam_succulent_rest",
    "Dracaena trifasciata": "cam_succulent_rest",
    "Echeveria elegans": "cam_succulent_rest",
    "Gymnocalycium mihanovichii": "cam_succulent_rest",
    "Haworthiopsis fasciata": "cam_succulent_rest",
    "Hoya carnosa": "cam_succulent_rest",
    "Mammillaria spp.": "cam_succulent_rest",
    "Opuntia microdasys": "cam_succulent_rest",
    "Peperomia obtusifolia": "cam_succulent_rest",
    "Phalaenopsis hybrida": "cam_succulent_rest",
    "Rhipsalis baccifera": "cam_succulent_rest",
    "Sedum morganianum": "cam_succulent_rest",
    "Tillandsia usneoides": "cam_succulent_rest",
    "Yucca elephantipes": "cam_succulent_rest",
    "Zamioculcas zamiifolia": "cam_succulent_rest",
    # -- D9b: CAM double rest (Lithops / mesembs) (1) --
    "Lithops spp.": "cam_double_rest",
    # -- D10: Clonal monocarp bromeliads — terminal bloom + Kindel continuation (4) --
    "Aechmea fasciata": "clonal_monocarp",
    "Guzmania lingulata": "clonal_monocarp",
    "Neoregelia carolinae": "clonal_monocarp",
    "Vriesea splendens": "clonal_monocarp",
    # -- D11: Photoperiodic short-day ornamentals (11; cannabis excluded) --
    "Aphelandra squarrosa": "photoperiodic_ornamental",
    "Dahlia pinnata": "photoperiodic_ornamental",
    "Dahlia x cultorum": "photoperiodic_ornamental",
    "Euphorbia pulcherrima": "photoperiodic_ornamental",
    "Gardenia jasminoides": "photoperiodic_ornamental",
    "Jasminum polyanthum": "photoperiodic_ornamental",
    "Kalanchoe blossfeldiana": "photoperiodic_ornamental",
    "Kalanchoe daigremontiana": "photoperiodic_ornamental",
    "Rhododendron simsii": "photoperiodic_ornamental",
    "Schlumbergera truncata": "photoperiodic_ornamental",
    "Stephanotis floribunda": "photoperiodic_ornamental",
    # -- D12a: Evergreen palms (4) --
    "Chamaedorea elegans": "palm_evergreen",
    "Dypsis lutescens": "palm_evergreen",
    "Howea forsteriana": "palm_evergreen",
    "Livistona chinensis": "palm_evergreen",
    # -- D12b: Spore-based ferns (4) --
    "Adiantum raddianum": "fern_spore",
    "Asplenium nidus": "fern_spore",
    "Nephrolepis exaltata": "fern_spore",
    "Platycerium bifurcatum": "fern_spore",
    # -- D12c: Fine-grained geophytes (6; Allium cepa/sativum are WP-8, excluded) --
    "Clivia miniata": "geophyte_fine",
    "Cyclamen persicum": "geophyte_fine",
    "Hippeastrum hybridum": "geophyte_fine",
    "Oxalis triangularis": "geophyte_fine",
    "Tigridia pavonia": "geophyte_fine",
    "Zantedeschia aethiopica": "geophyte_fine",
}


class FinetypeCamMonocarpPhotoperiodicSequencesMigration(Migration):
    version = "0027"
    name = "finetype_cam_monocarp_photoperiodic_sequences"
    description = "Re-point generic-blanket edges of the CAM/monocarp/photoperiodic/palm-fern-geophyte cohorts (#616)."
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
        the two generic blankets; ``inserts`` = ``[{from_id, to_id}]`` for cohort species
        that have no ``has_phase_sequence`` edge yet. Species already bound to a more
        precise sequence are left untouched.
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
            "finetype_cam_monocarp_photoperiodic_sequences",
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


migration = FinetypeCamMonocarpPhotoperiodicSequencesMigration()
