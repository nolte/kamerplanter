"""Seed lifecycle configs and growth phases for outdoor species from YAML."""

import structlog

from app.common.dependencies import get_db, get_lifecycle_repo, get_phase_sequence_repo
from app.common.enums import CycleType, PhotoperiodType, StressTolerance
from app.data_access.arango import collections as col
from app.domain.engines.resource_profile_generator import ResourceProfileGenerator
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def _build_sequence_name_map() -> dict[str, str]:
    """Build a name->key lookup for PhaseSequences."""
    ps_repo = get_phase_sequence_repo()
    seqs, _ = ps_repo.get_all_sequences(0, 200)
    return {s.name: s.key or "" for s in seqs}


def _ensure_has_phase_sequence_edge(
    species_key: str,
    phase_sequence_key: str,
) -> bool:
    """Create HAS_PHASE_SEQUENCE edge if it does not exist yet.

    Returns True if a new edge was created, False if it already existed.
    """
    db = get_db()
    species_id = f"{col.SPECIES}/{species_key}"
    seq_id = f"{col.PHASE_SEQUENCES}/{phase_sequence_key}"

    existing = list(
        db.aql.execute(
            "FOR e IN @@edge_col FILTER e._from == @from_id AND e._to == @to_id RETURN 1",
            bind_vars={
                "@edge_col": col.HAS_PHASE_SEQUENCE,
                "from_id": species_id,
                "to_id": seq_id,
            },
        )
    )
    if existing:
        return False

    edge_col = db.collection(col.HAS_PHASE_SEQUENCE)
    edge_col.insert({"_from": species_id, "_to": seq_id})
    return True


def run_seed_lifecycles_outdoor() -> None:
    """Create lifecycle configs + growth phases for species that don't have one yet."""
    repo = get_lifecycle_repo()
    species_data = load_yaml("species.yaml")
    profile_gen = ResourceProfileGenerator.from_yaml_phases(species_data.get("default_phases", []))
    data = load_yaml("lifecycles_outdoor.yaml")
    seq_map = _build_sequence_name_map()

    entries = data.get("lifecycles", [])
    created = 0
    skipped = 0

    for entry in entries:
        species_key = entry["species_key"]

        # Skip if lifecycle already exists for this species
        existing = repo.get_lifecycle_by_species(species_key)
        if existing:
            skipped += 1
            continue

        lc = LifecycleConfig(
            species_key=species_key,
            cycle_type=CycleType(entry["cycle_type"]),
            typical_lifespan_years=entry.get("typical_lifespan_years"),
            dormancy_required=entry.get("dormancy_required", False),
            vernalization_required=entry.get("vernalization_required", False),
            vernalization_min_days=entry.get("vernalization_min_days"),
            photoperiod_type=PhotoperiodType(entry.get("photoperiod_type", "day_neutral")),
            cycle_restart_phase_order=entry.get("cycle_restart_phase_order"),
        )
        created_lc = repo.create_lifecycle(lc)
        lc_key = created_lc.key or ""

        # Link to phase sequence if specified
        ps_name = entry.get("phase_sequence")
        ps_key: str = ""
        if ps_name:
            ps_key = seq_map.get(ps_name, "")
            if ps_key:
                created_lc.phase_sequence_key = ps_key
                repo.update_lifecycle(lc_key, created_lc)
            else:
                logger.warning(
                    "phase_sequence_not_found",
                    species_key=species_key,
                    phase_sequence=ps_name,
                )

        # Create HAS_PHASE_SEQUENCE edge (species -> phase_sequence)
        if ps_key and _ensure_has_phase_sequence_edge(species_key, ps_key):
            logger.info(
                "has_phase_sequence_edge_created",
                species_key=species_key,
                sequence=ps_name,
            )

        for phase_data in entry.get("phases", []):
            phase = GrowthPhase(
                name=phase_data["name"],
                display_name=phase_data.get("display_name", ""),
                lifecycle_key=lc_key,
                typical_duration_days=phase_data["typical_duration_days"],
                sequence_order=phase_data["sequence_order"],
                is_terminal=phase_data.get("is_terminal", False),
                allows_harvest=phase_data.get("allows_harvest", False),
                is_recurring=phase_data.get("is_recurring", False),
                stress_tolerance=StressTolerance(phase_data.get("stress_tolerance", "medium")),
            )
            created_phase = repo.create_phase(phase)
            phase_key = created_phase.key or ""

            req = profile_gen.generate_requirement_profile(phase_data["name"], phase_key)
            repo.create_requirement_profile(req)

            nut = profile_gen.generate_nutrient_profile(phase_data["name"], phase_key)
            repo.create_nutrient_profile(nut)

        created += 1
        logger.info("lifecycle_outdoor_created", species_key=species_key, phases=len(entry.get("phases", [])))

    logger.info("seed_lifecycles_outdoor_complete", created=created, skipped=skipped)
