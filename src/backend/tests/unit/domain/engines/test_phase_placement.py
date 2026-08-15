"""The one placement rule both phase repairs share (#1146, #1150).

#1146 re-homes a species whose binding no longer matches the resolver; #1150
re-homes a plant whose entry belongs to a deleted sequence generation. Both move a
plant between sequences, and #1150 asks explicitly that they use **one** rule.
These tests are that rule's contract, so the two repairs cannot drift.

The case that matters most is the backdated `entered_at`. `transition_plant_phase`
sets `entered_at = now`, which forces a false choice when correcting a plant by
hand: restart a 60-day `establishment` for a plant potted 59 days ago, or skip to
the next phase. A migration writing history directly has no such constraint, and
placing the plant at `planted_on + offset` is *both* correct and self-correcting —
the engine advances it on schedule with nobody deciding anything.

The second is that `today` is an argument. A migration re-run must place a plant
where it placed it before; reading the clock would move plants because a day
passed, and idempotence (M-3) would be unprovable.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.domain.engines.phase_placement import (
    ANCHOR_BY_ELAPSED_DAYS,
    ANCHOR_BY_NAME,
    PlacementCandidate,
    place_plant_in_sequence,
)

_PLANTED = date(2026, 6, 16)
_TODAY = date(2026, 8, 14)  # 59 days later — YUCCA-0617-DIJ's real age

#: `evergreen_foliage_perennial`, the sequence #1146's Yucca should move onto.
_EVERGREEN = [
    PlacementCandidate(entry_key="e1", phase_name="establishment", duration_days=60, sequence_order=0),
    PlacementCandidate(entry_key="e2", phase_name="active_growth", duration_days=120, sequence_order=1),
    PlacementCandidate(entry_key="e3", phase_name="flowering", duration_days=30, sequence_order=2),
    PlacementCandidate(entry_key="e4", phase_name="maintenance", duration_days=90, sequence_order=3),
]


def _place(**overrides):
    kwargs = {
        "current_phase_name": None,
        "planted_on": _PLANTED,
        "today": _TODAY,
        "candidates": _EVERGREEN,
    }
    kwargs.update(overrides)
    return place_plant_in_sequence(**kwargs)


# ── step 1: the name anchor ──────────────────────────────────────────────────


def test_a_matching_phase_name_wins() -> None:
    """v0021's rule: names are unique within a sequence, so a hit is unambiguous."""
    placement = _place(current_phase_name="flowering")

    assert placement is not None
    assert (placement.phase_name, placement.anchored_by) == ("flowering", ANCHOR_BY_NAME)


def test_the_name_anchor_beats_the_arithmetic() -> None:
    """A recognised phase is better evidence than an estimate from elapsed days.

    At 59 days the elapsed walk would say `establishment`. The plant says
    `flowering`. Recognition wins — otherwise the rule would silently *move* a
    plant whose phase the incoming sequence actually has.
    """
    placement = _place(current_phase_name="flowering")

    assert placement is not None
    assert placement.phase_name == "flowering"


def test_an_unknown_phase_name_falls_through_to_elapsed_days() -> None:
    """The common case, not the exception.

    `indoor_default` and `evergreen_foliage_perennial` intersect only in
    `flowering`, so a plant in `seedling` has no counterpart at all.
    """
    placement = _place(current_phase_name="seedling")

    assert placement is not None
    assert (placement.phase_name, placement.anchored_by) == ("establishment", ANCHOR_BY_ELAPSED_DAYS)


# ── step 2: elapsed-days placement ───────────────────────────────────────────


@pytest.mark.parametrize(
    ("age_days", "expected"),
    [(0, "establishment"), (59, "establishment"), (60, "active_growth"), (179, "active_growth"), (180, "flowering")],
)
def test_the_window_boundaries_are_where_they_are_meant_to_be(age_days: int, expected: str) -> None:
    """Pinned on the boundary, not inferred from one convenient age.

    Day 60 is the first day of the *second* phase, because the first covers days
    0..59. A rule written with `<=` would look identical at day 30 and disagree
    exactly at the seam.
    """
    placement = _place(planted_on=_TODAY - timedelta(days=age_days))

    assert placement is not None
    assert placement.phase_name == expected


