"""The Python reference runs against the shared geometry vectors (REQ-053 §19.6).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` is the single source
of truth for the Backend ↔ Frontend geometry logic: this test reads the file;
the TypeScript port (wave 2) reads the same file. A test that copied the cases
inline would certify nothing (plan §6 "Geteilte Vektoren"). The file is
required, not optional: an unreachable checkout root fails the module instead
of skipping it, because a silently skipped SSOT test is a vector file nobody
runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.domain.calculators import geometry_calculator as calc
from app.domain.models.geometry import GeometryFrame, parse_geometry
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared geometry vectors are unreachable from here")

VECTORS_PATH = _REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json"
VECTORS: dict[str, Any] = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
DEFAULT_TOLERANCE: float = VECTORS["default_tolerance"]
#: The planting-layout and adjacency operations live in the same file but run in their own test modules.
LAYOUT_OPERATIONS = frozenset(
    {"layout", "layout_error", "adjacency", "plant_state"}
)  # adjacency, plant_state: own modules
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] not in LAYOUT_OPERATIONS]


def _cases() -> list[Any]:
    return [pytest.param(case, id=case["id"]) for case in CASES]


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
    elif isinstance(expected, dict):
        assert isinstance(actual, dict)
        assert set(actual) == set(expected)
        for key, value in expected.items():
            _assert_close(actual[key], value, tolerance)
    else:  # pragma: no cover — the file format has no other leaf type
        raise AssertionError(f"unsupported expected value {expected!r}")


def _resolved_area(geometry: Any) -> float:
    shape = calc.to_shape(geometry)
    assert isinstance(shape, calc.VertexShape)
    return round(calc.shoelace_area(shape.vertices), 3)


def _run(case: dict[str, Any]) -> object:
    operation = case["operation"]
    inp = case["input"]
    tolerance_m = inp.get("tolerance_m", calc.DEFAULT_TOLERANCE_M)
    if operation == "area":
        return calc.area_m2(parse_geometry(inp["geometry"]))
    if operation == "resolved_area":
        return _resolved_area(parse_geometry(inp["geometry"]))
    if operation == "bbox":
        return list(calc.bounding_box(parse_geometry(inp["geometry"])))
    if operation == "centroid":
        return list(calc.centroid(parse_geometry(inp["geometry"])))
    if operation == "is_simple":
        return calc.is_simple_polygon(parse_geometry(inp["geometry"]).points)  # type: ignore[union-attr]
    if operation == "validate":
        return calc.validate_geometry(parse_geometry(inp["geometry"]))
    if operation == "contains":
        parent_geometry = parse_geometry(inp["parent"])
        if inp["mode"] == "bed":
            parent = calc.to_local_shape(parent_geometry)
            child = calc.to_shape(parse_geometry(inp["child"], frame=GeometryFrame.BED))
        else:
            parent = calc.to_shape(parent_geometry)
            child = calc.to_shape(parse_geometry(inp["child"]))
        return calc.contains(parent, child, tolerance_m=tolerance_m, inset_m=inp.get("inset_m", 0.0))
    if operation == "overlaps":
        a = calc.to_shape(parse_geometry(inp["a"]))
        b = calc.to_shape(parse_geometry(inp["b"]))
        return calc.overlaps(a, b, tolerance_m=tolerance_m)
    if operation == "bed_to_plan":
        return list(calc.transform_bed_to_plan(tuple(inp["point"]), parse_geometry(inp["bed"])))
    if operation == "plan_to_bed":
        return list(calc.transform_plan_to_bed(tuple(inp["point"]), parse_geometry(inp["bed"])))
    if operation == "validate_model":
        frame = GeometryFrame(inp.get("frame", GeometryFrame.PLAN))
        try:
            geometry = parse_geometry(inp["geometry"], frame=frame)
        except ValidationError:
            return {"valid": False}
        result: dict[str, Any] = {"valid": True}
        if "normalized" in case["expected"]:
            result["normalized"] = geometry.model_dump(mode="json")
        return result
    raise AssertionError(f"unknown operation {operation!r} in vector {case['id']}")


class TestVectorFile:
    def test_ids_are_unique(self) -> None:
        ids = [case["id"] for case in VECTORS["cases"]]
        assert len(ids) == len(set(ids))

    def test_every_operation_is_documented_and_exercised(self) -> None:
        documented = set(VECTORS["operations"]) - LAYOUT_OPERATIONS
        used = {case["operation"] for case in CASES}
        assert used == documented

    def test_acceptance_criteria_are_pinned(self) -> None:
        """GP-ACC-003 and GP-ACC-004 stay in the file — deleting them silently drops the acceptance proof."""
        specs = " ".join(case["spec"] for case in CASES)
        assert "GP-ACC-003" in specs
        assert "GP-ACC-004" in specs


class TestSharedVectors:
    @pytest.mark.parametrize("case", _cases())
    def test_vector(self, case: dict[str, Any]) -> None:
        actual = _run(case)
        _assert_close(actual, case["expected"], case.get("tolerance", DEFAULT_TOLERANCE))
