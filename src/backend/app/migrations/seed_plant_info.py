"""Seed plant-info data from spec/ref/plant-info/*.md (32 documents, 28 species).

Adds 1 new botanical family (Iridaceae), 4 new species (Dahlia pinnata,
Petunia x hybrida, Tigridia pavonia, Apium graveolens var. rapaceum),
enriches 24 existing species, adds art-specific growth phases for 11 species,
~120 cultivars, companion planting edges, and IPM data.

All hardcoded data lives in seed_data/plant_info.yaml — this module contains
only the loading, construction and seeding logic.

Sources: spec/ref/plant-info/*.md (32 plant-info documents)
"""

import time
from typing import Any

import structlog
from arango.exceptions import AQLQueryExecuteError

from app.common.dependencies import (
    get_family_repo,
    get_graph_repo,
    get_ipm_repo,
    get_lifecycle_repo,
    get_species_repo,
    get_substrate_repo,
)
from app.common.enums import (
    CycleType,
    FrostTolerance,
    GrowthHabit,
    PathogenType,
    PhotoperiodType,
    PlantTrait,
    RootType,
    StressTolerance,
    Suitability,
    TreatmentApplicationMethod,
    TreatmentType,
    WateringMethod,
)
from app.domain.models.botanical_family import BotanicalFamily, PhRange
from app.domain.models.ipm import Disease, Pest, Treatment
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.substrate import Substrate
from app.domain.models.phase import NutrientProfile, RequirementProfile
from app.domain.models.species import (
    Cultivar,
    SeasonalWateringAdjustment,
    Species,
    WateringGuide,
)
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING & MODEL CONSTRUCTION
# ══════════════════════════════════════════════════════════════════════════════


def _load_yaml() -> dict[str, Any]:
    """Load the plant-info YAML data."""
    return load_yaml("plant_info.yaml")


def _build_families(data: dict[str, Any]) -> list[BotanicalFamily]:
    """Construct BotanicalFamily models from YAML data."""
    families: list[BotanicalFamily] = []
    for entry in data.get("new_families", []):
        ph_pref = None
        if "soil_ph_preference" in entry and entry["soil_ph_preference"] is not None:
            ph_pref = PhRange(**entry["soil_ph_preference"])

        families.append(
            BotanicalFamily(
                name=entry["name"],
                common_name_de=entry.get("common_name_de", ""),
                common_name_en=entry.get("common_name_en", ""),
                order=entry.get("order"),
                typical_nutrient_demand=entry.get("typical_nutrient_demand", "medium"),
                frost_tolerance=FrostTolerance(entry.get("frost_tolerance", "moderate")),
                typical_root_depth=entry.get("typical_root_depth", "medium"),
                typical_growth_forms=[
                    GrowthHabit(g) for g in entry.get("typical_growth_forms", ["herb"])
                ],
                common_pests=entry.get("common_pests", []),
                common_diseases=entry.get("common_diseases", []),
                pollination_type=entry.get("pollination_type", ["insect"]),
                soil_ph_preference=ph_pref,
                description=entry.get("description", ""),
                rotation_category=entry.get("rotation_category", ""),
            )
        )
    return families


