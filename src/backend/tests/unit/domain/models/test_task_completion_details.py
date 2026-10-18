"""REQ-053 WP 4.3 — what a client may send besides the task fields of a completion (GP-API-031)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.models.task_completion import MAX_BATCH_COMPLETION, TaskCompletionDetails


def test_an_empty_body_is_valid_and_carries_no_care_field():
    # GP-FR-084: a tap on "Erledigt" without input is allowed.
    details = TaskCompletionDetails()

    assert details.carries_care_fields is False
    assert details.performed_at is None


def test_the_instant_alone_is_no_care_field():
    assert TaskCompletionDetails(performed_at=datetime(2026, 10, 1, tzinfo=UTC)).carries_care_fields is False


@pytest.mark.parametrize(
    "field",
    [
        {"plant_keys": ["p1"]},
        {"reason": "dry"},
        {"product_ref": {"kind": "fertilizer", "key": "f"}},
        {"product_label": "nettle tea"},
        {"quantity": 1, "unit": "l"},
        {"material": "compost"},
        {"measurements": [{"parameter": "ph", "value": 6.5, "unit": "pH"}]},
        {"observed_outcome": "ok"},
        {"outcome_rating": "positive"},
    ],
)
def test_every_other_field_makes_it_a_care_body(field):
    assert TaskCompletionDetails(**field).carries_care_fields is True


def test_a_naive_instant_is_read_as_utc():
    details = TaskCompletionDetails(performed_at=datetime(2026, 10, 1, 8, 0))

    assert details.performed_at == datetime(2026, 10, 1, 8, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "forged",
    [
        {"trigger": "system"},
        {"task_key": "t2"},
        {"source_ref": {"collection": "feeding_events", "key": "x"}},
        {"performed_by_user_key": "u_tom"},
        {"created_by": "u_tom"},
        {"tenant_key": "t"},
    ],
)
def test_the_server_owned_fields_are_refused(forged):
    with pytest.raises(ValidationError):
        TaskCompletionDetails(**forged)


@pytest.mark.parametrize(
    "bad",
    [
        {"quantity": 1},  # a quantity needs a unit
        {"unit": "gallon"},
        {"quantity": -1, "unit": "l"},
        {"outcome_rating": "great"},
        {"plant_keys": ["p1", "p1"]},
        {"product_ref": {"kind": "treatment", "key": "x"}},
    ],
)
def test_invalid_values_are_refused(bad):
    with pytest.raises(ValidationError):
        TaskCompletionDetails(**bad)


def test_the_batch_ceiling_is_the_spec_figure():
    assert MAX_BATCH_COMPLETION == 200
