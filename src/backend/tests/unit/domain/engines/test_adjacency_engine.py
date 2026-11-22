"""The adjacency engine derives ``adjacent_to`` pairs from slot geometry (REQ-053 GP-FR-130, GP-ACC-023).

The shared cases of ``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (operation ``adjacency``) are
read from the file, not copied; the limits and edge cases that need generated data are built here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.common.enums import GrowthHabit, SlotRole
from app.domain.engines.adjacency_engine import (
    POINT_SLOT_LIMIT,
    AdjacencyNode,
    derive_adjacency,
    lower_bound_cm,
)
from app.domain.models.geometry import GeometryFrame, parse_geometry
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared adjacency vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "adjacency"]
TOLERANCE: float = VECTORS["default_tolerance"]


def node_of(raw: dict[str, Any]) -> AdjacencyNode:
    return AdjacencyNode(
        key=raw["key"],
        role=SlotRole(raw["role"]),
        geometry=parse_geometry(raw["geometry"], frame=GeometryFrame.BED),
        spacing_cm=raw.get("spacing_cm"),
        row_spacing_cm=raw.get("row_spacing_cm"),
        mature_width_cm=raw.get("mature_width_cm"),
        growth_habit=GrowthHabit(raw["growth_habit"]) if raw.get("growth_habit") else None,
    )


def point(key: str, x: float, y: float, *, spacing_cm: float | None = 30.0) -> AdjacencyNode:
    geometry = parse_geometry({"kind": "point", "origin": [x, y]}, frame=GeometryFrame.BED)
    return AdjacencyNode(key=key, role=SlotRole.POSITION, geometry=geometry, spacing_cm=spacing_cm)


class TestSharedVectors:
    def test_the_vector_file_carries_the_adjacency_cases(self) -> None:
        assert "adjacency" in VECTORS["operations"]
        assert len(CASES) >= 8
        assert "GP-ACC-023" in " ".join(case["spec"] for case in CASES)

    @pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
    def test_the_reference_matches_the_vector(self, case: dict[str, Any]) -> None:
        nodes = [node_of(raw) for raw in case["input"]["slots"]]
        pairs = derive_adjacency(nodes, case["input"]["adjacency_factor"])
        got = [[pair.slot_a_key, pair.slot_b_key, pair.distance_cm] for pair in pairs]
        expected = case["expected"]
        assert [row[:2] for row in got] == [row[:2] for row in expected]
        for have, want in zip(got, expected, strict=True):
            assert have[2] == pytest.approx(want[2], abs=TOLERANCE + 0.05)


class TestTheNeighbourhoodRule:
    def test_gp_acc_023_edges_exist_exactly_up_to_45_cm(self) -> None:
        """Slots 30 cm apart at factor 1.5: 30 cm and the 42.4 cm diagonal count, 60 cm does not."""
        nodes = [point("a", 0.0, 0.0), point("b", 0.3, 0.0), point("c", 0.6, 0.0), point("d", 0.3, 0.3)]
        pairs = {(p.slot_a_key, p.slot_b_key): p.distance_cm for p in derive_adjacency(nodes, 1.5)}
        assert pairs == {("a", "b"): 30.0, ("b", "c"): 30.0, ("a", "d"): 42.4, ("b", "d"): 30.0, ("c", "d"): 42.4}

    def test_moving_a_slot_out_of_reach_drops_its_pairs(self) -> None:
        near = derive_adjacency([point("a", 0.0, 0.0), point("b", 0.3, 0.0)], 1.5)
        moved = derive_adjacency([point("a", 0.0, 0.0), point("b", 0.5, 0.0)], 1.5)
        assert [(p.slot_a_key, p.slot_b_key) for p in near] == [("a", "b")]
        assert moved == []

    def test_the_larger_spacing_of_the_two_sets_the_reach(self) -> None:
        """A 60 cm plant next to a 30 cm one reaches 90 cm."""
        pairs = derive_adjacency([point("a", 0.0, 0.0, spacing_cm=60), point("b", 0.9, 0.0, spacing_cm=30)], 1.5)
        assert [p.distance_cm for p in pairs] == [90.0]

    def test_slots_without_any_spacing_fall_back_to_thirty_centimetres(self) -> None:
        nodes = [
            point("a", 0.0, 0.0, spacing_cm=None),
            point("b", 0.4, 0.0, spacing_cm=None),
            point("c", 0.5, 0.0, spacing_cm=None),
        ]
        assert [(p.slot_a_key, p.slot_b_key) for p in derive_adjacency(nodes, 1.5)] == [("a", "b"), ("b", "c")]

    def test_a_pair_has_one_spelling_whatever_the_input_order(self) -> None:
        forward = derive_adjacency([point("a", 0.0, 0.0), point("b", 0.3, 0.0)], 1.5)
        backward = derive_adjacency([point("b", 0.3, 0.0), point("a", 0.0, 0.0)], 1.5)
        assert forward == backward

    def test_the_result_is_deterministic(self) -> None:
        nodes = [point(f"s{i:02d}", (i % 5) * 0.3, (i // 5) * 0.3) for i in range(25)]
        assert derive_adjacency(nodes, 1.5) == derive_adjacency(list(reversed(nodes)), 1.5)

    def test_a_slot_has_no_pair_with_itself(self) -> None:
        assert derive_adjacency([point("a", 0.0, 0.0)], 1.5) == []


class TestTheEdgeLimit:
    @staticmethod
    def _bed(point_count: int) -> list[AdjacencyNode]:
        positions = [point(f"p{i:04d}", i * 0.3, 0.0) for i in range(point_count)]
        row = AdjacencyNode(
            key="row",
            role=SlotRole.ROW,
            geometry=parse_geometry(
                {"kind": "polyline", "points": [[0, 0.1], [1, 0.1]], "width_m": 0.05}, frame=GeometryFrame.BED
            ),
            spacing_cm=30,
        )
        zone = AdjacencyNode(
            key="zone",
            role=SlotRole.ZONE,
            geometry=parse_geometry(
                {"kind": "polygon", "points": [[0, 0.2], [1, 0.2], [1, 0.6], [0, 0.6]]}, frame=GeometryFrame.BED
            ),
            spacing_cm=30,
        )
        return [*positions, row, zone]

    def test_up_to_the_limit_positions_are_linked(self) -> None:
        pairs = derive_adjacency(self._bed(POINT_SLOT_LIMIT), 1.5)
        assert any(p.slot_a_key.startswith("p") for p in pairs)

    def test_beyond_the_limit_only_zones_and_rows_are_linked(self) -> None:
        pairs = derive_adjacency(self._bed(POINT_SLOT_LIMIT + 1), 1.5)
        assert [(p.slot_a_key, p.slot_b_key) for p in pairs] == [("row", "zone")]


class TestLowerBound:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("30", 30.0),
            ("60--80", 60.0),
            ("45 - 90", 45.0),
            (25, 25.0),
            (None, None),
            ("", None),
            ("0", None),
            (-3, None),
        ],
    )
    def test_the_lower_value_of_a_centimetre_field(self, raw: str | float | None, expected: float | None) -> None:
        assert lower_bound_cm(raw) == expected