def _build_species(data: dict[str, Any]) -> list[Species]:
    """Construct Species models from YAML data."""
    species_list: list[Species] = []
    for entry in data.get("new_species", []):
        frost = entry.get("frost_sensitivity")
        species_list.append(
            Species(
                scientific_name=entry["scientific_name"],
                common_names=entry.get("common_names", []),
                genus=entry.get("genus", ""),
                growth_habit=GrowthHabit(entry.get("growth_habit", "herb")),
                root_type=RootType(entry.get("root_type", "fibrous")),
                hardiness_zones=entry.get("hardiness_zones", []),
                native_habitat=entry.get("native_habitat", ""),
                allelopathy_score=entry.get("allelopathy_score", 0.0),
                base_temp=entry.get("base_temp", 10.0),
                frost_sensitivity=FrostTolerance(frost) if frost else None,
                allows_harvest=entry.get("allows_harvest", True),
                sowing_indoor_weeks_before_last_frost=entry.get(
                    "sowing_indoor_weeks_before_last_frost"
                ),
                sowing_outdoor_after_last_frost_days=entry.get(
                    "sowing_outdoor_after_last_frost_days"
                ),
                direct_sow_months=entry.get("direct_sow_months", []),
                harvest_months=entry.get("harvest_months", []),
                bloom_months=entry.get("bloom_months", []),
                container_suitable=(
                    Suitability(entry["container_suitable"])
                    if entry.get("container_suitable")
                    else None
                ),
                recommended_container_volume_l=entry.get("recommended_container_volume_l"),
                min_container_depth_cm=entry.get("min_container_depth_cm"),
                mature_height_cm=entry.get("mature_height_cm"),
                mature_width_cm=entry.get("mature_width_cm"),
                spacing_cm=entry.get("spacing_cm"),
                indoor_suitable=(
                    Suitability(entry["indoor_suitable"])
                    if entry.get("indoor_suitable")
                    else None
                ),
                balcony_suitable=(
                    Suitability(entry["balcony_suitable"])
                    if entry.get("balcony_suitable")
                    else None
                ),
                greenhouse_recommended=entry.get("greenhouse_recommended", False),
                support_required=entry.get("support_required", False),
            )
        )
    return species_list


