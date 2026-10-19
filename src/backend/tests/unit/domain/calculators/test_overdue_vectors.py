"""The one definition of "overdue" runs against the shared vectors (REQ-053 GP-FR-192, #2461).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (operation ``overdue``) is read by this module and by
``features/gardenPlanner/model/overdue.vectors.test.ts``: due today at 00:00 and at 23:59 is not overdue,
yesterday is. The guard below keeps the bed counters on the same rule (no comparison against the current instant).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from app.domain.calculators.overdue_calculator import is_overdue, start_of_utc_day, utc_day
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared overdue vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "overdue"]


class TestOverdueVectors:
    @pytest.mark.parametrize("case", [pytest.param(case, id=case["id"]) for case in CASES])
    def test_vector(self, case: dict[str, Any]) -> None:
        now = datetime.fromisoformat(case["input"]["now"])
        assert is_overdue(case["input"]["due"], now) is case["expected"]

    def test_the_vector_file_carries_the_operation_and_the_boundaries(self) -> None:
        assert "overdue" in VECTORS["operations"]
        ids = {case["id"] for case in CASES}
        assert {"overdue-due-today-0000", "overdue-due-today-2359", "overdue-due-yesterday-2359"} <= ids

    def test_start_of_day_is_midnight_utc_and_matches_the_rule(self) -> None:
        now = datetime(2026, 10, 19, 15, 30, tzinfo=UTC)
        bound = start_of_utc_day(now)
        assert bound == datetime(2026, 10, 19, tzinfo=UTC)
        assert utc_day("2026-10-18T23:59:59Z") < bound.date()
        assert not (utc_day("2026-10-19T00:00:00Z") < bound.date())


def test_the_bed_counters_do_not_compare_against_the_current_instant() -> None:
    """Class guard: an overdue aggregate in the plan repository binds the UTC-day start, never ``@now``."""
    source = (
        _REPO_ROOT / "src" / "backend" / "app" / "data_access" / "arango" / "garden_plan_repository.py"
    ).read_text(encoding="utf-8")
    assert "DATE_TIMESTAMP(@now)" not in source
    assert source.count("< DATE_TIMESTAMP(@today_start)") >= 2
