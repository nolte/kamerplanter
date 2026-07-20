"""Seed↔migration convergence proof for the short-day ornamental cohort (#676 / NCT-1).

The 11 photoperiodic short-day ornamentals must bind to ``photoperiodic_ornamental`` on a
**fresh install** exactly as the ``v0027`` rebind migration binds them on an **existing**
install. Fresh installs derive the binding from the attribute-driven resolver
(:func:`~app.migrations.perennial_binding.resolve_phase_sequence_name`) fed by the seeded
``lifecycle_configs`` block and the species attributes; ``v0027`` carries the frozen
:data:`_TARGET_SEQUENCE`. Before #676 the cohort carried no ``lifecycle_configs`` block, so
the resolver saw ``photoperiod_type = None`` and could not fire Rule 1 → the CAM members
(Kalanchoe, Schlumbergera) fell through to Rule 3 (``cam_succulent_rest``), diverging from
the migration. This test reads the *real* seed YAML and proves the divergence is closed —
with the CAM members asserted explicitly, since they are the audit's residual-drift risk.
"""

from __future__ import annotations

import pytest

from app.migrations.perennial_binding import (
    PHOTOPERIODIC_ORNAMENTAL_SEQUENCE,
    resolve_phase_sequence_name,
)
from app.migrations.versions.v0027_finetype_cam_monocarp_photoperiodic_sequences import (
    _TARGET_SEQUENCE,
)
from app.migrations.yaml_loader import load_yaml

#: Every plant-info seed file the cohort's species and lifecycle blocks may live in.
_PLANT_INFO_FILES = (
    "plant_info.yaml",
    "plant_info_indoor_1.yaml",
    "plant_info_indoor_2.yaml",
    "plant_info_indoor_3.yaml",
    "plant_info_indoor_4.yaml",
    "plant_info_supplement_1.yaml",
)

#: The cohort is the SSOT slice of ``v0027`` that targets the photoperiodic sequence —
#: derived (not hard-coded) so the test tracks the migration if membership ever changes.
_SHORT_DAY_ORNAMENTALS = tuple(
    name for name, seq in _TARGET_SEQUENCE.items() if seq == PHOTOPERIODIC_ORNAMENTAL_SEQUENCE
)

#: CAM cohort members — the audit's "residual Seed↔Migration divergence": Rule 1 (short-day)
#: MUST beat Rule 3 (CAM) so these do NOT land on ``cam_succulent_rest``.
_CAM_COHORT_MEMBERS = frozenset({"Kalanchoe blossfeldiana", "Kalanchoe daigremontiana", "Schlumbergera truncata"})

_PERENNIAL = "perennial"
_SHORT_DAY = "short_day"
_CAM = "cam"


def _load_seeded_attributes() -> tuple[dict[str, dict], dict[str, dict]]:
    """Return ``(species_attr, lifecycles)`` keyed by scientific name across all seed files."""
    species_attr: dict[str, dict] = {}
    lifecycles: dict[str, dict] = {}
    for filename in _PLANT_INFO_FILES:
        data = load_yaml(filename)
        for species in data.get("new_species") or []:
            species_attr[species["scientific_name"]] = species
        for name, config in (data.get("lifecycle_configs") or {}).items():
            lifecycles[name] = config
    return species_attr, lifecycles


@pytest.fixture(scope="module")
def seeded() -> tuple[dict[str, dict], dict[str, dict]]:
    return _load_seeded_attributes()


def test_cohort_has_exactly_eleven_members() -> None:
    """Guard the ``11`` in the issue against silent v0027 edits."""
    assert len(_SHORT_DAY_ORNAMENTALS) == 11


@pytest.mark.parametrize("scientific_name", _SHORT_DAY_ORNAMENTALS)
def test_fresh_install_binding_matches_v0027(
    scientific_name: str, seeded: tuple[dict[str, dict], dict[str, dict]]
) -> None:
    """Seeded attributes → resolver → ``photoperiodic_ornamental`` == the frozen v0027 target."""
    species_attr, lifecycles = seeded

    assert scientific_name in species_attr, f"{scientific_name} missing from seeded new_species"
    lifecycle = lifecycles.get(scientific_name)
    assert lifecycle is not None, f"{scientific_name} missing a seeded lifecycle_configs block"

    # The two resolver-relevant lifecycle attributes must carry the cohort values.
    assert lifecycle["cycle_type"] == _PERENNIAL
    assert lifecycle["photoperiod_type"] == _SHORT_DAY

    resolved = resolve_phase_sequence_name(
        scientific_name,
        cycle_type=lifecycle["cycle_type"],
        flowering_strategy=lifecycle.get("flowering_strategy"),
        photosynthesis_type=species_attr[scientific_name].get("photosynthesis_type"),
        photoperiod_type=lifecycle["photoperiod_type"],
        growth_habit=species_attr[scientific_name].get("growth_habit"),
    )

    assert resolved == PHOTOPERIODIC_ORNAMENTAL_SEQUENCE
    assert resolved == _TARGET_SEQUENCE[scientific_name]


@pytest.mark.parametrize("scientific_name", sorted(_CAM_COHORT_MEMBERS))
@pytest.mark.parametrize("flowering_strategy", [None, "polycarpic", "monocarpic"])
def test_cam_members_are_not_diverted_to_cam_rest(
    scientific_name: str,
    flowering_strategy: str | None,
    seeded: tuple[dict[str, dict], dict[str, dict]],
) -> None:
    """CAM short-day members bind photoperiodic regardless of flowering_strategy.

    Directly exercises the CAM-short-day conflict the audit flagged: Rule 1 fires before
    the monocarpic-epiphyte (Rule 2) and CAM (Rule 3) branches, so even a monocarpic CAM
    Kalanchoe cannot be diverted onto ``cam_succulent_rest``.
    """
    species_attr, lifecycles = seeded

    assert species_attr[scientific_name].get("photosynthesis_type") == _CAM, (
        f"{scientific_name} is expected to be a CAM species in the seed"
    )
    lifecycle = lifecycles[scientific_name]

    resolved = resolve_phase_sequence_name(
        scientific_name,
        cycle_type=lifecycle["cycle_type"],
        flowering_strategy=flowering_strategy,
        photosynthesis_type=_CAM,
        photoperiod_type=lifecycle["photoperiod_type"],
        growth_habit=species_attr[scientific_name].get("growth_habit"),
    )

    assert resolved == PHOTOPERIODIC_ORNAMENTAL_SEQUENCE
