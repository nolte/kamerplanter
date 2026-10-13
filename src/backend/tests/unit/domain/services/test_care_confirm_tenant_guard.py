"""SEC-001 / #2107 — the tenant predicate of the request-driven care writes.

Every request-driven write of ``CareReminderService`` takes ``tenant_key``
keyword-only without a default and verifies the plant belongs to it **inside the
service** (``_require_owned_plant``) before any care state is read or written. A
foreign, unknown or tenant-less request fails closed with ``NotFoundError`` (→ 404,
never a 403 that would disclose the key's existence).

Until #2107 ``confirm_reminder`` ran the check only ``if tenant_key`` — an opt-in its
REST route did not opt into — and ``update_profile`` / ``snooze_reminder`` /
``reset_profile`` / ``get_or_create_profile`` had no check at all: only the router's
``require_owned_plant`` dependency stood between a foreign plant key and the write.
"""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import ReminderType
from app.common.exceptions import NotFoundError
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.services.care_reminder_service import CareReminderService

_OWN = "tenant-A"


def _plant(tenant_key: str) -> SimpleNamespace:
    return SimpleNamespace(
        key="plant-1",
        tenant_key=tenant_key,
        plant_name="Monstera",
        instance_id="PI-1",
        slot_key=None,
        current_phase_key=None,
        species_key=None,
        cultivar_key=None,
        removed_on=None,
    )


def _service(plant: SimpleNamespace | None) -> tuple[CareReminderService, MagicMock]:
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.return_value = CareProfile(key="cp-1", plant_key="plant-1")
    care_repo.update_profile.side_effect = lambda _key, profile: profile
    care_repo.create_linked_profile.side_effect = lambda profile, _plant_key: profile
    care_repo.get_confirmations_by_plant.return_value = []
    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = plant
    service = CareReminderService(care_repo, CareReminderEngine(), plant_repo=plant_repo)
    return service, care_repo


#: Each request-driven write, called for ``plant-1`` on behalf of ``tenant``.
_WRITES: dict[str, Callable[[CareReminderService, str], object]] = {
    "confirm_reminder": lambda s, t: s.confirm_reminder("plant-1", ReminderType.PEST_CHECK, tenant_key=t),
    "snooze_reminder": lambda s, t: s.snooze_reminder("plant-1", ReminderType.WATERING, 2, tenant_key=t),
    "update_profile": lambda s, t: s.update_profile("plant-1", {"notes": "x"}, tenant_key=t),
    "reset_profile": lambda s, t: s.reset_profile("plant-1", tenant_key=t),
    "get_or_create_profile": lambda s, t: s.get_or_create_profile("plant-1", may_create=True, tenant_key=t),
}


def _care_writes(care_repo: MagicMock) -> list[str]:
    names = ("create_confirmation", "create_confirmation_edges", "update_profile", "create_linked_profile")
    return [name for name in names if getattr(care_repo, name).called]


@pytest.mark.parametrize("write", sorted(_WRITES))
@pytest.mark.parametrize(
    ("plant", "tenant_key"),
    [
        pytest.param(_plant("tenant-B"), _OWN, id="foreign-plant"),
        pytest.param(None, _OWN, id="unknown-plant"),
        pytest.param(_plant(""), "", id="empty-tenant"),
    ],
)
def test_a_write_for_a_plant_the_tenant_does_not_own_is_refused_before_any_care_state(
    write: str, plant: SimpleNamespace | None, tenant_key: str
) -> None:
    service, care_repo = _service(plant)

    with pytest.raises(NotFoundError):
        _WRITES[write](service, tenant_key)

    care_repo.get_profile_by_plant_key.assert_not_called()  # fail-closed before the first care read
    assert _care_writes(care_repo) == []


@pytest.mark.parametrize("write", sorted(_WRITES))
def test_the_owning_tenant_reaches_the_write(write: str) -> None:
    """The positive twin: the same call for the owning tenant writes care state."""
    service, care_repo = _service(_plant(_OWN))
    if write == "get_or_create_profile":
        care_repo.get_profile_by_plant_key.return_value = None

    _WRITES[write](service, _OWN)

    assert _care_writes(care_repo) != []


def test_a_service_without_a_plant_repository_owns_nothing() -> None:
    """No ``plant_repo`` means nothing can be verified — refused, not skipped (#2107)."""
    care_repo = MagicMock()
    service = CareReminderService(care_repo, CareReminderEngine())

    with pytest.raises(NotFoundError):
        service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=_OWN)
    care_repo.create_confirmation.assert_not_called()
