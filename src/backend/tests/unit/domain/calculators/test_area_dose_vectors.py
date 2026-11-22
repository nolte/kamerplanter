"""Area doses of the bed care log run against the shared vectors (REQ-053 GP-FR-123, WP 8.9).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (operations ``area_dose``, ``nitrogen_approximation``,
``unit_identity``) is read by this module and by ``features/gardenPlanner/model/areaDose.vectors.test.ts``.
The review acceptance numbers are pinned by id: 3.6 m² × 80 g/m² = 288 g, 3 L/m² × 3.6 m² = 10.8 L,
80 g/m² × 13 % N = 10.4 g N/m² = 104 kg N/ha, 1 g/m² = 10 kg/ha, 1 L/m² = 1 mm.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.calculators.area_dose_calculator import (
    display_total,
    g_per_m2_to_kg_per_ha,
    l_per_m2_to_mm,
    nitrogen_approximation,
    quantity_total,
    round_half_up,
)
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared area-dose vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
OPERATIONS = ("area_dose", "nitrogen_approximation", "unit_identity")
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] in OPERATIONS]
TOLERANCE: float = VECTORS["default_tolerance"]


def _close(actual: float | None, expected: float | None) -> bool:
    if actual is None or expected is None:
        return actual is expected
    return abs(actual - expected) <= TOLERANCE


def _run(case: dict[str, Any]) -> object:
    data = case["input"]
    if case["operation"] == "area_dose":
        total, unit = quantity_total(data["quantity"], data["unit"], data["area_m2"])
        shown = None if total is None or unit is None else display_total(total, unit)
        return {"quantity_total": total, "quantity_total_unit": unit, "display_total": shown}
    if case["operation"] == "nitrogen_approximation":
        result = nitrogen_approximation(data["rate_g_per_m2"], data["n_percent"])
        return None if result is None else {"g_n_per_m2": result[0], "kg_n_per_ha": result[1]}
    if data["unit"] == "g_per_m2":
        return {"kg_per_ha": g_per_m2_to_kg_per_ha(data["value"])}
    return {"mm": l_per_m2_to_mm(data["value"])}


class TestAreaDoseVectors:
    @pytest.mark.parametrize("case", [pytest.param(case, id=case["id"]) for case in CASES])
    def test_vector(self, case: dict[str, Any]) -> None:
        actual = _run(case)
        expected = case["expected"]
        if expected is None:
            assert actual is None
            return
        assert isinstance(actual, dict)
        assert set(actual) == set(expected)
        for name, value in expected.items():
            if isinstance(value, str) or value is None:
                assert actual[name] == value, name
            else:
                assert _close(actual[name], value), (name, actual[name], value)

    def test_the_vector_file_carries_the_operations_and_the_acceptance_numbers(self) -> None:
        assert set(OPERATIONS) <= set(VECTORS["operations"])
        ids = {case["id"] for case in CASES}
        assert {
            "area-dose-g-bed-3x1.2",
            "area-dose-l-bed-3x1.2",
            "area-dose-no-area",
            "nitrogen-horn-shavings-13",
            "unit-g-per-m2-is-10-kg-per-ha",
            "unit-l-per-m2-is-1-mm",
        } <= ids


_RATES = st.floats(min_value=0.001, max_value=10_000, allow_nan=False, allow_infinity=False)
_AREAS = st.floats(min_value=0.01, max_value=10_000, allow_nan=False, allow_infinity=False)


class TestUnitIdentities:
    """Review U-001 as properties: the identities hold for every rate, not only for the vector values."""

    @given(_RATES)
    def test_one_g_per_m2_is_ten_kg_per_ha(self, rate: float) -> None:
        assert math.isclose(g_per_m2_to_kg_per_ha(rate), rate * 10, rel_tol=1e-12)
        assert math.isclose(g_per_m2_to_kg_per_ha(rate) / g_per_m2_to_kg_per_ha(1.0), rate, rel_tol=1e-12)

    @given(_RATES)
    def test_one_l_per_m2_is_one_mm(self, rate: float) -> None:
        assert l_per_m2_to_mm(rate) == rate

    @given(_RATES, _AREAS)
    def test_the_total_is_rate_times_area_within_its_rounding(self, rate: float, area: float) -> None:
        for unit, total_unit in (("g_per_m2", "g"), ("l_per_m2", "l")):
            total, got_unit = quantity_total(rate, unit, area)
            assert got_unit == total_unit
            assert total is not None
            assert abs(total - rate * area) <= 0.0005 + 1e-9 * rate * area

    @given(_RATES, st.floats(min_value=0.0, max_value=0.0) | st.floats(max_value=-0.001, allow_nan=False))
    def test_no_area_never_yields_a_total(self, rate: float, area: float) -> None:
        assert quantity_total(rate, "g_per_m2", area) == (None, None)

    @given(_RATES, st.floats(min_value=0.1, max_value=100, allow_nan=False))
    def test_kg_n_per_ha_is_ten_times_g_n_per_m2(self, rate: float, n_percent: float) -> None:
        result = nitrogen_approximation(rate, n_percent)
        assert result is not None
        unrounded = rate * n_percent / 100
        assert abs(result[0] - unrounded) <= 0.05 + 1e-9 * unrounded
        assert abs(result[1] - unrounded * 10) <= 0.5 + 1e-9 * unrounded


class TestRounding:
    def test_ties_round_away_from_zero_on_the_exact_binary_value(self) -> None:
        assert round_half_up(1.25, 1) == 1.3  # 1.25 is exact in binary
        assert round_half_up(2.5, 0) == 3.0  # Python's round() would give 2
        assert round_half_up(1.005, 2) == 1.0  # 1.005 is 1.00499... in binary
        assert round_half_up(-0.0001, 1) == 0.0
