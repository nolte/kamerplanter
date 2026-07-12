"""SEC-001 — CareReminderService.confirm_reminder tenant-ownership guard.

Defense-in-depth (mirrors the #517 shared guard): when a caller passes its
``tenant_key`` (the MCP path always does), the service re-verifies the plant
belongs to that tenant BEFORE mutating any care state. A foreign/missing plant
fails closed with NotFoundError (→ 404) and no care state is written.
"""

from __future__ import annotations

import contextlib
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import ReminderType
from app.common.exceptions import NotFoundError
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.services.care_reminder_service import CareReminderService


def _service(plant):
    care_repo = MagicMock()
    plant_repo = MagicMock()
    plant_repo.get_or_raise.return_value = plant
    service = CareReminderService(care_repo, CareReminderEngine(), plant_repo=plant_repo)
    return service, care_repo, plant_repo


def test_confirm_reminder_rejects_foreign_tenant_plant():
    # Plant belongs to tenant-B; caller is scoped to tenant-A → NotFoundError,
    # and no profile is ever read/written (no cross-tenant care mutation).
    foreign_plant = SimpleNamespace(key="plant-1", tenant_key="tenant-B")
    service, care_repo, plant_repo = _service(foreign_plant)

    with pytest.raises(NotFoundError):
        service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key="tenant-A")

    plant_repo.get_or_raise.assert_called_once_with("plant-1")
    care_repo.get_profile_by_plant_key.assert_not_called()  # fail-closed before any write


def test_confirm_reminder_missing_plant_raises_not_found():
    service, care_repo, plant_repo = _service(None)
    plant_repo.get_or_raise.side_effect = NotFoundError("PlantInstance", "ghost")

    with pytest.raises(NotFoundError):
        service.confirm_reminder("ghost", ReminderType.WATERING, tenant_key="tenant-A")
    care_repo.get_profile_by_plant_key.assert_not_called()


def test_confirm_reminder_skips_guard_without_tenant_key():
    # The REST path (no tenant_key) keeps its existing behaviour: the guard is
    # opt-in, so the ownership pre-check is not run.
    own_plant = SimpleNamespace(key="plant-1", tenant_key="tenant-A")
    service, _care_repo, plant_repo = _service(own_plant)
    service._repo.get_profile_by_plant_key.return_value = None
    service._repo.get_or_create_profile = MagicMock()

    # No tenant_key → the ownership pre-check is skipped entirely. Downstream mock
    # wiring is out of scope here, so any later failure is suppressed.
    with contextlib.suppress(Exception):
        service.confirm_reminder("plant-1", ReminderType.PEST_CHECK)
    plant_repo.get_or_raise.assert_not_called()
