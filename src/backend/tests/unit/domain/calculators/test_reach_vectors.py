"""The Python reference of ``reach`` runs against the shared vectors (REQ-053 GP-FR-166, WP 8.23, §19.6).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` is read by this module and by
``features/gardenPlanner/model/reach.vectors.test.ts``; a test that copied the cases inline would certify nothing.
The issue's acceptance cases are pinned by id, and the rules are stated once more apart from the file so the
reference is not only compared with a file written next to it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.common.enums import AccessSide
from app.domain.calculators.reach_calculator import (
    ACCESS_BOTH,
    ACCESS_ONE,
    ACCESS_UNKNOWN,
    HINT_REACH_TOO_WIDE,
    REACH_BOTH_SIDES_M,
    REACH_ONE_SIDE_M,
    access_class,
    assess,
)
from app.domain.models.geometry import parse_geometry
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared reach vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
DEFAULT_TOLERANCE: float = VECTORS["default_tolerance"]
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "reach"]

#: The acceptance of #2666 names these: a 1.3 m bed without access hints; with access from both sides a bed
#: within 1.2 m does not (a 1.3 m bed exceeds 1.2 m and still hints, pinned as well).
ACCEPTANCE_CASES = {
    "reach-rect-1-3-no-access": True,
    "reach-rect-1-2-both-sides-ns": False,
    "reach-rect-1-3-both-sides": True,
}


def _run(case: dict[str, Any]) -> dict[str, Any]:
    raw = case["input"]
    geometry = parse_geometry(raw["geometry"]) if raw["geometry"] is not None else None
    thresholds = {name: raw[name] for name in ("both_sides_m", "one_side_m") if name in raw}
    result = assess(geometry, raw["access_sides"], **thresholds)
    return {
        "hint": result.hint,
        "reason": result.reason,
        "access": result.access,
        "threshold_m": result.threshold_m,
        "width_m": result.width_m,
    }


@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in CASES])
def test_reference_matches_the_shared_vector(case: dict[str, Any]) -> None:
    actual = _run(case)
    expected = case["expected"]
    tolerance = case.get("tolerance", DEFAULT_TOLERANCE)

    for key in ("hint", "reason", "access"):
        assert actual[key] == expected[key], (key, case["spec"])
    assert actual["threshold_m"] == pytest.approx(expected["threshold_m"], abs=tolerance), case["spec"]
    if expected["width_m"] is None:
        assert actual["width_m"] is None, case["spec"]
    else:
        assert actual["width_m"] == pytest.approx(expected["width_m"], abs=tolerance), case["spec"]


def test_the_operation_is_documented_and_exercised() -> None:
    assert "reach" in VECTORS["operations"]
    assert CASES, "no reach vector: the shared file would certify nothing"


def test_acceptance_cases_are_in_the_file() -> None:
    by_id = {case["id"]: case for case in CASES}

    for case_id, hint in ACCEPTANCE_CASES.items():
        assert by_id[case_id]["expected"]["hint"] is hint


def test_the_file_covers_both_boundaries_and_configured_thresholds() -> None:
    expected = [case["expected"] for case in CASES]
    configured = [case for case in CASES if "both_sides_m" in case["input"] or "one_side_m" in case["input"]]

    assert any(e["access"] == ACCESS_BOTH and e["width_m"] == e["threshold_m"] and not e["hint"] for e in expected)
    assert any(e["access"] == ACCESS_ONE and e["width_m"] == e["threshold_m"] and not e["hint"] for e in expected)
    assert configured, "no case with a non-default threshold"


class TestRulesApartFromTheFile:
    def test_confirmed_defaults(self) -> None:
        assert (REACH_BOTH_SIDES_M, REACH_ONE_SIDE_M) == (1.2, 0.6)
        assert HINT_REACH_TOO_WIDE == "bed.reach_too_wide"

    @pytest.mark.parametrize(
        ("sides", "expected"),
        [
            ([], ACCESS_UNKNOWN),
            (None, ACCESS_UNKNOWN),
            (["N"], ACCESS_ONE),
            (["N", "E"], ACCESS_ONE),
            (["S", "W"], ACCESS_ONE),
            (["N", "S"], ACCESS_BOTH),
            (["W", "E"], ACCESS_BOTH),
            ([AccessSide.NORTH, AccessSide.EAST, AccessSide.WEST], ACCESS_BOTH),
        ],
    )
    def test_access_class(self, sides: list[str] | None, expected: str) -> None:
        assert access_class(sides) == expected

    def test_unknown_access_takes_the_strict_threshold(self) -> None:
        bed = parse_geometry({"kind": "rect", "origin": [0.0, 0.0], "width_m": 1.0, "length_m": 2.0})

        assert assess(bed, []).threshold_m == REACH_ONE_SIDE_M
        assert assess(bed, []).hint is True

    def test_never_raises_on_missing_data(self) -> None:
        result = assess(None, None)

        assert result.hint is False
        assert result.width_m is None
