"""Attribute-driven binding of Path-A perennials to a repeating phase sequence.

ADR-006 E2: perennials must not sit on the annual ``indoor_default`` blanket, which
terminates after one season (no cyclic restart). This pure classifier decides the
repeating perennial sequence a species should bind to, from its botanical attributes.
It is shared by BOTH the seed (fresh installs — ``seed_data._link_species_to_phase_sequence``)
and migration ``v0022`` (existing installs), so both derive the same target and no
drift can open up between them.

Scope (Phase 1): move perennials off ``indoor_default`` onto a *cyclic* sequence.
Fine biological typing (CAM winter-rest, photoperiodic short-day, geophyte storage,
fern rest, clonal-monocarp pup continuation — audit #576) is a later-phase sweep, so
those cohorts land on the safe generic ``evergreen_foliage_perennial`` repeating cycle
for now, except runner-propagated stauden (strawberry) which get the E4
``perennial_runner`` template, and monocarpic species which stay on ``indoor_default``
(they need the pup-continuation template, not a seasonal restart).
"""

from __future__ import annotations

#: The annual blanket sequence perennials are being moved off of.
INDOOR_DEFAULT_SEQUENCE = "indoor_default"
#: Generic repeating perennial cycle for evergreen/foliage & other polycarpic perennials.
EVERGREEN_PERENNIAL_SEQUENCE = "evergreen_foliage_perennial"
#: E4 runner-propagated staude cycle (establishment→sprouting-restart→…→dormancy).
RUNNER_PERENNIAL_SEQUENCE = "perennial_runner"

#: Species that are runner/division propagated and use the E4 establishment/sprouting
#: split. Strawberry is the flagship (#541); kept explicit rather than attribute-guessed.
_RUNNER_SPECIES = frozenset({"Fragaria x ananassa"})

_PERENNIAL = "perennial"
_MONOCARPIC = "monocarpic"


def resolve_perennial_sequence_name(
    scientific_name: str,
    cycle_type: str | None,
    flowering_strategy: str | None,
) -> str | None:
    """Return the repeating perennial sequence a Path-A perennial should bind to.

    Returns ``None`` when the species should NOT be moved off ``indoor_default``:

    * a non-perennial (annual/biennial/unknown) species — it stays where it is;
    * a monocarpic perennial — it needs the clonal-pup ``clonal_monocarp`` template
      (a later-phase sweep), not a seasonal restart.

    Otherwise: runner-propagated stauden → ``perennial_runner`` (E4); every other
    polycarpic perennial → ``evergreen_foliage_perennial``.
    """
    if cycle_type != _PERENNIAL:
        return None
    if flowering_strategy == _MONOCARPIC:
        return None
    if scientific_name in _RUNNER_SPECIES:
        return RUNNER_PERENNIAL_SEQUENCE
    return EVERGREEN_PERENNIAL_SEQUENCE
