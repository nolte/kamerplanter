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

Why it lives under ``domain/engines`` (#1006)
---------------------------------------------

It used to be ``app.migrations.perennial_binding``, which meant only the seed and the
migrations could reach it: a service may not import a migration module (NFR-001 /
BACKEND.md §2.1). So ``create_species`` and the CSV import — the two runtime paths
that also mint species — bound no sequence at all, and every plant created for such a
species came out with ``current_phase_key: null``. Moving the classifier here is what
lets the runtime paths apply the *same* rule as the seed instead of a second one.
``app.migrations.perennial_binding`` re-exports it, so the migrations keep their
import path and the v0022 contract is untouched.

Pure attribute inputs, no I/O — an engine, per BACKEND.md §2.1. The repository-facing
half lives in ``app.domain.services.phase_sequence_binder``.
"""

from __future__ import annotations

from app.domain.calculators.scientific_name import normalize_scientific_name

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
#:
#: Stored **normalized** and compared normalized (#1148). The live catalogue holds
#: ``Fragaria × ananassa`` with U+00D7, every seed source writes ASCII ``x``, and a
#: raw-string membership test therefore silently dropped the flagship species out of
#: its own cohort — landing it on ``evergreen_foliage_perennial``, the one sequence
#: without the establishment→sprouting restart a strawberry needs. Identity by raw
#: string over a field whose accepted spelling legitimately varies is the defect;
#: ``normalize_scientific_name`` is the project's existing answer to it and is
#: already what the dedup key is built from.
_RUNNER_SPECIES = frozenset({normalize_scientific_name("Fragaria x ananassa")})

#: Palm genera that get the ``palm_evergreen`` D12 cycle. ``growth_habit`` is ``tree``
#: for these (indistinguishable from Ficus/Dracaena), so palms are named by genus.
#: Normalized like :data:`_RUNNER_SPECIES`, so casing or a nothogenus prefix cannot
#: drop a genus out of its cohort (#1148).
_PALM_GENERA = frozenset(normalize_scientific_name(g) for g in ("Chamaedorea", "Dypsis", "Howea", "Livistona"))

#: Genus whose winter hull-change adds a second (summer) rest → ``cam_double_rest``.
_DOUBLE_REST_GENERA = frozenset({normalize_scientific_name("Lithops")})

_PERENNIAL = "perennial"
_MONOCARPIC = "monocarpic"
_CAM = "cam"
_SHORT_DAY = "short_day"
_EPIPHYTE = "epiphyte"
_FERN = "fern"
_BULB_GEOPHYTE = "bulb_geophyte"

#: Cycle types that are a *known, determinate* answer — the species really does
#: end its lifecycle after one or two seasons, so the harvest-terminated
#: ``indoor_default`` blanket is the correct destination for it. Anything outside
#: this set (most importantly ``None``) is **absence of an answer**, not an
#: annual, and must never be treated as one — see :func:`resolve_phase_sequence_name`.
_DETERMINATE_CYCLES = frozenset({"annual", "biennial"})


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
    # Normalized like its sibling below (#1148). This widens the v0022 contract
    # strictly — every name that matched before still matches, and the U+00D7
    # spelling the live catalogue actually holds now matches too.
    if normalize_scientific_name(scientific_name) in _RUNNER_SPECIES:
        return RUNNER_PERENNIAL_SEQUENCE
    return EVERGREEN_PERENNIAL_SEQUENCE


def _genus_of(scientific_name: str) -> str:
    """Return the **normalized** genus (first whitespace-delimited token) of a name.

    Normalized so the genus tests below compare like against like (#1148): the
    cohort sets are normalized at definition, and a caller's spelling — casing, a
    U+00D7 hybrid marker, stray whitespace — must not decide membership.
    """
    normalized = normalize_scientific_name(scientific_name)
    return normalized.split(" ", 1)[0] if normalized else ""


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

    **The inputs this keys on, and what each one being null means** (issue #949 —
    the previous behaviour was discoverable from no schema at all):

    ===================== =========================================== ==================================
    Input                 Read from                                   When null
    ===================== =========================================== ==================================
    ``scientific_name``   ``Species.scientific_name``                  genus tests (palm, Lithops) and
                                                                      the runner allowlist never match
    ``cycle_type``        the **effective** cycle — ``LifecycleConfig  the species is *unresolvable*;
                          .cultivation_cycle_type`` over              step 6 applies the safe fallback
                          ``.cycle_type`` via ``resolve_effective_
                          cycle`` — ``None`` when the species has
                          no ``LifecycleConfig`` at all
    ``flowering_strategy````LifecycleConfig.flowering_strategy``       rule 2 cannot fire; a monocarp is
                                                                      treated as polycarpic
    ``photosynthesis_type````Species.photosynthesis_type``             rule 3 cannot fire; a CAM
                                                                      succulent falls through to its
                                                                      cycle-type-based destination
    ``photoperiod_type``  ``LifecycleConfig.photoperiod_type``         rule 1 cannot fire
    ``growth_habit``      ``Species.growth_habit``                     rule 4's fern/geophyte tests
                                                                      cannot fire (the palm test keys
                                                                      on genus, not habit)
    ===================== =========================================== ==================================

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
    6. **A known determinate cycle** (``annual`` / ``biennial``) → ``None``, and the
       caller applies the ``indoor_default`` blanket. That is the correct home for a
       species that really does terminate after one or two seasons.
    7. **Anything else — i.e. an unresolvable species** → ``evergreen_foliage_perennial``.

    Step 7 is the issue-#949 fix and it is a **safety** rule, not a botanical claim.
    A null ``cycle_type`` means "no ``LifecycleConfig`` exists for this species", which
    is *absence of an answer*; routing it to ``indoor_default`` silently asserted the
    strongest possible one — a 126-day cycle ending in a terminal, harvest-allowing
    phase. That scheduled a *Yucca gigantea* (evergreen, perennial, polycarpic) to be
    harvest-ready and lifecycle-complete 126 days after planting. The two fallbacks are
    not symmetric in cost: putting a genuine annual on a repeating perennial cycle omits
    a harvest prompt a user can still trigger by hand, while putting a perennial tree on
    an annual cycle fabricates a harvest and an end-of-life that no one asked for. The
    fallback therefore lands on the repeating, non-terminal, harvest-free cycle.

    Runner-propagated stauden keep their E4 template. Pure attribute inputs; no I/O —
    shared by the seed linker and the rebind migration so neither can drift.
    """
    genus = _genus_of(scientific_name)

    if normalize_scientific_name(scientific_name) in _RUNNER_SPECIES:
        return RUNNER_PERENNIAL_SEQUENCE

    # 1. Short-day photoperiodic *perennial* ornamentals (poinsettia, Kalanchoe, …).
    #
    # Geophytes are excluded (#1149). A short-day *bulb or tuber* is not a
    # photoperiodic ornamental in the sense this sequence models: the cycle it
    # assigns runs active_growth → short_day_induction → **bract_coloring** →
    # rest_phase, and a dahlia has no bracts. What its year actually turns on —
    # tuber_formation and dry_storage — does not exist in that sequence, so nothing
    # in the lifecycle ever prompts lifting the tubers before frost on a species
    # marked frost-sensitive.
    #
    # Written as a narrower rule 1 rather than by moving rule 4 above it: the
    # documented precedence (photoperiod before growth_habit, REQ-003) is right for
    # every other short-day perennial, and inverting it to fix one cohort would
    # change the answer for cohorts nobody measured. A geophyte's dormancy is
    # organ-driven, so it was never rule 1's subject in the first place.
    if photoperiod_type == _SHORT_DAY and cycle_type == _PERENNIAL and growth_habit != _BULB_GEOPHYTE:
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

    # 6. A KNOWN determinate cycle → the caller's ``indoor_default`` blanket, which
    #    is where a species that truly terminates after one or two seasons belongs.
    if cycle_type in _DETERMINATE_CYCLES:
        return None

    # 7. Unresolvable (no LifecycleConfig, hence no cycle_type — issue #949) → the
    #    repeating perennial cycle. Never the annual blanket: see the docstring for
    #    why the two fallbacks are not symmetric in cost.
    return EVERGREEN_PERENNIAL_SEQUENCE
