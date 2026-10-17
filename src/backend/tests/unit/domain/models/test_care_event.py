"""REQ-053 §20.10 — the care-event model WP 1.9 writes (bed-status changes) and WP 4.1 extends."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.common.enums import TaskCategory
from app.domain.models.care_event import (
    CARE_EVENT_CATEGORIES,
    CARE_EVENT_TRIGGERS,
    PROTOCOL_ONLY_CATEGORIES,
    CareEvent,
)


def event(**kw) -> CareEvent:
    return CareEvent.model_validate(
        {
            "tenant_key": "t",
            "site_key": "s",
            "location_key": "l",
            "category": "bed_status_change",
            "performed_at": datetime(2026, 10, 17, tzinfo=UTC),
            **kw,
        }
    )


def test_the_category_set_is_the_union_of_task_categories_and_the_protocol_only_values() -> None:
    assert {c.value for c in TaskCategory} | PROTOCOL_ONLY_CATEGORIES == CARE_EVENT_CATEGORIES
    assert {"bed_status_change", "clearing", "feeding", "watering"} <= CARE_EVENT_CATEGORIES


def test_a_task_category_and_a_protocol_category_are_both_valid() -> None:
    assert event(category="feeding").category == "feeding"
    assert event(category="clearing").category == "clearing"


@pytest.mark.parametrize("field", ["category", "trigger"])
def test_an_unknown_value_is_refused(field: str) -> None:
    with pytest.raises(ValidationError):
        event(**{field: "fallow"})


def test_the_trigger_values_of_the_spec_are_all_known() -> None:
    assert {"task", "reminder", "suggestion", "manual", "observation", "backfill", "system"} == CARE_EVENT_TRIGGERS


def test_the_tenant_is_part_of_the_event() -> None:
    """Unlike locations, a care event is listed tenant-wide (§20.13), so ``tenant_key`` is required."""
    with pytest.raises(ValidationError):
        CareEvent.model_validate(
            {"site_key": "s", "location_key": "l", "category": "note", "performed_at": datetime(2026, 1, 1, tzinfo=UTC)}
        )


def test_the_dump_is_what_the_repository_stores() -> None:
    dumped = event(reason="x").model_dump(by_alias=True, exclude_none=True, mode="json")
    assert dumped["category"] == "bed_status_change" and dumped["reason"] == "x"
    assert dumped["performed_at"].startswith("2026-10-17") and "_key" not in dumped
