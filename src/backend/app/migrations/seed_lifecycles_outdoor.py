"""Seed lifecycle configs and growth phases for outdoor species from YAML."""

import structlog

from app.common.dependencies import get_lifecycle_repo
from app.common.enums import CycleType, PhotoperiodType, StressTolerance
from app.domain.engines.resource_profile_generator import ResourceProfileGenerator
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def run_seed_lifecycles_outdoor() -> None:
    """Create lifecycle configs + growth phases for species that don't have one yet."""
    repo = get_lifecycle_repo()
    profile_gen = ResourceProfileGenerator()
    data = load_yaml("lifecycles_outdoor.yaml")

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
        )
        created_lc = repo.create_lifecycle(lc)
        lc_key = created_lc.key or ""

        for phase_data in entry.get("phases", []):
            phase = GrowthPhase(
                name=phase_data["name"],
                display_name=phase_data.get("display_name", ""),
                lifecycle_key=lc_key,
                typical_duration_days=phase_data["typical_duration_days"],
                sequence_order=phase_data["sequence_order"],
                is_terminal=phase_data.get("is_terminal", False),
                allows_harvest=phase_data.get("allows_harvest", False),
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
