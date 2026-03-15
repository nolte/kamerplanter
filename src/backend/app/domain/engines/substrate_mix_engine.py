"""Engine for calculating blended substrate properties from mix components.

Computes weighted averages for pH, EC, porosity, water retention, etc.
"""

from typing import TYPE_CHECKING

from app.common.enums import BufferCapacity, IrrigationStrategy, WaterRetention

if TYPE_CHECKING:
    from app.domain.models.substrate import MixComponent, Substrate

# Numeric encoding for ordinal enums (for weighted averaging)
_RETENTION_ORDER = {WaterRetention.LOW: 1, WaterRetention.MEDIUM: 2, WaterRetention.HIGH: 3}
_BUFFER_ORDER = {BufferCapacity.LOW: 1, BufferCapacity.MEDIUM: 2, BufferCapacity.HIGH: 3}
_IRRIGATION_PRIORITY = {
    IrrigationStrategy.CONTINUOUS: 4,
    IrrigationStrategy.FREQUENT: 3,
    IrrigationStrategy.MODERATE: 2,
    IrrigationStrategy.INFREQUENT: 1,
}


def _weighted_avg(values: list[tuple[float, float]]) -> float:
    """Weighted average of (value, fraction) pairs."""
    return sum(v * f for v, f in values)


def _weighted_optional(values: list[tuple[float | None, float]]) -> float | None:
    """Weighted average, ignoring None entries. Returns None if all None."""
    filtered = [(v, f) for v, f in values if v is not None]
    if not filtered:
        return None
    total_fraction = sum(f for _, f in filtered)
    if total_fraction == 0:
        return None
    return sum(v * f for v, f in filtered) / total_fraction


def _resolve_retention(weighted: float) -> WaterRetention:
    if weighted <= 1.5:
        return WaterRetention.LOW
    if weighted <= 2.5:
        return WaterRetention.MEDIUM
    return WaterRetention.HIGH


def _resolve_buffer(weighted: float) -> BufferCapacity:
    if weighted <= 1.5:
        return BufferCapacity.LOW
    if weighted <= 2.5:
        return BufferCapacity.MEDIUM
    return BufferCapacity.HIGH


def _resolve_irrigation(substrates: list[tuple[Substrate, float]]) -> IrrigationStrategy | None:
    """Highest-demand irrigation strategy wins (conservative approach)."""
    best_priority = 0
    best_strategy: IrrigationStrategy | None = None
    for substrate, _fraction in substrates:
        if substrate.irrigation_strategy is None:
            continue
        prio = _IRRIGATION_PRIORITY.get(substrate.irrigation_strategy, 0)
        if prio > best_priority:
            best_priority = prio
            best_strategy = substrate.irrigation_strategy
    return best_strategy


def calculate_mix_properties(
    components: list[MixComponent],
    substrates: dict[str, Substrate],
) -> dict:
    """Calculate blended substrate properties from mix components.

    Args:
        components: List of MixComponent (substrate_key + fraction).
        substrates: Map of substrate_key → Substrate for all referenced components.

    Returns:
        Dict of calculated properties for the blended substrate.
    """
    pairs: list[tuple[Substrate, float]] = []
    for comp in components:
        sub = substrates[comp.substrate_key]
        pairs.append((sub, comp.fraction))

    ph = _weighted_avg([(s.ph_base, f) for s, f in pairs])
    ec = _weighted_avg([(s.ec_base_ms, f) for s, f in pairs])
    porosity = _weighted_avg([(s.air_porosity_percent, f) for s, f in pairs])

    retention_num = _weighted_avg([(_RETENTION_ORDER[s.water_retention], f) for s, f in pairs])
    buffer_num = _weighted_avg([(_BUFFER_ORDER[s.buffer_capacity], f) for s, f in pairs])

    whc = _weighted_optional([(s.water_holding_capacity_percent, f) for s, f in pairs])
    eaw = _weighted_optional([(s.easily_available_water_percent, f) for s, f in pairs])
    cec = _weighted_optional([(s.cec_meq_per_100g, f) for s, f in pairs])
    bulk = _weighted_optional([(s.bulk_density_g_per_l, f) for s, f in pairs])

    # Merged composition: combine raw-material compositions weighted by fraction
    merged_composition: dict[str, float] = {}
    for sub, frac in pairs:
        for material, amount in sub.composition.items():
            merged_composition[material] = merged_composition.get(material, 0.0) + amount * frac

    # Reusability: mix is reusable only if all components are reusable
    all_reusable = all(s.reusable for s, _ in pairs)
    min_cycles = min((s.max_reuse_cycles for s, _ in pairs), default=1)

    # Dominant type: component with largest fraction determines type
    dominant = max(pairs, key=lambda p: p[1])

    return {
        "type": dominant[0].type,
        "ph_base": round(ph, 2),
        "ec_base_ms": round(ec, 3),
        "air_porosity_percent": round(porosity, 1),
        "water_retention": _resolve_retention(retention_num),
        "buffer_capacity": _resolve_buffer(buffer_num),
        "water_holding_capacity_percent": round(whc, 1) if whc is not None else None,
        "easily_available_water_percent": round(eaw, 1) if eaw is not None else None,
        "cec_meq_per_100g": round(cec, 1) if cec is not None else None,
        "bulk_density_g_per_l": round(bulk, 1) if bulk is not None else None,
        "composition": {k: round(v, 4) for k, v in merged_composition.items()},
        "reusable": all_reusable,
        "max_reuse_cycles": min_cycles if all_reusable else 1,
        "irrigation_strategy": _resolve_irrigation(pairs),
    }
