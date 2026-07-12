"""REQ-047 §3.2 — the SeasonState transition owns the winter/spring reminders.

Verifies C2: ``CareReminderService.ensure_seasonal_winter_tasks`` creates the
winter_protection / tuber_dig tasks on ``pre_winter`` and spring_uncover on
``pre_spring`` — driven by the season phase, not the calendar month — and is
idempotent (no duplicate task when an equivalent one is already pending).
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.common.enums import (
    CareStyleType,
    FrostTolerance,
    HardinessRating,
    SeasonPhase,
    SpringAction,
    TaskCategory,
    TaskStatus,
    WinterAction,
)
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService


def _plant() -> PlantInstance:
    return PlantInstance(
        _key="plant-1",
        tenant_key="tenant-1",
        instance_id="i1",
        species_key="species-1",
        plant_name="Dahlia",
        planted_on=date(2024, 1, 1),
        site_key="site-1",
    )


def _care() -> CareProfile:
    return CareProfile(care_style=CareStyleType.FROST_TENDER_TUBER, plant_key="plant-1")


def _owp(**overrides) -> OverwinteringProfile:
    data = {
        "plant_key": "plant-1",
        "hardiness_rating": HardinessRating.NEEDS_PROTECTION,
        "winter_action": WinterAction.MULCH,
        "winter_action_month": 10,
        "spring_action": SpringAction.UNCOVER,
        "spring_action_month": 3,
    }
    data.update(overrides)
    return OverwinteringProfile(**data)


def _fake_open_care_lookup(existing: list[Task]):
    """Fake for the tenant-aware ``find_open_care_task`` helper (#509).

    Mirrors the repository predicate in-memory: a task matches only when its
    ``entity_key``, ``tenant_key``, category and reminder-type name suffix line
    up and it is still open — so the wiring test exercises the real dedup key,
    including the tenant scope.
    """

    def _lookup(entity_key, reminder_type, tenant_key, *, include_completed_today=True):  # noqa: ANN001, ANN202
        suffix = f"— {reminder_type.value}"
        for task in existing:
            if (
                (task.entity_key or "") == entity_key
                and task.tenant_key == tenant_key
                and task.category == TaskCategory.CARE_REMINDER.value
                and (task.name or "").endswith(suffix)
                and task.status in (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value)
            ):
                return task
        return None

    return _lookup


def _build_service(*, owp: OverwinteringProfile | None, existing_tasks: list[Task] | None = None):
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.return_value = _care()

    task_repo = MagicMock()
    task_repo.find_open_care_task.side_effect = _fake_open_care_lookup(existing_tasks or [])
    task_repo.create_task.side_effect = lambda t: t

    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = _plant()

    overwintering_repo = MagicMock()
    overwintering_repo.get_profile_by_plant_key.return_value = owp

    species = Species(scientific_name="Dahlia pinnata", frost_sensitivity=FrostTolerance.SENSITIVE)
    species_repo = MagicMock(
        get_by_key=MagicMock(return_value=species),
        get_cultivar_by_key=MagicMock(return_value=None),
    )

    service = CareReminderService(
        care_repo,
        CareReminderEngine(),
        task_repo=task_repo,
        plant_repo=plant_repo,
        species_repo=species_repo,
        overwintering_repo=overwintering_repo,
    )
    return service, task_repo


class TestEnsureSeasonalWinterTasks:
    def test_pre_winter_creates_winter_protection_regardless_of_month(self) -> None:
        service, task_repo = _build_service(owp=_owp())

        created = service.ensure_seasonal_winter_tasks("plant-1", SeasonPhase.PRE_WINTER)

        assert task_repo.create_task.called
        names = [t.name for t in created]
        assert any(n.endswith("— winter_protection") for n in names)
        # No calendar month was consulted — the phase alone drove creation.

    def test_pre_winter_creates_tuber_dig_for_dig_and_store(self) -> None:
        service, _ = _build_service(
            owp=_owp(hardiness_rating=HardinessRating.DIG_AND_STORE, winter_action=WinterAction.DIG_STORE)
        )

        created = service.ensure_seasonal_winter_tasks("plant-1", SeasonPhase.PRE_WINTER)

        names = [t.name for t in created]
        assert any(n.endswith("— winter_protection") for n in names)
        assert any(n.endswith("— tuber_dig") for n in names)

    def test_pre_spring_creates_spring_uncover(self) -> None:
        service, _ = _build_service(owp=_owp())

        created = service.ensure_seasonal_winter_tasks("plant-1", SeasonPhase.PRE_SPRING)

        names = [t.name for t in created]
        assert any(n.endswith("— spring_uncover") for n in names)

    def test_hardy_plant_without_profile_gets_no_task(self) -> None:
        service, task_repo = _build_service(owp=None)

        created = service.ensure_seasonal_winter_tasks("plant-1", SeasonPhase.PRE_WINTER)

        assert created == []
        task_repo.create_task.assert_not_called()

    def test_idempotent_when_pending_task_exists(self) -> None:
        """With a SeasonState transition already having produced the task, a second
        run must not create a duplicate (no double firing)."""
        # The repository wraps documents into Pydantic ``Task`` models, so the dedup
        # filter must use attribute access, not ``dict.get`` (regression #456).
        existing = [
            Task(
                name="Dahlia — winter_protection",
                instruction="Protect Dahlia for winter.",
                category=TaskCategory.CARE_REMINDER,
                entity_key="plant-1",
                entity_type="plant_instance",
                tenant_key="tenant-1",
                status=TaskStatus.PENDING,
            )
        ]
        service, task_repo = _build_service(owp=_owp(), existing_tasks=existing)

        created = service.ensure_seasonal_winter_tasks("plant-1", SeasonPhase.PRE_WINTER)

        assert all(not t.name.endswith("— winter_protection") for t in created)
        for call in task_repo.create_task.call_args_list:
            assert not call.args[0].name.endswith("— winter_protection")

    def test_growing_phase_creates_nothing(self) -> None:
        service, task_repo = _build_service(owp=_owp())

        created = service.ensure_seasonal_winter_tasks("plant-1", SeasonPhase.GROWING)

        assert created == []
        task_repo.create_task.assert_not_called()


@pytest.mark.parametrize("phase", [SeasonPhase.PRE_WINTER, SeasonPhase.PRE_SPRING])
def test_removed_plant_gets_no_task(phase: SeasonPhase) -> None:
    service, task_repo = _build_service(owp=_owp())
    service._plant_repo.get_by_key.return_value = PlantInstance(
        _key="plant-1",
        tenant_key="tenant-1",
        instance_id="i1",
        species_key="species-1",
        planted_on=date(2024, 1, 1),
        removed_on=date(2026, 6, 1),
    )

    created = service.ensure_seasonal_winter_tasks("plant-1", phase)

    assert created == []
    task_repo.create_task.assert_not_called()
