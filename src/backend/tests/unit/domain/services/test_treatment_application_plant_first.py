"""A treatment application resolves the plant before it reads that plant's history — #1871 B7.

``IpmService.create_treatment_application`` ran the resistance check first:
``get_recent_applications(plant_key)`` reads a plant's last 90 days of
applications without a tenant filter, and an over-limit active ingredient
answered **422 with the application count** — before the repository's
ownership check (404) ran. A foreign plant key plus a known treatment revealed
that the plant existed and how often an active ingredient had been applied to
it. The plant is now resolved under the application's tenant first.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.ipm import TreatmentApplication
from app.domain.services.ipm_service import IpmService


def _service() -> tuple[IpmService, MagicMock]:
    repo = MagicMock()

    def _verify(plant_key: str, tenant_key: str) -> None:
        if plant_key != "plant_own":
            raise NotFoundError("PlantInstance", plant_key)

    repo.verify_plant_ownership.side_effect = _verify
    repo.get_treatment_by_key.return_value = SimpleNamespace(key="tr1", active_ingredient="spinosad")
    repo.get_treatment_or_raise.return_value = SimpleNamespace(key="tr1", active_ingredient="spinosad")
    repo.get_recent_applications.return_value = [{"active_ingredient": "spinosad"}] * 10
    service = IpmService.__new__(IpmService)
    service._repo = repo  # type: ignore[attr-defined]
    service._resistance = MagicMock()  # type: ignore[attr-defined]
    service._resistance.validate_treatment.return_value = (False, "limit")
    service.get_treatment = lambda key: repo.get_treatment_or_raise(key)  # type: ignore[method-assign]
    return service, repo


def test_a_foreign_plant_answers_404_before_its_history_is_read() -> None:
    service, repo = _service()
    application = TreatmentApplication(treatment_key="tr1", tenant_key="t_a", plant_key="x")

    with pytest.raises(NotFoundError):
        service.create_treatment_application("plant_foreign", application)

    repo.get_recent_applications.assert_not_called()
    repo.create_treatment_application.assert_not_called()
