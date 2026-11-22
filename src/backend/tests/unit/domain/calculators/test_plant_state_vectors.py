"""The Python reference of the plant state runs against the shared vectors (REQ-053 §19.6, GP-ACC-050).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (operation ``plant_state``) is read by this module
and by ``features/gardenPlanner/model/plantState.vectors.test.ts``; a test that copied the cases inline would
certify nothing. GP-ACC-050 is also stated explicitly below from the spec, so the reference is not only
compared with itself.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from app.domain.calculators.plant_state_calculator import (
    ATTENTION_PRIORITY,
    LIFECYCLES,
    OpenTask,
    PhaseFacts,
    PlantFacts,
    PlantVisualState,
    compute,
)
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared plant state vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
TOLERANCE: float = VECTORS["default_tolerance"]
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "plant_state"]


def _day(value: str | None) -> date | None:
    return None if value is None else date.fromisoformat(value)


def run(raw: dict[str, Any]) -> PlantVisualState:
    plant = raw["plant"]
    phase = raw["phase"]
    return compute(
        PlantFacts(plant["kind"], _day(plant["removed_on"]), plant["termination_type"]),
        None
        if phase is None
        else PhaseFacts(
            phase["key"],
            date.fromisoformat(phase["started_on"]),
            phase["typical_days"],
            phase["allows_harvest"],
            phase["is_terminal"],
        ),
        [OpenTask(task["category"], _day(task["due"])) for task in raw["tasks"]],
        open_findings=raw["open_findings"],
        frost_risk=raw["frost_risk"],
        harvest_batches=raw["harvest_batches"],
        now=datetime.fromisoformat(raw["now"]),
    )


def view(state: PlantVisualState) -> dict[str, Any]:
    progress = state.phase_progress
    return {
        "lifecycle": state.lifecycle,
        "phase_key": state.phase_key,
        "phase_progress": None
        if progress is None
        else {
            "elapsed_d": progress.elapsed_d,
            "typical_d": progress.typical_d,
            "fraction": progress.fraction,
            "next_phase_eta": None if progress.next_phase_eta is None else progress.next_phase_eta.isoformat(),
        },
        "attention": [{"reason": item.reason, "count": item.count} for item in state.attention],
        "harvest_ready": state.harvest_ready,
        "harvest_ready_from": None if state.harvest_ready_from is None else state.harvest_ready_from.isoformat(),
    }


def assert_close(actual: Any, expected: Any, path: str = "") -> None:
    if isinstance(expected, float):
        assert actual is not None and abs(actual - expected) <= TOLERANCE, f"{path}: {actual!r} != {expected!r}"
    elif isinstance(expected, dict):
        assert set(actual) == set(expected), f"{path}: keys {sorted(actual)} != {sorted(expected)}"
        for key, value in expected.items():
            assert_close(actual[key], value, f"{path}.{key}")
    elif isinstance(expected, list):
        assert len(actual) == len(expected), f"{path}: {actual!r} != {expected!r}"
        for index, value in enumerate(expected):
            assert_close(actual[index], value, f"{path}[{index}]")
    else:
        assert actual == expected, f"{path}: {actual!r} != {expected!r}"


class TestPlantStateVectors:
    @pytest.mark.parametrize("case", [pytest.param(case, id=case["id"]) for case in CASES])
    def test_vector(self, case: dict[str, Any]) -> None:
        assert_close(view(run(case["input"])), case["expected"])

    def test_the_vector_file_carries_the_operation(self) -> None:
        assert "plant_state" in VECTORS["operations"]
        assert len(CASES) >= 20

    def test_every_lifecycle_and_every_reason_is_exercised(self) -> None:
        seen_lifecycles = {case["expected"]["lifecycle"] for case in CASES}
        seen_reasons = {item["reason"] for case in CASES for item in case["expected"]["attention"]}
        assert seen_lifecycles == set(LIFECYCLES)
        assert seen_reasons == set(ATTENTION_PRIORITY)


class TestGpAcc050:
    """GP-ACC-050 from the spec text, independent of the vector file."""

    def test_flowering_plant_with_two_overdue_tasks_and_an_open_finding(self) -> None:
        state = compute(
            PlantFacts(),
            PhaseFacts("bluete", date(2026, 5, 1), 60),
            [OpenTask("watering", date(2026, 6, 1)), OpenTask("pruning", date(2026, 6, 2))],
            open_findings=1,
            frost_risk=False,
            harvest_batches=0,
            now=datetime(2026, 6, 10, 8, 0, tzinfo=UTC),
        )
        assert state.lifecycle == "active"
        assert [item.reason for item in state.attention] == ["problem", "overdue"]
