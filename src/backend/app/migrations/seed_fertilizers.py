"""Seed database with fertilizer products and cannabis nutrient plans.

All data is loaded from seed_data/fertilizers.yaml — no hardcoded product
or plan data in this module.
"""

from typing import Any

import structlog

from app.common.dependencies import get_fertilizer_repo, get_nutrient_plan_repo
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import (
    FertilizerDosage,
    NutrientPlan,
    NutrientPlanPhaseEntry,
)
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def _build_fertilizer(data: dict[str, Any]) -> Fertilizer:
    """Construct a Fertilizer model from YAML data.

    Converts the npk_ratio list back to a tuple as expected by the model.
    """
    record = dict(data)
    if "npk_ratio" in record and isinstance(record["npk_ratio"], list):
        record["npk_ratio"] = tuple(record["npk_ratio"])
    return Fertilizer.model_validate(record)


def _build_nutrient_plan(data: dict[str, Any]) -> NutrientPlan:
    """Construct a NutrientPlan model from YAML data (without phase_entries)."""
    record = {k: v for k, v in data.items() if k != "phase_entries"}
    return NutrientPlan.model_validate(record)


def _build_phase_entries(
    plan_data: dict[str, Any],
    fert_keys: dict[str, str],
) -> list[tuple[NutrientPlanPhaseEntry, list[FertilizerDosage]]]:
    """Build phase entries with fertilizer dosages from YAML data.

    Resolves product_name references in dosages to runtime fertilizer keys.
    Returns (entry, dosages) tuples.
    """
    entries: list[tuple[NutrientPlanPhaseEntry, list[FertilizerDosage]]] = []

    for phase_data in plan_data.get("phase_entries", []):
        # Separate dosages from entry fields
        dosage_list = phase_data.get("dosages", [])
        entry_data = {k: v for k, v in phase_data.items() if k != "dosages"}

        # plan_key is filled by the caller after plan creation
        entry_data["plan_key"] = ""

        # Convert npk_ratio list to tuple
        if "npk_ratio" in entry_data and isinstance(entry_data["npk_ratio"], list):
            entry_data["npk_ratio"] = tuple(entry_data["npk_ratio"])

        entry = NutrientPlanPhaseEntry.model_validate(entry_data)

        # Resolve product_name references to fertilizer keys
        dosages: list[FertilizerDosage] = []
        for dosage_data in dosage_list:
            product_name = dosage_data["product_name"]
            fertilizer_key = fert_keys[product_name]
            dosages.append(
                FertilizerDosage(
                    fertilizer_key=fertilizer_key,
                    ml_per_liter=dosage_data["ml_per_liter"],
                    optional=dosage_data.get("optional", False),
                ),
            )

        entries.append((entry, dosages))

    return entries


def run_seed_fertilizers() -> None:
    """Create fertilizer products and nutrient plans."""
    fert_repo = get_fertilizer_repo()
    plan_repo = get_nutrient_plan_repo()
    data = load_yaml("fertilizers.yaml")

    # ── Create fertilizers ────────────────────────────────────────────────
    fert_keys: dict[str, str] = {}
    fertilizers = [_build_fertilizer(f) for f in data["fertilizers"]]

    for fert in fertilizers:
        existing, _ = fert_repo.get_all(offset=0, limit=1000)
        found = next(
            (f for f in existing if f.product_name == fert.product_name and f.brand == fert.brand),
            None,
        )
        if found:
            fert_keys[fert.product_name] = found.key or ""
            logger.info("fertilizer_exists", name=fert.product_name)
        else:
            created = fert_repo.create(fert)
            fert_keys[fert.product_name] = created.key or ""
            logger.info("fertilizer_created", name=fert.product_name)

    # ── Resolve cross-file fertilizer references ──────────────────────────
    # Some nutrient plans reference products from other seed files (e.g.
    # PK 13-14 from plagron.yaml).  Look up any existing fertilizers in
    # the DB that are not yet in fert_keys so cross-file references
    # resolve correctly.
    all_existing, _ = fert_repo.get_all(offset=0, limit=1000)
    for fert in all_existing:
        if fert.product_name not in fert_keys:
            fert_keys[fert.product_name] = fert.key or ""

    # ── Create nutrient plans ─────────────────────────────────────────────
    existing_plans, _ = plan_repo.get_all(offset=0, limit=100)
    existing_names = {p.name for p in existing_plans}

    plan_data_list = data["nutrient_plans"]
    for plan_data in plan_data_list:
        plan = _build_nutrient_plan(plan_data)

        if plan.name in existing_names:
            logger.info("plan_exists", name=plan.name)
            continue

        created_plan = plan_repo.create(plan)
        plan_key = created_plan.key or ""
        logger.info("plan_created", name=plan.name, key=plan_key)

        entries = _build_phase_entries(plan_data, fert_keys)
        for entry, dosages in entries:
            entry.plan_key = plan_key
            entry.fertilizer_dosages = dosages
            created_entry = plan_repo.create_phase_entry(entry)
            logger.info(
                "phase_entry_created",
                plan=plan.name,
                phase=entry.phase_name,
                week=f"{entry.week_start}-{entry.week_end}",
                dosages=len(dosages),
                key=created_entry.key,
            )

    logger.info(
        "seed_fertilizers_complete",
        fertilizers=len(fert_keys),
        plans=len(plan_data_list),
    )


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed_fertilizers()
