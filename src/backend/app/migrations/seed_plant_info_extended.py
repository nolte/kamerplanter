"""Seed extended plant-info data from spec/knowledge/plants/*.md and spec/knowledge/plants/*.md.

Loads 7 additional YAML files (plant_info_indoor_1/2/3/4, plant_info_outdoor_1/2/3)
and seeds them using the same logic as seed_plant_info.py.

All hardcoded data lives in seed_data/plant_info_indoor_*.yaml and
seed_data/plant_info_outdoor_*.yaml — this module contains only the loading,
construction and seeding logic (reusing patterns from seed_plant_info).

Sources: spec/knowledge/plants/*.md (185 plant-info documents)
"""

import contextlib
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
)
from app.common.enums import (
    CycleType,
    FrostTolerance,
    GrowthHabit,
    NutrientDemandLevel,
    PhotoperiodType,
    PlantCategory,
    PlantTrait,
    RootType,
    StressTolerance,
    Suitability,
    WateringMethod,
)
from app.domain.models.botanical_family import BotanicalFamily, PhRange
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase import NutrientProfile, RequirementProfile
from app.domain.models.species import (
    Cultivar,
    SeasonalWateringAdjustment,
    Species,
    WateringGuide,
)
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()

# YAML files to process (order matters: indoor first, then outdoor)
YAML_FILES = [
    "plant_info_indoor_1.yaml",
    "plant_info_indoor_2.yaml",
    "plant_info_indoor_3.yaml",
    "plant_info_indoor_4.yaml",
    "plant_info_outdoor_1.yaml",
    "plant_info_outdoor_2.yaml",
    "plant_info_outdoor_3.yaml",
    "plant_info_supplement_1.yaml",
]


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING & MODEL CONSTRUCTION (same patterns as seed_plant_info.py)
# ══════════════════════════════════════════════════════════════════════════════


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
                typical_growth_forms=[GrowthHabit(g) for g in entry.get("typical_growth_forms", ["herb"])],
                common_pests=entry.get("common_pests", []),
                common_diseases=entry.get("common_diseases", []),
                pollination_type=entry.get("pollination_type", ["insect"]),
                soil_ph_preference=ph_pref,
                description=entry.get("description", ""),
                rotation_category=entry.get("rotation_category", ""),
            )
        )
    return families


def _to_list(value: Any) -> list[str]:
    """Convert semicolon-separated string to list, or pass through if already a list."""
    if isinstance(value, str):
        return [v.strip() for v in value.split(";") if v.strip()]
    return value or []


