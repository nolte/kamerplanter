"""REQ-004 — the watering-log cross-field rules and their single source (#970).

``find_watering_log_violations`` is the one statement of the rules; the domain
model and the API request schema both read them from here. These tests pin the
function *and* the fact that the domain model keeps raising: it is the last line
of defence for callers that never pass through the API layer (Celery tasks, MCP
tools, migrations), so making the boundary strict must not soften it.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.v1.watering_logs.schemas import WateringLogCreate
from app.common.enums import ApplicationMethod
from app.domain.models.watering_log import WateringLog, find_watering_log_violations


def _violations(**overrides) -> list:
    kwargs = {
        "is_supplemental": False,
        "application_method": ApplicationMethod.DRENCH,
        "slot_keys": [],
        "plant_keys": ["plant_1"],
    }
    kwargs.update(overrides)
    return find_watering_log_violations(**kwargs)


class TestFindWateringLogViolations:
    def test_valid_values_produce_no_violation(self):
        assert _violations() == []

    def test_slot_only_is_valid(self):
        assert _violations(slot_keys=["slot_a1"], plant_keys=[]) == []

    def test_missing_target_is_reported_on_both_target_fields(self):
        violations = _violations(slot_keys=[], plant_keys=[])

        assert len(violations) == 1
        assert violations[0].code == "watering_target_required"
        assert violations[0].message == "At least one of slot_keys or plant_keys must be provided"
        assert violations[0].fields == ("slot_keys", "plant_keys")

    def test_supplemental_fertigation_is_reported_on_both_fields(self):
        violations = _violations(is_supplemental=True, application_method=ApplicationMethod.FERTIGATION)

        assert len(violations) == 1
        assert violations[0].code == "supplemental_cannot_fertigate"
        assert violations[0].fields == ("is_supplemental", "application_method")

    def test_supplemental_with_another_method_is_valid(self):
        assert _violations(is_supplemental=True, application_method=ApplicationMethod.FOLIAR) == []

    def test_two_broken_rules_are_both_reported(self):
        violations = _violations(
            is_supplemental=True,
            application_method=ApplicationMethod.FERTIGATION,
            slot_keys=[],
            plant_keys=[],
        )

        assert [v.code for v in violations] == ["supplemental_cannot_fertigate", "watering_target_required"]


class TestDomainModelStaysTheLastLineOfDefence:
    """Non-HTTP callers never see the request schema — the model must still refuse."""

    def test_missing_target_still_raises(self):
        with pytest.raises(ValidationError, match="At least one of slot_keys or plant_keys must be provided"):
            WateringLog(volume_liters=1.5)

    def test_supplemental_fertigation_still_raises(self):
        with pytest.raises(ValidationError, match="Supplemental watering cannot use fertigation"):
            WateringLog(
                volume_liters=1.5,
                plant_keys=["plant_1"],
                is_supplemental=True,
                application_method=ApplicationMethod.FERTIGATION,
            )

    def test_a_valid_log_is_accepted(self):
        log = WateringLog(volume_liters=1.5, plant_keys=["plant_1"])

        assert log.application_method is ApplicationMethod.DRENCH


class TestRequestSchemaAndDomainModelAgree:
    """The two ends of the rule must never drift apart.

    They cannot, structurally — both call ``find_watering_log_violations`` — but a
    future refactoring that inlines one of them would be caught here: whatever the
    request schema accepts, the domain model must accept too, and vice versa.
    """

    @pytest.mark.parametrize(
        "payload",
        [
            {"volume_liters": 1.5},
            {"volume_liters": 1.5, "plant_keys": [], "slot_keys": []},
            {
                "volume_liters": 1.5,
                "plant_keys": ["plant_1"],
                "is_supplemental": True,
                "application_method": "fertigation",
            },
        ],
    )
    def test_what_the_domain_rejects_the_request_schema_rejects(self, payload):
        with pytest.raises(ValidationError):
            WateringLog(**payload)
        with pytest.raises(ValidationError):
            WateringLogCreate(**payload)

    @pytest.mark.parametrize(
        "payload",
        [
            {"volume_liters": 1.5, "plant_keys": ["plant_1"]},
            {"volume_liters": 1.5, "slot_keys": ["slot_a1"]},
            {
                "volume_liters": 1.5,
                "slot_keys": ["slot_a1"],
                "is_supplemental": True,
                "application_method": "foliar",
            },
        ],
    )
    def test_what_the_request_schema_accepts_the_domain_accepts(self, payload):
        body = WateringLogCreate(**payload)

        assert WateringLog(**body.model_dump()).volume_liters == 1.5
