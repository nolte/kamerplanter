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
    GEOPHYTE_FINE_SEQUENCE,
    PHOTOPERIODIC_ORNAMENTAL_SEQUENCE,
    resolve_phase_sequence_name,
)
from app.migrations.versions.v0027_finetype_cam_monocarp_photoperiodic_sequences import (
    _TARGET_SEQUENCE,
)
from app.migrations.versions.v0039_rebind_short_day_geophytes import (
    _AFFECTED_SPECIES as _V0039_AFFECTED,
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

#: Species ``v0027`` sent to ``photoperiodic_ornamental`` that ``v0039`` has since
#: moved to ``geophyte_fine`` (#1149). Rule 1 fired on them before rule 4 could see
#: ``bulb_geophyte``, so they were never really members of this cohort — a dahlia
#: has no bracts to colour. Subtracted rather than removed from ``v0027``'s map: a
#: shipped migration records what it did, and editing it would rewrite history
#: instead of correcting it.
_REBOUND_BY_V0039 = frozenset(_V0039_AFFECTED)

#: The cohort is the SSOT slice of ``v0027`` that targets the photoperiodic sequence,
#: minus what a later migration moved off it — derived (not hard-coded) so the test
#: tracks both migrations if membership ever changes.
_SHORT_DAY_ORNAMENTALS = tuple(
    name
    for name, seq in _TARGET_SEQUENCE.items()
    if seq == PHOTOPERIODIC_ORNAMENTAL_SEQUENCE and name not in _REBOUND_BY_V0039
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


def test_cohort_has_exactly_nine_members() -> None:
    """Guard the count against silent edits to either migration.

    Was 11 (the number in #676). ``v0039`` moved the two dahlias to ``geophyte_fine``
    (#1149), so the photoperiodic cohort is 9. Asserting the arithmetic as well
    keeps a later reader from reading the drop as an accidental deletion.
    """
    assert len(_SHORT_DAY_ORNAMENTALS) == 9
    assert len(_REBOUND_BY_V0039) == 2
    assert len(_SHORT_DAY_ORNAMENTALS) + len(_REBOUND_BY_V0039) == 11


@pytest.mark.parametrize("scientific_name", sorted(_REBOUND_BY_V0039))
def test_a_rebound_geophyte_now_converges_on_geophyte_fine(
    scientific_name: str, seeded: tuple[dict[str, dict], dict[str, dict]]
) -> None:
    """The other half of convergence: fresh install and ``v0039`` must agree too.

    Without this the subtraction above would merely *exclude* the dahlias from the
    proof, which is how a convergence test quietly stops covering the species it
    was failing on.
    """
    species_attr, lifecycles = seeded
    lifecycle = lifecycles.get(scientific_name) or {}
    species = species_attr.get(scientific_name) or {}

    resolved = resolve_phase_sequence_name(
        scientific_name,
        cycle_type=lifecycle.get("cycle_type"),
        flowering_strategy=lifecycle.get("flowering_strategy"),
        photosynthesis_type=species.get("photosynthesis_type"),
        photoperiod_type=lifecycle.get("photoperiod_type"),
        growth_habit=species.get("growth_habit"),
    )

    assert resolved == GEOPHYTE_FINE_SEQUENCE, (
        f"{scientific_name} is what v0039 rebinds; a fresh install must reach the same target"
    )


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
