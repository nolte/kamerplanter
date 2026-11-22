"""The Python reference of ``site_fit`` runs against the shared vectors (REQ-053 GP-FR-160, §19.6).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` is read by this module and by
``features/gardenPlanner/model/siteFit.vectors.test.ts``; a test that copied the cases inline would
certify nothing. The matrix is also stated explicitly below from the spec, so the reference is not only
compared with a file that was written next to it, and GP-ACC-053's named cases are pinned by id.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.common.enums import SiteFit, SunExposure
from app.domain.calculators.site_fit_calculator import assess, assess_axes, compute
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared site_fit vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "site_fit"]

AXIS_CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "site_fit_axes"]

#: GP-ACC-053 names these; the file must keep them.
GP_ACC_053_CASES = {
    "site-fit-sunnier-two-steps": "poor",
    "site-fit-shadier-two-steps": "poor",
    "site-fit-shadier-one-step-covered": "marginal",
    "site-fit-shadier-one-step-tolerance-unknown": "marginal",
    "site-fit-unknown-bed": "unknown",
    "site-fit-unknown-requirement": "unknown",
}


@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in CASES])
def test_reference_matches_the_shared_vector(case: dict[str, Any]) -> None:
    result = assess(**case["input"])

    assert {"fit": result.fit.value, "reason": result.reason} == case["expected"], case["spec"]
    assert compute(**case["input"]) is result.fit


def test_the_operation_is_documented_and_exercised() -> None:
    assert "site_fit" in VECTORS["operations"]
    assert CASES, "no site_fit vector: the shared file would certify nothing"


def test_gp_acc_053_cases_are_in_the_file() -> None:
    by_id = {case["id"]: case for case in CASES}

    for case_id, fit in GP_ACC_053_CASES.items():
        assert by_id[case_id]["expected"]["fit"] == fit


def test_every_cell_of_the_bed_by_demand_matrix_is_covered_by_a_vector() -> None:
    """One case per (bed class, demand) pair — the vector file may not leave a cell out (GP-FR-160)."""
    covered = {(c["input"]["sun_exposure"], c["input"]["light_requirement"]) for c in CASES}

    for bed in ("full_sun", "partial_shade", "shade", "deep_shade"):
        for demand in ("full_sun", "partial_shade", "shade"):
            assert (bed, demand) in covered, f"no vector for {bed} x {demand}"
    assert ("unknown", "full_sun") in covered
    assert ("full_sun", None) in covered


class TestRules:
    """The spec's rules stated independently of the vector file."""

    def test_enum_input_is_accepted(self) -> None:
        assert compute(SunExposure.SHADE, "full_sun", None) is SiteFit.POOR

    def test_unknown_class_gives_no_hint_whatever_the_species_says(self) -> None:
        assert compute(SunExposure.UNKNOWN, "full_sun", "deep_shade") is SiteFit.UNKNOWN

    def test_light_requirement_is_never_derived_from_shade_tolerance(self) -> None:
        assert compute("full_sun", None, "deep_shade") is SiteFit.UNKNOWN

    def test_a_requirement_outside_the_enum_is_treated_as_missing(self) -> None:
        assert compute("full_sun", "deep_shade", None) is SiteFit.UNKNOWN

    def test_a_value_that_is_not_a_step_is_missing_as_in_the_port(self) -> None:
        """The TypeScript port is tested with inherited property names; the reference answers the same."""
        assert assess("constructor", "full_sun", None).reason == "bed_unknown"
        assert assess("full_sun", "constructor", None).reason == "requirement_unknown"
        assert assess("partial_shade", "full_sun", "__proto__").reason == "tolerance_unknown"

    def test_steps_are_negative_when_the_bed_is_shadier(self) -> None:
        assert assess("shade", "partial_shade", "shade").steps == -1
        assert assess("full_sun", "shade", None).steps == 2


@pytest.mark.parametrize("case", [pytest.param(c, id=c["id"]) for c in AXIS_CASES])
def test_axes_reference_matches_the_shared_vector(case: dict[str, Any]) -> None:
    assert assess_axes(**case["input"]) == case["expected"], case["spec"]


class TestAxes:
    """GP-FR-161: three cells speak, every other cell and every unknown side is off (E-10)."""

    def test_the_operation_is_documented_and_every_axis_cell_is_covered(self) -> None:
        assert "site_fit_axes" in VECTORS["operations"]
        frost = {(c["input"]["frost_risk"], c["input"]["frost_sensitivity"]) for c in AXIS_CASES}
        for bed in ("low", "normal", "high", "unknown"):
            for species in ("sensitive", "moderate", "hardy", "very_hardy", None):
                assert (bed, species) in frost
        wind = {(c["input"]["wind_exposure"], c["input"]["support_required"]) for c in AXIS_CASES}
        for bed in ("sheltered", "normal", "exposed", "unknown"):
            for flag in (True, False, None):
                assert (bed, flag) in wind
        drainage = {(c["input"]["drainage"], c["input"]["waterlogging_tolerance"]) for c in AXIS_CASES}
        for bed in ("poor", "moderate", "good", "unknown"):
            for species in ("sensitive", "moderate", "tolerant", None):
                assert (bed, species) in drainage

    def test_exactly_the_three_confirmed_cells_speak(self) -> None:
        speaking = {c["id"] for c in AXIS_CASES if c["expected"] and len(c["expected"]) == 1}
        assert speaking == {
            "site-fit-axes-frost-high-sensitive",
            "site-fit-axes-wind-exposed-true",
            "site-fit-axes-drainage-poor-sensitive",
        }

    @pytest.mark.parametrize(
        "args",
        [
            ("high", "moderate", None, None, None, None),  # a cell without a source stays off
            ("normal", "sensitive", None, None, None, None),
            (None, None, "exposed", False, None, None),
            (None, None, None, None, "poor", "moderate"),
        ],
    )
    def test_a_mapping_cell_without_a_source_gives_no_hint(self, args) -> None:
        assert assess_axes(*args) == []

    def test_enums_are_accepted_and_a_missing_species_value_is_never_tolerant(self) -> None:
        from app.common.enums import FrostRisk, SoilDrainage, WindExposure

        assert assess_axes(FrostRisk.HIGH, "sensitive", WindExposure.EXPOSED, True, SoilDrainage.POOR, None) == [
            "frost_mismatch",
            "wind_support_needed",
        ]
