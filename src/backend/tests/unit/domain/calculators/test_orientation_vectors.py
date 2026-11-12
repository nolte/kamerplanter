"""The bed axis of GP-FR-017 runs against the shared vectors (REQ-053 §9.3, §19.6, #2894).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (operation ``bed_axis``) is read by this module and by
``features/gardenPlanner/model/bedOrientation.vectors.test.ts``; a test that copied the cases inline would certify
nothing. The priority rules of :func:`derived_orientation` (aspect first, GP-FR-168) and of
:meth:`Location.orientation_on_plan` (the manual value stands without a long axis) are stated independently below.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.common.enums import Orientation
from app.domain.calculators.orientation_calculator import bed_axis, derived_orientation, orientation_from_axis
from app.domain.models.geometry import parse_geometry
from app.domain.models.site import Location, SiteConditions
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared bed-axis vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
AXIS_CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "bed_axis"]

_LONG_Y = {"kind": "rect", "origin": [1, 1], "width_m": 1, "length_m": 4}
_CIRCLE = {"kind": "circle", "origin": [5, 5], "radius_m": 2}


@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in AXIS_CASES])
def test_bed_axis_matches_the_shared_vector(case: dict[str, Any]) -> None:
    raw = case["input"]

    axis = bed_axis(parse_geometry(raw["geometry"]), raw["north_angle_deg"])

    actual = None if axis is None else {"azimuth_deg": axis.azimuth_deg, "orientation": axis.orientation.value}
    assert actual == case["expected"], case["spec"]


class TestTheVectorFile:
    def test_the_operation_is_documented_and_exercised(self) -> None:
        assert "bed_axis" in VECTORS["operations"]
        assert len(AXIS_CASES) >= 10

    def test_every_axis_name_and_the_no_axis_case_are_covered(self) -> None:
        names = {c["expected"]["orientation"] if c["expected"] is not None else None for c in AXIS_CASES}
        assert names == {"north", "northeast", "east", "southeast", None}

    def test_every_area_kind_is_covered(self) -> None:
        assert {c["input"]["geometry"]["kind"] for c in AXIS_CASES} == {"rect", "circle", "polygon"}


class TestAxisRules:
    """The axis rules, independently of the vector file."""

    @pytest.mark.parametrize("rotation", [0.0, 37.0, 90.0, 180.0, 271.5])
    def test_an_axis_has_two_ends_so_half_a_turn_changes_nothing(self, rotation: float) -> None:
        turned = parse_geometry({**_LONG_Y, "rotation_deg": rotation})
        opposite = parse_geometry({**_LONG_Y, "rotation_deg": (rotation + 180.0) % 360.0})

        assert bed_axis(turned, 12.0) == bed_axis(opposite, 12.0)

    def test_only_the_four_ends_between_north_and_southeast_name_an_axis(self) -> None:
        names = {orientation_from_axis(float(degree)) for degree in range(0, 360)}

        assert names == {Orientation.NORTH, Orientation.NORTHEAST, Orientation.EAST, Orientation.SOUTHEAST}

    def test_turning_north_clockwise_turns_the_axis_counter_clockwise(self) -> None:
        axis = bed_axis(parse_geometry(_LONG_Y), 30.0)

        assert axis is not None
        assert axis.azimuth_deg == 150.0


class TestPriority:
    """GP-FR-017/168: aspect first, then the long axis, else nothing derived."""

    def test_an_aspect_wins_over_the_geometry(self) -> None:
        assert derived_orientation(200.0, parse_geometry(_LONG_Y), 0.0) is Orientation.SOUTH

    def test_without_an_aspect_the_long_axis_decides(self) -> None:
        assert derived_orientation(None, parse_geometry(_LONG_Y), 90.0) is Orientation.EAST

    def test_without_geometry_or_long_axis_nothing_is_derived(self) -> None:
        assert derived_orientation(None, None, 0.0) is None
        assert derived_orientation(None, parse_geometry(_CIRCLE), 0.0) is None


class TestLocationOrientationOnPlan:
    def test_a_placed_bed_takes_its_axis(self) -> None:
        location = Location(name="Bed", site_key="s1", area_m2=1.0, geometry=_LONG_Y, orientation=Orientation.WEST)

        assert location.orientation_on_plan(0.0) is Orientation.NORTH

    def test_an_aspect_keeps_its_priority(self) -> None:
        location = Location(
            name="Bed", site_key="s1", area_m2=1.0, geometry=_LONG_Y, site_conditions=SiteConditions(aspect_deg=135.0)
        )

        assert location.orientation_on_plan(0.0) is Orientation.SOUTHEAST

    @pytest.mark.parametrize("geometry", [None, _CIRCLE])
    def test_the_manual_value_stands_without_a_long_axis(self, geometry: dict[str, Any] | None) -> None:
        location = Location(name="Bed", site_key="s1", area_m2=1.0, geometry=geometry, orientation=Orientation.WEST)

        assert location.orientation_on_plan(45.0) is Orientation.WEST
