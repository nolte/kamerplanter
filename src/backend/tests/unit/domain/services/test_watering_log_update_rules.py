"""REQ-004 — ``WateringLogService.update_log`` judges a patch against the merge (#970).

The repository writes the document **first** and rebuilds the domain model from it
afterwards, so a patch that breaks a cross-field rule used to be persisted *and*
answered with a 500 — the caller got "we broke" and the log was left in a state
that every later read chokes on. The service now checks the merged state before
writing and raises the application's own 422 error instead.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import ApplicationMethod
from app.common.exceptions import ValidationError
from app.domain.models.watering_log import WateringLog
from app.domain.services.watering_log_service import WateringLogService


def _service(stored: WateringLog) -> tuple[WateringLogService, MagicMock]:
    repo = MagicMock()
    repo.get_or_raise.return_value = stored
    repo.update_fields.side_effect = lambda key, fields: stored.model_copy(update=fields)
    service = WateringLogService(repo, MagicMock(), MagicMock())
    return service, repo


def _stored(**overrides) -> WateringLog:
    values = {
        "_key": "log_1",
        "tenant_key": "tenant_lisa",
        "volume_liters": 1.5,
        "plant_keys": ["plant_1"],
        "application_method": ApplicationMethod.DRENCH,
        "is_supplemental": False,
    }
    values.update(overrides)
    return WateringLog(**values)


class TestUpdateLogMergedStateValidation:
    def test_supplemental_alone_against_a_stored_fertigation_is_rejected(self):
        """The half the request schema cannot see: the other value is in the store."""
        service, repo = _service(_stored(application_method=ApplicationMethod.FERTIGATION))

        with pytest.raises(ValidationError) as exc_info:
            service.update_log("log_1", {"is_supplemental": True})

        assert exc_info.value.status_code == 422
        assert exc_info.value.error_code == "VALIDATION_ERROR"
        repo.update_fields.assert_not_called()

    def test_method_alone_against_a_stored_supplemental_is_rejected(self):
        service, repo = _service(_stored(is_supplemental=True))

        with pytest.raises(ValidationError):
            service.update_log("log_1", {"application_method": ApplicationMethod.FERTIGATION})

        repo.update_fields.assert_not_called()

    def test_both_in_one_patch_is_rejected(self):
        service, repo = _service(_stored())

        with pytest.raises(ValidationError):
            service.update_log(
                "log_1",
                {"application_method": ApplicationMethod.FERTIGATION, "is_supplemental": True},
            )

        repo.update_fields.assert_not_called()

    def test_error_details_name_both_offending_fields(self):
        service, _repo = _service(_stored(application_method=ApplicationMethod.FERTIGATION))

        with pytest.raises(ValidationError) as exc_info:
            service.update_log("log_1", {"is_supplemental": True})

        assert {d["field"] for d in exc_info.value.details} == {"is_supplemental", "application_method"}
        assert {d["code"] for d in exc_info.value.details} == {"supplemental_cannot_fertigate"}

    def test_a_patch_that_resolves_the_conflict_is_accepted(self):
        """Switching the method away from fertigation makes the supplemental flag legal."""
        service, repo = _service(_stored(application_method=ApplicationMethod.FERTIGATION))

        updated = service.update_log(
            "log_1",
            {"application_method": ApplicationMethod.FOLIAR, "is_supplemental": True},
        )

        assert updated.application_method is ApplicationMethod.FOLIAR
        repo.update_fields.assert_called_once()

    def test_an_unrelated_patch_still_goes_through(self):
        service, repo = _service(_stored())

        updated = service.update_log("log_1", {"notes": "Nachgegossen"})

        assert updated.notes == "Nachgegossen"
        assert repo.update_fields.call_args.args[1] == {"notes": "Nachgegossen"}

    def test_an_empty_patch_touches_nothing(self):
        service, repo = _service(_stored())

        updated = service.update_log("log_1", {"unknown_field": "x", "notes": None})

        assert updated.notes is None
        repo.update_fields.assert_not_called()
