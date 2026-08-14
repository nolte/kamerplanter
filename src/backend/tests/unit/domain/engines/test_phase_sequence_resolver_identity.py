"""Two ways the resolver answered wrongly on the reference instance (#1148, #1149).

Both were measured against live data, and neither *failed* — each produced a
plausible binding that no later check questions.

**#1148 — identity by raw string.** The live catalogue holds `Fragaria × ananassa`
with U+00D7; every seed source writes ASCII `x`. A raw membership test against
`_RUNNER_SPECIES` therefore dropped the flagship of the runner cohort out of its
own cohort, and rule 5 bound it to `evergreen_foliage_perennial` — the one
sequence *without* the establishment→sprouting restart a strawberry needs. The
project already owns the answer: `normalize_scientific_name`, which the persisted
dedup key is built from. The resolver simply was not using it.

**#1149 — a short-day geophyte is not a photoperiodic ornamental.** Rule 1 fired
on `Dahlia pinnata` before rule 4 could see `bulb_geophyte`, assigning a cycle
whose phases are `active_growth → short_day_induction → bract_coloring →
rest_phase`. A dahlia has no bracts, and the two phases its year actually turns on
— `tuber_formation`, `dry_storage` — exist only in `geophyte_fine`. Nothing in the
assigned lifecycle ever prompted lifting the tubers of a frost-sensitive species.

The fix narrows rule 1 rather than reordering the chain. The documented precedence
(photoperiod before growth habit, REQ-003) is correct for every other short-day
perennial; inverting it to repair one cohort would change the answer for cohorts
nobody measured. A geophyte's dormancy is organ-driven, so it was never rule 1's
subject.
"""

from __future__ import annotations

import pytest

from app.domain.engines.phase_sequence_resolver import (
    EVERGREEN_PERENNIAL_SEQUENCE,
    GEOPHYTE_FINE_SEQUENCE,
    PALM_EVERGREEN_SEQUENCE,
    PHOTOPERIODIC_ORNAMENTAL_SEQUENCE,
    RUNNER_PERENNIAL_SEQUENCE,
    resolve_perennial_sequence_name,
    resolve_phase_sequence_name,
)


def _resolve(name: str, **overrides: str | None) -> str | None:
    kwargs: dict[str, str | None] = {
        "cycle_type": "perennial",
        "flowering_strategy": "polycarpic",
        "photosynthesis_type": None,
        "photoperiod_type": "day_neutral",
        "growth_habit": "herb",
    }
    kwargs.update(overrides)
    return resolve_phase_sequence_name(name, **kwargs)  # type: ignore[arg-type]


# ── #1148: the spelling of a name must not decide its cohort ─────────────────


#: The exact spelling stored on the reference instance, the seed spelling, and two
#: variants the normalizer is documented to fold. All four name one taxon.
_STRAWBERRY_SPELLINGS = [
    "Fragaria x ananassa",
    "Fragaria × ananassa",
    "Fragaria ×ananassa",
    "  fragaria   X   ananassa  ",
]


@pytest.mark.parametrize("name", _STRAWBERRY_SPELLINGS)
def test_every_spelling_of_the_strawberry_reaches_the_runner_cohort(name: str) -> None:
    assert _resolve(name) == RUNNER_PERENNIAL_SEQUENCE


@pytest.mark.parametrize("name", _STRAWBERRY_SPELLINGS)
def test_the_frozen_v0022_classifier_agrees(name: str) -> None:
    """The two classifiers must not disagree about who is a runner.

    `resolve_perennial_sequence_name` is the frozen Phase-1 contract, and it
    carried the same raw comparison. Normalizing it is a strict widening — every
    name that matched before still matches — but *both* have to move, or the seed
    and the migration would bind the same species differently.
    """
    assert resolve_perennial_sequence_name(name, "perennial", "polycarpic") == RUNNER_PERENNIAL_SEQUENCE


def test_the_unicode_spelling_used_to_land_on_the_wrong_sequence() -> None:
    """Names the concrete harm, so the test is not just "normalization happens".

    Without the fix this returned `evergreen_foliage_perennial`: a repeating cycle,
    so nothing looked broken, but the one without the establishment→sprouting
    restart. The failure was a *wrong* sequence, not a missing one.
    """
    assert _resolve("Fragaria × ananassa") != EVERGREEN_PERENNIAL_SEQUENCE


@pytest.mark.parametrize("genus_spelling", ["Chamaedorea elegans", "chamaedorea elegans", " Howea  forsteriana "])
def test_genus_cohorts_are_matched_normalized_too(genus_spelling: str) -> None:
    """The palm test keys on genus, and had the same raw-string exposure."""
    assert _resolve(genus_spelling, growth_habit="tree") == PALM_EVERGREEN_SEQUENCE


def test_a_letter_x_inside_a_name_is_not_a_hybrid_marker() -> None:
    """The normalizer's own rule, pinned where it matters.

    If normalization ever started rewriting a plain ASCII `x`, `Maxillaria` would
    collapse toward a different token and could be pulled into a cohort it does not
    belong to. Cheap to assert, and it fails loudly if that rule is relaxed.
    """
    assert _resolve("Maxillaria tenuifolia", growth_habit="epiphyte") == EVERGREEN_PERENNIAL_SEQUENCE


# ── #1149: a short-day geophyte takes the geophyte cycle ─────────────────────


def test_a_short_day_geophyte_takes_the_geophyte_cycle() -> None:
    assert (
        _resolve("Dahlia pinnata", photoperiod_type="short_day", growth_habit="bulb_geophyte") == GEOPHYTE_FINE_SEQUENCE
    )


def test_a_short_day_perennial_that_is_not_a_geophyte_keeps_the_ornamental_cycle() -> None:
    """The rule was narrowed, not inverted — and this is what says so.

    Without this, the change would be indistinguishable from deleting rule 1, which
    would move poinsettia and Kalanchoe onto a cycle with no short-day induction at
    all.
    """
    assert (
        _resolve("Euphorbia pulcherrima", photoperiod_type="short_day", growth_habit="shrub")
        == PHOTOPERIODIC_ORNAMENTAL_SEQUENCE
    )


def test_a_day_neutral_geophyte_was_already_correct() -> None:
    """Pins that the fix did not need to touch the path that already worked."""
    assert _resolve("Tulipa gesneriana", growth_habit="bulb_geophyte") == GEOPHYTE_FINE_SEQUENCE


def test_an_annual_short_day_crop_still_terminates() -> None:
    """Cannabis must keep its harvest-terminated blanket; rule 1's perennial
    restriction is untouched by the geophyte carve-out."""
    assert _resolve("Cannabis sativa", cycle_type="annual", photoperiod_type="short_day") is None
