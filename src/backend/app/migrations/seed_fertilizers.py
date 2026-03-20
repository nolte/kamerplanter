"""Seed database with fertilizer products and cannabis nutrient plans.

All data is loaded from seed_data/fertilizers.yaml — no hardcoded product
or plan data in this module.
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


def _resolve_dosages(
    raw_dosages: list[dict[str, Any]],
    fert_keys: dict[str, str],
) -> list[FertilizerDosage]:
    """Resolve product_name references to fertilizer keys."""
    dosages: list[FertilizerDosage] = []
    for dos_data in raw_dosages:
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
    return dosages


def _build_method_params(
    channel_data: dict[str, Any],
) -> DrenchParams | FertigationParams | None:
    """Build method params from drench_params or fertigation_params keys."""
    drench_raw = channel_data.get("drench_params")
    fertigation_raw = channel_data.get("fertigation_params")
    if drench_raw is not None:
        return DrenchParams.model_validate(drench_raw)
    if fertigation_raw is not None and fertigation_raw:
        return FertigationParams.model_validate(fertigation_raw)
    return None


def _build_delivery_channels(
    raw_channels: list[dict[str, Any]],
    fert_keys: dict[str, str],
) -> list[DeliveryChannel]:
    """Build DeliveryChannel list from YAML delivery_channels data."""
    channels: list[DeliveryChannel] = []
    for ch_data in raw_channels:
        dosages = _resolve_dosages(
            ch_data.get("fertilizer_dosages", []),
            fert_keys,
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
    plan_data: dict[str, Any],
    fert_keys: dict[str, str],
) -> list[NutrientPlanPhaseEntry]:
    """Build phase entries from YAML data.

    Supports two YAML formats:
    - Flat: dosages + target_ec/ph at phase level (Sensi/GMB simple plans)
    - Structured: delivery_channels with nested dosages (Tank+Gießkanne plans)
    """
    entries: list[NutrientPlanPhaseEntry] = []

    for phase_data in plan_data.get("phase_entries", []):
        raw_channels = phase_data.get("delivery_channels")

        if raw_channels is not None:
            # Structured format — delivery_channels already in YAML
            channels = _build_delivery_channels(raw_channels, fert_keys)
        else:
            # Flat format — convert dosages + phase-level EC/pH into a channel
            dosages = _resolve_dosages(phase_data.get("dosages", []), fert_keys)
            volume = phase_data.get("volume_per_feeding_liters", 0.5)
            channels = [
                DeliveryChannel(
                    channel_id="fertigation",
                    label="Fertigation",
                    application_method="fertigation",
                    target_ec_ms=phase_data.get("target_ec_ms"),
                    target_ph=phase_data.get("target_ph"),
                    fertilizer_dosages=dosages,
                    method_params=DrenchParams(volume_per_feeding_liters=volume),
                ),
            ]

        # Strip non-model fields before validation
        # Note: target_ec_ms is now a model field (REQ-004 §4b), so it is NOT stripped.
        entry_data = {
            k: v
            for k, v in phase_data.items()
            if k
            not in {
                "dosages",
                "delivery_channels",
                "target_ph",
                "feeding_frequency_per_week",
                "volume_per_feeding_liters",
            }
        }
        entry_data["plan_key"] = ""
        entry_data["delivery_channels"] = channels

        if "npk_ratio" in entry_data and isinstance(entry_data["npk_ratio"], list):
            entry_data["npk_ratio"] = tuple(entry_data["npk_ratio"])

        entries.append(NutrientPlanPhaseEntry.model_validate(entry_data))

    return entries


def run_seed_fertilizers() -> None:
    """Create fertilizer products and nutrient plans."""
    from app.migrations.seed_upsert_helpers import upsert_fertilizers, upsert_nutrient_plan_with_entries

    fert_repo = get_fertilizer_repo()
    plan_repo = get_nutrient_plan_repo()
    data = load_yaml("fertilizers.yaml")

    # ── Upsert fertilizers ────────────────────────────────────────────────
    fertilizers = [_build_fertilizer(f) for f in data["fertilizers"]]
    fert_keys = upsert_fertilizers(fert_repo, fertilizers)

    # ── Resolve cross-file fertilizer references ──────────────────────────
    # Some nutrient plans reference products from other seed files (e.g.
    # PK 13-14 from plagron.yaml).  Look up any existing fertilizers in
    # the DB that are not yet in fert_keys so cross-file references
    # resolve correctly.
    all_existing, _ = fert_repo.get_all(offset=0, limit=1000)
    for fert in all_existing:
        if fert.product_name not in fert_keys:
            fert_keys[fert.product_name] = fert.key or ""

    # ── Upsert nutrient plans ─────────────────────────────────────────────
    existing_plans, _ = plan_repo.get_all(offset=0, limit=100)
    existing_plan_map = {p.name: p for p in existing_plans}

    plan_data_list = data["nutrient_plans"]
    for plan_data in plan_data_list:
        plan = _build_nutrient_plan(plan_data)
        entries = _build_phase_entries(plan_data, fert_keys)
        upsert_nutrient_plan_with_entries(plan_repo, plan, entries, existing_plan_map)

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
