"""REQ-053 WP 7.14 (#2480) - the underlay model refuses what it cannot compute with (non-finite numbers first)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.models.site import SitePlan, SiteUnderlay

_CAL = {"p1_px": [0, 0], "p2_px": [400, 0], "distance_m": 4.0}


def _build(**overrides) -> SiteUnderlay:
    return SiteUnderlay.model_validate({"attachment_key": "att_1", "calibration": _CAL, **overrides})


def test_defaults_are_the_origin_no_rotation_and_half_opacity() -> None:
    underlay = _build()

    assert underlay.origin == (0.0, 0.0) and underlay.rotation_deg == 0.0 and underlay.opacity == 0.5


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize(
    "overrides",
    [
        {"opacity": "BAD"},
        {"rotation_deg": "BAD"},
        {"origin": ["BAD", 0]},
        {"origin": [0, "BAD"]},
        {"calibration": {**_CAL, "distance_m": "BAD"}},
        {"calibration": {**_CAL, "p1_px": ["BAD", 0]}},
        {"calibration": {**_CAL, "p2_px": [400, "BAD"]}},
    ],
)
def test_nan_and_infinity_are_refused_everywhere(overrides, bad) -> None:
    def substitute(value):
        if value == "BAD":
            return bad
        if isinstance(value, list):
            return [substitute(item) for item in value]
        if isinstance(value, dict):
            return {key: substitute(item) for key, item in value.items()}
        return value

    with pytest.raises(ValidationError):
        _build(**substitute(overrides))


@pytest.mark.parametrize(
    "overrides",
    [
        {"calibration": {**_CAL, "p2_px": [0, 0]}},
        {"calibration": {**_CAL, "p2_px": [0.4, 0.4]}},
        {"calibration": {**_CAL, "distance_m": 0}},
        {"calibration": {**_CAL, "distance_m": -1}},
        {"calibration": {**_CAL, "p1_px": [-1, 0]}},
        {"opacity": 0.0},
        {"opacity": 1.5},
        {"rotation_deg": 361},
        {"origin": [5000, 0]},
        {"attachment_key": ""},
    ],
)
def test_out_of_range_values_are_refused(overrides) -> None:
    with pytest.raises(ValidationError):
        _build(**overrides)


def test_rotation_is_stored_within_a_full_turn() -> None:
    assert _build(rotation_deg=-90).rotation_deg == 270.0
    assert _build(rotation_deg=360).rotation_deg == 0.0


def test_a_plan_without_an_underlay_stays_valid() -> None:
    assert SitePlan().underlay is None
