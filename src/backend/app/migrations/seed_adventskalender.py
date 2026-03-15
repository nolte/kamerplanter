"""Seed Adventskalender 2025 (Historische Sorten) species data.

Adds 2 new botanical families, 4 new species, enriches 14 existing species,
replaces generic phases with art-specific growth phases (18 species),
adds ~120 cultivars, companion planting edges, and IPM data.

Sources: spec/ref/plant-info/*.md (18 plant-info documents)
Data loaded from seed_data/adventskalender.yaml.
"""

from typing import Any

import structlog

from app.common.dependencies import (
    get_family_repo,
    get_graph_repo,
    get_ipm_repo,
    get_lifecycle_repo,
    get_species_repo,
)
from app.common.enums import (
    CycleType,
    PhotoperiodType,
    PlantTrait,
    StressTolerance,
    Suitability,
)
from app.domain.models.botanical_family import BotanicalFamily, PhRange
from app.domain.models.ipm import Disease, Pest, Treatment
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase import NutrientProfile, RequirementProfile
from app.domain.models.species import Cultivar, GrowingPeriod, Species
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


# ══════════════════════════════════════════════════════════════════════════════
# YAML DATA LOADING & MODEL CONSTRUCTION
# ══════════════════════════════════════════════════════════════════════════════


def _load_data() -> dict[str, Any]:
    """Load adventskalender seed data from YAML."""
    return load_yaml("adventskalender.yaml")


def _build_families(data: dict[str, Any]) -> list[BotanicalFamily]:
    """Construct BotanicalFamily models from YAML data."""
    families: list[BotanicalFamily] = []
    for entry in data.get("new_families", []):
        ph_pref = entry.get("soil_ph_preference")
        families.append(
            BotanicalFamily(
                name=entry["name"],
                common_name_de=entry["common_name_de"],
                common_name_en=entry["common_name_en"],
                order=entry["order"],
                typical_nutrient_demand=entry["typical_nutrient_demand"],
                frost_tolerance=entry["frost_tolerance"],
                typical_root_depth=entry["typical_root_depth"],
                typical_growth_forms=entry["typical_growth_forms"],
                common_pests=entry["common_pests"],
                common_diseases=entry["common_diseases"],
                pollination_type=entry["pollination_type"],
                soil_ph_preference=PhRange(
                    min_ph=ph_pref["min_ph"], max_ph=ph_pref["max_ph"]
                )
                if ph_pref
                else None,
                description=entry.get("description", ""),
                rotation_category=entry.get("rotation_category"),
            )
        )
    return families


def _build_species(data: dict[str, Any]) -> list[Species]:
    """Construct Species models from YAML data."""
    species_list: list[Species] = []
    for entry in data.get("new_species", []):
        growing_periods = None
        if entry.get("growing_periods"):
            growing_periods = [
                GrowingPeriod(
                    label=gp["label"],
                    direct_sow_months=gp.get("direct_sow_months"),
                    harvest_months=gp.get("harvest_months"),
                )
                for gp in entry["growing_periods"]
            ]

        # Build kwargs, omitting None values to let model defaults apply
        kwargs: dict[str, Any] = {
            "scientific_name": entry["scientific_name"],
        }
        # Optional fields — only set if present and not None
        optional_fields = [
            "common_names", "genus", "growth_habit", "root_type",
            "hardiness_zones", "native_habitat", "allelopathy_score",
            "base_temp", "frost_sensitivity", "allows_harvest",
            "sowing_indoor_weeks_before_last_frost",
            "sowing_outdoor_after_last_frost_days",
            "direct_sow_months", "harvest_months", "bloom_months",
            "bloom_from_year", "container_suitable",
            "recommended_container_volume_l", "min_container_depth_cm",
            "mature_height_cm", "mature_width_cm", "spacing_cm",
            "indoor_suitable", "balcony_suitable",
            "greenhouse_recommended", "support_required",
        ]
        for field in optional_fields:
            if field in entry and entry[field] is not None:
                kwargs[field] = entry[field]
        if growing_periods:
            kwargs["growing_periods"] = growing_periods

        species_list.append(Species(**kwargs))
    return species_list