def _build_species(data: dict[str, Any]) -> list[Species]:
    """Construct Species models from YAML data."""
    species_list: list[Species] = []
    for entry in data.get("new_species", []):
        frost = entry.get("frost_sensitivity")
        ndl = entry.get("nutrient_demand_level")
        pc = entry.get("plant_category")
        species_list.append(
            Species(
                scientific_name=entry["scientific_name"],
                common_names=_to_list(entry.get("common_names", [])),
                genus=entry.get("genus", ""),
                plant_category=PlantCategory(pc) if pc else None,
                growth_habit=GrowthHabit(entry.get("growth_habit", "herb")),
                root_type=RootType(entry.get("root_type", "fibrous")),
                hardiness_zones=_to_list(entry.get("hardiness_zones", [])),
                native_habitat=entry.get("native_habitat", ""),
                allelopathy_score=entry.get("allelopathy_score", 0.0),
                base_temp=entry.get("base_temp", 10.0),
                frost_sensitivity=FrostTolerance(frost) if frost else None,
                nutrient_demand_level=NutrientDemandLevel(ndl) if ndl else None,
                allows_harvest=entry.get("allows_harvest", True),
                sowing_indoor_weeks_before_last_frost=entry.get("sowing_indoor_weeks_before_last_frost"),
                sowing_outdoor_after_last_frost_days=entry.get("sowing_outdoor_after_last_frost_days"),
                direct_sow_months=entry.get("direct_sow_months", []),
                harvest_months=entry.get("harvest_months", []),
                bloom_months=entry.get("bloom_months", []),
                container_suitable=(
                    Suitability(entry["container_suitable"]) if entry.get("container_suitable") else None
                ),
                recommended_container_volume_l=entry.get("recommended_container_volume_l"),
                min_container_depth_cm=entry.get("min_container_depth_cm"),
                mature_height_cm=entry.get("mature_height_cm"),
                mature_width_cm=entry.get("mature_width_cm"),
                spacing_cm=entry.get("spacing_cm"),
                indoor_suitable=(Suitability(entry["indoor_suitable"]) if entry.get("indoor_suitable") else None),
                balcony_suitable=(Suitability(entry["balcony_suitable"]) if entry.get("balcony_suitable") else None),
                green_manure_suitable=entry.get("green_manure_suitable", False),
                pruning_months=entry.get("pruning_months", []),
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
        "nutrient_demand_level": NutrientDemandLevel,
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
    adjustments = [SeasonalWateringAdjustment(**adj) for adj in data.get("seasonal_adjustments", [])]
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
            "cycle_restart_phase_order": lc.get("cycle_restart_phase_order"),
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
            result[sci_name].append(
                {
                    "phase": phase,
                    "requirement": phase.get("requirement_profile", {}),
                    "nutrient": phase.get("nutrient_profile", {}),
                }
            )
    return result


# ══════════════════════════════════════════════════════════════════════════════
# SEED ONE YAML FILE
# ══════════════════════════════════════════════════════════════════════════════


def _seed_yaml_file(yaml_filename: str) -> None:  # noqa: C901, PLR0912, PLR0915
    """Seed one plant-info YAML file (idempotent)."""
    yaml_data = load_yaml(yaml_filename)

    family_repo = get_family_repo()
    species_repo = get_species_repo()
    lifecycle_repo = get_lifecycle_repo()
    graph_repo = get_graph_repo()
    get_ipm_repo()

    new_families = _build_families(yaml_data)
    new_species = _build_species(yaml_data)
    new_species_family_map: dict[str, str] = yaml_data.get("new_species_family_map", {})
    species_enrichment = _build_enrichment(yaml_data)
    lifecycle_configs = _build_lifecycle_configs(yaml_data)
    phase_data = _build_phase_data(yaml_data)
    cultivar_data: dict[str, list[dict[str, Any]]] = yaml_data.get("cultivars", {})
    companion_compatible: list[dict[str, Any]] = yaml_data.get("companion_planting", {}).get("compatible", [])
    companion_incompatible: list[dict[str, Any]] = yaml_data.get("companion_planting", {}).get("incompatible", [])

    # ── S1: Seed new families ────────────────────────────────────────────
    family_map: dict[str, str] = {}

    for family in new_families:
        existing = family_repo.get_by_name(family.name)
        if existing:
            family_map[family.name] = existing.key or ""
            logger.info("family_exists", name=family.name, source=yaml_filename)
        else:
            created = family_repo.create_family(family)
            family_map[family.name] = created.key or ""
            logger.info("family_created", name=family.name, source=yaml_filename)

    # Load all existing families referenced by species
    all_family_names: set[str] = set()
    for name in new_species_family_map.values():
        all_family_names.add(name)
    for name in all_family_names:
        if name not in family_map:
            existing = family_repo.get_by_name(name)
            if existing:
                family_map[name] = existing.key or ""

    # ── S2: Create new species ───────────────────────────────────────────
    species_key_map: dict[str, str] = {}

    for sp in new_species:
        family_name = new_species_family_map.get(sp.scientific_name, "")
        sp.family_key = family_map.get(family_name, "")

        existing = species_repo.get_by_scientific_name(sp.scientific_name)
        if existing:
            species_key_map[sp.scientific_name] = existing.key or ""
            # Update phase-relevant fields from YAML (idempotent)
            sp.family_key = sp.family_key or existing.family_key
            species_repo.update(existing.key or "", sp)
            logger.info("species_updated", name=sp.scientific_name, source=yaml_filename)
            continue

        created = species_repo.create(sp)
        species_key_map[sp.scientific_name] = created.key or ""
        logger.info("species_created", name=sp.scientific_name, source=yaml_filename)

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
            logger.info("species_enriched", name=sci_name, source=yaml_filename)

    # Resolve species keys for companion/cultivar references
    all_referenced_species: set[str] = set()
    for sci in cultivar_data:
        all_referenced_species.add(sci)
    for edge in companion_compatible:
        all_referenced_species.add(edge.get("species_a") or edge.get("source", ""))
        all_referenced_species.add(edge.get("species_b") or edge.get("target", ""))
    for edge in companion_incompatible:
        all_referenced_species.add(edge.get("species_a") or edge.get("source", ""))
        all_referenced_species.add(edge.get("species_b") or edge.get("target", ""))

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
        lifespan = lc_cfg.get("typical_lifespan_years")
        dormancy = lc_cfg.get("dormancy_required", False)
        vernal = lc_cfg.get("vernalization_required", False)
        vernal_days = lc_cfg.get("vernalization_min_days")
        critical = lc_cfg.get("critical_day_length_hours")
        restart_order = lc_cfg.get("cycle_restart_phase_order")

        existing_lc = lifecycle_repo.get_lifecycle_by_species(sp_key)
        if existing_lc:
            lc_key = existing_lc.key or ""

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
                    cycle_restart_phase_order=restart_order,
                )
                lifecycle_repo.update_lifecycle(lc_key, updated_lc)
                logger.info("lifecycle_updated", species=sci_name, cycle=cycle.value)

            existing_phases = lifecycle_repo.get_phases_by_lifecycle(lc_key)
            phase_names = {p.name for p in existing_phases}
            existing_phase_map = {p.name: p for p in existing_phases}

            if sci_name in phase_data:
                first_phase_name = phase_data[sci_name][0]["phase"]["name"]
                if first_phase_name in phase_names:
                    # Update existing art-specific phases
                    updated_count = 0
                    for phase_entry in phase_data[sci_name]:
                        p = phase_entry["phase"]
                        req = phase_entry["requirement"]
                        nut = phase_entry["nutrient"]
                        ep = existing_phase_map.get(p["name"])
                        if not ep:
                            continue
                        changed = False
                        new_desc = p.get("description", "")
                        if ep.description != new_desc:
                            ep.description = new_desc
                            changed = True
                        dur = p.get("duration_days") or p.get("duration_days_min")
                        if dur and ep.typical_duration_days != dur:
                            ep.typical_duration_days = dur
                            changed = True
                        ah = p.get("allows_harvest", p.get("is_harvest_allowed"))
                        if ah is not None and ep.allows_harvest != ah:
                            ep.allows_harvest = ah
                            changed = True
                        it = p.get("is_terminal")
                        if it is not None and ep.is_terminal != it:
                            ep.is_terminal = it
                            changed = True
                        new_display = p.get("display_name", ep.display_name)
                        if ep.display_name != new_display:
                            ep.display_name = new_display
                            changed = True
                        new_watering = p.get("watering_interval_days")
                        if new_watering is None and req.get("irrigation_frequency_days"):
                            new_watering = int(req["irrigation_frequency_days"])
                        if ep.watering_interval_days != new_watering:
                            ep.watering_interval_days = new_watering
                            changed = True
                        if changed:
                            lifecycle_repo.update_phase(ep.key or "", ep)
                            updated_count += 1

                        # Patch requirement profile
                        req_profile = lifecycle_repo.get_requirement_profile(ep.key or "")
                        if req_profile and req_profile.key:
                            req_changed = False
                            for field in (
                                "light_ppfd_target",
                                "temperature_day_c",
                                "temperature_night_c",
                                "humidity_day_percent",
                                "humidity_night_percent",
                                "vpd_target_kpa",
                                "photoperiod_hours",
                                "co2_ppm",
                                "irrigation_frequency_days",
                                "irrigation_volume_ml_per_plant",
                            ):
                                if field not in req or not hasattr(req_profile, field):
                                    continue
                                if getattr(req_profile, field) != req[field]:
                                    setattr(req_profile, field, req[field])
                                    req_changed = True
                            if req_changed:
                                lifecycle_repo.update_requirement_profile(req_profile.key, req_profile)
                                updated_count += 1

                        # Patch nutrient profile
                        nut_profile = lifecycle_repo.get_nutrient_profile(ep.key or "")
                        if nut_profile and nut_profile.key:
                            nut_changed = False
                            for field in ("target_ec_ms", "target_ph", "calcium_ppm", "magnesium_ppm"):
                                if field not in nut or not hasattr(nut_profile, field):
                                    continue
                                if getattr(nut_profile, field) != nut[field]:
                                    setattr(nut_profile, field, nut[field])
                                    nut_changed = True
                            if "npk_ratio" in nut:
                                npk_raw = nut["npk_ratio"]
                                yaml_npk = (
                                    tuple(float(x) for x in npk_raw.split("-"))
                                    if isinstance(npk_raw, str)
                                    else tuple(npk_raw)
                                )
                                if nut_profile.npk_ratio != yaml_npk:
                                    nut_profile.npk_ratio = yaml_npk
                                    nut_changed = True
                            if nut_changed:
                                lifecycle_repo.update_nutrient_profile(nut_profile.key, nut_profile)
                                updated_count += 1

                    if updated_count:
                        logger.info("phases_updated", species=sci_name, count=updated_count)
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
            if existing_phases:
                logger.info(
                    "generic_phases_deleted",
                    species=sci_name,
                    count=len(existing_phases),
                )
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
                cycle_restart_phase_order=restart_order,
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

            watering_interval = p.get("watering_interval_days")
            if watering_interval is None and req.get("irrigation_frequency_days"):
                watering_interval = int(req["irrigation_frequency_days"])
            phase = GrowthPhase(
                name=p["name"],
                display_name=p.get("display_name", p["name"].replace("_", " ").title()),
                description=p.get("description", ""),
                lifecycle_key=lc_key,
                typical_duration_days=p.get("duration_days") or p.get("duration_days_min", 30),
                sequence_order=p.get("sequence_order") or p.get("order", 1),
                is_terminal=p.get("is_terminal", False),
                allows_harvest=p.get("allows_harvest", p.get("is_harvest_allowed", False)),
                is_recurring=p.get("is_recurring", False),
                stress_tolerance=StressTolerance(p.get("stress_tolerance", "medium")),
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
                co2_ppm=req.get("co2_ppm"),
                irrigation_frequency_days=req.get("irrigation_frequency_days"),
                irrigation_volume_ml_per_plant=req["irrigation_volume_ml_per_plant"],
            )
            lifecycle_repo.create_requirement_profile(requirement)

            npk_raw = nut.get("npk_ratio", (1, 1, 1))
            npk = tuple(float(x) for x in npk_raw.split("-")) if isinstance(npk_raw, str) else tuple(npk_raw)
            nutrient = NutrientProfile(
                phase_key=phase_key,
                npk_ratio=npk,
                target_ec_ms=nut.get("target_ec_ms", 0.0) or nut.get("ec_min", 0.0),
                target_ph=nut.get("target_ph", 6.0) or nut.get("ph_min", 6.0),
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
                continue

            trait_strings = cv_entry.get("traits", [])
            cultivar = Cultivar(
                name=cv_name,
                species_key=sp_key,
                breeder=cv_entry.get("breeder"),
                days_to_maturity=cv_entry.get("days_to_maturity"),
                traits=[PlantTrait(t) for t in trait_strings if t in PlantTrait.__members__.values()],
                seed_type=cv_entry.get("seed_type", ""),
            )
            species_repo.create_cultivar(cultivar)
            logger.info(
                "cultivar_created",
                species=sci_name,
                cultivar=cv_name,
                source=yaml_filename,
            )

    # ── S6: Companion planting edges ─────────────────────────────────────
    for edge in companion_compatible:
        a_key = species_key_map.get(edge.get("species_a") or edge.get("source", ""), "")
        b_key = species_key_map.get(edge.get("species_b") or edge.get("target", ""), "")
        if a_key and b_key:
            with contextlib.suppress(Exception):
                graph_repo.set_compatibility(a_key, b_key, edge.get("score", 0.5))

    for edge in companion_incompatible:
        a_key = species_key_map.get(edge.get("species_a") or edge.get("source", ""), "")
        b_key = species_key_map.get(edge.get("species_b") or edge.get("target", ""), "")
        if a_key and b_key:
            with contextlib.suppress(Exception):
                graph_repo.set_incompatibility(a_key, b_key, edge.get("reason", ""))

    logger.info("yaml_seed_complete", source=yaml_filename)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════


def run_seed_plant_info_extended() -> None:
    """Seed all extended plant-info YAML files (idempotent)."""
    for yaml_file in YAML_FILES:
        try:
            _seed_yaml_file(yaml_file)
        except FileNotFoundError:
            logger.warning("yaml_file_not_found", file=yaml_file)
        except Exception:
            logger.exception("yaml_seed_error", file=yaml_file)
