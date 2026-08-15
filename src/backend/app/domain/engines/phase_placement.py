"""Where does a plant land when its sequence changes underneath it? (#1146, #1150)

Two repairs need this answer and must not answer it twice: #1146 re-homes a
species whose binding no longer matches the resolver, and #1150 re-homes a plant
whose phase entry belongs to a sequence generation that was deleted. Both move a
plant from one sequence to another, and #1150 says explicitly that they share one
placement rule rather than growing two.

**Two steps, in order.**

1. **Name anchor**, as ``v0021`` established: match the plant's current phase name
   against a phase in the incoming sequence. Phase names are unique within a
   sequence, so a hit is unambiguous and needs no arithmetic.
2. **Elapsed-days placement** when the name does not exist there — which is the
   *common* case, not the exception: ``indoor_default`` (seedling, vegetative,
   flowering, flushing, ripening) and ``evergreen_foliage_perennial``
   (establishment, active_growth, flowering, maintenance) intersect only in
   ``flowering``. Walk the incoming sequence accumulating durations and place the
   plant in the phase whose window contains the days since planting.

**``entered_at`` is backdated**, and this is the part worth being explicit about.
``transition_plant_phase`` sets ``entered_at = now``, so correcting a plant by hand
forces a choice between restarting a 60-day ``establishment`` for a plant potted 59
days ago, or skipping ahead to the next phase. Neither is faithful. A repair that
writes the history record directly has no such constraint: placing the plant at
``planted_on`` plus the chosen phase's cumulative offset is *both* correct and
self-correcting — the engine advances it on schedule without anyone deciding
anything.

**Nothing is guessed.** A plant that neither step can place is returned unplaced
and reported, exactly as v0021 refuses to guess a dangling key.

Pure: models and primitives in, a decision out. No I/O, no clock — ``today`` is an
argument, so the same inputs always yield the same placement (BACKEND.md §2.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

#: How the plant's new phase was chosen. Carried on the result so a migration
#: report can distinguish a confident anchor from an arithmetic estimate — an
#: operator reviewing a dry run needs to see which plants were *computed* into
#: place rather than recognised.
ANCHOR_BY_NAME = "name"
ANCHOR_BY_ELAPSED_DAYS = "elapsed_days"


@dataclass(frozen=True)
class PlacementCandidate:
    """One phase of the incoming sequence, as the placement rule needs it."""

    entry_key: str
    phase_name: str
    duration_days: int
    sequence_order: int


@dataclass(frozen=True)
class Placement:
    """Where a plant goes, and when it is to be considered to have arrived."""

    entry_key: str
    phase_name: str
    entered_at: date
    anchored_by: str


def place_plant_in_sequence(
    *,
    current_phase_name: str | None,
    planted_on: date | None,
    today: date,
    candidates: list[PlacementCandidate],
) -> Placement | None:
    """Return where the plant belongs in ``candidates``, or ``None`` to leave it alone.

    Args:
        current_phase_name: The plant's open phase, for the name anchor. ``None``
            or unknown falls through to elapsed days.
        planted_on: Used for both the elapsed-days walk and the backdated
            ``entered_at``. Without it neither is possible.
        today: Injected rather than read, so the placement of a given plant is
            reproducible — a migration re-run must not move a plant because a day
            passed.
        candidates: The incoming sequence, in order.

    ``None`` means *unplaceable*, and the caller must leave the plant untouched
    and report it. The three ways to get there are all "we do not know", never "we
    could guess": an empty sequence, no ``planted_on`` with no name match, or a
    sequence whose durations do not reach the plant's age.
    """
    if not candidates:
        return None

    ordered = sorted(candidates, key=lambda c: c.sequence_order)

    if current_phase_name:
        for candidate in ordered:
            if candidate.phase_name == current_phase_name:
                return Placement(
                    entry_key=candidate.entry_key,
                    phase_name=candidate.phase_name,
                    entered_at=_entered_at(ordered, candidate, planted_on, today),
                    anchored_by=ANCHOR_BY_NAME,
                )

    if planted_on is None:
        # No name match and no age: there is no information left to place on.
        return None

    elapsed = (today - planted_on).days
    if elapsed < 0:
        # A plant planted in the future is a data defect, not a placement problem.
        return None

    cumulative = 0
    for candidate in ordered:
        cumulative += max(candidate.duration_days, 1)
        if elapsed < cumulative:
            return Placement(
                entry_key=candidate.entry_key,
                phase_name=candidate.phase_name,
                entered_at=_entered_at(ordered, candidate, planted_on, today),
                anchored_by=ANCHOR_BY_ELAPSED_DAYS,
            )

    # Older than the whole sequence. Deliberately unplaced rather than pinned to
    # the last phase: a repeating sequence restarts and a terminal one has ended,
    # and which of those applies is a lifecycle decision this rule does not own.
    return None


def _entered_at(
    ordered: list[PlacementCandidate],
    chosen: PlacementCandidate,
    planted_on: date | None,
    today: date,
) -> date:
    """``planted_on`` plus the cumulative duration of everything before ``chosen``.

    Falls back to ``today`` only when ``planted_on`` is unknown — which the
    elapsed-days path cannot reach, and the name-anchor path can. There the
    backdating is impossible and "arrived now" is the honest remainder, not a
    guess about the past.

    Clamped to ``today``: a sequence whose earlier phases are longer than the
    plant's age would otherwise produce an ``entered_at`` in the future, and a
    phase the plant has not yet entered is worse than one it entered late.
    """
    if planted_on is None:
        return today
    offset = sum(max(c.duration_days, 1) for c in ordered if c.sequence_order < chosen.sequence_order)
    entered = planted_on + timedelta(days=offset)
    return min(entered, today)
