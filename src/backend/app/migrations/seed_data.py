"""Seed database with botanical families, common species, cultivars, and default profiles.

All data is loaded from YAML files in the seed_data/ directory.
"""

import structlog

from app.common.dependencies import (
    get_family_repo,
    get_graph_repo,
    get_harvest_repo,
    get_ipm_repo,
    get_lifecycle_repo,
    get_species_repo,
    get_task_repo,
)
from app.common.enums import (
    CycleType,
    PhotoperiodType,
    PlantTrait,
    StressTolerance,
)
from app.domain.engines.resource_profile_generator import ResourceProfileGenerator
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.harvest import HarvestIndicator
from app.domain.models.ipm import Disease, Pest, Treatment
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.species import Cultivar, Species
from app.domain.models.task import TaskTemplate, WorkflowTemplate
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def _load_families() -> list[BotanicalFamily]:
    """Load botanical families from YAML and construct Pydantic models."""
    data = load_yaml("botanical_families.yaml")
    return [BotanicalFamily.model_validate(f) for f in data["families"]]


def _load_rotation_edges() -> list[tuple[str, str, int, float, str]]:
    """Load rotation edges from YAML."""
    data = load_yaml("botanical_families.yaml")
    return [
        (e[0], e[1], e[2], e[3], e[4])
        for e in data["rotation_edges"]
    ]


def _load_species() -> list[Species]:
    """Load species from YAML and construct Pydantic models."""
    data = load_yaml("species.yaml")
    return [Species.model_validate(s) for s in data["species"]]


def _load_species_family_map() -> dict[str, str]:
    """Build species->family mapping from YAML data."""
    data = load_yaml("species.yaml")
    return {s["scientific_name"]: s["family"] for s in data["species"]}


def _load_cultivars() -> dict[str, list[dict]]:
    """Load cultivar data from YAML."""
    data = load_yaml("species.yaml")
    return data.get("cultivars", {})


def _load_perennial_species() -> set[str]:
    """Load the set of perennial species names."""
    data = load_yaml("species.yaml")
    return set(data.get("perennial_species", []))


def _load_default_phases() -> list[dict]:
    """Load default growth phases from YAML."""
    data = load_yaml("species.yaml")
    return data.get("default_phases", [])


def _load_companion_planting() -> dict:
    """Load companion planting data from YAML."""
    return load_yaml("companion_planting.yaml")


def _load_ipm_data() -> dict:
    """Load IPM seed data from YAML."""
    return load_yaml("ipm.yaml")


def _load_workflow_data() -> dict:
    """Load workflow and task template data from YAML."""
    return load_yaml("workflows.yaml")


def _load_harvest_indicators() -> list[dict]:
    """Load harvest indicator data from YAML."""
    data = load_yaml("harvest_indicators.yaml")
    return data.get("harvest_indicators", [])


