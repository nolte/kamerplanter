"""Orientation from aspect: 0-359 degrees into eight compass sectors (REQ-053 GP-FR-017/168, WP 8.24, #2667)."""

from __future__ import annotations

import math

import pytest

from app.common.enums import Orientation
from app.domain.calculators.orientation_calculator import orientation_from_aspect

N, NE, E, SE = Orientation.NORTH, Orientation.NORTHEAST, Orientation.EAST, Orientation.SOUTHEAST
S, SW, W, NW = Orientation.SOUTH, Orientation.SOUTHWEST, Orientation.WEST, Orientation.NORTHWEST


@pytest.mark.parametrize(
    ("aspect", "expected"),
    [
        # every sector centre
        (0.0, N),
        (45.0, NE),
        (90.0, E),
        (135.0, SE),
        (180.0, S),
        (225.0, SW),
        (270.0, W),
        (315.0, NW),
        # every boundary belongs to the sector that starts there, clockwise
        (22.5, NE),
        (67.5, E),
        (112.5, SE),
        (157.5, S),
        (202.5, SW),
        (247.5, W),
        (292.5, NW),
        (337.5, N),
        # just below every boundary stays in the sector before it
        (22.49, N),
        (67.49, NE),
        (112.49, E),
        (157.49, SE),
        (202.49, S),
        (247.49, SW),
        (292.49, W),
        (337.49, NW),
        # the wrap-around at north
        (359.0, N),
        (359.9, N),
        (359.999, N),
        (0.001, N),
    ],
)
def test_aspect_falls_into_its_sector(aspect: float, expected: Orientation) -> None:
    assert orientation_from_aspect(aspect) is expected


def test_every_whole_degree_from_0_to_359_maps_to_one_of_the_eight_sectors() -> None:
    """The acceptance of #2667: 0-359 degrees -> 8 orientations, each sector exactly 45 whole degrees wide."""
    table = {degree: orientation_from_aspect(float(degree)) for degree in range(360)}

    assert set(table.values()) == set(Orientation)
    assert len(set(Orientation)) == 8
    for orientation in Orientation:
        assert sum(1 for value in table.values() if value is orientation) == 45
    # the sector of a whole degree, written out independently of the implementation
    sectors = (N, NE, E, SE, S, SW, W, NW)
    for degree, orientation in table.items():
        expected = sectors[math.floor((degree + 22.5) / 45) % 8]
        assert orientation is expected, degree


@pytest.mark.parametrize(("aspect", "expected"), [(360.0, N), (405.0, NE), (-45.0, NW), (-0.0, N)])
def test_an_angle_outside_one_turn_is_normalised(aspect: float, expected: Orientation) -> None:
    assert orientation_from_aspect(aspect) is expected


@pytest.mark.parametrize("aspect", [math.nan, math.inf, -math.inf])
def test_a_non_finite_angle_names_no_direction(aspect: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        orientation_from_aspect(aspect)
