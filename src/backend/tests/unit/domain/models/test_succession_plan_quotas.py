"""#2776 SEC-001 — the operational quotas of a succession plan, at and over each bound.

The quotas bound the work one generation does (every batch is a run, an entry, a slot choice and an edge in one
request). They live on the domain model so REST, MCP and the update path refuse the same plan; the engine refuses
on its own as well, for a stored row that predates the quota.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.common.exceptions import PlanError
from app.domain.engines.succession_plan_engine import SuccessionPlanEngine
from app.domain.models.succession_plan import (
    ERROR_SUCCESSION_QUOTA,
    MAX_PLANTS_PER_BATCH,
    MAX_SUCCESSION_BATCHES,
    MAX_SUCCESSION_INTERVAL_DAYS,
    MAX_SUCCESSION_WINDOW_DAYS,
    SuccessionPlan,
)

START = date(2027, 1, 1)


def _plan(**overrides) -> SuccessionPlan:
    fields = {
        "name": "Salat",
        "species_key": "sp",
        "interval_days": 7,
        "start_date": START,
        "end_date": START + timedelta(days=70),
        "plants_per_batch": 6,
        **overrides,
    }
    return SuccessionPlan(**fields)


def _quota_error(exc: PydanticValidationError) -> dict:
    (error,) = exc.errors()
    assert error["type"] == ERROR_SUCCESSION_QUOTA
    return error["ctx"]


def test_the_quotas_are_the_recorded_values():
    """REQ-013 v2.9 names them; a change here is a change of the spec."""
    assert (MAX_SUCCESSION_BATCHES, MAX_SUCCESSION_INTERVAL_DAYS, MAX_SUCCESSION_WINDOW_DAYS, MAX_PLANTS_PER_BATCH) == (
        104,
        365,
        1096,
        10_000,
    )


def test_a_plan_at_the_batch_quota_is_accepted_and_one_over_is_refused():
    at = _plan(interval_days=1, end_date=START + timedelta(days=MAX_SUCCESSION_BATCHES - 1))
    assert SuccessionPlanEngine().compute_total_batches(at.start_date, at.end_date, at.interval_days) == 104

    with pytest.raises(PydanticValidationError) as refused:
        _plan(interval_days=1, end_date=START + timedelta(days=MAX_SUCCESSION_BATCHES))
    assert _quota_error(refused.value) == {"quota": "batches", "limit": 104, "current": 105}


def test_a_window_at_the_quota_is_accepted_and_one_day_longer_is_refused():
    _plan(interval_days=365, end_date=START + timedelta(days=MAX_SUCCESSION_WINDOW_DAYS))

    with pytest.raises(PydanticValidationError) as refused:
        _plan(interval_days=365, end_date=START + timedelta(days=MAX_SUCCESSION_WINDOW_DAYS + 1))
    assert _quota_error(refused.value) == {"quota": "window_days", "limit": 1096, "current": 1097}


def test_a_ten_year_daily_plan_is_refused_without_building_anything():
    """The case of the finding: ~3650 batches. Refused at construction, by the window quota first."""
    with pytest.raises(PydanticValidationError) as refused:
        _plan(interval_days=1, end_date=START + timedelta(days=3650))
    assert _quota_error(refused.value)["quota"] == "window_days"


@pytest.mark.parametrize(
    ("field", "at", "over"),
    [
        ("interval_days", MAX_SUCCESSION_INTERVAL_DAYS, MAX_SUCCESSION_INTERVAL_DAYS + 1),
        ("plants_per_batch", 10_000, 10_001),
    ],
)
def test_the_field_bounds_hold_at_and_over(field: str, at: int, over: int):
    _plan(**{field: at})
    with pytest.raises(PydanticValidationError):
        _plan(**{field: over})


def test_the_engine_never_builds_more_runs_than_the_quota():
    """A stored legacy row is not re-validated on every path; generation still refuses it."""
    legacy = _plan().model_copy(update={"interval_days": 1, "end_date": START + timedelta(days=500)})

    with pytest.raises(PlanError) as refused:
        SuccessionPlanEngine().generate_batch_runs(legacy)

    assert refused.value.error_code == ERROR_SUCCESSION_QUOTA
    assert refused.value.details[0]["limit"] == 104
