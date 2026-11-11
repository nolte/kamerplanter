"""The Python reference of the window orientation runs against the shared vectors (REQ-053 GP-FR-181, §19.6).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (operations ``window_facing`` and ``window_sun_window``) is
read by this module and by ``features/gardenPlanner/model/windowOrientation.vectors.test.ts``; a test that copied
the cases inline would certify nothing. The rules of the agrobiology review are also stated independently below,
so the reference is not only compared with a file written next to it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.common.enums import Orientation, SunWindow
from app.domain.calculators.orientation_calculator import orientation_from_aspect
from app.domain.calculators.window_orientation import (
    SUGGESTION_CAVEATS,
    FacingBasis,
    WindowHint,
    contribution,
    round_azimuth,
    suggest_sun_window,
    window_facing,
)
from app.domain.models.geometry import parse_geometry
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared window vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
FACING_CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "window_facing"]
SUN_CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "window_sun_window"]


@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in FACING_CASES])
def test_window_facing_matches_the_shared_vector(case: dict[str, Any]) -> None:
    raw = case["input"]
    boundary = parse_geometry(raw["boundary"]) if raw["boundary"] is not None else None

    facing = window_facing(parse_geometry(raw["window"]), raw["north_angle_deg"], boundary)

    actual = (
        None
        if facing is None
        else {"azimuth_deg": facing.azimuth_deg, "orientation": facing.orientation.value, "basis": facing.basis.value}
    )
    assert actual == case["expected"], case["spec"]


@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in SUN_CASES])
def test_suggest_sun_window_matches_the_shared_vector(case: dict[str, Any]) -> None:
    result = suggest_sun_window(case["input"]["azimuths"], case["input"]["latitude"])

    actual = {
        "sun_window": result.sun_window.value if result.sun_window is not None else None,
        "hints": [hint.value for hint in result.hints],
    }
    assert actual == case["expected"], case["spec"]


class TestTheVectorFile:
    def test_both_operations_are_documented_and_exercised(self) -> None:
        assert {"window_facing", "window_sun_window"} <= set(VECTORS["operations"])
        assert FACING_CASES and SUN_CASES

    def test_every_direction_and_every_combination_is_covered(self) -> None:
        """Every one of the eight sectors, both hemispheres, the tropics, no latitude and every combination rule."""
        northern = [c for c in SUN_CASES if c["input"]["latitude"] == 50.0 and len(c["input"]["azimuths"]) == 1]
        sectors = {orientation_from_aspect(c["input"]["azimuths"][0]) for c in northern}
        assert sectors == set(Orientation)
        suggestions = {c["expected"]["sun_window"] for c in SUN_CASES}
        assert suggestions == {"morning", "midday", "afternoon", "all_day", "mixed", None}
        hints = {hint for c in SUN_CASES for hint in c["expected"]["hints"]}
        assert hints == {hint.value for hint in WindowHint}
        assert any(c["input"]["latitude"] is not None and c["input"]["latitude"] < 0 for c in SUN_CASES)

    def test_both_bases_of_the_facing_are_covered(self) -> None:
        bases = {c["expected"]["basis"] for c in FACING_CASES if c["expected"] is not None}
        assert bases == {basis.value for basis in FacingBasis}


class TestRules:
    """The review's rules, independently of the vector file."""

    @pytest.mark.parametrize(
        ("azimuth", "expected"),
        [
            (0.0, None),
            (45.0, SunWindow.MORNING),
            (90.0, SunWindow.MORNING),
            (135.0, SunWindow.MORNING),
            (180.0, SunWindow.MIDDAY),
            (225.0, SunWindow.AFTERNOON),
            (270.0, SunWindow.AFTERNOON),
            (315.0, SunWindow.AFTERNOON),
        ],
    )
    def test_the_northern_table(self, azimuth: float, expected: SunWindow | None) -> None:
        assert contribution(azimuth, 52.5) is expected

    def test_a_single_window_is_never_all_day(self) -> None:
        for azimuth in range(0, 360, 5):
            assert suggest_sun_window([float(azimuth)], 48.0).sun_window is not SunWindow.ALL_DAY

    def test_a_suggestion_carries_every_caveat_and_no_suggestion_none(self) -> None:
        assert suggest_sun_window([180.0], 48.0).hints == SUGGESTION_CAVEATS
        assert suggest_sun_window([0.0], 48.0).hints == (WindowHint.DIFFUSE_LIGHT_ONLY,)

    def test_the_southern_hemisphere_mirrors_north_and_south(self) -> None:
        assert contribution(0.0, -35.0) is SunWindow.MIDDAY
        assert contribution(180.0, -35.0) is None

    def test_the_order_of_the_azimuths_does_not_matter(self) -> None:
        assert suggest_sun_window([270.0, 90.0, 180.0], 50.0) == suggest_sun_window([90.0, 180.0, 270.0], 50.0)

    def test_the_rounding_wraps_360_to_0(self) -> None:
        assert round_azimuth(359.96) == 0.0
        assert round_azimuth(-0.04) == 0.0
        assert round_azimuth(-45.0) == 315.0

    def test_a_point_window_has_no_direction(self) -> None:
        assert window_facing(parse_geometry({"kind": "point", "origin": [1, 1]}), 0.0) is None

    def test_a_window_without_outline_uses_the_left_of_the_drawing_direction(self) -> None:
        line = parse_geometry({"kind": "polyline", "points": [[0, 0], [0, 2]], "width_m": 0.1})

        facing = window_facing(line, 0.0)

        assert facing is not None
        assert (facing.orientation, facing.basis) == (Orientation.WEST, FacingBasis.DRAWING_DIRECTION)

    def test_a_circular_outline_tells_the_outside(self) -> None:
        circle = parse_geometry({"kind": "circle", "origin": [5, 5], "radius_m": 3})
        line = parse_geometry({"kind": "polyline", "points": [[5, 8], [6, 8]], "width_m": 0.1})

        facing = window_facing(line, 0.0, circle)

        assert facing is not None
        assert (facing.orientation, facing.basis) == (Orientation.NORTH, FacingBasis.BOUNDARY)
