"""Unit tests for the derived ``grown_as_annual`` flag on ``LifecycleResponse``.

The flag is a read-only pydantic ``computed_field`` (WP-3): a species is "grown
as an annual" when it is cultivated as an annual while its botanical cycle is
not (a tender perennial, e.g. tomato). It is never persisted on the domain
model; it is derived from ``cycle_type`` / ``cultivation_cycle_type`` and appears
in the serialised JSON response.
"""

import pytest

from app.api.v1.lifecycle_configs.schemas import LifecycleResponse
from app.common.enums import CycleType


def _response(cycle_type: CycleType, cultivation_cycle_type: CycleType | None) -> LifecycleResponse:
    return LifecycleResponse(
        key="lc-1",
        species_key="species-1",
        cycle_type=cycle_type,
        cultivation_cycle_type=cultivation_cycle_type,
        typical_lifespan_years=None,
        dormancy_required=False,
        vernalization_required=False,
        vernalization_min_days=None,
        photoperiod_type="day_neutral",
        critical_day_length_hours=None,
    )


@pytest.mark.parametrize(
    ("cycle_type", "cultivation_cycle_type", "expected"),
    [
        (CycleType.PERENNIAL, CycleType.ANNUAL, True),
        (CycleType.ANNUAL, CycleType.ANNUAL, False),
        (CycleType.PERENNIAL, None, False),
        (CycleType.BIENNIAL, CycleType.ANNUAL, True),
    ],
)
def test_grown_as_annual_truth_table(
    cycle_type: CycleType,
    cultivation_cycle_type: CycleType | None,
    expected: bool,
) -> None:
    assert _response(cycle_type, cultivation_cycle_type).grown_as_annual is expected


def test_grown_as_annual_serialised_in_json() -> None:
    payload = _response(CycleType.PERENNIAL, CycleType.ANNUAL).model_dump()
    assert payload["grown_as_annual"] is True
