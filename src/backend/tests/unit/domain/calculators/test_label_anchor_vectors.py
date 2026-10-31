"""The Python reference of ``label_anchor`` runs against the shared vectors (REQ-053 GP-UX-047, GP-FR-003, #2490).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` is read by this module and by
``features/gardenPlanner/model/labelAnchor.vectors.test.ts``, the TypeScript port the editor draws its names with; a
test that copied the cases inline would certify nothing. The PDF writer (``plan_svg_engine``) places names on the
same point, which ``test_plan_svg_engine_label_placement.py`` pins.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.domain.calculators.geometry_calculator import centroid
from app.domain.calculators.label_anchor_calculator import label_anchor
from app.domain.models.geometry import parse_geometry
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared label_anchor vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
DEFAULT_TOLERANCE: float = VECTORS["default_tolerance"]
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "label_anchor"]


@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in CASES])
def test_reference_matches_the_shared_vector(case: dict[str, Any]) -> None:
    anchor = label_anchor(parse_geometry(case["input"]["geometry"]))

    tolerance = case.get("tolerance", DEFAULT_TOLERANCE)
    expected = case["expected"]
    assert set(expected) == {"point", "width_m"}
    assert anchor.point == pytest.approx(tuple(expected["point"]), abs=tolerance)
    assert anchor.width_m == pytest.approx(expected["width_m"], abs=tolerance)


def test_the_operation_is_documented_and_covers_every_kind() -> None:
    assert "label_anchor" in VECTORS["operations"]
    assert {case["input"]["geometry"]["kind"] for case in CASES} == {"rect", "circle", "polygon", "polyline", "point"}


def test_the_vectors_hold_a_concave_bed_whose_centroid_is_outside_it() -> None:
    """The case the rule exists for: a vector set of convex shapes only could not tell the pole from the centroid."""
    differing = [
        case
        for case in CASES
        if case["input"]["geometry"]["kind"] == "polygon"
        and tuple(case["expected"]["point"]) != centroid(parse_geometry(case["input"]["geometry"]))
    ]
    assert any("l-shape" in case["id"] for case in differing)