def run_seed() -> None:  # noqa: C901, PLR0912, PLR0915
    """Seed all reference data into the database. Idempotent (upsert behavior)."""
    # ── Seed location types (REQ-002) — delegated to startup module ──
    from app.migrations.seed_location_types import seed_location_types
    db = get_family_repo()._db  # reuse connection
    seed_location_types(db)

    family_repo = get_family_repo()
    species_repo = get_species_repo()
    lifecycle_repo = get_lifecycle_repo()
    graph_repo = get_graph_repo()
    profile_gen = ResourceProfileGenerator()

    # ── Load data from YAML ──────────────────────────────────────────
    families = _load_families()
    rotation_edges = _load_rotation_edges()
    species_list = _load_species()
    family_species_map = _load_species_family_map()
    cultivar_data = _load_cultivars()
    perennial_species = _load_perennial_species()
    default_phases = _load_default_phases()
    companion_data = _load_companion_planting()
    ipm_data = _load_ipm_data()
    workflow_data = _load_workflow_data()
    harvest_indicator_data = _load_harvest_indicators()

    # ── Seed families (upsert) ───────────────────────────────────────
    family_map: dict[str, str] = {}
    for family in families:
        existing = family_repo.get_by_name(family.name)
        if existing:
            family_map[family.name] = existing.key or ""
            family_repo.update_family(existing.key or "", family)
            logger.info("family_updated", name=family.name)
        else:
            created = family_repo.create_family(family)
            family_map[family.name] = created.key or ""
            logger.info("family_created", name=family.name)

    # ── Seed rotation edges ──────────────────────────────────────────
    for from_name, to_name, wait_years, benefit_score, benefit_reason in rotation_edges:
        from_key = family_map.get(from_name, "")
        to_key = family_map.get(to_name, "")
        if from_key and to_key:
            try:
                graph_repo.set_rotation_successor(
                    from_key, to_key, wait_years,
                    benefit_score=benefit_score, benefit_reason=benefit_reason,
                )
                logger.info("rotation_edge_created", from_family=from_name, to_family=to_name)
            except Exception:
                logger.info("rotation_edge_exists", from_family=from_name, to_family=to_name)

    # ── Seed family-level edges ──────────────────────────────────────
    for edge in companion_data.get("family_pest_risk", []):
        a_key = family_map.get(edge["family_a"], "")
        b_key = family_map.get(edge["family_b"], "")
        if a_key and b_key:
            try:
                graph_repo.set_pest_risk(
                    a_key, b_key,
                    edge["shared_pests"], edge["shared_diseases"],
                    edge["risk_level"],
                )
                logger.info("pest_risk_edge_created", a=edge["family_a"], b=edge["family_b"])
            except Exception:
                logger.info("pest_risk_edge_exists", a=edge["family_a"], b=edge["family_b"])

    for edge in companion_data.get("family_compatible", []):
        a_key = family_map.get(edge["family_a"], "")
        b_key = family_map.get(edge["family_b"], "")
        if a_key and b_key:
            try:
                graph_repo.set_family_compatible(
                    a_key, b_key,
                    edge["benefit_type"], edge["score"], edge["notes"],
                )
                logger.info("family_compatible_edge_created", a=edge["family_a"], b=edge["family_b"])
            except Exception:
                logger.info("family_compatible_edge_exists", a=edge["family_a"], b=edge["family_b"])

    for edge in companion_data.get("family_incompatible", []):
        a_key = family_map.get(edge["family_a"], "")
        b_key = family_map.get(edge["family_b"], "")
        if a_key and b_key:
            try:
                graph_repo.set_family_incompatible(
                    a_key, b_key, edge["reason"], edge["severity"],
                )
                logger.info("family_incompatible_edge_created", a=edge["family_a"], b=edge["family_b"])
            except Exception:
                logger.info("family_incompatible_edge_exists", a=edge["family_a"], b=edge["family_b"])

    # ── Seed species ─────────────────────────────────────────────────
    seed_update_fields = (
        "sowing_indoor_weeks_before_last_frost", "sowing_outdoor_after_last_frost_days",
        "direct_sow_months", "harvest_months", "bloom_months", "frost_sensitivity",
        "allows_harvest", "growing_periods",
        "container_suitable", "recommended_container_volume_l", "min_container_depth_cm",
        "mature_height_cm", "mature_width_cm", "spacing_cm",
        "indoor_suitable", "balcony_suitable", "greenhouse_recommended", "support_required",
    )

    species_key_map: dict[str, str] = {}

    for sp in species_list:
        existing = species_repo.get_by_scientific_name(sp.scientific_name)
        if existing:
            species_key_map[sp.scientific_name] = existing.key or ""
            # Update seed fields if they changed
            needs_update = False
            for field in seed_update_fields:
                if getattr(sp, field) != getattr(existing, field):
                    needs_update = True
                    break
            if needs_update:
                for field in seed_update_fields:
                    setattr(existing, field, getattr(sp, field))
                species_repo.update(existing.key or "", existing)
                logger.info("species_updated", name=sp.scientific_name)
            else:
                logger.info("species_exists", name=sp.scientific_name)
            continue

        family_name = family_species_map.get(sp.scientific_name, "")
        sp.family_key = family_map.get(family_name, "")
        created_sp = species_repo.create(sp)
        species_key = created_sp.key or ""
        species_key_map[sp.scientific_name] = species_key
        logger.info("species_created", name=sp.scientific_name, key=species_key)

        # Create lifecycle — perennials get PERENNIAL cycle type
        cycle = (
            CycleType.PERENNIAL if sp.scientific_name in perennial_species
            else CycleType.ANNUAL
        )
        lc = LifecycleConfig(
            species_key=species_key,
            cycle_type=cycle,
            photoperiod_type=PhotoperiodType.DAY_NEUTRAL,
        )
        created_lc = lifecycle_repo.create_lifecycle(lc)
        lc_key = created_lc.key or ""

        # Create default phases with profiles
        for phase_data in default_phases:
            phase = GrowthPhase(
                name=phase_data["name"],
                display_name=phase_data["display_name"],
                lifecycle_key=lc_key,
                typical_duration_days=phase_data["typical_duration_days"],
                sequence_order=phase_data["sequence_order"],
                is_terminal=phase_data["is_terminal"],
                allows_harvest=phase_data["allows_harvest"],
                stress_tolerance=StressTolerance(phase_data["stress_tolerance"]),
                watering_interval_days=phase_data.get("watering_interval_days"),
            )
            created_phase = lifecycle_repo.create_phase(phase)
            phase_key = created_phase.key or ""

            req = profile_gen.generate_requirement_profile(phase_data["name"], phase_key)
            lifecycle_repo.create_requirement_profile(req)

            nut = profile_gen.generate_nutrient_profile(phase_data["name"], phase_key)
            lifecycle_repo.create_nutrient_profile(nut)

            logger.info("phase_created", species=sp.scientific_name, phase=phase_data["name"])

    # ── Seed cultivars ───────────────────────────────────────────────
    for sci_name, cv_list in cultivar_data.items():
        sp_key = species_key_map.get(sci_name, "")
        if not sp_key:
            logger.info("cultivar_species_not_found", species=sci_name)
            continue
        for cv_data in cv_list:
            existing_cultivars = species_repo.get_cultivars(sp_key)
            if any(c.name == cv_data["name"] for c in existing_cultivars):
                logger.info("cultivar_exists", species=sci_name, cultivar=cv_data["name"])
                continue

            cultivar = Cultivar(
                name=cv_data["name"],
                species_key=sp_key,
                breeder=cv_data.get("breeder"),
                days_to_maturity=cv_data.get("days_to_maturity"),
                traits=[PlantTrait(t) for t in cv_data.get("traits", [])],
            )
            species_repo.create_cultivar(cultivar)
            logger.info("cultivar_created", species=sci_name, cultivar=cv_data["name"])

    # ── Seed companion planting edges (species-level) ────────────────
    for entry in companion_data.get("compatible", []):
        a_sci, b_sci, score = entry[0], entry[1], entry[2]
        a_key = species_key_map.get(a_sci, "")
        b_key = species_key_map.get(b_sci, "")
        if a_key and b_key:
            try:
                graph_repo.set_compatibility(a_key, b_key, score)
                logger.info("companion_compatible_created", a=a_sci, b=b_sci)
            except Exception:
                logger.info("companion_compatible_exists", a=a_sci, b=b_sci)

    for entry in companion_data.get("incompatible", []):
        a_sci = entry["species_a"]
        b_sci = entry["species_b"]
        reason = entry["reason"]
        a_key = species_key_map.get(a_sci, "")
        b_key = species_key_map.get(b_sci, "")
        if a_key and b_key:
            try:
                graph_repo.set_incompatibility(a_key, b_key, reason)
                logger.info("companion_incompatible_created", a=a_sci, b=b_sci)
            except Exception:
                logger.info("companion_incompatible_exists", a=a_sci, b=b_sci)

    # ── Seed IPM data (REQ-010) ──────────────────────────────────────
    ipm_repo = get_ipm_repo()
    pest_key_map: dict[str, str] = {}
    for pest_data in ipm_data.get("pests", []):
        pest = Pest.model_validate(pest_data)
        existing_pests, _ = ipm_repo.get_all_pests(0, 200)
        if any(p.scientific_name == pest.scientific_name for p in existing_pests):
            for p in existing_pests:
                if p.scientific_name == pest.scientific_name:
                    pest_key_map[pest.common_name] = p.key or ""
            logger.info("pest_exists", name=pest.common_name)
            continue
        created = ipm_repo.create_pest(pest)
        pest_key_map[pest.common_name] = created.key or ""
        logger.info("pest_created", name=pest.common_name)

    disease_key_map: dict[str, str] = {}
    for disease_data in ipm_data.get("diseases", []):
        disease = Disease.model_validate(disease_data)
        existing_diseases, _ = ipm_repo.get_all_diseases(0, 200)
        if any(d.scientific_name == disease.scientific_name for d in existing_diseases):
            for d in existing_diseases:
                if d.scientific_name == disease.scientific_name:
                    disease_key_map[d.common_name] = d.key or ""
            logger.info("disease_exists", name=disease.common_name)
            continue
        created = ipm_repo.create_disease(disease)
        disease_key_map[disease.common_name] = created.key or ""
        logger.info("disease_created", name=disease.common_name)

    treatment_key_map: dict[str, str] = {}
    for treatment_data in ipm_data.get("treatments", []):
        treatment = Treatment.model_validate(treatment_data)
        existing_treatments, _ = ipm_repo.get_all_treatments(0, 200)
        if any(t.name == treatment.name for t in existing_treatments):
            for t in existing_treatments:
                if t.name == treatment.name:
                    treatment_key_map[t.name] = t.key or ""
            logger.info("treatment_exists", name=treatment.name)
            continue
        created = ipm_repo.create_treatment(treatment)
        treatment_key_map[treatment.name] = created.key or ""
        logger.info("treatment_created", name=treatment.name)

    for entry in ipm_data.get("pest_treatments", []):
        treat_name, pest_name = entry[0], entry[1]
        t_key = treatment_key_map.get(treat_name, "")
        p_key = pest_key_map.get(pest_name, "")
        if t_key and p_key:
            try:
                ipm_repo.create_targets_pest_edge(t_key, p_key)
                logger.info("targets_pest_edge", treatment=treat_name, pest=pest_name)
            except Exception:
                logger.info("targets_pest_edge_exists", treatment=treat_name, pest=pest_name)

    for entry in ipm_data.get("disease_treatments", []):
        treat_name, disease_name = entry[0], entry[1]
        t_key = treatment_key_map.get(treat_name, "")
        d_key = disease_key_map.get(disease_name, "")
        if t_key and d_key:
            try:
                ipm_repo.create_targets_disease_edge(t_key, d_key)
                logger.info("targets_disease_edge", treatment=treat_name, disease=disease_name)
            except Exception:
                logger.info("targets_disease_edge_exists", treatment=treat_name, disease=disease_name)

    for entry in ipm_data.get("contraindications", []):
        a_name, b_name = entry[0], entry[1]
        a_key = treatment_key_map.get(a_name, "")
        b_key = treatment_key_map.get(b_name, "")
        if a_key and b_key:
            try:
                ipm_repo.create_contraindicated_edge(a_key, b_key)
                logger.info("contraindicated_edge", a=a_name, b=b_name)
            except Exception:
                logger.info("contraindicated_edge_exists", a=a_name, b=b_name)

    # ── Seed Harvest indicators (REQ-007) ────────────────────────────
    harvest_repo = get_harvest_repo()
    for ind_data in harvest_indicator_data:
        sp_key = species_key_map.get(ind_data["species_name"], "")
        indicator = HarvestIndicator(
            indicator_type=ind_data["indicator_type"],
            measurement_unit=ind_data["measurement_unit"],
            measurement_method=ind_data["measurement_method"],
            observation_frequency=ind_data["observation_frequency"],
            reliability_score=ind_data["reliability_score"],
            species_key=sp_key or None,
        )
        try:
            harvest_repo.create_indicator(indicator)
            logger.info("harvest_indicator_created", type=ind_data["indicator_type"], species=ind_data["species_name"])
        except Exception:
            logger.info("harvest_indicator_exists", type=ind_data["indicator_type"], species=ind_data["species_name"])

    # ── Deduplicate task templates (one-time cleanup) ────────────────
    from app.data_access.arango import collections as seed_col
    tt_col = db.collection(seed_col.TASK_TEMPLATES)
    dedup_query = (
        f"FOR doc IN {seed_col.TASK_TEMPLATES} "
        f"COLLECT name = doc.name, wfk = doc.workflow_template_key INTO group "
        f"LET docs = group[*].doc "
        f"FILTER LENGTH(docs) > 1 "
        f"LET to_remove = SLICE(docs, 1) "
        f"FOR d IN to_remove RETURN d._key"
    )
    dup_keys = list(db.aql.execute(dedup_query))
    if dup_keys:
        for dk in dup_keys:
            tt_col.delete(dk)
        logger.info("task_template_duplicates_removed", count=len(dup_keys))

    # ── Seed Workflow templates + Task templates (REQ-006) ───────────
    task_repo = get_task_repo()
    wf_key_map: dict[str, str] = {}

    for wt_data in workflow_data.get("workflow_templates", []):
        wt = WorkflowTemplate.model_validate(wt_data)
        existing_wfs, _ = task_repo.get_all_workflow_templates(0, 200)
        if any(w.name == wt.name for w in existing_wfs):
            for w in existing_wfs:
                if w.name == wt.name:
                    wf_key_map[w.name] = w.key or ""
            logger.info("workflow_template_exists", name=wt.name)
            continue
        created = task_repo.create_workflow_template(wt)
        wf_key_map[wt.name] = created.key or ""
        logger.info("workflow_template_created", name=wt.name)

    # Build lookup of existing task templates per workflow to avoid duplicates
    existing_tt_names: dict[str, set[str]] = {}
    for _wf_name, wf_key in wf_key_map.items():
        existing_tts = task_repo.get_task_templates_for_workflow(wf_key)
        existing_tt_names[wf_key] = {tt.name for tt in existing_tts}

    for tt_data in workflow_data.get("task_templates", []):
        wf_name = tt_data["workflow_name"]
        wf_key = wf_key_map.get(wf_name, "")
        if not wf_key:
            continue
        if tt_data["name"] in existing_tt_names.get(wf_key, set()):
            logger.info("task_template_exists", name=tt_data["name"], workflow=wf_name)
            continue
        tt = TaskTemplate(
            name=tt_data["name"],
            instruction=tt_data["instruction"],
            category=tt_data["category"],
            trigger_type=tt_data["trigger_type"],
            trigger_phase=tt_data.get("trigger_phase"),
            days_offset=tt_data["days_offset"],
            stress_level=tt_data["stress_level"],
            estimated_duration_minutes=tt_data["estimated_duration_minutes"],
            requires_photo=tt_data["requires_photo"],
            skill_level=tt_data["skill_level"],
            workflow_template_key=wf_key,
            sequence_order=tt_data["sequence_order"],
            timer_duration_seconds=tt_data.get("timer_duration_seconds"),
            timer_label=tt_data.get("timer_label"),
        )
        task_repo.create_task_template(tt)
        logger.info("task_template_created", name=tt_data["name"], workflow=wf_name)

    logger.info("seed_complete")


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed()
