"""Attribute-driven binding of indoor species to their phase sequence.

ADR-006 E2: perennials must not sit on the annual ``indoor_default`` blanket, which
terminates after one season (no cyclic restart). This pure classifier decides the
phase sequence a species should bind to, from its botanical attributes. It is shared
by BOTH the seed (fresh installs) and the rebind migrations (existing installs), so
both derive the same target and no drift can open up between them.

Two classifiers live here:

* :func:`resolve_perennial_sequence_name` — the original **Phase 1** (#565 / v0022)
  classifier that only moved polycarpic perennials off ``indoor_default`` onto the
  generic cyclic ``evergreen_foliage_perennial`` (runner stauden → ``perennial_runner``).
  Kept unchanged for the v0022 contract.
* :func:`resolve_phase_sequence_name` — the **fine-typing** classifier (audit #576 /
  #616) that additionally routes the CAM-succulent, clonal-monocarp (Kindel),
  photoperiodic-ornamental and palm/fern/geophyte cohorts onto their biologically
  precise sequences (REQ-003 D9–D12). ``indoor_default`` is the last-resort fallback.
"""

from __future__ import annotations

#: The annual blanket sequence perennials are being moved off of.
INDOOR_DEFAULT_SEQUENCE = "indoor_default"
#: Generic repeating perennial cycle for evergreen/foliage & other polycarpic perennials.
EVERGREEN_PERENNIAL_SEQUENCE = "evergreen_foliage_perennial"
#: E4 runner-propagated staude cycle (establishment→sprouting-restart→…→dormancy).
RUNNER_PERENNIAL_SEQUENCE = "perennial_runner"

#: Fine-typed cohort sequences (REQ-003 D9–D12, audit #576).
CAM_SUCCULENT_REST_SEQUENCE = "cam_succulent_rest"
CAM_DOUBLE_REST_SEQUENCE = "cam_double_rest"
CLONAL_MONOCARP_SEQUENCE = "clonal_monocarp"
PHOTOPERIODIC_ORNAMENTAL_SEQUENCE = "photoperiodic_ornamental"
PALM_EVERGREEN_SEQUENCE = "palm_evergreen"
FERN_SPORE_SEQUENCE = "fern_spore"
GEOPHYTE_FINE_SEQUENCE = "geophyte_fine"

#: Species that are runner/division propagated and use the E4 establishment/sprouting
#: split. Strawberry is the flagship (#541); kept explicit rather than attribute-guessed.
_RUNNER_SPECIES = frozenset({"Fragaria x ananassa"})

#: Palm genera that get the ``palm_evergreen`` D12 cycle. ``growth_habit`` is ``tree``
#: for these (indistinguishable from Ficus/Dracaena), so palms are named by genus.
_PALM_GENERA = frozenset({"Chamaedorea", "Dypsis", "Howea", "Livistona"})

#: Genus whose winter hull-change adds a second (summer) rest → ``cam_double_rest``.
_DOUBLE_REST_GENERA = frozenset({"Lithops"})

_PERENNIAL = "perennial"
_MONOCARPIC = "monocarpic"
_CAM = "cam"
_SHORT_DAY = "short_day"
_EPIPHYTE = "epiphyte"
_FERN = "fern"
_BULB_GEOPHYTE = "bulb_geophyte"


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

    This is the frozen Phase-1 (v0022) contract; new work uses
    :func:`resolve_phase_sequence_name`.
    """
    if cycle_type != _PERENNIAL:
        return None
    if flowering_strategy == _MONOCARPIC:
        return None
    if scientific_name in _RUNNER_SPECIES:
        return RUNNER_PERENNIAL_SEQUENCE
    return EVERGREEN_PERENNIAL_SEQUENCE


def _genus_of(scientific_name: str) -> str:
    """Return the genus (first whitespace-delimited token) of a scientific name."""
    return scientific_name.split(" ", 1)[0] if scientific_name else ""


def resolve_phase_sequence_name(
    scientific_name: str,
    *,
    cycle_type: str | None,
    flowering_strategy: str | None,
    photosynthesis_type: str | None,
    photoperiod_type: str | None,
    growth_habit: str | None,
) -> str | None:
    """Return the biologically precise phase sequence for an indoor species.

    Attribute precedence (audit #576 ``target()`` logic, REQ-003 D9–D12)::

        flowering_strategy → photosynthesis_type → photoperiod_type → growth_habit → cycle_type

    Realised as an ordered decision so the strongest biological signal wins:

    1. **Short-day PERENNIAL ornamentals** (D11) → ``photoperiodic_ornamental``.
       Restricted to perennials so annual short-day *crops* (cannabis) keep their
       harvest-terminated ``indoor_default`` flow instead of a no-harvest ornamental
       cycle.
    2. **Monocarpic perennial epiphytes** (bromeliads, D10) → ``clonal_monocarp``
       (terminal bloom + Kindel/pup continuation, not a seasonal restart).
    3. **CAM succulents** (D9) → ``cam_double_rest`` for Lithops/mesembs, else
       ``cam_succulent_rest``.
    4. **Growth-habit fine typing** (D12): ferns → ``fern_spore``; bulb geophytes →
       ``geophyte_fine``; palm genera → ``palm_evergreen``.
    5. **Any other perennial** → ``evergreen_foliage_perennial`` (largest indoor cohort).
    6. Otherwise ``None`` → caller applies the ``indoor_default`` last-resort blanket.

    Runner-propagated stauden keep their E4 template. Pure attribute inputs; no I/O —
    shared by the seed linker and the rebind migration so neither can drift.
    """
    genus = _genus_of(scientific_name)

    if scientific_name in _RUNNER_SPECIES:
        return RUNNER_PERENNIAL_SEQUENCE

    # 1. Short-day photoperiodic *perennial* ornamentals (poinsettia, Kalanchoe, …).
    if photoperiod_type == _SHORT_DAY and cycle_type == _PERENNIAL:
        return PHOTOPERIODIC_ORNAMENTAL_SEQUENCE

    # 2. Monocarpic perennial rosette epiphytes (bromeliads) → clonal continuation.
    if flowering_strategy == _MONOCARPIC and cycle_type == _PERENNIAL and growth_habit == _EPIPHYTE:
        return CLONAL_MONOCARP_SEQUENCE

    # 3. CAM succulents — distinct cool-dry rest physiology.
    if photosynthesis_type == _CAM:
        if genus in _DOUBLE_REST_GENERA:
            return CAM_DOUBLE_REST_SEQUENCE
        return CAM_SUCCULENT_REST_SEQUENCE

    # 4. Growth-habit fine typing (palms named by genus — habit is ``tree``).
    if growth_habit == _FERN:
        return FERN_SPORE_SEQUENCE
    if growth_habit == _BULB_GEOPHYTE:
        return GEOPHYTE_FINE_SEQUENCE
    if genus in _PALM_GENERA:
        return PALM_EVERGREEN_SEQUENCE

    # 5. Any remaining perennial → the generic evergreen foliage cycle.
    if cycle_type == _PERENNIAL:
        return EVERGREEN_PERENNIAL_SEQUENCE

    # 6. Annual / biennial / unknown → indoor_default blanket (caller's last resort).
    return None
