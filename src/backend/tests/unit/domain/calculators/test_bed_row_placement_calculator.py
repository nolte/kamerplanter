"""REQ-053 WP 8.26 (#2669) - the beds of a CSV bed list in rows from the top-left, 0.5 m apart (#2643 question 6)."""

from __future__ import annotations

import time

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.calculators.bed_row_placement_calculator import (
    MAX_PLACEMENT_STEPS,
    PlacementTooComplexError,
    place_in_rows,
)

_FRAME = (0.0, 0.0, 10.0, 6.0)


def _box(origin: tuple[float, float], size: tuple[float, float]) -> tuple[float, float, float, float]:
    return (origin[0], origin[1], origin[0] + size[0], origin[1] + size[1])


def _overlap(a, b) -> bool:
    return a[0] < b[2] - 1e-9 and b[0] < a[2] - 1e-9 and a[1] < b[3] - 1e-9 and b[1] < a[3] - 1e-9


class TestOneRow:
    def test_beds_hang_from_the_top_edge_left_to_right_with_the_gap(self) -> None:
        positions = place_in_rows([(2.0, 1.0), (3.0, 1.2), (1.0, 1.0)], frame=_FRAME, gap=0.5)

        # top edge y = 6: the lower-left corner of a bed is (x, 6 - length)
        assert positions == [(0.0, 5.0), (2.5, 4.8), (6.0, 5.0)]

    def test_the_frame_need_not_start_at_the_origin(self) -> None:
        assert place_in_rows([(1.0, 1.0)], frame=(3.0, 2.0, 9.0, 8.0), gap=0.5) == [(3.0, 7.0)]


class TestWrapping:
    def test_a_bed_past_the_right_edge_starts_the_next_row_below_the_tallest(self) -> None:
        positions = place_in_rows([(4.0, 1.0), (4.0, 1.5), (4.0, 1.0)], frame=_FRAME, gap=0.5)

        # row 1: x 0..4 and 4.5..8.5 (tallest 1.5); 9..13 does not fit -> row 2 starts at y = 6 - 1.5 - 0.5 = 4
        assert positions == [(0.0, 5.0), (4.5, 4.5), (0.0, 3.0)]

    def test_a_bed_that_fits_exactly_stays_in_the_row(self) -> None:
        assert place_in_rows([(4.75, 1.0), (4.75, 1.0)], frame=_FRAME, gap=0.5) == [(0.0, 5.0), (5.25, 5.0)]

    def test_what_finds_no_row_any_more_gets_no_position(self) -> None:
        assert place_in_rows([(10.0, 4.0), (10.0, 4.0)], frame=_FRAME, gap=0.5) == [(0.0, 2.0), None]

    def test_a_bed_wider_than_the_frame_gets_no_position(self) -> None:
        assert place_in_rows([(12.0, 1.0)], frame=_FRAME, gap=0.5) == [None]

    def test_a_bed_that_does_not_fit_takes_no_space_from_the_next(self) -> None:
        positions = place_in_rows([(4.0, 1.0), (8.0, 8.0), (4.0, 1.0)], frame=_FRAME, gap=0.5)

        assert positions == [(0.0, 5.0), None, (4.5, 5.0)]


class TestExistingBeds:
    def test_an_existing_bed_in_the_row_is_stepped_over(self) -> None:
        positions = place_in_rows([(2.0, 1.0), (2.0, 1.0)], frame=_FRAME, obstacles=[(1.0, 4.5, 3.0, 6.0)], gap=0.5)

        assert positions == [(3.5, 5.0), (6.0, 5.0)]

    def test_a_bed_that_only_touches_is_no_obstacle(self) -> None:
        assert place_in_rows([(2.0, 1.0)], frame=_FRAME, obstacles=[(2.0, 0.0, 3.0, 6.0)], gap=0.5) == [(0.0, 5.0)]

    def test_a_row_blocked_across_the_whole_width_moves_down(self) -> None:
        positions = place_in_rows([(2.0, 1.0)], frame=_FRAME, obstacles=[(0.0, 4.0, 10.0, 6.0)], gap=0.5)

        # below the obstacle (bottom edge y = 4) with the gap: top 3.5, lower-left corner y = 2.5
        assert positions == [(0.0, 2.5)]


