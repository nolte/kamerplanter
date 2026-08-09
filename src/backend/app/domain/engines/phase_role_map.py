"""D8 engine-role mapping (REQ-003 Lifecycle-Vollständigkeits-Audit).

The seed data uses 36 archetype-specific phase names in addition to the 17
engine-core phases. Each extended phase behaves — for state-machine purposes —
like one of the core phases. This module is the single source of that mapping so
every engine (transition, resource resolver, cyclic) resolves an extended phase
to the same core role instead of re-deriving it.

Per-record ``is_recurring`` / ``is_terminal`` / ``allows_harvest`` on the
``GrowthPhase`` always win; this map only supplies the default core role and the
coarse classifications (rest / productive / establishment) used when a phase has
no explicit flags.
"""

from __future__ import annotations

# Extended phase name -> core engine phase it behaves like (REQ-003 §D8 table).
# Core phases map to themselves and are omitted for brevity (see CORE_PHASES).
_EXTENDED_TO_CORE: dict[str, str] = {
    # Reproduction / flowering fine-phases
    "pre_bloom": "flowering",
    "bud_formation": "flowering",
    "budding": "flowering",
    "growth_bloom": "flowering",
    "flowering_fruit": "flowering",
    "fruiting": "fruit_development",
    "autumn_growth_bloom": "flowering",
    "rest_after_bloom": "dormancy",
    "bract_coloring": "flowering",
    "short_day_induction": "flowering",
    # CAM / succulent rest
    "winter_rest": "dormancy",
    "summer_rest": "dormancy",
    "cool_rest": "dormancy",
    "rest_phase": "dormancy",
    "rest": "dormancy",
    "winter_dormancy": "dormancy",
    "summer_dormancy": "dormancy",
    "winter_hull_change": "dormancy",
    # Geophyte fine-phases
    "sprouting": "bud_break",
    "sprout_formation": "bud_break",
    "corm_ripening": "senescence",
    "tuber_formation": "fruit_development",
    "bulbil_establishment": "seedling",
    "dry_storage": "dormancy",
    # Establishment / maturity / special culture
    "establishment": "seedling",
    "pup_establishment": "seedling",
    "young_palm": "vegetative",
    "shaft_growth": "vegetative",
    "leaf_phase": "active_growth",
    "juvenile": "vegetative",
    "climbing": "vegetative",
    "mature": "vegetative",
    "recovery": "repotting_recovery",
    "spring_growth": "active_growth",
    "autumn_ripening": "ripening",
}

CORE_PHASES: frozenset[str] = frozenset(
    {
        "germination",
        "rooting",
        "seedling",
        "vegetative",
        "bolting",
        "flowering",
        "ripening",
        "dormancy",
        "flushing",
        "bud_break",
        "fruit_development",
        "senescence",
        "hardening_off",
        "acclimatization",
        "active_growth",
        "maintenance",
        "repotting_recovery",
    }
)

# Core phases whose role is "a rest / no-feed / minimal-water period".
_REST_CORE: frozenset[str] = frozenset({"dormancy"})
# Core phases whose role is "productive — harvest may occur".
_PRODUCTIVE_CORE: frozenset[str] = frozenset({"ripening", "fruit_development", "flowering"})

# Core engine phase -> the coarse EC/nutrient-plan phase vocabulary (``PhaseName``)
# the EC-budget engine keys its EC_MAX table on. That table distinguishes only
# seedling / vegetative / flowering / flushing (every other value falls to a
# neutral range), so the 17 core phases collapse onto the seven-value nutrient
# vocabulary here. Built on top of ``core_phase`` so a fine-typed phase from the
# v0027 phase-definition catalogue (``active_growth``, ``establishment``,
# ``bract_coloring``, ``tuber_formation``, …) resolves through the same single
# source every other engine already uses, instead of the pre-#576 ``PhaseName``
# enum the catalogue replaced. Every core phase is mapped explicitly so a new
# core phase fails the ``test_ec_phase_covers_every_core_phase`` guard rather
# than silently defaulting.
_CORE_TO_EC_PHASE: dict[str, str] = {
    # Establishment: young/recovering roots feed gently.
    "germination": "germination",
    "rooting": "seedling",
    "seedling": "seedling",
    "hardening_off": "seedling",
    "acclimatization": "seedling",
    "repotting_recovery": "seedling",
    # Vegetative growth: the steady-state feeding band.
    "vegetative": "vegetative",
    "active_growth": "vegetative",
    "maintenance": "vegetative",
    "bud_break": "vegetative",
    # Reproductive / high-demand: flowering-band EC.
    "bolting": "flowering",
    "flowering": "flowering",
    "fruit_development": "flowering",
    # Winding down.
    "ripening": "ripening",
    "senescence": "ripening",
    # Rest and flush keep their own regimes.
    "dormancy": "dormancy",
    "flushing": "flushing",
}


def core_phase(name: str) -> str:
    """Resolve an (extended or core) phase name to its core engine phase."""
    if name in CORE_PHASES:
        return name
    return _EXTENDED_TO_CORE.get(name, name)


def ec_phase(name: str) -> str:
    """Resolve any (fine, extended or core) phase name to the coarse EC-budget phase.

    Returns one of the ``PhaseName`` values the EC-budget engine understands. An
    unknown name resolves to ``vegetative`` — the engine's own neutral default —
    so a caller passing a phase this map has never seen still gets a sane feeding
    band rather than an error. Runs the name through :func:`core_phase` first, so
    the whole extended/fine-typed vocabulary is covered via one mapping.
    """
    return _CORE_TO_EC_PHASE.get(core_phase(name), "vegetative")


def is_rest_phase(name: str) -> bool:
    """True if the phase is a dormancy/rest period (no feed, minimal water)."""
    return core_phase(name) in _REST_CORE


def is_productive_phase(name: str) -> bool:
    """True if the phase is a productive/harvestable period."""
    return core_phase(name) in _PRODUCTIVE_CORE
