"""REQ-053 WP 5.4 — the server-side pure calculators on the "large" class, as assertions (GP-NFR-040, E-13).

GP-NFR-040 asks that the targets are *asserted*, not described: a pytest benchmark for the containment check
with 3 000 slots (this file) next to the vitest benchmark of `applyOperation` (frontend) and the `GET /plan`
benchmark against ArangoDB (`tests/integration/test_garden_plan_repository.py`).

The "large" class (§25.1) is 150 beds, 300 objects, **3 000 slots**, 2 000 plants. Timing a pure function on a
shared CI runner needs a statistic that one slow run cannot move and a budget with margin: every case runs 20
times after a warm-up and is judged on the nearest-rank p95 (the 19th of 20), against the spec's own budget -
not against a number fitted to today's machine. Measured 2026-10-20 on a developer machine for scale: the
containment check ~64 ms median / ~105 ms worst, the 200-position layout ~8 ms median / ~10 ms worst.
"""

from __future__ import annotations

import math
import statistics
import time
from collections.abc import Callable

from app.common.enums import LayoutStrategy
from app.domain.calculators.planting_layout_calculator import EntryLayout, compute_layout
from app.domain.engines.garden_plan_engine import slots_outside_bed
from app.domain.models.geometry import Geometry, parse_geometry

RUNS = 20
SLOT_COUNT = 3000
#: GP-NFR-035: batch save of 50 operations p95 <= 500 ms, "containment checks O(n*m) with bbox pre-test" - the
#: V-04 check of a bed's slots runs inside that budget, so it may not use more than all of it on its own.
CONTAINMENT_P95_BUDGET_SECONDS = 0.500
#: GP-NFR-036: layout preview, 200 positions, polygon bed, <= 100 ms server side.
LAYOUT_P95_BUDGET_SECONDS = 0.100


def p95(samples: list[float]) -> float:
    """Nearest-rank 95th percentile: with 20 runs this is the 19th value, so one slow run is tolerated."""
    ordered = sorted(samples)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def timed_runs(work: Callable[[], object]) -> tuple[list[float], object]:
    """One untimed warm-up, then ``RUNS`` timed calls; the durations and the last result."""
    result = work()
    durations: list[float] = []
    for _ in range(RUNS):
        started = time.perf_counter()
        result = work()
        durations.append(time.perf_counter() - started)
    return durations, result


def large_bed() -> Geometry:
    """A 10 x 10 m bed in its own frame; the 3 000 slots below lie well inside it."""
    return parse_geometry({"kind": "rect", "origin": [0, 0], "width_m": 10.0, "length_m": 10.0, "rotation_deg": 0})


def point_slots(count: int) -> list[tuple[str, Geometry]]:
    """``count`` position slots on a 10 cm x 25 cm lattice, 90 per row - all inside ``large_bed``."""
    return [
        (f"slot_{n}", parse_geometry({"kind": "point", "origin": [0.1 + (n % 90) * 0.1, 0.1 + (n // 90) * 0.25]}))
        for n in range(count)
    ]


class TestContainmentWith3000Slots:
    def test_the_bed_check_of_3000_slots_stays_within_the_batch_budget(self) -> None:
        """GP-ACC-033 / GP-NFR-040: V-04 over 3 000 slots, p95 <= 500 ms, and the answer is right.

        Breaks if the per-slot test loses its early exit or grows a quadratic step. The result is asserted
        too - a benchmark of a function that quietly returns early would pass at any speed.
        """
        bed, slots = large_bed(), point_slots(SLOT_COUNT)
        assert len(slots) == SLOT_COUNT

        durations, outside = timed_runs(lambda: slots_outside_bed(bed, slots))

        assert outside == [], f"all {SLOT_COUNT} slots lie inside the bed, the check reported {outside[:5]}"
        measured = p95(durations)
        assert measured <= CONTAINMENT_P95_BUDGET_SECONDS, (
            f"p95 {measured * 1000:.0f} ms over {RUNS} runs (budget {CONTAINMENT_P95_BUDGET_SECONDS * 1000:.0f} ms); "
            f"median {statistics.median(durations) * 1000:.0f} ms"
        )

    def test_a_check_that_finds_the_outsiders_costs_the_same_order(self) -> None:
        """The positive control: 100 slots pushed outside are all reported, inside the same budget.

        Without it the test above could pass on a `slots_outside_bed` that never reports anything.
        """
        bed = large_bed()
        inside = point_slots(SLOT_COUNT - 100)
        outside_keys = [f"out_{n}" for n in range(100)]
        outside = [
            (key, parse_geometry({"kind": "point", "origin": [11.0 + n * 0.01, 5.0]}))
            for n, key in enumerate(outside_keys)
        ]

        durations, found = timed_runs(lambda: slots_outside_bed(bed, [*inside, *outside]))

        assert found == sorted(outside_keys)
        assert p95(durations) <= CONTAINMENT_P95_BUDGET_SECONDS


class TestLayoutPreview:
    def test_200_positions_in_a_polygon_bed_stay_within_the_preview_budget(self) -> None:
        """GP-NFR-036: 200 positions, polygon bed, p95 <= 100 ms server side, exactly 200 positions."""
        polygon = parse_geometry({"kind": "polygon", "points": [[0, 0], [10, 0], [10, 6], [6, 10], [0, 10]]})
        entry = EntryLayout(LayoutStrategy.GRID, spacing_cm=60)

        durations, result = timed_runs(lambda: compute_layout(polygon, entry, max_count=200))

        assert result.count == 200
        measured = p95(durations)
        assert measured <= LAYOUT_P95_BUDGET_SECONDS, (
            f"p95 {measured * 1000:.0f} ms over {RUNS} runs (budget {LAYOUT_P95_BUDGET_SECONDS * 1000:.0f} ms)"
        )