def _build_enrichment(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build enrichment map with proper enum conversions."""
    enum_field_map: dict[str, type] = {
        "container_suitable": Suitability,
        "indoor_suitable": Suitability,
        "balcony_suitable": Suitability,
        "frost_sensitivity": FrostTolerance,
    }

    result: dict[str, dict[str, Any]] = {}
    for sci_name, fields in data.get("species_enrichment", {}).items():
        converted: dict[str, Any] = {}
        for field, value in fields.items():
            if field == "watering_guide" and value is not None:
                converted[field] = _build_watering_guide(value)
            elif field in enum_field_map and value is not None:
                converted[field] = enum_field_map[field](value)
            else:
                converted[field] = value
        result[sci_name] = converted
    return result


def _build_watering_guide(data: dict[str, Any]) -> WateringGuide:
    """Construct a WateringGuide from YAML data."""
    adjustments = [
        SeasonalWateringAdjustment(**adj)
        for adj in data.get("seasonal_adjustments", [])
    ]
    return WateringGuide(
        interval_days=data.get("interval_days", 7),
        volume_ml_min=data.get("volume_ml_min", 100),
        volume_ml_max=data.get("volume_ml_max", 500),
        watering_method=WateringMethod(data.get("watering_method", "top_water")),
        water_quality_hint=data.get("water_quality_hint"),
        practical_tip=data.get("practical_tip"),
        seasonal_adjustments=adjustments,
    )


def _build_lifecycle_configs(
    data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Build lifecycle config dict with enum conversions."""
    result: dict[str, dict[str, Any]] = {}
    for sci_name, lc in data.get("lifecycle_configs", {}).items():
        result[sci_name] = {
            "cycle_type": CycleType(lc["cycle_type"]),
            "photoperiod_type": PhotoperiodType(lc["photoperiod_type"]),
            "typical_lifespan_years": lc.get("typical_lifespan_years"),
            "dormancy_required": lc.get("dormancy_required", False),
            "vernalization_required": lc.get("vernalization_required", False),
            "vernalization_min_days": lc.get("vernalization_min_days"),
            "critical_day_length_hours": lc.get("critical_day_length_hours"),
        }
    return result


def _build_phase_data(
    data: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Build growth phase data dict from YAML."""
    result: dict[str, list[dict[str, Any]]] = {}
    for sci_name, phases in data.get("growth_phases", {}).items():
        result[sci_name] = []
        for phase in phases:
            result[sci_name].append({
                "phase": phase,
                "requirement": phase["requirement_profile"],
                "nutrient": phase["nutrient_profile"],
            })
    return result


# ══════════════════════════════════════════════════════════════════════════════
# SEED FUNCTION
# ══════════════════════════════════════════════════════════════════════════════


def run_seed_plant_info() -> None:  # noqa: C901, PLR0912, PLR0915
    """Seed plant-info data from 32 spec documents (idempotent)."""
    yaml_data = _load_yaml()

    family_repo = get_family_repo()
    species_repo = get_species_repo()
    lifecycle_repo = get_lifecycle_repo()
    graph_repo = get_graph_repo()
    ipm_repo = get_ipm_repo()

    new_families = _build_families(yaml_data)
    new_species = _build_species(yaml_data)
    new_species_family_map: dict[str, str] = yaml_data.get("new_species_family_map", {})
    species_enrichment = _build_enrichment(yaml_data)
    lifecycle_configs = _build_lifecycle_configs(yaml_data)
    phase_data = _build_phase_data(yaml_data)
    cultivar_data: dict[str, list[dict[str, Any]]] = yaml_data.get("cultivars", {})
    companion_compatible: list[dict[str, Any]] = (
        yaml_data.get("companion_planting", {}).get("compatible", [])
    )
    companion_incompatible: list[dict[str, Any]] = (
        yaml_data.get("companion_planting", {}).get("incompatible", [])
    )
    ipm_pests_data: list[dict[str, Any]] = yaml_data.get("pests", [])
    ipm_diseases_data: list[dict[str, Any]] = yaml_data.get("diseases", [])
    ipm_treatments_data: list[dict[str, Any]] = yaml_data.get("treatments", [])
    ipm_targets_pest: list[dict[str, str]] = yaml_data.get("pest_treatments", [])
    ipm_targets_disease: list[dict[str, str]] = yaml_data.get("disease_treatments", [])

    # ── S1: Seed new families ────────────────────────────────────────────
    family_map: dict[str, str] = {}

    for family in new_families:
        existing = family_repo.get_by_name(family.name)
        if existing:
            family_map[family.name] = existing.key or ""
            family_repo.update_family(existing.key or "", family)
            logger.info("family_updated", name=family.name)
        else:
            created = family_repo.create_family(family)
            family_map[family.name] = created.key or ""
            logger.info("family_created", name=family.name)

    # Also load existing families needed for species creation
    for name in (
        "Asteraceae", "Solanaceae", "Apiaceae", "Rosaceae",
        "Asparagaceae", "Araceae", "Bromeliaceae", "Violaceae",
    ):
        existing = family_repo.get_by_name(name)
        if existing:
            family_map[name] = existing.key or ""

    # ── S2: Create new species ───────────────────────────────────────────
    species_key_map: dict[str, str] = {}

    for sp in new_species:
        existing = species_repo.get_by_scientific_name(sp.scientific_name)
        if existing:
            species_key_map[sp.scientific_name] = existing.key or ""
            logger.info("species_exists", name=sp.scientific_name)
            continue

        family_name = new_species_family_map.get(sp.scientific_name, "")
        sp.family_key = family_map.get(family_name, "")
        created = species_repo.create(sp)
        species_key_map[sp.scientific_name] = created.key or ""
        logger.info("species_created", name=sp.scientific_name)

    # ── S3: Enrich existing species ──────────────────────────────────────
    for sci_name, updates in species_enrichment.items():
        existing = species_repo.get_by_scientific_name(sci_name)
        if not existing:
            logger.info("enrichment_species_not_found", name=sci_name)
            continue

        species_key_map[sci_name] = existing.key or ""
        needs_update = False

        for field, value in updates.items():
            current = getattr(existing, field, None)
            if current is None or current == "" or current == []:
                setattr(existing, field, value)
                needs_update = True

        if needs_update:
            species_repo.update(existing.key or "", existing)
            logger.info("species_enriched", name=sci_name)
        else:
            logger.info("species_already_enriched", name=sci_name)

    # Also load all species that appear in cultivars or companion edges
    all_referenced_species: set[str] = set()
    for sci in cultivar_data:
        all_referenced_species.add(sci)
    for edge in companion_compatible:
        all_referenced_species.add(edge["species_a"])
        all_referenced_species.add(edge["species_b"])
    for edge in companion_incompatible:
        all_referenced_species.add(edge["species_a"])
        all_referenced_species.add(edge["species_b"])

    for sci_name in all_referenced_species:
        if sci_name not in species_key_map:
            existing = species_repo.get_by_scientific_name(sci_name)
            if existing:
                species_key_map[sci_name] = existing.key or ""

    # ── S4: Lifecycle configs + art-specific phases ──────────────────────
    for sci_name, lc_cfg in lifecycle_configs.items():
        sp_key = species_key_map.get(sci_name, "")
        if not sp_key:
            logger.info("lifecycle_species_not_found", name=sci_name)
            continue

        cycle = lc_cfg["cycle_type"]
        photo = lc_cfg["photoperiod_type"]
        lifespan = lc_cfg["typical_lifespan_years"]
        dormancy = lc_cfg["dormancy_required"]
        vernal = lc_cfg["vernalization_required"]
        vernal_days = lc_cfg["vernalization_min_days"]
        critical = lc_cfg["critical_day_length_hours"]

        existing_lc = lifecycle_repo.get_lifecycle_by_species(sp_key)
        if existing_lc:
            lc_key = existing_lc.key or ""

            # Check if lifecycle needs updating
            lc_needs_update = (
                existing_lc.cycle_type != cycle
                or existing_lc.photoperiod_type != photo
                or existing_lc.dormancy_required != dormancy
                or existing_lc.vernalization_required != vernal
            )
            if lc_needs_update:
                updated_lc = LifecycleConfig(
                    species_key=sp_key,
                    cycle_type=cycle,
                    photoperiod_type=photo,
                    typical_lifespan_years=lifespan,
                    dormancy_required=dormancy,
                    vernalization_required=vernal,
                    vernalization_min_days=vernal_days,
                    critical_day_length_hours=critical,
                )
                lifecycle_repo.update_lifecycle(lc_key, updated_lc)
                logger.info("lifecycle_updated", species=sci_name, cycle=cycle.value)

            # Check if phases are already art-specific
            existing_phases = lifecycle_repo.get_phases_by_lifecycle(lc_key)
            phase_names = {p.name for p in existing_phases}
            existing_phase_map = {p.name: p for p in existing_phases}
            # Update existing phases: descriptions, durations, flags, and profiles
            if sci_name in phase_data:
                first_phase_name = phase_data[sci_name][0]["phase"]["name"]
                if first_phase_name in phase_names:
                    updated_count = 0
                    for phase_entry in phase_data[sci_name]:
                        p = phase_entry["phase"]
                        req = phase_entry["requirement"]
                        nut = phase_entry["nutrient"]
                        existing = existing_phase_map.get(p["name"])
                        if not existing:
                            continue
                        # Patch phase fields
                        changed = False
                        new_desc = p.get("description", "")
                        if existing.description != new_desc:
                            existing.description = new_desc
                            changed = True
                        if existing.typical_duration_days != p["duration_days"]:
                            existing.typical_duration_days = p["duration_days"]
                            changed = True
                        if existing.allows_harvest != p["allows_harvest"]:
                            existing.allows_harvest = p["allows_harvest"]
                            changed = True
                        if existing.is_terminal != p["is_terminal"]:
                            existing.is_terminal = p["is_terminal"]
                            changed = True
                        new_display = p.get("display_name", existing.display_name)
                        if existing.display_name != new_display:
                            existing.display_name = new_display
                            changed = True
                        new_watering = p.get("watering_interval_days")
                        if new_watering is None and req.get("irrigation_frequency_days"):
                            new_watering = int(req["irrigation_frequency_days"])
                        if existing.watering_interval_days != new_watering:
                            existing.watering_interval_days = new_watering
                            changed = True
                        if changed:
                            lifecycle_repo.update_phase(existing.key or "", existing)
                            updated_count += 1
                        # Patch requirement profile
                        req_profile = lifecycle_repo.get_requirement_profile(existing.key or "")
                        if req_profile and req_profile.key:
                            req_changed = False
                            for field in ("light_ppfd_target", "temperature_day_c", "temperature_night_c",
                                          "humidity_day_percent", "humidity_night_percent",
                                          "vpd_target_kpa", "photoperiod_hours",
                                          "co2_ppm", "irrigation_frequency_days",
                                          "irrigation_volume_ml_per_plant"):
                                if field not in req or not hasattr(req_profile, field):
                                    continue
                                if getattr(req_profile, field) != req[field]:
                                    setattr(req_profile, field, req[field])
                                    req_changed = True
                            if req_changed:
                                lifecycle_repo.update_requirement_profile(req_profile.key, req_profile)
                                updated_count += 1
                        # Patch nutrient profile
                        nut_profile = lifecycle_repo.get_nutrient_profile(existing.key or "")
                        if nut_profile and nut_profile.key:
                            nut_changed = False
                            for field in ("target_ec_ms", "target_ph",
                                          "calcium_ppm", "magnesium_ppm"):
                                if field not in nut or not hasattr(nut_profile, field):
                                    continue
                                if getattr(nut_profile, field) != nut[field]:
                                    setattr(nut_profile, field, nut[field])
                                    nut_changed = True
                            # npk_ratio: YAML list vs Pydantic tuple
                            yaml_npk = tuple(nut["npk_ratio"])
                            if nut_profile.npk_ratio != yaml_npk:
                                nut_profile.npk_ratio = yaml_npk
                                nut_changed = True
                            if nut_changed:
                                lifecycle_repo.update_nutrient_profile(nut_profile.key, nut_profile)
                                updated_count += 1
                    if updated_count:
                        logger.info("phases_updated", species=sci_name, count=updated_count)
                    else:
                        logger.info("phases_already_artspezifisch", species=sci_name)
                    continue

            # Delete generic phases (retry on write-write conflict)
            for phase in existing_phases:
                for attempt in range(3):
                    try:
                        lifecycle_repo.delete_phase(phase.key or "")
                        break
                    except AQLQueryExecuteError:
                        if attempt < 2:
                            time.sleep(0.1 * (attempt + 1))
                        else:
                            raise
            logger.info("generic_phases_deleted", species=sci_name, count=len(existing_phases))
        else:
            # Create new lifecycle
            new_lc = LifecycleConfig(
                species_key=sp_key,
                cycle_type=cycle,
                photoperiod_type=photo,
                typical_lifespan_years=lifespan,
                dormancy_required=dormancy,
                vernalization_required=vernal,
                vernalization_min_days=vernal_days,
                critical_day_length_hours=critical,
            )
            created_lc = lifecycle_repo.create_lifecycle(new_lc)
            lc_key = created_lc.key or ""
            logger.info("lifecycle_created", species=sci_name, cycle=cycle.value)

        # Create art-specific phases with profiles
        if sci_name not in phase_data:
            continue

        for phase_entry in phase_data[sci_name]:
            p = phase_entry["phase"]
            req = phase_entry["requirement"]
            nut = phase_entry["nutrient"]

            # Derive watering_interval_days from explicit field or requirement_profile
            watering_interval = p.get("watering_interval_days")
            if watering_interval is None and req.get("irrigation_frequency_days"):
                watering_interval = int(req["irrigation_frequency_days"])
            phase = GrowthPhase(
                name=p["name"],
                display_name=p["display_name"],
                description=p.get("description", ""),
                lifecycle_key=lc_key,
                typical_duration_days=p["duration_days"],
                sequence_order=p["sequence_order"],
                is_terminal=p["is_terminal"],
                allows_harvest=p["allows_harvest"],
                stress_tolerance=StressTolerance(p["stress_tolerance"]),
                watering_interval_days=watering_interval,
            )
            created_phase = lifecycle_repo.create_phase(phase)
            phase_key = created_phase.key or ""

            requirement = RequirementProfile(
                phase_key=phase_key,
                light_ppfd_target=req["light_ppfd_target"],
                photoperiod_hours=req["photoperiod_hours"],
                temperature_day_c=req["temperature_day_c"],
                temperature_night_c=req["temperature_night_c"],
                humidity_day_percent=req["humidity_day_percent"],
                humidity_night_percent=req["humidity_night_percent"],
                vpd_target_kpa=req["vpd_target_kpa"],
                co2_ppm=req["co2_ppm"],
                irrigation_frequency_days=req.get("irrigation_frequency_days"),
                irrigation_volume_ml_per_plant=req["irrigation_volume_ml_per_plant"],
            )
            lifecycle_repo.create_requirement_profile(requirement)

            npk = nut["npk_ratio"]
            nutrient = NutrientProfile(
                phase_key=phase_key,
                npk_ratio=tuple(npk),
                target_ec_ms=nut["target_ec_ms"],
                target_ph=nut["target_ph"],
                calcium_ppm=nut.get("calcium_ppm"),
                magnesium_ppm=nut.get("magnesium_ppm"),
            )
            lifecycle_repo.create_nutrient_profile(nutrient)

            logger.info("phase_created", species=sci_name, phase=p["name"])

    # ── S5: Seed cultivars ───────────────────────────────────────────────
    for sci_name, cv_list in cultivar_data.items():
        sp_key = species_key_map.get(sci_name, "")
        if not sp_key:
            logger.info("cultivar_species_not_found", species=sci_name)
            continue

        existing_cultivars = species_repo.get_cultivars(sp_key)
        existing_names = {c.name for c in existing_cultivars}

        for cv_entry in cv_list:
            cv_name = cv_entry["name"]
            if cv_name in existing_names:
                logger.info("cultivar_exists", species=sci_name, cultivar=cv_name)
                continue

            trait_strings = cv_entry.get("traits", [])
            cultivar = Cultivar(
                name=cv_name,
                species_key=sp_key,
                breeder=cv_entry.get("breeder"),
                days_to_maturity=cv_entry.get("days_to_maturity"),
                traits=[
                    PlantTrait(t) for t in trait_strings
                    if t in PlantTrait.__members__.values()
                ],
                seed_type=cv_entry.get("seed_type", ""),
            )
            species_repo.create_cultivar(cultivar)
            logger.info("cultivar_created", species=sci_name, cultivar=cv_name)

    # ── S6: Companion planting edges ─────────────────────────────────────
    for edge in companion_compatible:
        a_key = species_key_map.get(edge["species_a"], "")
        b_key = species_key_map.get(edge["species_b"], "")
        if a_key and b_key:
            try:
                graph_repo.set_compatibility(a_key, b_key, edge["score"])
                logger.info(
                    "companion_compatible_created",
                    a=edge["species_a"],
                    b=edge["species_b"],
                )
            except Exception:
                logger.info(
                    "companion_compatible_exists",
                    a=edge["species_a"],
                    b=edge["species_b"],
                )

    for edge in companion_incompatible:
        a_key = species_key_map.get(edge["species_a"], "")
        b_key = species_key_map.get(edge["species_b"], "")
        if a_key and b_key:
            try:
                graph_repo.set_incompatibility(a_key, b_key, edge["reason"])
                logger.info(
                    "companion_incompatible_created",
                    a=edge["species_a"],
                    b=edge["species_b"],
                )
            except Exception:
                logger.info(
                    "companion_incompatible_exists",
                    a=edge["species_a"],
                    b=edge["species_b"],
                )

    # ── S7: IPM data ─────────────────────────────────────────────────────
    # Build IPM models from YAML
    ipm_pests = [
        Pest(
            scientific_name=p["scientific_name"],
            common_name=p["common_name"],
            pest_type=p.get("pest_type", "insect"),
            lifecycle_days=p.get("lifecycle_days"),
            optimal_temp_min=p.get("optimal_temp_min"),
            optimal_temp_max=p.get("optimal_temp_max"),
            detection_difficulty=p.get("detection_difficulty", "medium"),
            description=p.get("description"),
        )
        for p in ipm_pests_data
    ]

    ipm_diseases = [
        Disease(
            scientific_name=d["scientific_name"],
            common_name=d["common_name"],
            pathogen_type=PathogenType(d["pathogen_type"]),
            incubation_period_days=d.get("incubation_period_days"),
            environmental_triggers=d.get("environmental_triggers", []),
            affected_plant_parts=d.get("affected_plant_parts", []),
            description=d.get("description"),
        )
        for d in ipm_diseases_data
    ]

    ipm_treatments = [
        Treatment(
            name=t["name"],
            treatment_type=TreatmentType(t["treatment_type"]),
            active_ingredient=t.get("active_ingredient"),
            application_method=TreatmentApplicationMethod(
                t.get("application_method", "spray")
            ),
            safety_interval_days=t.get("safety_interval_days", 0),
            dosage_per_liter=t.get("dosage_per_liter"),
            description=t.get("description"),
            protective_equipment=t.get("protective_equipment", []),
        )
        for t in ipm_treatments_data
    ]

    pest_key_map: dict[str, str] = {}
    existing_pests, _ = ipm_repo.get_all_pests(0, 500)
    existing_pest_names = {p.scientific_name for p in existing_pests}
    for p in existing_pests:
        pest_key_map[p.common_name] = p.key or ""

    for pest in ipm_pests:
        if pest.scientific_name in existing_pest_names:
            logger.info("pest_exists", name=pest.common_name)
            continue
        created = ipm_repo.create_pest(pest)
        pest_key_map[pest.common_name] = created.key or ""
        logger.info("pest_created", name=pest.common_name)

    disease_key_map: dict[str, str] = {}
    existing_diseases, _ = ipm_repo.get_all_diseases(0, 500)
    existing_disease_names = {d.scientific_name for d in existing_diseases}
    for d in existing_diseases:
        disease_key_map[d.common_name] = d.key or ""

    for disease in ipm_diseases:
        if disease.scientific_name in existing_disease_names:
            logger.info("disease_exists", name=disease.common_name)
            continue
        created = ipm_repo.create_disease(disease)
        disease_key_map[disease.common_name] = created.key or ""
        logger.info("disease_created", name=disease.common_name)

    treatment_key_map: dict[str, str] = {}
    existing_treatments, _ = ipm_repo.get_all_treatments(0, 500)
    existing_treatment_names = {t.name for t in existing_treatments}
    for t in existing_treatments:
        treatment_key_map[t.name] = t.key or ""

    for treatment in ipm_treatments:
        if treatment.name in existing_treatment_names:
            logger.info("treatment_exists", name=treatment.name)
            continue
        created = ipm_repo.create_treatment(treatment)
        treatment_key_map[treatment.name] = created.key or ""
        logger.info("treatment_created", name=treatment.name)

    for target in ipm_targets_pest:
        treat_name = target["treatment"]
        pest_name = target["pest"]
        t_key = treatment_key_map.get(treat_name, "")
        p_key = pest_key_map.get(pest_name, "")
        if t_key and p_key:
            try:
                ipm_repo.create_targets_pest_edge(t_key, p_key)
                logger.info("targets_pest_edge", treatment=treat_name, pest=pest_name)
            except Exception:
                logger.info("targets_pest_edge_exists", treatment=treat_name, pest=pest_name)

    for target in ipm_targets_disease:
        treat_name = target["treatment"]
        disease_name = target["disease"]
        t_key = treatment_key_map.get(treat_name, "")
        d_key = disease_key_map.get(disease_name, "")
        if t_key and d_key:
            try:
                ipm_repo.create_targets_disease_edge(t_key, d_key)
                logger.info(
                    "targets_disease_edge", treatment=treat_name, disease=disease_name,
                )
            except Exception:
                logger.info(
                    "targets_disease_edge_exists",
                    treatment=treat_name,
                    disease=disease_name,
                )

    # ── S9: Seed substrates ─────────────────────────────────────────────
    substrate_repo = get_substrate_repo()
    substrates_data: list[dict[str, Any]] = yaml_data.get("substrates", [])

    existing_substrates, _ = substrate_repo.get_all_substrates(offset=0, limit=500)
    existing_substrate_set = {(s.type.value, s.name_de or s.brand or "") for s in existing_substrates}

    substrates_created = 0
    for raw in substrates_data:
        substrate = Substrate.model_validate(raw)
        ident = (substrate.type.value, substrate.name_de or substrate.brand or "")

        if ident in existing_substrate_set:
            continue

        substrate_repo.create_substrate(substrate)
        existing_substrate_set.add(ident)
        substrates_created += 1
        logger.info("substrate_seeded", type=substrate.type.value, name_de=substrate.name_de)

    logger.info(
        "seed_plant_info_complete",
        families=len(new_families),
        new_species=len(new_species),
        enriched_species=len(species_enrichment),
        cultivar_groups=len(cultivar_data),
        compatible_edges=len(companion_compatible),
        incompatible_edges=len(companion_incompatible),
        pests=len(ipm_pests),
        diseases=len(ipm_diseases),
        treatments=len(ipm_treatments),
        substrates=substrates_created,
    )


# ══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed_plant_info()
