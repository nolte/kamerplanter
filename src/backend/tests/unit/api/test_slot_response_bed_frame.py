"""REQ-053 WP 1.8 — ``SlotResponse`` carries slot geometry in the bed frame, where coordinates are negative.

A circular bed's frame has its origin at the centre, a polygon bed's at its first vertex (§9.2), so a
slot at the left of a round bed sits at a negative ``x``. ``SlotResponse.geometry`` is typed
``BedFrameGeometry`` (-1 000..1 000); with the plan-frame ``Geometry`` the same response would fail
validation at the first such slot — a 500 on ``GET /slots/{key}``.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.v1.slots.schemas import SlotResponse

_BASE = {"key": "s", "slot_id": "BED_P1", "location_key": "loc", "capacity_plants": 1, "currently_occupied": False}


@pytest.mark.parametrize(
    "geometry",
    [
        {"kind": "point", "origin": [-0.45, -0.3]},
        {"kind": "point", "origin": [-1000, 1000]},
        {"kind": "polyline", "points": [[-1.0, -0.5], [1.0, -0.5]], "width_m": 0.1},
        {"kind": "polygon", "points": [[-0.5, -0.5], [0.5, -0.5], [0.0, 0.5]]},
    ],
)
def test_a_negative_bed_frame_coordinate_is_a_valid_response(geometry) -> None:
    response = SlotResponse(**_BASE, last_sanitization=None, geometry=geometry)
    assert response.geometry is not None
    assert response.model_dump(mode="json")["geometry"]["kind"] == geometry["kind"]


def test_the_bed_frame_still_has_an_edge() -> None:
    with pytest.raises(ValidationError):
        SlotResponse(**_BASE, last_sanitization=None, geometry={"kind": "point", "origin": [-1000.001, 0]})
