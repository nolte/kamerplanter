"""Seed database with Plagron fertilizer products and nutrient plans.

Loads all product and plan data from seed_data/plagron.yaml.

Sources — Plagron:
  https://plagron.com/en/hobby/products/terra-grow      (NPK 3-1-3)
  https://plagron.com/en/hobby/products/terra-bloom      (NPK 2-2-4)
  https://plagron.com/en/hobby/products/power-roots      (NPK 0-0-2)
  https://plagron.com/en/hobby/products/pure-zym         (enzyme)
  https://plagron.com/en/hobby/products/sugar-royal      (NPK 9-0-0)
  https://plagron.com/en/hobby/products/green-sensation  (NPK 0-8-9)
  https://plagron.com/downloads/en/grow-schedule-100-terra
  https://plagron.com/downloads/en/grow-schedule-100-coco
"""

from typing import Any

import structlog

from app.common.dependencies import get_fertilizer_repo, get_nutrient_plan_repo
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import (
    DeliveryChannel,
    DrenchParams,
    FertigationParams,
    FertilizerDosage,
    NutrientPlan,
    NutrientPlanPhaseEntry,
    WateringSchedule,
)
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def _build_fertilizers(raw_list: list[dict[str, Any]]) -> list[Fertilizer]:
    """Build Fertilizer models from YAML data."""
    fertilizers: list[Fertilizer] = []
    for raw in raw_list:
        data = {**raw}
        # Convert npk_ratio list to tuple for Pydantic validation
        if "npk_ratio" in data:
            data["npk_ratio"] = tuple(data["npk_ratio"])
        fertilizers.append(Fertilizer.model_validate(data))
    return fertilizers


def _build_watering_schedule(raw: dict[str, Any] | None) -> WateringSchedule | None:
    """Build a WateringSchedule from YAML data, or None."""
    if raw is None:
        return None
    return WateringSchedule.model_validate(raw)


def _build_method_params(
    channel_data: dict[str, Any],
) -> DrenchParams | FertigationParams | None:
    """Build method_params from drench_params/fertigation_params in YAML."""
    drench_raw = channel_data.get("drench_params")
    fertigation_raw = channel_data.get("fertigation_params")
    if drench_raw is not None:
        return DrenchParams.model_validate(drench_raw)
    if fertigation_raw is not None:
        return FertigationParams.model_validate(fertigation_raw)
    return None


def _build_delivery_channels(
    raw_channels: list[dict[str, Any]],
    fert_keys: dict[str, str],
) -> list[DeliveryChannel]:
    """Build DeliveryChannel list, resolving product_name to fertilizer_key."""
    channels: list[DeliveryChannel] = []
    for ch_data in raw_channels:
        dosages: list[FertilizerDosage] = []
        for dos_data in ch_data.get("fertilizer_dosages", []):
            product_name = dos_data["product_name"]
            dosages.append(
                FertilizerDosage(
                    fertilizer_key=fert_keys[product_name],
                    ml_per_liter=dos_data["ml_per_liter"],
                    optional=dos_data.get("optional", False),
                ),
            )

        channels.append(
            DeliveryChannel(
                channel_id=ch_data["channel_id"],
                label=ch_data.get("label", ""),
                application_method=ch_data["application_method"],
                target_ec_ms=ch_data.get("target_ec_ms"),
                target_ph=ch_data.get("target_ph"),
                method_params=_build_method_params(ch_data),
                fertilizer_dosages=dosages,
            ),
        )
    return channels


def _build_phase_entries(
    raw_entries: list[dict[str, Any]],
    fert_keys: dict[str, str],
) -> list[NutrientPlanPhaseEntry]:
    """Build NutrientPlanPhaseEntry list from YAML phase data."""
    entries: list[NutrientPlanPhaseEntry] = []
    for entry_data in raw_entries:
        npk = entry_data.get("npk_ratio", [0.0, 0.0, 0.0])

        entries.append(
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=entry_data["phase_name"],
                sequence_order=entry_data["sequence_order"],
                week_start=entry_data["week_start"],
                week_end=entry_data["week_end"],
                npk_ratio=tuple(npk),
                is_recurring=entry_data.get("is_recurring", False),
                calcium_ppm=entry_data.get("calcium_ppm"),
                magnesium_ppm=entry_data.get("magnesium_ppm"),
                sulfur_ppm=entry_data.get("sulfur_ppm"),
                iron_ppm=entry_data.get("iron_ppm"),
                boron_ppm=entry_data.get("boron_ppm"),
                notes=entry_data.get("notes"),
                watering_schedule_override=_build_watering_schedule(
                    entry_data.get("watering_schedule_override"),
                ),
                delivery_channels=_build_delivery_channels(
                    entry_data.get("delivery_channels", []),
                    fert_keys,
                ),
            ),
        )
    return entries


