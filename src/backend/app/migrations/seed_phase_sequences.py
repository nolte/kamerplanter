"""Seed PhaseDefinitions and PhaseSequences from YAML.

Creates reusable phase definitions and sequence templates that can be
referenced by LifecycleConfigs.  Idempotent — safe to run multiple times.
"""

import structlog

from app.common.dependencies import get_phase_sequence_repo
from app.common.enums import CycleType, PhotoperiodType, StressTolerance
from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def run_seed_phase_sequences() -> None:
    """Seed PhaseDefinitions and PhaseSequences from YAML."""
    repo = get_phase_sequence_repo()
    data = load_yaml("phase_sequences.yaml")

    # ── Step 1: Seed PhaseDefinitions ──
    def_key_map: dict[str, str] = {}  # name -> _key
    defs_created = 0
    defs_updated = 0

    for d in data.get("phase_definitions", []):
        name = d["name"]
        existing = repo.get_definition_by_name(name)

        defn = PhaseDefinition(
            name=name,
            display_name=d.get("display_name", ""),
            display_name_de=d.get("display_name_de", ""),
            description=d.get("description", ""),
            description_de=d.get("description_de", ""),
            typical_duration_days=d["typical_duration_days"],
            stress_tolerance=StressTolerance(d.get("stress_tolerance", "medium")),
            watering_interval_days=d.get("watering_interval_days"),
            illustration=d.get("illustration", ""),
            tags=d.get("tags", []),
            is_system=d.get("is_system", True),
        )

        if existing:
            repo.update_definition(existing.key or "", defn)
            def_key_map[name] = existing.key or ""
            defs_updated += 1
        else:
            created = repo.create_definition(defn)
            def_key_map[name] = created.key or ""
            defs_created += 1

    logger.info(
        "phase_definitions_seeded",
        created=defs_created,
        updated=defs_updated,
    )

    # ── Step 2: Seed PhaseSequences + Entries ──
    seqs_created = 0
    seqs_updated = 0

    # Build a lookup of existing sequences by name
    existing_seqs, _ = repo.get_all_sequences(0, 200)
    seq_by_name: dict[str, PhaseSequence] = {s.name: s for s in existing_seqs}

    for s in data.get("phase_sequences", []):
        name = s["name"]
        existing = seq_by_name.get(name)

        seq = PhaseSequence(
            name=name,
            display_name=s.get("display_name", ""),
            display_name_de=s.get("display_name_de", ""),
            description=s.get("description", ""),
            description_de=s.get("description_de", ""),
            cycle_type=CycleType(s.get("cycle_type", "annual")),
            is_repeating=s.get("is_repeating", False),
            cycle_restart_entry_order=s.get("cycle_restart_entry_order"),
            dormancy_required=s.get("dormancy_required", False),
            vernalization_required=s.get("vernalization_required", False),
            vernalization_min_days=s.get("vernalization_min_days"),
            photoperiod_type=PhotoperiodType(s.get("photoperiod_type", "day_neutral")),
            critical_day_length_hours=s.get("critical_day_length_hours"),
            tags=s.get("tags", []),
            is_system=s.get("is_system", True),
        )

        if existing:
            repo.update_sequence(existing.key or "", seq)
            seq_key = existing.key or ""
            seqs_updated += 1
        else:
            created_seq = repo.create_sequence(seq)
            seq_key = created_seq.key or ""
            seqs_created += 1

        # ── Key-stable entry regeneration (#579) ──
        # A re-seed MUST preserve each entry's ``_key`` so that a plant's
        # ``current_phase_key`` (a PhaseSequenceEntry key) never dangles across
        # re-seeds. Match existing entries to the YAML by ``phase_definition_key``
        # (unique within a sequence — no sequence repeats a phase name) and update
        # in place; only genuinely new phases are inserted and genuinely dropped
        # phases are deleted.
        existing_entries = repo.get_entries_for_sequence(seq_key)
        entries_by_def: dict[str, PhaseSequenceEntry] = {
            e.phase_definition_key: e for e in existing_entries if e.phase_definition_key
        }

        entries_data = s.get("entries", [])
        seen_def_keys: set[str] = set()
        for e in entries_data:
            phase_def_key = def_key_map.get(e["phase_name"], "")
            if not phase_def_key:
                logger.warning(
                    "phase_definition_not_found",
                    phase_name=e["phase_name"],
                    sequence=name,
                )
                continue
            seen_def_keys.add(phase_def_key)

            entry = PhaseSequenceEntry(
                phase_sequence_key=seq_key,
                phase_definition_key=phase_def_key,
                sequence_order=e["sequence_order"],
                override_duration_days=e.get("override_duration_days"),
                is_terminal=e.get("is_terminal", False),
                allows_harvest=e.get("allows_harvest", False),
                is_recurring=e.get("is_recurring", False),
            )

            prior = entries_by_def.get(phase_def_key)
            if prior is not None:
                # Preserve the existing ``_key`` (key-stable update).
                repo.update_entry(prior.key or "", entry)
            else:
                repo.create_entry(entry)

        # Remove entries for phases no longer part of the sequence.
        for def_key, prior in entries_by_def.items():
            if def_key not in seen_def_keys:
                repo.delete_entry(prior.key or "")

        logger.info(
            "phase_sequence_seeded",
            name=name,
            entries=len(entries_data),
        )

    logger.info(
        "seed_phase_sequences_complete",
        sequences_created=seqs_created,
        sequences_updated=seqs_updated,
    )