def test_a_plant_older_than_the_whole_sequence_is_left_alone() -> None:
    """Not pinned to the last phase, deliberately.

    A repeating sequence restarts and a terminal one has ended; which applies is a
    lifecycle decision this rule does not own. Guessing here would put a
    three-year-old plant into `maintenance` as if it had just arrived.
    """
    assert _place(planted_on=date(2020, 1, 1)) is None


# ── the backdated entered_at ─────────────────────────────────────────────────


def test_entered_at_is_backdated_to_when_the_phase_began() -> None:
    """The whole point of repairing in a migration rather than by hand.

    A plant potted 59 days ago and placed in a 60-day `establishment` entered that
    phase *when it was potted* — not today. Setting `entered_at = now` would
    restart the phase and delay every downstream schedule by 59 days.
    """
    placement = _place(current_phase_name="seedling")

    assert placement is not None
    assert placement.entered_at == _PLANTED


def test_entered_at_accounts_for_the_phases_before_it() -> None:
    """A plant placed in the second phase entered it after the first one elapsed."""
    planted = date(2026, 5, 1)  # 105 days before _TODAY → lands in active_growth

    placement = _place(planted_on=planted)

    assert placement is not None
    assert placement.phase_name == "active_growth"
    # establishment is 60 days, so active_growth began on day 60. Written as the
    # literal date rather than as arithmetic on the same inputs the code uses —
    # an expectation derived the same way as the answer proves nothing.
    assert placement.entered_at == date(2026, 6, 30)


def test_entered_at_never_lands_in_the_future() -> None:
    """A name anchor can pick a phase the plant has not arithmetically reached.

    Placing it there is right — the plant says it is in that phase — but dating the
    arrival in the future would make `days_in_phase` negative and every consumer
    of it nonsense. Clamped to today.
    """
    placement = _place(current_phase_name="maintenance", planted_on=_TODAY)

    assert placement is not None
    assert placement.entered_at <= _TODAY


def test_a_missing_planted_on_still_places_by_name() -> None:
    """Backdating is impossible without a planting date; the placement is not.

    `entered_at = today` here is the honest remainder — an admission that the past
    is unknown, not a claim about it.
    """
    placement = _place(current_phase_name="flowering", planted_on=None)

    assert placement is not None
    assert (placement.phase_name, placement.entered_at) == ("flowering", _TODAY)


# ── what must be left alone ──────────────────────────────────────────────────


def test_an_empty_sequence_places_nothing() -> None:
    assert _place(candidates=[]) is None


def test_no_name_and_no_planting_date_places_nothing() -> None:
    """Nothing is guessed — v0021's rule, carried over."""
    assert _place(current_phase_name=None, planted_on=None) is None


def test_a_plant_planted_in_the_future_is_left_alone() -> None:
    """A data defect, and not one a placement rule should paper over."""
    assert _place(planted_on=date(2027, 1, 1)) is None


# ── reproducibility ──────────────────────────────────────────────────────────


def test_the_same_inputs_always_yield_the_same_placement() -> None:
    """`today` is an argument for this reason.

    A migration re-run must place a plant where it placed it before. Reading the
    clock inside would move plants because a day passed, and M-3 idempotence would
    be unprovable rather than merely untested.
    """
    first = _place(current_phase_name="seedling")
    second = _place(current_phase_name="seedling")

    assert first == second


def test_a_later_run_does_not_move_a_name_anchored_plant() -> None:
    """Once placed, the plant's phase name matches the incoming sequence — so the
    next run anchors on the name and returns the same entry, regardless of age."""
    placement = _place(current_phase_name="establishment", today=date(2027, 1, 1))

    assert placement is not None
    assert placement.entry_key == "e1"


def test_candidates_out_of_order_are_sorted_before_walking() -> None:
    """Input order is an accident of the query, not part of the contract."""
    shuffled = [_EVERGREEN[2], _EVERGREEN[0], _EVERGREEN[3], _EVERGREEN[1]]

    assert _place(candidates=shuffled) == _place(candidates=_EVERGREEN)
