"""Phase-driven irrigation & nutrient regime resolver (REQ-003 E7/E8).

Consolidates the per-phase resource rules into one place so the watering and
nutrient services apply the same lifecycle logic:

* **E7 irrigation** — germination/seedling get frequent low-volume watering; rest
  phases (dormancy / winter_rest / …) get minimal water; ``flushing`` is
  water-only; ``dry_storage`` (geophytes) is dry; ``waterlogging_tolerance`` caps
  the volume.
* **E8 nutrients** — rest phases get no feed; ``flushing`` is 0-0-0; otherwise the
  EC target is scaled by the species ``nutrient_demand_level`` (feeder class).

Pure logic — callers pass the base profile values; the ET/sensor override
(REQ-037/005) and the tank/mixing wiring (REQ-004/014) stay in their services and
consume the regime produced here.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.common.enums import NutrientDemandLevel
from app.domain.engines.phase_role_map import core_phase, is_rest_phase

# EC scaling per feeder class (multiplies the phase base EC target).
_FEEDER_EC_FACTOR: dict[NutrientDemandLevel, float] = {
    NutrientDemandLevel.HEAVY_FEEDER: 1.15,
    NutrientDemandLevel.MEDIUM_FEEDER: 1.0,
    NutrientDemandLevel.LIGHT_FEEDER: 0.7,
    NutrientDemandLevel.NITROGEN_FIXER: 0.6,
}

# Waterlogging tolerance -> max fraction of the base volume that may be applied.
_WATERLOGGING_VOLUME_CAP: dict[str, float] = {
    "sensitive": 0.7,
    "moderate": 1.0,
    "tolerant": 1.3,
}


@dataclass(frozen=True)
class IrrigationRegime:
    """Effective per-phase irrigation guidance."""

    frequency_days: float
    volume_ml_per_plant: float
    water_only: bool  # flushing / rest — water without nutrients
    note: str


@dataclass(frozen=True)
class NutrientRegime:
    """Effective per-phase nutrient guidance."""

    feed: bool
    npk_ratio: tuple[int, int, int]
    target_ec_ms: float
    note: str


def resolve_irrigation(
    phase_name: str,
    *,
    base_frequency_days: float = 3.0,
    base_volume_ml: float = 300.0,
    waterlogging_tolerance: str | None = None,
) -> IrrigationRegime:
    """E7: resolve the irrigation regime for a phase."""
    core = core_phase(phase_name)
    cap = _WATERLOGGING_VOLUME_CAP.get(waterlogging_tolerance or "moderate", 1.0)
    max_volume = base_volume_ml * cap

    if phase_name == "dry_storage":
        return IrrigationRegime(0.0, 0.0, water_only=True, note="dry storage — no watering")
    if is_rest_phase(phase_name):
        # rest: much less frequent, minimal volume
        return IrrigationRegime(
            frequency_days=base_frequency_days * 4,
            volume_ml_per_plant=min(base_volume_ml * 0.25, max_volume),
            water_only=True,
            note="rest/dormancy — minimal water, no feed",
        )
    if core == "flushing":
        return IrrigationRegime(
            base_frequency_days, min(base_volume_ml, max_volume), water_only=True, note="flush — water only"
        )
    if core in ("germination", "seedling"):
        return IrrigationRegime(
            frequency_days=max(1.0, base_frequency_days / 2),
            volume_ml_per_plant=min(base_volume_ml * 0.4, max_volume),
            water_only=False,
            note="establishment — frequent, low volume",
        )
    return IrrigationRegime(base_frequency_days, min(base_volume_ml, max_volume), water_only=False, note="standard")


def resolve_nutrient(
    phase_name: str,
    *,
    base_npk: tuple[int, int, int] = (3, 1, 2),
    base_ec_ms: float = 1.5,
    nutrient_demand_level: NutrientDemandLevel | None = None,
) -> NutrientRegime:
    """E8: resolve the nutrient regime for a phase."""
    core = core_phase(phase_name)
    if is_rest_phase(phase_name):
        return NutrientRegime(feed=False, npk_ratio=(0, 0, 0), target_ec_ms=0.0, note="rest/dormancy — no feed")
    if core == "flushing":
        return NutrientRegime(feed=False, npk_ratio=(0, 0, 0), target_ec_ms=0.0, note="flush — 0-0-0")
    factor = _FEEDER_EC_FACTOR.get(nutrient_demand_level or NutrientDemandLevel.MEDIUM_FEEDER, 1.0)
    return NutrientRegime(
        feed=True,
        npk_ratio=base_npk,
        target_ec_ms=round(base_ec_ms * factor, 2),
        note=f"feed scaled by {nutrient_demand_level.value if nutrient_demand_level else 'medium_feeder'}",
    )
