"""Seed database with botanical families, common species, and default profiles."""

import structlog

from app.common.dependencies import get_family_repo, get_lifecycle_repo, get_species_repo
from app.common.enums import (
    CycleType,
    GrowthHabit,
    NutrientDemand,
    PhotoperiodType,
    RootType,
    StressTolerance,
)
from app.domain.engines.resource_profile_generator import ResourceProfileGenerator
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.species import Species

logger = structlog.get_logger()

FAMILIES = [
    BotanicalFamily(
        name="Solanaceae", typical_nutrient_demand=NutrientDemand.HEAVY,
        common_pests=["aphids", "whitefly", "hornworm"], rotation_category="fruit",
    ),
    BotanicalFamily(
        name="Cannabaceae", typical_nutrient_demand=NutrientDemand.HEAVY,
        common_pests=["spider_mites", "fungus_gnats", "thrips"], rotation_category="fiber",
    ),
    BotanicalFamily(
        name="Lamiaceae", typical_nutrient_demand=NutrientDemand.LIGHT,
        common_pests=["aphids", "spider_mites"], rotation_category="herb",
    ),
    BotanicalFamily(
        name="Apiaceae", typical_nutrient_demand=NutrientDemand.MEDIUM,
        common_pests=["carrot_fly", "aphids"], rotation_category="root",
    ),
    BotanicalFamily(
        name="Brassicaceae", typical_nutrient_demand=NutrientDemand.HEAVY,
        common_pests=["cabbage_white", "flea_beetle", "clubroot"], rotation_category="brassica",
    ),
    BotanicalFamily(
        name="Fabaceae", typical_nutrient_demand=NutrientDemand.LIGHT,
        common_pests=["aphids", "bean_beetle"], rotation_category="legume",
    ),
    BotanicalFamily(
        name="Cucurbitaceae", typical_nutrient_demand=NutrientDemand.HEAVY,
        common_pests=["powdery_mildew", "cucumber_beetle", "squash_bug"], rotation_category="cucurbit",
    ),
    BotanicalFamily(
        name="Asteraceae", typical_nutrient_demand=NutrientDemand.MEDIUM,
        common_pests=["aphids", "slugs"], rotation_category="composite",
    ),
]

SPECIES = [
    Species(
        scientific_name="Solanum lycopersicum", common_names=["Tomato", "Tomate"],
        genus="Solanum", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=10.0,
    ),
    Species(
        scientific_name="Cannabis sativa", common_names=["Hemp", "Cannabis", "Hanf"],
        genus="Cannabis", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=12.0,
    ),
    Species(
        scientific_name="Ocimum basilicum", common_names=["Basil", "Basilikum"],
        genus="Ocimum", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=10.0,
    ),
    Species(
        scientific_name="Capsicum annuum", common_names=["Pepper", "Paprika", "Chili"],
        genus="Capsicum", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=12.0,
    ),
    Species(
        scientific_name="Lactuca sativa", common_names=["Lettuce", "Salat"],
        genus="Lactuca", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=4.0,
    ),
]

DEFAULT_PHASES = [
    ("seedling", "Seedling", 14, 0, False, False, StressTolerance.LOW),
    ("vegetative", "Vegetative", 28, 1, False, False, StressTolerance.MEDIUM),
    ("flowering", "Flowering", 56, 2, False, False, StressTolerance.MEDIUM),
    ("ripening", "Ripening", 14, 3, False, True, StressTolerance.HIGH),
]


def run_seed() -> None:
    family_repo = get_family_repo()
    species_repo = get_species_repo()
    lifecycle_repo = get_lifecycle_repo()
    profile_gen = ResourceProfileGenerator()

    # Seed families
    family_map: dict[str, str] = {}
    for family in FAMILIES:
        existing = family_repo.get_by_name(family.name)
        if existing:
            family_map[family.name] = existing.key or ""
            logger.info("family_exists", name=family.name)
        else:
            created = family_repo.create_family(family)
            family_map[family.name] = created.key or ""
            logger.info("family_created", name=family.name)

    # Seed species
    family_species_map = {
        "Solanum lycopersicum": "Solanaceae",
        "Cannabis sativa": "Cannabaceae",
        "Ocimum basilicum": "Lamiaceae",
        "Capsicum annuum": "Solanaceae",
        "Lactuca sativa": "Asteraceae",
    }

    for sp in SPECIES:
        existing = species_repo.get_by_scientific_name(sp.scientific_name)
        if existing:
            logger.info("species_exists", name=sp.scientific_name)
            continue

        family_name = family_species_map.get(sp.scientific_name, "")
        sp.family_key = family_map.get(family_name, "")
        created_sp = species_repo.create(sp)
        species_key = created_sp.key or ""
        logger.info("species_created", name=sp.scientific_name, key=species_key)

        # Create lifecycle
        lc = LifecycleConfig(
            species_key=species_key,
            cycle_type=CycleType.ANNUAL,
            photoperiod_type=PhotoperiodType.DAY_NEUTRAL,
        )
        created_lc = lifecycle_repo.create_lifecycle(lc)
        lc_key = created_lc.key or ""

        # Create default phases with profiles
        for name, display, duration, order, terminal, harvest, stress in DEFAULT_PHASES:
            phase = GrowthPhase(
                name=name,
                display_name=display,
                lifecycle_key=lc_key,
                typical_duration_days=duration,
                sequence_order=order,
                is_terminal=terminal,
                allows_harvest=harvest,
                stress_tolerance=stress,
            )
            created_phase = lifecycle_repo.create_phase(phase)
            phase_key = created_phase.key or ""

            req = profile_gen.generate_requirement_profile(name, phase_key)
            lifecycle_repo.create_requirement_profile(req)

            nut = profile_gen.generate_nutrient_profile(name, phase_key)
            lifecycle_repo.create_nutrient_profile(nut)

            logger.info("phase_created", species=sp.scientific_name, phase=name)

    logger.info("seed_complete")


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed()