def _build_nutrient_plan(raw: dict[str, Any]) -> NutrientPlan:
    """Build a NutrientPlan model from YAML data (without phase entries)."""
    return NutrientPlan(
        name=raw["name"],
        description=raw.get("description", ""),
        recommended_substrate_type=raw.get("recommended_substrate_type"),
        author=raw.get("author", ""),
        is_template=raw.get("is_template", False),
        version=raw.get("version", "1.0"),
        tags=raw.get("tags", []),
        watering_schedule=_build_watering_schedule(raw.get("watering_schedule")),
        cycle_restart_from_sequence=raw.get("cycle_restart_from_sequence"),
    )


def run_seed_plagron() -> None:
    """Create Plagron fertilizer products and nutrient plans."""
    data = load_yaml("plagron.yaml")
    fert_repo = get_fertilizer_repo()
    plan_repo = get_nutrient_plan_repo()

    # ── Create fertilizers ────────────────────────────────────────────────
    fertilizers = _build_fertilizers(data["fertilizers"])
    fert_keys: dict[str, str] = {}
    for fert in fertilizers:
        existing, _ = fert_repo.get_all(offset=0, limit=1000)
        found = next(
            (f for f in existing if f.product_name == fert.product_name and f.brand == fert.brand),
            None,
        )
        if found:
            fert_keys[fert.product_name] = found.key or ""
            logger.info("fertilizer_exists", name=fert.product_name, brand=fert.brand)
        else:
            created = fert_repo.create(fert)
            fert_keys[fert.product_name] = created.key or ""
            logger.info("fertilizer_created", name=fert.product_name, brand=fert.brand)

    # ── Create nutrient plans ─────────────────────────────────────────────
    existing_plans, _ = plan_repo.get_all(offset=0, limit=100)
    existing_plan_map = {p.name: p for p in existing_plans}

    raw_plans = data["nutrient_plans"]
    for raw_plan in raw_plans:
        plan = _build_nutrient_plan(raw_plan)

        if plan.name in existing_plan_map:
            existing = existing_plan_map[plan.name]
            plan_key = existing.key or ""
            existing_entries = plan_repo.get_phase_entries(plan_key)
            if existing_entries:
                # Backfill missing entries by sequence_order
                existing_seqs = {e.sequence_order for e in existing_entries}
                desired = _build_phase_entries(raw_plan.get("phase_entries", []), fert_keys)
                missing = [e for e in desired if e.sequence_order not in existing_seqs]
                if not missing:
                    logger.info("plan_exists", name=plan.name, entries=len(existing_entries))
                    continue
                for entry in missing:
                    entry.plan_key = plan_key
                    dosage_count = sum(len(ch.fertilizer_dosages) for ch in entry.delivery_channels)
                    created_entry = plan_repo.create_phase_entry(entry)
                    logger.info(
                        "phase_entry_backfilled",
                        plan=plan.name,
                        phase=entry.phase_name,
                        seq=entry.sequence_order,
                        week=f"{entry.week_start}-{entry.week_end}",
                        dosages=dosage_count,
                        key=created_entry.key,
                    )
                logger.info(
                    "plan_backfill_complete",
                    name=plan.name,
                    added=len(missing),
                    total=len(existing_entries) + len(missing),
                )
                continue
            logger.info("plan_exists_no_entries", name=plan.name, key=plan_key)
        else:
            created_plan = plan_repo.create(plan)
            plan_key = created_plan.key or ""
            logger.info("plan_created", name=plan.name, key=plan_key)

        entries = _build_phase_entries(raw_plan.get("phase_entries", []), fert_keys)
        for entry in entries:
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

    logger.info(
        "seed_plagron_complete",
        fertilizers=len(fert_keys),
        plans=len(raw_plans),
    )


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed_plagron()
