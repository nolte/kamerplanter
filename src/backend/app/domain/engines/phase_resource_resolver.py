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

# Waterlogging tolerance -> multiplier on the phase-modulated volume. A sensitive
# root zone gets less water per event (drainage/anoxia risk), a tolerant one may
# take more. Applied AFTER the per-phase factor so a phase that legitimately needs
# elevated volume (flowering/flushing) is not silently clamped to the base for the
# common ``moderate``/unset case.
_WATERLOGGING_VOLUME_CAP: dict[str, float] = {
    "sensitive": 0.7,
    "moderate": 1.0,
    "tolerant": 1.3,
}

# Per-phase volume factor relative to the vegetative baseline (core-phase keyed).
# Consolidated from the former WateringVolumeEngine._PHASE_FACTOR so the resolver is
# the single authoritative phase-modulation source; extended phase names inherit the
# factor of their core phase via ``core_phase`` (e.g. pre_bloom -> flowering). Rest
# phases, flushing and dry_storage are handled by their dedicated regimes below.
_PHASE_VOLUME_FACTOR: dict[str, float] = {
    "germination": 0.30,
    "seedling": 0.50,
    "flowering": 1.20,
    "ripening": 0.60,  # formerly the retired "harvest" phase (0.60)
}

# Flushing gets an elevated water-only volume to leach accumulated salts.
_FLUSHING_VOLUME_FACTOR = 1.40
# Rest/dormancy: minimal maintenance water.
_REST_VOLUME_FACTOR = 0.25

# E8 pH-gating: most micronutrients (Fe, Mn, Zn, Cu, B) are most available in the
# slightly-acidic window pH 6.0–6.5 (soil_ph_preference, REQ-001); molybdenum is the
# inverse — its availability rises as pH climbs.
_MICRO_PH_OPTIMAL_MIN = 6.0
_MICRO_PH_OPTIMAL_MAX = 6.5


def ph_micronutrient_availability(target_ph: float) -> tuple[bool, str]:
    """E8: whether the phase target pH keeps micronutrients available, plus a note.

    Pure lookup — returns ``(available, note)`` where ``available`` is True only inside
    the optimal micronutrient window. Above the window the base micros (Fe/Mn/Zn/Cu/B)
    lock out while molybdenum stays available; below it micro uptake rises but Mo and
    phosphorus drop.
    """
    if target_ph > _MICRO_PH_OPTIMAL_MAX:
        return False, (
            f"pH {target_ph} above {_MICRO_PH_OPTIMAL_MAX}: Fe/Mn/Zn/Cu/B lock out "
            "(chlorosis risk); molybdenum stays available"
        )
    if target_ph < _MICRO_PH_OPTIMAL_MIN:
        return False, (
            f"pH {target_ph} below {_MICRO_PH_OPTIMAL_MIN}: micronutrient uptake rises "
            "but molybdenum and phosphorus availability drop"
        )
    return True, (
        f"pH {target_ph} within the optimal micronutrient window ({_MICRO_PH_OPTIMAL_MIN}-{_MICRO_PH_OPTIMAL_MAX})"
    )


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
    # E8 pH-gating — the phase target pH and the resulting micronutrient availability.
    target_ph: float = 6.0
    micros_available: bool = True
    ph_note: str = ""


def resolve_irrigation(
    phase_name: str,
    *,
    base_frequency_days: float = 3.0,
    base_volume_ml: float = 300.0,
    waterlogging_tolerance: str | None = None,
) -> IrrigationRegime:
    """E7: resolve the irrigation regime for a phase.

    ``base_volume_ml`` is the caller's already-resolved per-event volume (from the
    phase profile / species guide / container calc). This function applies the
    authoritative per-phase factor and the waterlogging-tolerance multiplier on top
    of it, so the watering engine no longer needs its own phase-factor table.
    """
    core = core_phase(phase_name)
    tolerance_factor = _WATERLOGGING_VOLUME_CAP.get(waterlogging_tolerance or "moderate", 1.0)

    # ``dry_storage`` maps to dormancy but is drier than a normal rest — check first.
    if phase_name == "dry_storage":
        return IrrigationRegime(0.0, 0.0, water_only=True, note="dry storage — no watering")
    if is_rest_phase(phase_name):
        return IrrigationRegime(
            frequency_days=base_frequency_days * 4,
            volume_ml_per_plant=base_volume_ml * _REST_VOLUME_FACTOR * tolerance_factor,
            water_only=True,
            note="rest/dormancy — minimal water, no feed",
        )
    if core == "flushing":
        return IrrigationRegime(
            frequency_days=base_frequency_days,
            volume_ml_per_plant=base_volume_ml * _FLUSHING_VOLUME_FACTOR * tolerance_factor,
            water_only=True,
            note="flush — water only, elevated volume to leach salts",
        )
    if core in ("germination", "seedling"):
        return IrrigationRegime(
            frequency_days=max(1.0, base_frequency_days / 2),
            volume_ml_per_plant=base_volume_ml * _PHASE_VOLUME_FACTOR[core] * tolerance_factor,
            water_only=False,
            note="establishment — frequent, low volume",
        )
    factor = _PHASE_VOLUME_FACTOR.get(core, 1.0)
    if factor > 1.0:
        note = f"{core} — elevated volume (x{factor})"
    elif factor < 1.0:
        note = f"{core} — reduced volume (x{factor})"
    else:
        note = "standard"
    return IrrigationRegime(
        frequency_days=base_frequency_days,
        volume_ml_per_plant=base_volume_ml * factor * tolerance_factor,
        water_only=False,
        note=note,
    )


def resolve_nutrient(
    phase_name: str,
    *,
    base_npk: tuple[int, int, int] = (3, 1, 2),
    base_ec_ms: float = 1.5,
    base_ph: float = 6.0,
    nutrient_demand_level: NutrientDemandLevel | None = None,
) -> NutrientRegime:
    """E8: resolve the nutrient regime for a phase.

    Surfaces the per-phase ``target_ph`` and the pH-gated micronutrient availability
    (``micros_available`` / ``ph_note``) alongside the NPK/EC guidance, so the caller
    can warn when the phase pH would lock micronutrients out.
    """
    micros_available, ph_note = ph_micronutrient_availability(base_ph)
    if is_rest_phase(phase_name):
        return NutrientRegime(
            feed=False,
            npk_ratio=(0, 0, 0),
            target_ec_ms=0.0,
            note="rest/dormancy — no feed",
            target_ph=base_ph,
            micros_available=micros_available,
            ph_note=ph_note,
        )
    core = core_phase(phase_name)
    if core == "flushing":
        return NutrientRegime(
            feed=False,
            npk_ratio=(0, 0, 0),
            target_ec_ms=0.0,
            note="flush — 0-0-0",
            target_ph=base_ph,
            micros_available=micros_available,
            ph_note=ph_note,
        )
    factor = _FEEDER_EC_FACTOR.get(nutrient_demand_level or NutrientDemandLevel.MEDIUM_FEEDER, 1.0)
    return NutrientRegime(
        feed=True,
        npk_ratio=base_npk,
        target_ec_ms=round(base_ec_ms * factor, 2),
        note=f"feed scaled by {nutrient_demand_level.value if nutrient_demand_level else 'medium_feeder'}",
        target_ph=base_ph,
        micros_available=micros_available,
        ph_note=ph_note,
    )
