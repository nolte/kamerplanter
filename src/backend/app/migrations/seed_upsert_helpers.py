"""Shared upsert helpers for seed scripts.

Provides common functions for upserting fertilizers, nutrient plans,
and phase entries so all seed scripts consistently sync YAML → DB.
"""

from typing import Any

import structlog

from app.data_access.arango.fertilizer_repository import ArangoFertilizerRepository
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry

logger = structlog.get_logger()


def upsert_fertilizers(
    fert_repo: ArangoFertilizerRepository,
    fertilizers: list[Fertilizer],
) -> dict[str, str]:
    """Upsert fertilizers: update existing, create new. Returns product_name→key map."""
    all_existing, _ = fert_repo.get_all(offset=0, limit=1000)
    existing_map = {(f.product_name, f.brand): f for f in all_existing}

    fert_keys: dict[str, str] = {}
    for fert in fertilizers:
        found = existing_map.get((fert.product_name, fert.brand))
        if found:
            fert_keys[fert.product_name] = found.key or ""
            fert.key = found.key
            fert_repo.update(found.key or "", fert)
            logger.info("fertilizer_upserted", name=fert.product_name, brand=fert.brand)
        else:
            created = fert_repo.create(fert)
            fert_keys[fert.product_name] = created.key or ""
            logger.info("fertilizer_created", name=fert.product_name, brand=fert.brand)

    return fert_keys


def upsert_nutrient_plan_with_entries(
    plan_repo: ArangoNutrientPlanRepository,
    plan: NutrientPlan,
    desired_entries: list[NutrientPlanPhaseEntry],
    existing_plan_map: dict[str, Any],
) -> str:
    """Upsert a nutrient plan and its phase entries. Returns the plan key."""
    if plan.name in existing_plan_map:
        existing = existing_plan_map[plan.name]
        plan_key = existing.key or ""

        # Upsert plan metadata
        plan.key = existing.key
        plan_repo.update(plan_key, plan)
        logger.info("plan_upserted", name=plan.name)

        # Upsert phase entries
        existing_entries = plan_repo.get_phase_entries(plan_key)
        existing_by_seq = {e.sequence_order: e for e in existing_entries}
        desired_seqs = {e.sequence_order for e in desired_entries}

        for entry in desired_entries:
            entry.plan_key = plan_key
            dosage_count = sum(len(ch.fertilizer_dosages) for ch in entry.delivery_channels)
            if entry.sequence_order in existing_by_seq:
                existing_entry = existing_by_seq[entry.sequence_order]
                plan_repo.update_phase_entry(existing_entry.key or "", entry)
                logger.info(
                    "phase_entry_upserted",
                    plan=plan.name,
                    phase=entry.phase_name,
                    seq=entry.sequence_order,
                    dosages=dosage_count,
                )
            else:
                created_entry = plan_repo.create_phase_entry(entry)
                logger.info(
                    "phase_entry_created",
                    plan=plan.name,
                    phase=entry.phase_name,
                    seq=entry.sequence_order,
                    dosages=dosage_count,
                    key=created_entry.key,
                )

        # Remove entries from DB that are no longer in YAML
        for seq, existing_entry in existing_by_seq.items():
            if seq not in desired_seqs:
                plan_repo.delete_phase_entry(existing_entry.key or "")
                logger.info("phase_entry_removed", plan=plan.name, seq=seq)
    else:
        created_plan = plan_repo.create(plan)
        plan_key = created_plan.key or ""
        logger.info("plan_created", name=plan.name, key=plan_key)

        for entry in desired_entries:
            entry.plan_key = plan_key
            dosage_count = sum(len(ch.fertilizer_dosages) for ch in entry.delivery_channels)
            created_entry = plan_repo.create_phase_entry(entry)
            logger.info(
                "phase_entry_created",
                plan=plan.name,
                phase=entry.phase_name,
                week=f"{entry.week_start}-{entry.week_end}",
                dosages=dosage_count,
                key=created_entry.key,
            )

    return plan_key
