"""WP 8.3 (#2646, GP-FR-106) — a care confirmation also logs a care event when the plant stands in a bed.

The service builds the event through the M4 mapper (``trigger = reminder``); the repository writes it in the
confirmation's transaction (measured in ``tests/integration/test_care_confirmation_event.py``). Here the repository is
a recorder that stores the confirmation like the real one and then asks ``event_for`` for the event.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import ReminderType, TaskCategory
from app.common.exceptions import NotFoundError
from app.domain.engines.care_event_backfill_mapper import REMINDER_CATEGORIES
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_event import CARE_EVENT_CATEGORIES, CareEvent
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.site import Location, Site
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService

OWN, OTHER = "tenant-A", "tenant-B"


def _plant(tenant: str = OWN, location_key: str | None = "L1", slot_key: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        key="plant-1",
        tenant_key=tenant,
        plant_name="Basil",
        instance_id="PI-1",
        slot_key=slot_key,
        location_key=location_key,
        current_phase_key=None,
        species_key=None,
        cultivar_key=None,
        removed_on=None,
    )


class _Sites:
    """``SiteAnchorSource`` over one site (tenant ``site_tenant``) with the location ``L1``."""

    def __init__(self, site_tenant: str = OWN) -> None:
        self.site = Site(_key="S1", tenant_key=site_tenant, name="Garden")

    def get_site_by_key(self, key: str) -> Site | None:
        return self.site if key == "S1" else None

    def get_location_by_key(self, key: str) -> Location | None:
        return (
            Location(_key="L1", site_key="S1", name="Bed 1", location_type_key="bed", area_m2=1.0)
            if key == "L1"
            else None
        )

    def get_slot_by_key(self, key: str) -> SimpleNamespace | None:
        return SimpleNamespace(key="s1", location_key="L1") if key == "s1" else None


class _Repo:
    """Stores confirmations like the real repository does and records the events ``event_for`` produces."""

    def __init__(self, *, abort: bool = False) -> None:
        self.confirmations: list[CareConfirmation] = []
        self.events: list[CareEvent] = []
        self.abort = abort

    def __getattr__(self, name: str) -> Any:  # every other repository method is a harmless mock
        mock = MagicMock()
        mock.return_value = None
        return mock

    def get_profile_by_plant_key(self, plant_key: str) -> CareProfile:
        return CareProfile(_key="cp-1", plant_key=plant_key)

    def get_confirmations_by_plant(self, *_args: Any, **_kwargs: Any) -> list[CareConfirmation]:
        return []

    def create_confirmation_logged(
        self,
        confirmation: CareConfirmation,
        *,
        profile_key: str,
        plant_key: str,
        event_for: Callable[[str], CareEvent | None],
    ) -> CareConfirmation:
        key = f"conf-{len(self.confirmations) + 1}"
        event = event_for(key)  # built before anything is stored: a refusal here stores nothing
        if self.abort:
            raise RuntimeError("the transaction aborted")
        stored = CareConfirmation(**{**confirmation.model_dump(), "_key": key})
        self.confirmations.append(stored)
        if event is not None:
            self.events.append(event)
        return stored


def _service(
    plant: SimpleNamespace | None, *, site_tenant: str = OWN, repo: _Repo | None = None, with_sites: bool = True
):  # type: ignore[no-untyped-def]
    repo = repo or _Repo()
    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = plant
    service = CareReminderService(
        repo,  # type: ignore[arg-type]
        CareReminderEngine(),
        plant_repo=plant_repo,
        site_repo=_Sites(site_tenant) if with_sites else None,
    )
    return service, repo


def test_one_confirmation_writes_exactly_one_event_in_the_plants_bed() -> None:
    service, repo = _service(_plant())

    service.confirm_reminder("plant-1", ReminderType.PEST_CHECK, tenant_key=OWN, user_key="u1")

    assert len(repo.confirmations) == 1 and len(repo.events) == 1
    event = repo.events[0]
    assert (event.trigger, event.category) == ("reminder", "monitoring")
    assert (event.tenant_key, event.site_key, event.location_key, event.plant_keys) == (OWN, "S1", "L1", ["plant-1"])
    assert event.source_ref == {"collection": "care_confirmations", "key": "conf-1"}
    assert event.performed_by_user_key == "u1"
    assert event.performed_at == repo.confirmations[0].confirmed_at


def test_a_plant_without_a_bed_gets_no_event_and_no_error() -> None:
    service, repo = _service(_plant(location_key=None))

    service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN)

    assert len(repo.confirmations) == 1  # the confirmation itself is unchanged
    assert repo.events == []
    # counter-case: the same call for a plant that stands in a bed DOES write the event
    service, repo = _service(_plant())
    service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN)
    assert len(repo.events) == 1


def test_a_service_without_a_site_repository_logs_nothing() -> None:
    service, repo = _service(_plant(), with_sites=False)

    service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN)

    assert len(repo.confirmations) == 1 and repo.events == []


def test_the_bed_of_another_tenants_site_is_not_logged_into() -> None:
    """The tenant is the bed's site's: a plant whose location belongs to another tenant's site gets no event."""
    service, repo = _service(_plant(), site_tenant=OTHER)

    service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN)

    assert repo.events == []


