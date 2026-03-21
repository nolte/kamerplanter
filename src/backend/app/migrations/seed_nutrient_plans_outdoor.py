"""Seed outdoor Plagron Terra nutrient plans.

Loads all plan data from seed_data/nutrient_plans_outdoor.yaml.

Auto-generated from spec/ref/nutrient-plans/
*_plagron_terra.md JSON blocks.
"""

from typing import Any

import structlog

from app.common.dependencies import (
    get_fertilizer_repo,
    get_nutrient_plan_repo,
)
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


def _build_watering_schedule(raw: dict[str, Any] | None) -> WateringSchedule | None:
    if raw is None:
        return None
    return WateringSchedule.model_validate(raw)


def _build_method_params(
    channel_data: dict[str, Any],
) -> DrenchParams | FertigationParams | None:
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
    channels: list[DeliveryChannel] = []
    for ch_data in raw_channels:
        dosages: list[FertilizerDosage] = []
        for dos_data in ch_data.get("fertilizer_dosages", []):
            product_name = dos_data["product_name"]
            if product_name not in fert_keys:
                logger.warning("fertilizer_not_found", product_name=product_name)
                continue
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
                reference_ec_ms=entry_data.get("reference_ec_ms"),
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
    return NutrientPlan(
        name=raw["name"],
        description=raw.get("description", ""),
        recommended_substrate_type=raw.get("recommended_substrate_type"),
        reference_substrate_type=raw.get("reference_substrate_type", "soil"),
        author=raw.get("author", ""),
        is_template=raw.get("is_template", False),
        version=raw.get("version", "1.0"),
        tags=raw.get("tags", []),
        watering_schedule=_build_watering_schedule(raw.get("watering_schedule")),
        cycle_restart_from_sequence=raw.get("cycle_restart_from_sequence"),
    )


def run_seed_nutrient_plans_outdoor() -> None:
    """Create outdoor Plagron Terra nutrient plans."""
    from app.migrations.seed_upsert_helpers import upsert_nutrient_plan_with_entries

    data = load_yaml("nutrient_plans_outdoor.yaml")
    fert_repo = get_fertilizer_repo()
    plan_repo = get_nutrient_plan_repo()

    # ── Load fertilizer keys ──
    existing_ferts, _ = fert_repo.get_all(offset=0, limit=1000)
    fert_keys: dict[str, str] = {}
    for f in existing_ferts:
        if f.brand == "Plagron" and f.key:
            fert_keys[f.product_name] = f.key

    if not fert_keys:
        logger.warning(
            "no_plagron_fertilizers_found",
            hint="Run run_seed_plagron() first.",
        )
        return

    # ── Upsert nutrient plans ──
    existing_plans, _ = plan_repo.get_all(offset=0, limit=200)
    existing_plan_map = {p.name: p for p in existing_plans}

    raw_plans = data["nutrient_plans"]
    for raw_plan in raw_plans:
        plan = _build_nutrient_plan(raw_plan)
        entries = _build_phase_entries(raw_plan.get("phase_entries", []), fert_keys)
        upsert_nutrient_plan_with_entries(plan_repo, plan, entries, existing_plan_map)

    logger.info(
        "seed_nutrient_plans_outdoor_complete",
        plans=len(raw_plans),
    )


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed_nutrient_plans_outdoor()
