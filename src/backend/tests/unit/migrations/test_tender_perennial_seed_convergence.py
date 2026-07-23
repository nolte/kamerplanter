"""Seed convergence proof for the tender-perennial reclassification (ADR-006 E1).

Eleven frost-tender species (tomato, pepper, basil, geranium, …) are botanically
``perennial`` but cultivated as annuals. Classifying them botanically perennial activates
``LifecycleResponse.grown_as_annual`` while the effective (cultivation) cycle keeps every
lifecycle engine treating them as annuals.

The botanical ``cycle_type`` is set from MULTIPLE seed sources whose order decides the final
value (``perennial_species`` in species.yaml for base species; per-file ``lifecycle_configs``
blocks in the plant-info files and adventskalender.yaml, applied by the later seed jobs). A
single leftover ``annual`` in any of those sources would let a later seed job reset the
botanical cycle back to annual and silently defeat the reclassification. These tests read the
*real* seed YAML and prove full convergence:

1. every seed source that names one of the eleven agrees on ``cycle_type = perennial``;
2. each carries ``cultivation_cycle_type = annual`` in lifecycle_overrides;
3. the resulting LifecycleResponse reports ``grown_as_annual = True``;
4. the effective (annual) cycle routes the seed phase-sequence linker to ``indoor_default``
   (with ripening/harvest), NOT the harvest-less ``evergreen_foliage_perennial``.
"""

from __future__ import annotations

import pytest

from app.api.v1.lifecycle_configs.schemas import LifecycleResponse
from app.common.enums import CycleType, PhotoperiodType
from app.domain.engines.cycle_resolver import resolve_effective_cycle
from app.domain.models.lifecycle import LifecycleConfig
from app.migrations.perennial_binding import resolve_phase_sequence_name
from app.migrations.yaml_loader import load_yaml

#: The eleven tender perennials reclassified botanically perennial (grown as annuals).
_TENDER_PERENNIALS = (
    "Begonia semperflorens",
    "Capsicum annuum",
    "Impatiens walleriana",
    "Ocimum basilicum",
    "Pelargonium zonale",
    "Petunia x hybrida",
    "Physalis peruviana",
    "Solanum lycopersicum",
    "Solanum melongena",
    "Verbena x hybrida",
    "Viola x wittrockiana",
)

#: Every seed file whose ``lifecycle_configs`` block may set the botanical cycle_type.
_LIFECYCLE_CONFIG_FILES = (
    "plant_info.yaml",
    "plant_info_indoor_1.yaml",
    "plant_info_indoor_2.yaml",
    "plant_info_indoor_3.yaml",
    "plant_info_indoor_4.yaml",
    "plant_info_outdoor_1.yaml",
    "plant_info_outdoor_3.yaml",
    "plant_info_supplement_1.yaml",
    "adventskalender.yaml",
)

#: Every seed file whose ``new_species``/``species`` block may carry the resolver attributes.
_SPECIES_ATTR_FILES = (
    "species.yaml",
    "plant_info.yaml",
    "plant_info_indoor_1.yaml",
    "plant_info_indoor_2.yaml",
    "plant_info_indoor_3.yaml",
    "plant_info_indoor_4.yaml",
    "plant_info_outdoor_1.yaml",
    "plant_info_outdoor_2.yaml",
    "plant_info_outdoor_3.yaml",
    "plant_info_supplement_1.yaml",
)


def _perennial_species() -> set[str]:
    return set(load_yaml("species.yaml").get("perennial_species", []))


def _lifecycle_overrides() -> dict[str, dict]:
    return load_yaml("species.yaml").get("lifecycle_overrides", {}) or {}


def _cycle_type_sources(scientific_name: str) -> list[tuple[str, str]]:
    """Collect every seeded botanical cycle_type for a species as ``(source, cycle_type)``."""
    sources: list[tuple[str, str]] = []
    species_yaml = load_yaml("species.yaml")
    base_names = {s["scientific_name"] for s in species_yaml.get("species", [])}
    if scientific_name in base_names:
        in_perennial = scientific_name in _perennial_species()
        sources.append(("species.yaml:perennial_species", "perennial" if in_perennial else "annual"))
    for filename in _LIFECYCLE_CONFIG_FILES:
        block = (load_yaml(filename).get("lifecycle_configs") or {}).get(scientific_name)
        if block and "cycle_type" in block:
            sources.append((f"{filename}:lifecycle_configs", block["cycle_type"]))
    return sources