@given(
    sizes=st.lists(
        st.tuples(
            st.integers(min_value=10, max_value=6000).map(lambda mm: mm / 1000),  # lengths are stored in mm (§9.2)
            st.integers(min_value=10, max_value=3000).map(lambda mm: mm / 1000),
        ),
        max_size=30,
    ),
    obstacles=st.lists(
        st.tuples(st.floats(0, 9), st.floats(0, 5), st.floats(0.1, 3), st.floats(0.1, 3)).map(
            lambda t: (t[0], t[1], t[0] + t[2], t[1] + t[3])
        ),
        max_size=8,
    ),
)
def test_placed_beds_never_overlap_each_other_or_an_obstacle(sizes, obstacles) -> None:
    """Terminates for any input, one answer per bed, and every placed bed is inside the frame and overlaps nothing."""
    positions = place_in_rows(sizes, frame=_FRAME, obstacles=obstacles, gap=0.5)

    assert len(positions) == len(sizes)
    placed = [_box(origin, size) for origin, size in zip(positions, sizes, strict=True) if origin is not None]
    for index, box in enumerate(placed):
        assert _FRAME[0] - 1e-6 <= box[0] and box[2] <= _FRAME[2] + 1e-6  # inside the frame, left to right
        assert _FRAME[1] - 1e-6 <= box[1] and box[3] <= _FRAME[3] + 1e-6  # and top to bottom
        assert not any(_overlap(box, other) for other in placed[index + 1 :])
        assert not any(_overlap(box, obstacle) for obstacle in obstacles)


class TestTheWorkIsBounded:
    """#2669 SEC-001: rows blocked across the width and beds that fit nowhere cannot buy unbounded CPU."""

    @staticmethod
    def _blocked_garden() -> tuple[tuple[float, float, float, float], list[tuple[float, float, float, float]]]:
        """A 60 x 16 m frame covered by 480 posts (30 per row, 2 m apart, 16 rows): no 3 m bed fits anywhere, so
        every bed walks every row and steps over every post of it before it is given up."""
        frame = (0.0, 0.0, 60.0, 16.0)
        posts = [(2.0 * col, float(row), 2.0 * col + 0.1, row + 1.0) for row in range(16) for col in range(30)]
        return frame, posts

    def test_the_step_budget_ends_a_crafted_placement(self) -> None:
        frame, posts = self._blocked_garden()

        with pytest.raises(PlacementTooComplexError):
            place_in_rows([(3.0, 1.0)] * 500, frame=frame, obstacles=posts, gap=0.5, max_steps=100_000)

    def test_480_obstacles_and_500_beds_are_refused_by_the_default_budget_in_well_under_a_second(self) -> None:
        frame, posts = self._blocked_garden()
        started = time.perf_counter()

        with pytest.raises(PlacementTooComplexError):
            place_in_rows([(3.0, 1.0)] * 500, frame=frame, obstacles=posts, gap=0.5)

        assert time.perf_counter() - started < 2.0  # measured ~0.13 s; the batch's time budget is 10 s

    def test_a_realistic_list_stays_far_below_the_budget(self) -> None:
        sizes = [(2.0, 1.2)] * 250
        existing = [(x * 3.0, 50.0, x * 3.0 + 2.0, 51.0) for x in range(250)]

        positions = place_in_rows(sizes, frame=(0.0, 0.0, 100.0, 100.0), obstacles=existing, gap=0.5,
                                  max_steps=MAX_PLACEMENT_STEPS // 10)  # fmt: skip

        assert all(position is not None for position in positions)