def test_a_foreign_tenants_confirmation_is_a_404_and_writes_nothing() -> None:
    service, repo = _service(_plant(tenant=OTHER))

    with pytest.raises(NotFoundError):
        service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN)

    assert repo.confirmations == [] and repo.events == []


def test_an_aborted_write_stores_neither() -> None:
    service, repo = _service(_plant(), repo=_Repo(abort=True))

    with pytest.raises(RuntimeError):
        service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN)

    assert repo.confirmations == [] and repo.events == []


def test_the_volume_the_caller_typed_is_logged_and_none_is_invented() -> None:
    service, repo = _service(_plant())

    service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN, volume_liters=2.5)
    service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN)

    typed, untyped = repo.events
    assert (typed.quantity, typed.unit) == (2.5, "l")
    assert (untyped.quantity, untyped.unit) == (None, None)


def test_a_care_task_completion_logs_the_same_event() -> None:
    """The second write site: completing a ``care_reminder`` task confirms the reminder through the same method."""
    service, repo = _service(_plant())
    task = Task(
        _key="task-1",
        tenant_key=OWN,
        name="Water",
        category=TaskCategory.CARE_REMINDER,
        entity_type="plant_instance",
        entity_key="plant-1",
        status="completed",
    )
    service._resolve_care_task_context = lambda _task, _tenant: (  # type: ignore[method-assign]
        "plant-1",
        CareProfile(_key="cp-1", plant_key="plant-1"),
        ReminderType.WATERING,
    )
    service.complete_care_task_with_log = lambda *a, **k: None  # type: ignore[method-assign]

    service.record_care_task_completion(task, tenant_key=OWN)

    assert len(repo.confirmations) == 1 and len(repo.events) == 1
    assert repo.events[0].trigger == "reminder" and repo.events[0].category == "watering"


def test_every_reminder_type_has_a_category_and_it_is_a_care_event_category() -> None:
    assert {t.value for t in ReminderType} == set(REMINDER_CATEGORIES)
    assert set(REMINDER_CATEGORIES.values()) <= CARE_EVENT_CATEGORIES
    assert not set(REMINDER_CATEGORIES.values()) & {"pest_control", "ipm"}  # a check is not a PflSchG treatment


def test_a_reminder_of_every_type_produces_a_valid_event() -> None:
    for reminder_type in ReminderType:
        service, repo = _service(_plant())
        service.confirm_reminder("plant-1", reminder_type, tenant_key=OWN)
        assert [e.category for e in repo.events] == [REMINDER_CATEGORIES[reminder_type.value]], reminder_type


def test_the_time_of_the_event_is_the_time_of_the_confirmation() -> None:
    service, repo = _service(_plant())
    before = datetime.now(UTC)

    service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN)

    assert before <= repo.events[0].performed_at <= datetime.now(UTC)


def test_a_plant_placed_by_its_slot_only_is_logged_in_the_slots_bed() -> None:
    """The backfill scan walks plant -> slot -> location; the live write walks the same way, so the lines agree."""
    service, repo = _service(_plant(location_key=None, slot_key="s1"))

    service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN)

    assert [e.location_key for e in repo.events] == ["L1"]
    # counter-case: a slot that names no location leaves the plant without a bed
    service, repo = _service(_plant(location_key=None, slot_key="gone"))
    service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN)
    assert repo.events == []


def test_an_event_the_model_refuses_does_not_block_the_confirmation(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from app.domain.services import care_reminder_service as module

    def refuses(*_args: Any, **_kwargs: Any) -> CareEvent:
        raise ValueError("refused")

    monkeypatch.setattr(module, "map_document", refuses)
    service, repo = _service(_plant())

    service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key=OWN)

    assert len(repo.confirmations) == 1 and repo.events == []
