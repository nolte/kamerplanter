"""REQ-053 WP 4.3 — a dry dose logged by a task completion has no volume; the wire still carries a number.

``FeedingEvent.volume_applied_liters`` is optional since a bed-task completion can log ``g`` / ``kg`` / ``g_per_m2``
(compost, horn shavings); the clients read the response field as a number (``${r.volume_applied_liters} L``), so the
response maps "no volume" to ``0`` rather than ``null``. The API still refuses a create without a positive volume.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.mapping import to_response
from app.api.v1.feeding_events.schemas import FeedingEventCreate, FeedingEventResponse
from app.domain.models.feeding_event import FeedingEvent


def test_a_dry_dose_is_answered_as_zero_litres():
    event = FeedingEvent(_key="fe1", tenant_key="t", plant_key="", dose_quantity=50, dose_unit="g_per_m2")

    response = to_response(event, FeedingEventResponse)

    assert response.volume_applied_liters == 0.0


def test_a_fertigation_keeps_its_volume():
    event = FeedingEvent(_key="fe1", tenant_key="t", plant_key="p", volume_applied_liters=2.5)

    assert to_response(event, FeedingEventResponse).volume_applied_liters == 2.5


def test_the_create_body_still_demands_a_positive_volume():
    with pytest.raises(ValidationError):
        FeedingEventCreate(plant_key="p")
    with pytest.raises(ValidationError):
        FeedingEventCreate(plant_key="p", volume_applied_liters=0)
