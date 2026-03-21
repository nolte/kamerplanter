"""Seed database with Gardol fertilizer products and nutrient plans.

Sources — Gardol:
  Gardol Grünpflanzendünger NPK 6-4-6 (Bauhaus)
  spec/ref/products/gardol_gruenpflanzenduenger.md

Nutrient plans:
  spec/ref/nutrient-plans/monstera_deliciosa_gardol.md
  spec/ref/nutrient-plans/gruenlilie_gardol.md
  spec/ref/nutrient-plans/einblatt_gardol.md
  spec/ref/nutrient-plans/guzmania_gardol.md
  spec/ref/nutrient-plans/yucca_gardol.md
"""

from typing import Any

import structlog

from app.common.dependencies import get_fertilizer_repo, get_nutrient_plan_repo
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import (
    DeliveryChannel,
    DrenchParams,
    FertilizerDosage,
    FoliarParams,
    NutrientPlan,
    NutrientPlanPhaseEntry,
    WateringSchedule,
)
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()

METHOD_PARAMS_BUILDERS: dict[str, type] = {
    "drench": DrenchParams,
    "foliar": FoliarParams,
}


def _build_watering_schedule(data: dict[str, Any]) -> WateringSchedule:
    """Construct a WateringSchedule from YAML dict."""
    return WateringSchedule.model_validate(data)


def _build_delivery_channels(
    channels_data: list[dict[str, Any]],
    fert_keys: dict[str, str],
) -> list[DeliveryChannel]:
    """Construct DeliveryChannel list, resolving product_name to fertilizer key."""
    channels: list[DeliveryChannel] = []
    for ch_data in channels_data:
        method_type = ch_data["method_type"]
        params_cls = METHOD_PARAMS_BUILDERS[method_type]
        method_params = params_cls(**ch_data["method_params"])

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
                label=ch_data["label"],
                application_method=ch_data["application_method"],
                target_ec_ms=ch_data.get("target_ec_ms"),
                target_ph=ch_data.get("target_ph"),
                method_params=method_params,
                fertilizer_dosages=dosages,
            ),
        )
    return channels


def _build_phase_entries(
    entries_data: list[dict[str, Any]],
    fert_keys: dict[str, str],
) -> list[NutrientPlanPhaseEntry]:
    """Construct NutrientPlanPhaseEntry list from YAML data."""
    entries: list[NutrientPlanPhaseEntry] = []
    for entry_data in entries_data:
        watering_override = None
        if entry_data.get("watering_schedule_override"):
            watering_override = _build_watering_schedule(
                entry_data["watering_schedule_override"],
            )

        channels = _build_delivery_channels(
            entry_data.get("delivery_channels", []),
            fert_keys,
        )

        entries.append(
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=entry_data["phase_name"],
                sequence_order=entry_data["sequence_order"],
                week_start=entry_data["week_start"],
                week_end=entry_data["week_end"],
                is_recurring=entry_data.get("is_recurring", False),
                npk_ratio=tuple(entry_data["npk_ratio"]),
                calcium_ppm=entry_data.get("calcium_ppm"),
                magnesium_ppm=entry_data.get("magnesium_ppm"),
                reference_ec_ms=entry_data.get("reference_ec_ms"),
                notes=entry_data.get("notes"),
                watering_schedule_override=watering_override,
                delivery_channels=channels,
            ),
        )
    return entries


def _build_fertilizers(data: list[dict[str, Any]]) -> list[Fertilizer]:
    """Construct Fertilizer models from YAML data."""
    fertilizers: list[Fertilizer] = []
    for fert_data in data:
        fertilizers.append(
            Fertilizer(
                product_name=fert_data["product_name"],
                brand=fert_data["brand"],
                fertilizer_type=fert_data["fertilizer_type"],
                is_organic=fert_data["is_organic"],
                tank_safe=fert_data["tank_safe"],
                recommended_application=fert_data["recommended_application"],
                npk_ratio=tuple(fert_data["npk_ratio"]),
                ec_contribution_per_ml=fert_data.get("ec_contribution_per_ml"),
                ec_contribution_uncertain=fert_data.get("ec_contribution_uncertain", False),
                max_dose_ml_per_liter=fert_data.get("max_dose_ml_per_liter"),
                mixing_priority=fert_data.get("mixing_priority", 50),
                ph_effect=fert_data.get("ph_effect"),
                bioavailability=fert_data.get("bioavailability"),
                notes=fert_data.get("notes"),
            ),
        )
    return fertilizers


def _build_nutrient_plan(plan_data: dict[str, Any]) -> NutrientPlan:
    """Construct a NutrientPlan model from YAML data (without phase entries)."""
    watering_schedule = None
    if plan_data.get("watering_schedule"):
        watering_schedule = _build_watering_schedule(plan_data["watering_schedule"])

    return NutrientPlan(
        name=plan_data["name"],
        description=plan_data.get("description"),
        recommended_substrate_type=plan_data.get("recommended_substrate_type"),
        reference_substrate_type=plan_data.get("reference_substrate_type", "soil"),
        author=plan_data.get("author"),
        is_template=plan_data.get("is_template", False),
        version=plan_data.get("version"),
        tags=plan_data.get("tags", []),
        water_mix_ratio_ro_percent=plan_data.get("water_mix_ratio_ro_percent"),
        cycle_restart_from_sequence=plan_data.get("cycle_restart_from_sequence"),
        watering_schedule=watering_schedule,
    )


# ── Entry point ───────────────────────────────────────────────────────────────


def run_seed_gardol() -> None:
    """Create Gardol fertilizer products and nutrient plans."""
    from app.migrations.seed_upsert_helpers import upsert_fertilizers, upsert_nutrient_plan_with_entries

    data = load_yaml("gardol.yaml")

    fert_repo = get_fertilizer_repo()
    plan_repo = get_nutrient_plan_repo()

    # ── Upsert fertilizers ────────────────────────────────────────────────
    fertilizers = _build_fertilizers(data["fertilizers"])
    fert_keys = upsert_fertilizers(fert_repo, fertilizers)

    # ── Upsert nutrient plans ─────────────────────────────────────────────
    existing_plans, _ = plan_repo.get_all(offset=0, limit=100)
    existing_plan_map = {p.name: p for p in existing_plans}

    plans_data = data["nutrient_plans"]
    for plan_data in plans_data:
        plan = _build_nutrient_plan(plan_data)
        entries = _build_phase_entries(plan_data.get("phase_entries", []), fert_keys)
        upsert_nutrient_plan_with_entries(plan_repo, plan, entries, existing_plan_map)

    logger.info(
        "seed_gardol_complete",
        fertilizers=len(fert_keys),
        plans=len(plans_data),
    )


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed_gardol()
