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
    data = load_yaml("gardol.yaml")

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

    plans_data = data["nutrient_plans"]
    for plan_data in plans_data:
        plan = _build_nutrient_plan(plan_data)

        if plan.name in existing_plan_map:
            existing_plan = existing_plan_map[plan.name]
            plan_key = existing_plan.key or ""
            existing_entries = plan_repo.get_phase_entries(plan_key)
            if existing_entries:
                # Backfill missing entries by sequence_order
                existing_seqs = {e.sequence_order for e in existing_entries}
                desired = _build_phase_entries(plan_data.get("phase_entries", []), fert_keys)
                missing = [e for e in desired if e.sequence_order not in existing_seqs]
                if not missing:
                    logger.info("plan_exists", name=plan.name, entries=len(existing_entries))
                    continue
                for entry in missing:
                    entry.plan_key = plan_key
                    dosage_count = sum(
                        len(ch.fertilizer_dosages) for ch in entry.delivery_channels
                    )
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

        entries = _build_phase_entries(plan_data.get("phase_entries", []), fert_keys)
        for entry in entries:
            entry.plan_key = plan_key
            dosage_count = sum(
                len(ch.fertilizer_dosages) for ch in entry.delivery_channels
            )
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
