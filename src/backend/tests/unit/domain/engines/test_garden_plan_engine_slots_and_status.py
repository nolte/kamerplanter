"""REQ-053 WP 1.9 — the two pure rules the single-resource service added to the plan engine.

V-10 (``bed_status.invalid_transition``): the transition table of §7.4, exhaustively — every pair of the
three states, so a fourth state or an added edge cannot slip in unnoticed.
V-06 (``slot.overlap``): zone slots of one bed may not overlap; positions and rows have no overlap notion.
The geometry itself is the calculator's, pinned against ``garden-plan-vectors.json`` by
``test_geometry_vectors.py``; here is only what the engine does with it.
"""

from __future__ import annotations

from itertools import product

import pytest

from app.common.enums import BedStatus
from app.domain.engines.garden_plan_engine import (
    BED_STATUS_TRANSITIONS,
    bed_status_transition_allowed,
    overlapping_zones,
)
from app.domain.models.geometry import GeometryFrame, parse_geometry


def zone(*points: tuple[float, float]):
    return parse_geometry({"kind": "polygon", "points": [list(p) for p in points]}, frame=GeometryFrame.BED)


def position(x: float, y: float):
    return parse_geometry({"kind": "point", "origin": [x, y]}, frame=GeometryFrame.BED)


ALLOWED = {
    (BedStatus.PLANNED, BedStatus.ACTIVE),
    (BedStatus.PLANNED, BedStatus.RETIRED),
    (BedStatus.ACTIVE, BedStatus.RETIRED),
    (BedStatus.RETIRED, BedStatus.ACTIVE),
}


@pytest.mark.parametrize(("current", "target"), list(product(BedStatus, BedStatus)))
def test_exactly_the_four_transitions_of_7_4_are_allowed(current: BedStatus, target: BedStatus) -> None:
    assert bed_status_transition_allowed(current, target) is ((current, target) in ALLOWED)


def test_every_state_has_a_row_in_the_table() -> None:
    assert set(BED_STATUS_TRANSITIONS) == set(BedStatus)


class TestOverlappingZones:
    left = zone((0, 0), (1, 0), (1, 1), (0, 1))

    def test_overlapping_zones_are_reported_as_a_pair(self) -> None:
        right = zone((0.5, 0), (1.5, 0), (1.5, 1), (0.5, 1))
        assert overlapping_zones([("a", self.left), ("b", right)]) == [("a", "b")]

    def test_zones_that_only_touch_do_not_overlap(self) -> None:
        right = zone((1, 0), (2, 0), (2, 1), (1, 1))
        assert overlapping_zones([("a", self.left), ("b", right)]) == []

    def test_a_position_inside_a_zone_is_not_an_overlap(self) -> None:
        assert overlapping_zones([("a", self.left), ("p", position(0.5, 0.5))]) == []

    def test_every_pair_is_listed_once(self) -> None:
        middle = zone((0.4, 0), (0.6, 0), (0.6, 1), (0.4, 1))
        pairs = overlapping_zones([("a", self.left), ("b", middle), ("c", zone((0.5, 0), (2, 0), (2, 1), (0.5, 1)))])
        assert sorted(pairs) == [("a", "b"), ("a", "c"), ("b", "c")]

    def test_nothing_overlaps_nothing(self) -> None:
        assert overlapping_zones([]) == [] and overlapping_zones([("a", self.left)]) == []
