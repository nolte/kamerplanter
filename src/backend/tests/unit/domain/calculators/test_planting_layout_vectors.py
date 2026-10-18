"""The Python reference of the planting layout runs against the shared vectors (REQ-053 §19.6).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` is read by this module and by
``features/gardenPlanner/model/layout.vectors.test.ts``; a test that copied the cases inline would
certify nothing. GP-ACC-017/018/043 are pinned by id so the acceptance proof cannot be dropped
quietly. The expected numbers of GP-ACC-017 are also stated explicitly below, from the spec, so the
reference is not only compared with itself.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.common.enums import LayoutStrategy, RowDirection
from app.common.exceptions import PlanError
from app.domain.calculators.planting_layout_calculator import EntryLayout, LayoutResult, compute_layout
from app.domain.models.geometry import parse_geometry
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared layout vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
TOLERANCE: float = VECTORS["default_tolerance"]
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] in {"layout", "layout_error"}]


def entry_of(raw: dict[str, Any]) -> tuple[EntryLayout, int | None]:
    fields = dict(raw)
    max_count = fields.pop("max_count", None)
    fields["layout_strategy"] = LayoutStrategy(fields["layout_strategy"])
    if "row_direction" in fields:
        fields["row_direction"] = RowDirection(fields["row_direction"])
    if fields.get("row_assignment") is not None:
        fields["row_assignment"] = tuple(fields["row_assignment"])
    return EntryLayout(**fields), max_count


def view(result: LayoutResult) -> dict[str, Any]:
    positions = [slot for slot in result.slots if slot.point is not None]
    return {
        "count": result.count,
        "capacity_max": result.capacity_max,
        "warnings": [warning.code for warning in result.warnings],
        "points": [list(slot.point) for slot in positions if slot.point is not None],
        "row_indices": [slot.row_index for slot in positions],
        "zones": [
            {"outline": [list(p) for p in slot.outline], "capacity_plants": slot.capacity_plants}
            for slot in result.slots
            if slot.outline is not None
        ],
    }


def assert_close(actual: object, expected: object) -> None:
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        assert actual == expected
    elif isinstance(expected, int | float):
        assert isinstance(actual, int | float)
        assert actual == pytest.approx(expected, abs=TOLERANCE)
    elif isinstance(expected, list):
        assert isinstance(actual, list)
        assert len(actual) == len(expected)
        for item_actual, item_expected in zip(actual, expected, strict=True):
            assert_close(item_actual, item_expected)
    elif isinstance(expected, dict):
        assert isinstance(actual, dict)
        assert set(actual) == set(expected)
        for key, value in expected.items():
            assert_close(actual[key], value)
    else:  # pragma: no cover - the file format has no other leaf type
        raise AssertionError(f"unsupported expected value {expected!r}")


class TestVectorFile:
    def test_layout_operations_are_documented_and_exercised(self) -> None:
        assert {case["operation"] for case in CASES} == {"layout", "layout_error"}
        assert {"layout", "layout_error"} <= set(VECTORS["operations"])

    def test_acceptance_criteria_are_pinned(self) -> None:
        by_id = {case["id"]: case for case in CASES}
        assert "GP-ACC-017" in by_id["layout-001-acc-017-rows-rect"]["spec"]
        assert "GP-ACC-018" in by_id["layout-003-acc-018-triangle-grid"]["spec"]
        assert "GP-ACC-043" in by_id["layout-error-001-acc-043-too-many-positions"]["spec"]


class TestSharedVectors:
    @pytest.mark.parametrize("case", [pytest.param(case, id=case["id"]) for case in CASES])
    def test_vector(self, case: dict[str, Any]) -> None:
        bed = parse_geometry(case["input"]["bed"])
        entry, max_count = entry_of(case["input"]["entry"])
        if case["operation"] == "layout":
            assert_close(view(compute_layout(bed, entry, max_count)), case["expected"])
            return
        with pytest.raises(PlanError) as raised:
            compute_layout(bed, entry, max_count)
        detail = raised.value.details[0]
        assert raised.value.status_code == 422
        expected = case["expected"]
        assert detail["code"] == expected["code"]
        if "estimated" in expected:
            assert detail["estimated"] == expected["estimated"]


class TestAcceptanceStatedFromTheSpec:
    """GP-ACC-017/018/043 asserted from the requirement text, not from the vector file."""

    def test_acc_017_three_rows_of_ten(self) -> None:
        bed = parse_geometry({"kind": "rect", "origin": [2.0, 3.5], "width_m": 3.0, "length_m": 1.2})
        entry = EntryLayout(
            LayoutStrategy.ROWS,
            spacing_cm=30,
            row_spacing_cm=40,
            edge_margin_along_cm=15,
            edge_margin_across_cm=15,
        )
        result = compute_layout(bed, entry)
        assert result.count == 30
        assert sorted({slot.point[1] for slot in result.slots if slot.point}) == pytest.approx([0.15, 0.55, 0.95])
        row_xs = [slot.point[0] for slot in result.slots if slot.point and slot.row_index == 0]
        assert row_xs == pytest.approx([0.15 + 0.3 * i for i in range(10)])

    def test_acc_018_every_position_inside_the_triangle(self) -> None:
        bed = parse_geometry({"kind": "polygon", "points": [[0, 0], [4, 0], [0, 3]]})
        entry = EntryLayout(LayoutStrategy.GRID, spacing_cm=50, edge_margin_along_cm=0, edge_margin_across_cm=0)
        result = compute_layout(bed, entry)
        assert result.count > 0
        for slot in result.slots:
            assert slot.point is not None
            x, y = slot.point
            assert x >= -TOLERANCE and y >= -TOLERANCE
            assert x / 4 + y / 3 <= 1 + TOLERANCE  # the hypotenuse

    def test_acc_043_refuses_before_generating_points(self) -> None:
        bed = parse_geometry({"kind": "rect", "origin": [0, 0], "width_m": 1000, "length_m": 1000})
        with pytest.raises(PlanError) as raised:
            compute_layout(bed, EntryLayout(LayoutStrategy.GRID, spacing_cm=5))
        assert raised.value.details[0]["code"] == "layout.too_many_positions"
        assert raised.value.details[0]["estimated"] == pytest.approx(4e8, rel=1e-6)
