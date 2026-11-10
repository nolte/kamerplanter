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

from app.common.enums import IrrigationSystem
from app.domain.calculators.container_volume_calculator import (
    POT_FREE_IRRIGATION_SYSTEMS,
    check_container_volume,
    recommended_volume_l,
)
from app.domain.engines.phase_role_map import YOUNG_PHASE_NAMES
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
    given: dict[str, Any] = case["input"]
    check = check_container_volume(
        given["container_volume_l"],
        given["recommended_container_volume_l"],
        phase_code=given.get("phase_code"),
        irrigation_system=given.get("irrigation_system"),
    )
    assert {"volume_below": check.volume_below, "recommended_l": check.recommended_l} == case["expected"]


def test_the_vector_file_carries_the_operation_and_the_boundaries() -> None:
    assert "container_volume" in VECTORS["operations"]
    ids = {case["id"] for case in CASES}
    assert {
        "container-volume-below-range",
        "container-volume-equal-lower-bound",
        "container-volume-no-recommendation",
        "container-volume-zero-recommendation",
        "container-volume-young-phase-seedling",
        "container-volume-young-phase-rooting",
        "container-volume-hydro",
        "container-volume-nft",
        "container-volume-ebb-flow",
    } <= ids


def test_the_young_phases_are_the_establishing_ones() -> None:
    """The frontend keeps the same list (``YOUNG_PHASE_NAMES`` in ``plantingLogic.ts``); this pins the backend's."""
    assert (
        frozenset({"germination", "seedling", "rooting", "establishment", "pup_establishment", "bulbil_establishment"})
        == YOUNG_PHASE_NAMES
    )


def test_the_pot_free_systems_are_hydro_and_nft() -> None:
    assert frozenset({"hydro", "nft"}) == POT_FREE_IRRIGATION_SYSTEMS
    assert {member.value for member in IrrigationSystem} >= POT_FREE_IRRIGATION_SYSTEMS


@pytest.mark.parametrize("value", [True, False, float("nan"), float("inf"), -3, "", "   "])
def test_no_usable_recommendation_is_none(value: object) -> None:
    assert recommended_volume_l(value) is None  # type: ignore[arg-type]
