"""The pot-volume warning runs against the shared vectors (REQ-053 §9.2a, W-016.5, WP 10.11 #2832).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (operation ``container_volume``) is read by this module and by
``features/gardenPlanner/planting/containerCheck.vectors.test.ts``: the planting dialog and the server warn on the
same pots.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.domain.calculators.container_volume_calculator import check_container_volume, recommended_volume_l
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared container-volume vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "container_volume"]


@pytest.mark.parametrize("case", [pytest.param(case, id=case["id"]) for case in CASES])
def test_vector(case: dict[str, Any]) -> None:
    check = check_container_volume(case["input"]["container_volume_l"], case["input"]["recommended_container_volume_l"])
    assert {"volume_below": check.volume_below, "recommended_l": check.recommended_l} == case["expected"]


def test_the_vector_file_carries_the_operation_and_the_boundaries() -> None:
    assert "container_volume" in VECTORS["operations"]
    ids = {case["id"] for case in CASES}
    assert {
        "container-volume-below-range",
        "container-volume-equal-lower-bound",
        "container-volume-no-recommendation",
        "container-volume-zero-recommendation",
    } <= ids


@pytest.mark.parametrize("value", [True, False, float("nan"), float("inf"), -3, "", "   "])
def test_no_usable_recommendation_is_none(value: object) -> None:
    assert recommended_volume_l(value) is None  # type: ignore[arg-type]
