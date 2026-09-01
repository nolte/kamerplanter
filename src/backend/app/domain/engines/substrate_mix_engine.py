"""Engine for calculating blended substrate properties from mix components.

Weighting is per-property physics, not one-size-fits-all:

* Per-volume properties (porosity, water retention, WHC, EAW, bulk density,
  EC) are volume-weighted by the component fractions, which are volume shares.
* CEC is **also** volume-weighted, because the catalogue's values are per unit
  VOLUME (``cec_meq_per_100cm3``) — see below.
* pH is buffering-weighted: a blend's pH is set by the fraction that actually
  buffers, not by volume. An inert diluent (near-zero CEC) dilutes the medium
  toward the buffered component's set point rather than shifting it linearly.

The CEC unit, and why this reverts part of #1099 (#1152 §F)
-----------------------------------------------------------

#1099 read the old field name ``cec_meq_per_100g`` as a statement of fact and
mass-weighted accordingly. The values do not support that reading: seven of seven
sampled materials land outside their literature band as written, and inside it
once divided by bulk density. Peat at 10 against a literature 100–200; vermiculite
at 15 against 100–150; perlite at 0.1 against ≈1.5. They behave as meq per 100 cm³.

The field is renamed to say so, and the weighting follows the values rather than
the old label. The divergence is not academic: a 50/50 blend of perlite (100 g/L)
and worm humus (600 g/L) computes 15.1 volume-weighted and 25.7 mass-weighted —
70 %, growing with the density spread of the components. It stayed unnoticed
because the blends people actually had were made of similarly dense media.

``bulk_density_g_per_l`` is still required wherever CEC is declared, and
``_mass_fractions`` still exists: bulk density is a mix output in its own right,
and keeping the conversion available is what makes the other reading testable
rather than merely arguable.

See issue #1099 (defects 2 and 3) and #1152 §F, which corrects defect 3.
"""

from app.common.enums import BufferCapacity, IrrigationStrategy, WaterRetention
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

# Representative CEC (meq/100 g) used only as a buffering-weight fallback when a
# component does not declare cec_meq_per_100cm3. Ordinal buffer_capacity is the
# coarse stand-in the model offers; these magnitudes keep an inert (low) tier
# well below a limed (medium/high) tier.
_BUFFER_NOMINAL_CEC = {BufferCapacity.LOW: 1.0, BufferCapacity.MEDIUM: 8.0, BufferCapacity.HIGH: 20.0}


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


def _mass_fractions(pairs: list[tuple[Substrate, float]]) -> list[float] | None:
    """Convert volume fractions to mass fractions via bulk density.

    Returns None when any component lacks a bulk density (mass conversion
    impossible) or the total mass is zero, so callers can fall back to
    volume-weighting.
    """
    masses: list[float] = []
    for sub, fraction in pairs:
        if sub.bulk_density_g_per_l is None:
            return None
        masses.append(sub.bulk_density_g_per_l * fraction)
    total = sum(masses)
    if total == 0:
        return None
    return [m / total for m in masses]


def _effective_cec(sub: Substrate) -> float:
    """Buffering magnitude of a component: declared CEC, else a buffer-tier proxy."""
    if sub.cec_meq_per_100cm3 is not None:
        return sub.cec_meq_per_100cm3
    return _BUFFER_NOMINAL_CEC[sub.buffer_capacity]


