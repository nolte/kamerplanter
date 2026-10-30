"""The Python reference of ``place_geometry`` runs against the shared vectors (REQ-053 GP-FR-044, §19.6, #2536).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` is read by this module and by
``features/gardenPlanner/templates/placeGeometry.vectors.test.ts``, the TypeScript port the editor's template ghost
uses; a test that copied the cases inline would certify nothing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.domain.calculators.template_placement_calculator import place_geometry
from app.domain.models.geometry import GeometryFrame, parse_geometry
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared place_geometry vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
DEFAULT_TOLERANCE: float = VECTORS["default_tolerance"]
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "place_geometry"]


def _assert_close(actual: object, expected: object, tolerance: float) -> None:
    """Numbers within *tolerance*, everything else exact; recurses into lists and dicts."""
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        assert actual == expected
    elif isinstance(expected, int | float):
        assert isinstance(actual, int | float)
        assert actual == pytest.approx(expected, abs=tolerance)
    elif isinstance(expected, list):
        assert isinstance(actual, list | tuple)
        assert len(actual) == len(expected)
        for item_actual, item_expected in zip(actual, expected, strict=True):
            _assert_close(item_actual, item_expected, tolerance)
    else:
        assert isinstance(expected, dict)
        assert isinstance(actual, dict)
        assert set(actual) == set(expected)
        for key, value in expected.items():
            _assert_close(actual[key], value, tolerance)


@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in CASES])
def test_reference_matches_the_shared_vector(case: dict[str, Any]) -> None:
    raw = case["input"]
    geometry = parse_geometry(raw["geometry"], frame=GeometryFrame.BED)
    origin = (float(raw["origin"][0]), float(raw["origin"][1]))

    placed = place_geometry(geometry, origin=origin, rotation_deg=raw["rotation_deg"])

    _assert_close(placed, case["expected"], case.get("tolerance", DEFAULT_TOLERANCE))


def test_the_operation_is_documented_and_exercised() -> None:
    assert "place_geometry" in VECTORS["operations"]
    assert {case["input"]["geometry"]["kind"] for case in CASES} == {"rect", "circle", "polygon"}