def _build_enrichment(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build species enrichment map from YAML data.

    Converts Suitability string values to enum instances.
    """
    enrichment: dict[str, dict[str, Any]] = {}
    suitability_fields = {
        "container_suitable",
        "indoor_suitable",
        "balcony_suitable",
    }
    for sci_name, fields in data.get("species_enrichment", {}).items():
        converted: dict[str, Any] = {}
        for field, value in fields.items():
            if field in suitability_fields and isinstance(value, str):
                converted[field] = Suitability(value)
            else:
                converted[field] = value
        enrichment[sci_name] = converted
    return enrichment


def _build_lifecycle_configs(
    data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Build lifecycle config map from YAML data."""
    configs: dict[str, dict[str, Any]] = {}
    for sci_name, entry in data.get("lifecycle_configs", {}).items():
        configs[sci_name] = {
            "cycle_type": CycleType(entry["cycle_type"]),
            "photoperiod_type": PhotoperiodType(entry["photoperiod_type"]),
            "lifespan_years": entry.get("lifespan_years"),
            "dormancy_required": entry.get("dormancy_required", False),
            "vernalization_required": entry.get(
                "vernalization_required", False
            ),
            "vernalization_min_days": entry.get("vernalization_min_days"),
            "critical_day_length_hours": entry.get(
                "critical_day_length_hours"
            ),
        }
    return configs


def _build_phase_data(
    data: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Build growth phase data map from YAML data."""
    phase_data: dict[str, list[dict[str, Any]]] = {}
    for sci_name, phases in data.get("growth_phases", {}).items():
        phase_list: list[dict[str, Any]] = []
        for entry in phases:
            phase_list.append(
                {
                    "phase": entry["phase"],
                    "requirements": entry["requirements"],
                    "nutrients": entry["nutrients"],
                }
            )
        phase_data[sci_name] = phase_list
    return phase_data


def _build_cultivars(
    data: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Build cultivar map from YAML data."""
    return data.get("cultivars", {})


def _build_companion_planting(
    data: dict[str, Any],
) -> tuple[list[tuple[str, str, float]], list[tuple[str, str, str]]]:
    """Build companion planting edge lists from YAML data."""
    cp_data = data.get("companion_planting", {})

    compatible: list[tuple[str, str, float]] = [
        (e[0], e[1], float(e[2])) for e in cp_data.get("compatible", [])
    ]
    incompatible: list[tuple[str, str, str]] = [
        (e[0], e[1], str(e[2])) for e in cp_data.get("incompatible", [])
    ]
    return compatible, incompatible


def _build_ipm_pests(data: dict[str, Any]) -> list[Pest]:
    """Construct Pest models from YAML data."""
    return [Pest.model_validate(entry) for entry in data.get("pests", [])]


def _build_ipm_diseases(data: dict[str, Any]) -> list[Disease]:
    """Construct Disease models from YAML data."""
    return [
        Disease.model_validate(entry) for entry in data.get("diseases", [])
    ]


def _build_ipm_treatments(data: dict[str, Any]) -> list[Treatment]:
    """Construct Treatment models from YAML data."""
    return [
        Treatment.model_validate(entry)
        for entry in data.get("treatments", [])
    ]


def _build_ipm_target_edges(
    data: dict[str, Any],
) -> tuple[
    list[tuple[str, str]], list[tuple[str, str]]
]:
    """Build IPM targeting edge lists from YAML data."""
    pest_targets: list[tuple[str, str]] = [
        (e[0], e[1]) for e in data.get("pest_treatments", [])
    ]
    disease_targets: list[tuple[str, str]] = [
        (e[0], e[1]) for e in data.get("disease_treatments", [])
    ]
    return pest_targets, disease_targets


# ══════════════════════════════════════════════════════════════════════════════
# SEED FUNCTION
# ══════════════════════════════════════════════════════════════════════════════


def run_seed_adventskalender() -> None:  # noqa: C901, PLR0912, PLR0915
    """Seed Adventskalender 2025 species data (idempotent)."""
    family_repo = get_family_repo()
    species_repo = get_species_repo()
    lifecycle_repo = get_lifecycle_repo()
    graph_repo = get_graph_repo()
    ipm_repo = get_ipm_repo()

    # Load all data from YAML
    data = _load_data()
    new_families = _build_families(data)
    new_species = _build_species(data)
    new_species_family_map: dict[str, str] = data.get(
        "new_species_family_map", {}
    )
    species_enrichment = _build_enrichment(data)
    lifecycle_configs = _build_lifecycle_configs(data)
    phase_data = _build_phase_data(data)
    cultivar_data = _build_cultivars(data)
    companion_compatible, companion_incompatible = _build_companion_planting(
        data
    )
    ipm_pests = _build_ipm_pests(data)
    ipm_diseases = _build_ipm_diseases(data)
    ipm_treatments = _build_ipm_treatments(data)
    ipm_targets_pest, ipm_targets_disease = _build_ipm_target_edges(data)
    existing_families_needed: list[str] = data.get(
        "existing_families_needed", []
    )

    # ── §1: Seed new families ────────────────────────────────────────────
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
    for name in existing_families_needed:
        existing = family_repo.get_by_name(name)
        if existing:
            family_map[name] = existing.key or ""

    # ── §2: Create new species ───────────────────────────────────────────
    species_key_map: dict[str, str] = {}

    for sp in new_species:
        existing = species_repo.get_by_scientific_name(sp.scientific_name)
        if existing:
            species_key_map[sp.scientific_name] = existing.key or ""
            # Update growing_periods if changed (GrowingPeriod model migration)
            if (
                sp.growing_periods
                and sp.growing_periods != existing.growing_periods
            ):
                existing.growing_periods = sp.growing_periods
                species_repo.update(existing.key or "", existing)
                logger.info(
                    "species_growing_periods_updated",
                    name=sp.scientific_name,
                )
            else:
                logger.info("species_exists", name=sp.scientific_name)
            continue

        family_name = new_species_family_map.get(sp.scientific_name, "")
        sp.family_key = family_map.get(family_name, "")
        created = species_repo.create(sp)
        species_key_map[sp.scientific_name] = created.key or ""
        logger.info("species_created", name=sp.scientific_name)

    # ── §3: Enrich existing species ──────────────────────────────────────
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

    # ── §4: Lifecycle configs + art-specific phases ──────────────────────
    for sci_name, lc_conf in lifecycle_configs.items():
        sp_key = species_key_map.get(sci_name, "")
        if not sp_key:
            logger.info("lifecycle_species_not_found", name=sci_name)
            continue

        cycle = lc_conf["cycle_type"]
        photo = lc_conf["photoperiod_type"]
        lifespan = lc_conf["lifespan_years"]
        dormancy = lc_conf["dormancy_required"]
        vernal = lc_conf["vernalization_required"]
        vernal_days = lc_conf["vernalization_min_days"]
        critical = lc_conf["critical_day_length_hours"]

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
                logger.info(
                    "lifecycle_updated",
                    species=sci_name,
                    cycle=cycle.value,
                )

            # Check if phases are already art-specific
            existing_phases = lifecycle_repo.get_phases_by_lifecycle(lc_key)
            has_germination = any(
                p.name == "germination" for p in existing_phases
            )
            if has_germination:
                logger.info(
                    "phases_already_artspezifisch", species=sci_name
                )
                continue

            # Delete generic phases
            for phase in existing_phases:
                lifecycle_repo.delete_phase(phase.key or "")
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
            )
            created_lc = lifecycle_repo.create_lifecycle(new_lc)
            lc_key = created_lc.key or ""
            logger.info(
                "lifecycle_created", species=sci_name, cycle=cycle.value
            )

        # Create art-specific phases with profiles
        if sci_name not in phase_data:
            continue

        for phase_entry in phase_data[sci_name]:
            p = phase_entry["phase"]
            req = phase_entry["requirements"]
            nut = phase_entry["nutrients"]

            phase = GrowthPhase(
                name=p["name"],
                display_name=p["display_name"],
                lifecycle_key=lc_key,
                typical_duration_days=p["duration"],
                sequence_order=p["order"],
                is_terminal=p["terminal"],
                allows_harvest=p["harvest"],
                stress_tolerance=StressTolerance(p["stress"]),
            )
            created_phase = lifecycle_repo.create_phase(phase)
            phase_key = created_phase.key or ""

            req_profile = RequirementProfile(
                phase_key=phase_key,
                light_ppfd_target=req["ppfd"],
                photoperiod_hours=req["photoperiod"],
                temperature_day_c=req["temp_day"],
                temperature_night_c=req["temp_night"],
                humidity_day_percent=req["hum_day"],
                humidity_night_percent=req["hum_night"],
                vpd_target_kpa=req["vpd"],
                co2_ppm=req["co2"],
                irrigation_frequency_days=req["irrigation_freq"],
                irrigation_volume_ml_per_plant=req["irrigation_vol"],
            )
            lifecycle_repo.create_requirement_profile(req_profile)

            npk = nut["npk"]
            nut_profile = NutrientProfile(
                phase_key=phase_key,
                npk_ratio=tuple(npk),
                target_ec_ms=nut["ec"],
                target_ph=nut["ph"],
                calcium_ppm=nut["ca"],
                magnesium_ppm=nut["mg"],
            )
            lifecycle_repo.create_nutrient_profile(nut_profile)

            logger.info(
                "phase_created", species=sci_name, phase=p["name"]
            )

    # ── §5: Seed cultivars ───────────────────────────────────────────────
    for sci_name, cultivar_list in cultivar_data.items():
        sp_key = species_key_map.get(sci_name, "")
        if not sp_key:
            logger.info("cultivar_species_not_found", species=sci_name)
            continue

        existing_cultivars = species_repo.get_cultivars(sp_key)
        existing_names = {c.name for c in existing_cultivars}

        for cv_entry in cultivar_list:
            cv_name = cv_entry["name"]
            if cv_name in existing_names:
                logger.info(
                    "cultivar_exists", species=sci_name, cultivar=cv_name
                )
                continue

            cultivar = Cultivar(
                name=cv_name,
                species_key=sp_key,
                breeder=cv_entry.get("breeder"),
                days_to_maturity=cv_entry["days_to_maturity"],
                traits=[
                    PlantTrait(t) for t in cv_entry.get("traits", [])
                ],
            )
            species_repo.create_cultivar(cultivar)
            logger.info(
                "cultivar_created", species=sci_name, cultivar=cv_name
            )

    # ── §6: Companion planting edges ─────────────────────────────────────
    for a_sci, b_sci, score in companion_compatible:
        a_key = species_key_map.get(a_sci, "")
        b_key = species_key_map.get(b_sci, "")
        if a_key and b_key:
            try:
                graph_repo.set_compatibility(a_key, b_key, score)
                logger.info(
                    "companion_compatible_created", a=a_sci, b=b_sci
                )
            except Exception:
                logger.info(
                    "companion_compatible_exists", a=a_sci, b=b_sci
                )

    for a_sci, b_sci, reason in companion_incompatible:
        a_key = species_key_map.get(a_sci, "")
        b_key = species_key_map.get(b_sci, "")
        if a_key and b_key:
            try:
                graph_repo.set_incompatibility(a_key, b_key, reason)
                logger.info(
                    "companion_incompatible_created", a=a_sci, b=b_sci
                )
            except Exception:
                logger.info(
                    "companion_incompatible_exists", a=a_sci, b=b_sci
                )

    # ── §7: IPM data ─────────────────────────────────────────────────────
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

    for treat_name, pest_name in ipm_targets_pest:
        t_key = treatment_key_map.get(treat_name, "")
        p_key = pest_key_map.get(pest_name, "")
        if t_key and p_key:
            try:
                ipm_repo.create_targets_pest_edge(t_key, p_key)
                logger.info(
                    "targets_pest_edge",
                    treatment=treat_name,
                    pest=pest_name,
                )
            except Exception:
                logger.info(
                    "targets_pest_edge_exists",
                    treatment=treat_name,
                    pest=pest_name,
                )

    for treat_name, disease_name in ipm_targets_disease:
        t_key = treatment_key_map.get(treat_name, "")
        d_key = disease_key_map.get(disease_name, "")
        if t_key and d_key:
            try:
                ipm_repo.create_targets_disease_edge(t_key, d_key)
                logger.info(
                    "targets_disease_edge",
                    treatment=treat_name,
                    disease=disease_name,
                )
            except Exception:
                logger.info(
                    "targets_disease_edge_exists",
                    treatment=treat_name,
                    disease=disease_name,
                )

    logger.info(
        "seed_adventskalender_complete",
        families=len(new_families),
        new_species=len(new_species),
        enriched_species=len(species_enrichment),
        cultivar_groups=len(cultivar_data),
        compatible_edges=len(companion_compatible),
        incompatible_edges=len(companion_incompatible),
        pests=len(ipm_pests),
        diseases=len(ipm_diseases),
        treatments=len(ipm_treatments),
    )


# ══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed_adventskalender()