def _buffering_weighted_ph(pairs: list[tuple[Substrate, float]]) -> float:
    """Blend pH weighted by buffering capacity rather than by volume.

    Each component's pH weight is its volume fraction scaled by the cube root of
    its (effective) CEC. The cube-root damping credits an inert diluent with the
    partial pore-water participation it really has — a raw CEC weight would pin
    the pH almost entirely to the strongest buffer, a volume weight ignores
    buffering altogether. When buffering is equal across components the weights
    reduce to the volume fractions, so the blend is the plain volume-weighted
    mean (see the control case in the tests).
    """
    weights = [(sub.ph_base, fraction * (_effective_cec(sub) ** (1.0 / 3.0))) for sub, fraction in pairs]
    total_weight = sum(w for _, w in weights)
    if total_weight == 0:
        # Every component is fully inert (CEC 0): nothing buffers, fall back to
        # the volume-weighted mean.
        return _weighted_avg([(sub.ph_base, fraction) for sub, fraction in pairs])
    return sum(ph * w for ph, w in weights) / total_weight


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

    # pH is buffering-weighted (per-mass buffering, not volume) — issue #1099 #2.
    ph = _buffering_weighted_ph(pairs)

    # Per-volume properties: volume-weighted by the component fractions.
    ec = _weighted_avg([(s.ec_base_ms, f) for s, f in pairs])
    # Optional, not required: a component may decline to have an air porosity at
    # all (`Hydrokultur (kein Substrat)`, #1175). `_weighted_optional` renormalises
    # over the components that do declare one, which is the right reading here —
    # a nutrient-solution share contributes no pore space to average in, and
    # `_weighted_avg` would have folded its `None` in as a `TypeError` or, before
    # the field was nullable, as a placeholder 100 that pulled every mix containing
    # it upwards.
    porosity = _weighted_optional([(s.air_porosity_percent, f) for s, f in pairs])

    retention_num = _weighted_avg([(_RETENTION_ORDER[s.water_retention], f) for s, f in pairs])
    buffer_num = _weighted_avg([(_BUFFER_ORDER[s.buffer_capacity], f) for s, f in pairs])

    whc = _weighted_optional([(s.water_holding_capacity_percent, f) for s, f in pairs])
    eaw = _weighted_optional([(s.easily_available_water_percent, f) for s, f in pairs])
    bulk = _weighted_optional([(s.bulk_density_g_per_l, f) for s, f in pairs])

    # CEC is declared per 100 cm³ of VOLUME, so the component fractions — which are
    # volume shares — weight it directly (#1152 §F). #1099 mass-weighted this on the
    # strength of the old field name; the values never supported that reading, and
    # converting them made a correct number wrong by up to 70 % on a density-spread
    # blend.
    cec = _weighted_optional([(s.cec_meq_per_100cm3, f) for s, f in pairs])

    # Merged composition: combine raw-material compositions weighted by fraction
    merged_composition: dict[str, float] = {}
    for sub, frac in pairs:
        for material, amount in sub.composition.items():
            merged_composition[material] = merged_composition.get(material, 0.0) + amount * frac

    # Additives carry no quantity, so they merge as a set union rather than a
    # weighted sum (#1175). Propagating them at all is the point: a blend of a
    # limed peat and an inert diluent is still limed, and the whole reason the
    # additives left `composition` is that nothing downstream could read a lime
    # fraction correctly. Dropping them here would have moved the loss one layer
    # down instead of fixing it.
    merged_additives = sorted({a for sub, _ in pairs for a in sub.additives})

    # Reusability: mix is reusable only if all components are reusable
    all_reusable = all(s.reusable for s, _ in pairs)
    min_cycles = min((s.max_reuse_cycles for s, _ in pairs), default=1)

    # Dominant type: component with largest fraction determines type
    dominant = max(pairs, key=lambda p: p[1])

    return {
        "type": dominant[0].type,
        "ph_base": round(ph, 2),
        "ec_base_ms": round(ec, 3),
        "air_porosity_percent": round(porosity, 1) if porosity is not None else None,
        "water_retention": _resolve_retention(retention_num),
        "buffer_capacity": _resolve_buffer(buffer_num),
        "water_holding_capacity_percent": round(whc, 1) if whc is not None else None,
        "easily_available_water_percent": round(eaw, 1) if eaw is not None else None,
        "cec_meq_per_100cm3": round(cec, 1) if cec is not None else None,
        "bulk_density_g_per_l": round(bulk, 1) if bulk is not None else None,
        "composition": {k: round(v, 4) for k, v in merged_composition.items()},
        "additives": merged_additives,
        "reusable": all_reusable,
        "max_reuse_cycles": min_cycles if all_reusable else 1,
        "irrigation_strategy": _resolve_irrigation(pairs),
    }
