"""v0021_heal_dangling_phase_current_key — repoint plants at live phase entries.

#579 error #2. Before #579 a PhaseSequence re-seed deleted and recreated every
entry, minting fresh ``_key``s each time (fixed in ``seed_phase_sequences`` — the
re-seed is now key-stable). Plants created against an earlier generation therefore
point their ``current_phase_key`` at a PhaseSequenceEntry ``_key`` that no longer
exists — a dangling key that makes ``create_plant`` reject the plant
(``Phase '…' is not part of the phase sequence of species '…'``) and leaves phase
transitions unable to resolve the current phase.

This one-time, idempotent, additive backfill (ADR-005 / NFR-016) heals every such
plant: for each plant whose ``current_phase_key`` resolves in *neither* key-space
(not a live PhaseSequenceEntry, not a live GrowthPhase), it finds the species'
PhaseSequence and repoints the plant — and its open phase-history entry — onto the
entry whose PhaseDefinition **name** matches the plant's current phase (anchored on
the open phase-history ``phase_name``, which survives a re-seed). Phase names are
unique within a sequence, so the match is unambiguous.

Plants whose key already resolves are skipped (idempotent, M-3): a re-run finds no
danglers. A plant with no resolvable sequence or no name anchor is left untouched
and reported, never guessed. Dry-run (M-5) counts danglers and writes nothing.
Irreversible (M-6): the prior dangling key is not retained, so there is no honest
inverse.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()


def open_phase_name(histories: list[dict[str, Any]]) -> str:
    """Return the phase name of a plant's current (open) phase-history entry.

    Prefers the open entry (``exited_at is None``); falls back to the most recent
    entry so a plant whose open entry was already closed can still be anchored.
    The stored ``phase_name`` survives a sequence re-seed, so it is the stable
    anchor for matching a dangling key back to a live entry.
    """
    open_entries = [h for h in histories if h.get("exited_at") is None]
    if open_entries:
        return open_entries[-1].get("phase_name") or ""
    if histories:
        return histories[-1].get("phase_name") or ""
    return ""


def plan_healed_key(
    phase_name: str,
    entries: list[dict[str, Any]],
    definitions_by_key: dict[str, dict[str, Any]],
) -> str | None:
    """Return the live entry ``_key`` whose definition name matches ``phase_name``.

    Matches by PhaseDefinition **name** (phase names are unique within a sequence)
    and, on the theoretical tie, the lowest ``sequence_order``. Returns ``None``
    when there is no name anchor or no matching entry — the plant is then reported
    unhealable rather than guessed.
    """
    if not phase_name:
        return None
    for entry in sorted(entries, key=lambda e: e.get("sequence_order", 0)):
        defn = definitions_by_key.get(entry.get("phase_definition_key", ""))
        if defn and defn.get("name") == phase_name:
            return entry.get("_key")
    return None


class HealDanglingPhaseCurrentKeyMigration(Migration):
    version = "0021"
    name = "heal_dangling_phase_current_key"
    description = (
        "Repoint plants whose current_phase_key dangles onto the live PhaseSequenceEntry matched by phase name (#579)."
    )
    reversible = False

    # ── read helpers (AQL-only, no-op-safe on an empty database) ──────────────

    def _scan(self, db: StandardDatabase, collection: str) -> list[dict[str, Any]]:
        """Return every document of ``collection`` (empty cursor → empty list)."""
        return list(db.aql.execute(f"FOR d IN {collection} RETURN d"))

    def _sequence_key_for_species(self, edges: list[dict[str, Any]], species_key: str) -> str | None:
        """Resolve a species' PhaseSequence key via the has_phase_sequence edge."""
        species_id = f"{col.SPECIES}/{species_key}"
        for edge in edges:
            if edge.get("_from") == species_id:
                to = edge.get("_to") or ""
                return to.split("/", 1)[1] if "/" in to else None
        return None

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        plants = self._scan(db, col.PLANT_INSTANCES)
        histories = self._scan(db, col.PHASE_HISTORIES)
        entries = self._scan(db, col.PHASE_SEQUENCE_ENTRIES)
        definitions = self._scan(db, col.PHASE_DEFINITIONS)
        growth_phases = self._scan(db, col.GROWTH_PHASES)
        seq_edges = self._scan(db, col.HAS_PHASE_SEQUENCE)

        # A key resolves when it is a live PhaseSequenceEntry OR a live GrowthPhase;
        # anything else on a plant's current_phase_key is dangling (#579 error #2).
        live_keys: set[str] = {e["_key"] for e in entries} | {g["_key"] for g in growth_phases}

        defs_by_key: dict[str, dict[str, Any]] = {d["_key"]: d for d in definitions}
        entries_by_seq: dict[str, list[dict[str, Any]]] = {}
        for entry in entries:
            entries_by_seq.setdefault(entry.get("phase_sequence_key", ""), []).append(entry)
        histories_by_plant: dict[str, list[dict[str, Any]]] = {}
        for h in histories:
            histories_by_plant.setdefault(h.get("plant_instance_key", ""), []).append(h)

        scanned = 0
        changed = 0
        healed: list[dict[str, str]] = []
        unhealable: list[str] = []

        for plant in plants:
            current = plant.get("current_phase_key")
            if not current or current in live_keys:
                continue

            # Dangling: neither a live entry nor a live growth phase.
            scanned += 1
            species_key = plant.get("species_key") or ""
            seq_key = self._sequence_key_for_species(seq_edges, species_key) if species_key else None
            if not seq_key:
                unhealable.append(plant["_key"])
                continue

            plant_histories = histories_by_plant.get(plant["_key"], [])
            phase_name = open_phase_name(plant_histories)
            new_key = plan_healed_key(phase_name, entries_by_seq.get(seq_key, []), defs_by_key)
            if not new_key or new_key == current:
                unhealable.append(plant["_key"])
                continue

            changed += 1
            healed.append({"plant": plant["_key"], "from": current, "to": new_key})
            if dry_run:
                continue

            db.aql.execute(
                f"UPDATE {{_key: @key, current_phase_key: @new_key}} IN {col.PLANT_INSTANCES}",
                bind_vars={"key": plant["_key"], "new_key": new_key},
            )
            for h in plant_histories:
                if h.get("exited_at") is None and h.get("phase_key") == current:
                    db.aql.execute(
                        f"UPDATE {{_key: @key, phase_key: @new_key}} IN {col.PHASE_HISTORIES}",
                        bind_vars={"key": h["_key"], "new_key": new_key},
                    )

        logger.info(
            "heal_dangling_phase_current_key",
            scanned=scanned,
            changed=changed,
            unhealable=len(unhealable),
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=dry_run,
            details={"healed": healed, "unhealable": unhealable},
        )


migration = HealDanglingPhaseCurrentKeyMigration()