def _species_attrs(scientific_name: str) -> dict:
    """Return ``photosynthesis_type``/``growth_habit`` for a species across all seed files."""
    attrs: dict = {}
    for filename in _SPECIES_ATTR_FILES:
        data = load_yaml(filename)
        for block in (data.get("species") or [], data.get("new_species") or []):
            for entry in block:
                if entry.get("scientific_name") == scientific_name:
                    attrs.update(
                        {
                            "photosynthesis_type": entry.get("photosynthesis_type"),
                            "growth_habit": entry.get("growth_habit"),
                        }
                    )
    return attrs


@pytest.mark.parametrize("scientific_name", _TENDER_PERENNIALS)
def test_all_cycle_type_sources_agree_on_perennial(scientific_name: str) -> None:
    """No seed source may leave a stale ``annual`` that a later seed job could re-apply."""
    sources = _cycle_type_sources(scientific_name)
    assert sources, f"{scientific_name} has no seeded botanical cycle_type at all"
    annual_sources = [src for src, cycle in sources if cycle != "perennial"]
    assert not annual_sources, f"{scientific_name} still seeded annual by: {annual_sources}"


@pytest.mark.parametrize("scientific_name", _TENDER_PERENNIALS)
def test_cultivation_cycle_type_is_annual(scientific_name: str) -> None:
    """Each tender perennial carries the ``cultivation_cycle_type=annual`` override."""
    override = _lifecycle_overrides().get(scientific_name, {})
    assert override.get("cultivation_cycle_type") == "annual"


@pytest.mark.parametrize("scientific_name", _TENDER_PERENNIALS)
def test_lifecycle_response_reports_grown_as_annual(scientific_name: str) -> None:
    """The seeded (perennial + cultivation-annual) shape yields grown_as_annual=True."""
    response = LifecycleResponse(
        key="lc-1",
        species_key="sp-1",
        cycle_type=CycleType.PERENNIAL,
        cultivation_cycle_type=CycleType.ANNUAL,
        typical_lifespan_years=None,
        dormancy_required=False,
        vernalization_required=False,
        vernalization_min_days=None,
        photoperiod_type=PhotoperiodType.DAY_NEUTRAL,
        critical_day_length_hours=None,
    )
    assert response.grown_as_annual is True


@pytest.mark.parametrize("scientific_name", _TENDER_PERENNIALS)
def test_effective_annual_cycle_binds_indoor_default(scientific_name: str) -> None:
    """The effective (annual) cycle routes the linker to indoor_default, not evergreen."""
    override = _lifecycle_overrides().get(scientific_name, {})
    lifecycle = LifecycleConfig(
        species_key="sp-1",
        cycle_type=CycleType.PERENNIAL,
        cultivation_cycle_type=CycleType(override["cultivation_cycle_type"]),
    )
    effective = resolve_effective_cycle(None, lifecycle)
    assert effective == CycleType.ANNUAL

    attrs = _species_attrs(scientific_name)
    target = resolve_phase_sequence_name(
        scientific_name,
        cycle_type=effective.value,
        flowering_strategy=override.get("flowering_strategy"),
        photosynthesis_type=attrs.get("photosynthesis_type"),
        photoperiod_type="day_neutral",
        growth_habit=attrs.get("growth_habit"),
    )
    # None → the linker applies the ``indoor_default`` last-resort blanket (harvest-bearing).
    assert target is None


def test_tomato_flagship_end_to_end() -> None:
    """Explicit flagship assertion for Solanum lycopersicum (the tender-perennial exemplar)."""
    name = "Solanum lycopersicum"
    assert all(cycle == "perennial" for _, cycle in _cycle_type_sources(name))
    assert _lifecycle_overrides()[name]["cultivation_cycle_type"] == "annual"
