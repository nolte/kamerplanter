"""The Python reference of the edge-to-edge distance runs against the shared vectors (REQ-053 GP-FR-167, WP 9.12).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` is read by this module and by
``features/gardenPlanner/model/geometryDistance.vectors.test.ts``; a test that copied the cases inline would certify
nothing. The rules the file pins are stated once more apart from it (symmetry, containment, ``None`` without a
source), so the reference is not only compared with a file written next to it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.common.enums import GardenObjectType
from app.domain.calculators.geometry_distance import (
    WATER_SOURCE_OBJECT_TYPE,
    WATER_SOURCES_ON_SITE_ONLY,
    edge_distance_m,
    is_water_source,
    nearest_water_source_m,
)
from app.domain.models.geometry import Geometry, parse_geometry
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared distance vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
DEFAULT_TOLERANCE: float = VECTORS["default_tolerance"]
OPERATIONS = ("edge_distance", "nearest_water_source", "is_water_source")
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] in OPERATIONS]


def _geometry(raw: dict[str, Any] | None) -> Geometry | None:
    return parse_geometry(raw) if raw is not None else None


def _run(case: dict[str, Any]) -> float | bool | None:
    raw = case["input"]
    if case["operation"] == "is_water_source":
        return is_water_source(raw["object_type"], raw["off_site"])
    if case["operation"] == "edge_distance":
        a, b = parse_geometry(raw["a"]), parse_geometry(raw["b"])
        return edge_distance_m(a, b)
    return nearest_water_source_m(_geometry(raw["bed"]), [parse_geometry(source) for source in raw["sources"]])


@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in CASES])
def test_reference_matches_the_shared_vector(case: dict[str, Any]) -> None:
    actual = _run(case)
    expected = case["expected"]

    if expected is None or isinstance(expected, bool):
        assert actual is expected, case["spec"]
    else:
        assert actual == pytest.approx(expected, abs=case.get("tolerance", DEFAULT_TOLERANCE)), case["spec"]


def test_the_operations_are_documented_and_exercised() -> None:
    assert set(OPERATIONS) <= set(VECTORS["operations"])
    assert {case["operation"] for case in CASES} == set(OPERATIONS)


def test_the_file_covers_the_rules_a_centre_or_box_measure_would_get_wrong() -> None:
    """Containment, a crossing without a vertex inside, a concave notch, a rotation and a stroke stay in the file."""
    ids = {case["id"] for case in CASES}

    assert {
        "edge-distance-rect-contains-rect",
        "edge-distance-crossing-bars",
        "edge-distance-concave-notch",
        "edge-distance-rotated-rect-to-point",
        "edge-distance-polyline-stroke",
        "nearest-water-source-none",
    } <= ids


def _parsed(raw: dict[str, Any]) -> Geometry:
    return parse_geometry(raw)


class TestRulesApartFromTheFile:
    @pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in CASES if c["operation"] == "edge_distance"])
    def test_the_measure_is_symmetric(self, case: dict[str, Any]) -> None:
        a, b = _parsed(case["input"]["a"]), _parsed(case["input"]["b"])
        assert edge_distance_m(a, b) == edge_distance_m(b, a)

    def test_the_query_narrowing_is_the_same_rule(self) -> None:
        """The service narrows its query with these constants; they must say what the predicate says."""
        assert WATER_SOURCE_OBJECT_TYPE is GardenObjectType.WATER_SOURCE
        assert WATER_SOURCES_ON_SITE_ONLY is True
        assert is_water_source(WATER_SOURCE_OBJECT_TYPE, False) and not is_water_source(WATER_SOURCE_OBJECT_TYPE, True)

    def test_a_shape_is_zero_from_itself(self) -> None:
        bed = _parsed({"kind": "polygon", "points": [[0, 0], [3, 0], [3, 2]]})
        assert edge_distance_m(bed, bed) == 0.0

    def test_no_source_is_none_not_zero(self) -> None:
        bed = _parsed({"kind": "rect", "origin": [0, 0], "width_m": 1, "length_m": 1})
        assert nearest_water_source_m(bed, []) is None
        assert nearest_water_source_m(None, [_parsed({"kind": "point", "origin": [1, 1]})]) is None

    def test_the_result_is_rounded_half_up_to_a_millimetre(self) -> None:
        a = _parsed({"kind": "point", "origin": [0, 0]})
        b = _parsed({"kind": "point", "origin": [0.0015, 0]})
        assert edge_distance_m(a, b) == 0.002
