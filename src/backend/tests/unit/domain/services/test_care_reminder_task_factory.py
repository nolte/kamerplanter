"""Focused tests for the shared care-reminder Task factory (P4, DRY, #511).

Guards the single-source invariant introduced by de-duplicating the copy-pasted
``Task(...)`` builders (previously in ``care_reminder_service._ensure_care_task``,
``care_reminder_service.ensure_next_watering_task`` and the daily Celery producer
``care_tasks.generate_due_care_reminders``) and the two identical per-reminder-type
instruction dicts. Both the service path and the Celery path must now construct
care-reminder tasks through :func:`build_care_reminder_task`, which is the only
consumer of the single instruction source :func:`care_reminder_instruction`, so the
two paths can never drift on task shape or wording.
"""

import sys
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.common.enums import ReminderType, TaskCategory, TaskPriority, TaskStatus
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.services.care_reminder_service import (
    CareReminderService,
    build_care_reminder_task,
    care_reminder_instruction,
)

_FACTORY_PATH = "app.domain.services.care_reminder_service.build_care_reminder_task"
_DUE = datetime(2026, 6, 14, tzinfo=UTC)


def _record_factory():  # noqa: ANN202 — test helper
    """Return a real-factory delegate that also records every task it builds.

    Used as ``patch(..., side_effect=...)`` so the production behaviour is
    unchanged (the genuine factory runs) while the test can assert identity
    between the persisted task and the factory's exact output.
    """

    def _delegate(**kwargs):  # noqa: ANN003, ANN202
        task = build_care_reminder_task(**kwargs)
        _delegate.tasks.append(task)
        return task

    _delegate.tasks = []
    return _delegate


class TestBuildCareReminderTask:
    """The factory itself: single instruction source, stable task shape."""

    def test_default_instruction_matches_single_source_for_every_type(self) -> None:
        """The factory's default instruction is exactly ``care_reminder_instruction``.

        Proves there is a single per-reminder-type instruction source: whatever the
        factory emits for a type is byte-for-byte the shared instruction text.
        """
        for rt in ReminderType:
            task = build_care_reminder_task(
                plant_key="p1",
                plant_label="Monstera",
                tenant_key="t1",
                reminder_type=rt,
                due_date=_DUE,
            )
            assert task.instruction == care_reminder_instruction(rt, "Monstera")

    def test_builds_expected_task_shape(self) -> None:
        task = build_care_reminder_task(
            plant_key="p1",
            plant_label="Monstera",
            tenant_key="t1",
            reminder_type=ReminderType.FERTILIZING,
            due_date=_DUE,
        )
        assert task.name == "Monstera — fertilizing"
        assert task.category == TaskCategory.CARE_REMINDER
        assert task.entity_key == "p1"
        assert task.entity_type == "plant_instance"
        assert task.tenant_key == "t1"
        assert task.due_date == _DUE
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM

    def test_explicit_instruction_and_priority_override(self) -> None:
        task = build_care_reminder_task(
            plant_key="p1",
            plant_label="Monstera",
            tenant_key="t1",
            reminder_type=ReminderType.WATERING,
            due_date=_DUE,
            instruction="Water Monstera (every 7 days).",
            priority=TaskPriority.HIGH,
        )
        assert task.instruction == "Water Monstera (every 7 days)."
        assert task.priority == TaskPriority.HIGH


class TestServicePathUsesFactory:
    """The synchronous service path constructs its tasks via the factory."""

    def _service(self, task_repo: MagicMock, care_repo: MagicMock) -> CareReminderService:
        return CareReminderService(care_repo, CareReminderEngine(), task_repo)

    def test_ensure_next_watering_task_routes_through_factory(self) -> None:
        care_repo = MagicMock()
        care_repo.get_last_confirmation.return_value = CareConfirmation(
            plant_key="plant-1",
            care_profile_key="cp-1",
            reminder_type=ReminderType.WATERING,
            action="confirmed",
            confirmed_at=datetime(2026, 3, 1, tzinfo=UTC),
        )
        task_repo = MagicMock()
        task_repo.find_open_care_task.return_value = None
        task_repo.create_task.side_effect = lambda task: task
        service = self._service(task_repo, care_repo)
        profile = CareProfile(
            watering_interval_days=7,
            plant_key="plant-1",
            auto_create_watering_task=True,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        built = _record_factory()
        with patch(_FACTORY_PATH, side_effect=built) as spy:
            result = service.ensure_next_watering_task(profile)

        spy.assert_called_once()
        assert spy.call_args.kwargs["reminder_type"] == ReminderType.WATERING
        # The watering path passes its interval-specific instruction explicitly.
        assert spy.call_args.kwargs["instruction"].startswith("Water plant-1")
        # The task the service persists is exactly the factory's output.
        assert result is built.tasks[0]

    def test_ensure_care_task_routes_through_factory(self) -> None:
        task_repo = MagicMock()
        task_repo.find_open_care_task.return_value = None
        task_repo.create_task.side_effect = lambda task: task
        service = self._service(task_repo, MagicMock())
        plant = SimpleNamespace(
            key="plant-1",
            plant_name="Monstera",
            instance_id="m1",
            tenant_key="tenant-1",
        )

        with patch(_FACTORY_PATH, wraps=build_care_reminder_task) as spy:
            result = service._ensure_care_task(plant, ReminderType.PEST_CHECK)

        spy.assert_called_once()
        # Byte-for-byte: the produced task equals a direct factory build for the
        # same input (no override -> shared instruction source).
        expected = build_care_reminder_task(
            plant_key="plant-1",
            plant_label="Monstera",
            tenant_key="tenant-1",
            reminder_type=ReminderType.PEST_CHECK,
            due_date=result.due_date,
        )
        assert result == expected


class TestCeleryPathUsesFactory:
    """The daily Celery producer constructs its tasks via the same factory."""

    @pytest.fixture
    def _mock_dependencies(self, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
        mock_deps = ModuleType("app.common.dependencies")
        for getter in (
            "get_care_reminder_service",
            "get_lifecycle_repo",
            "get_nutrient_plan_repo",
            "get_phase_sequence_repo",
            "get_plant_repo",
            "get_planting_run_repo",
            "get_season_state_repo",
            "get_task_repo",
        ):
            setattr(mock_deps, getter, MagicMock())
        monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)
        return mock_deps

    def _wire(self, deps: ModuleType) -> MagicMock:
        care_service = MagicMock()
        care_service._repo.get_all_profiles.return_value = [SimpleNamespace(plant_key="plant_1")]
        care_service._repo.get_last_confirmation.return_value = None
        care_service.ensure_next_watering_task.return_value = None
        care_service.resolve_overwintering_profile.return_value = None
        care_service._resolve_species.return_value = None
        care_service._resolve_cultivar_traits.return_value = None
        deps.get_care_reminder_service.return_value = care_service

        run_repo = MagicMock()
        run_repo.get_plant_keys_with_active_schedule.return_value = set()
        deps.get_planting_run_repo.return_value = run_repo

        plant_repo = MagicMock()
        plant_repo.get_by_key.return_value = SimpleNamespace(
            current_phase_key=None,
            plant_name="Monstera",
            instance_id="m1",
            tenant_key="tenant_1",
            removed_on=None,
            species_key="species_1",
            cultivar_key=None,
            site_key=None,
        )
        deps.get_plant_repo.return_value = plant_repo

        nutrient_plan_repo = MagicMock()
        nutrient_plan_repo.get_plant_plan.return_value = None
        deps.get_nutrient_plan_repo.return_value = nutrient_plan_repo

        deps.get_lifecycle_repo.return_value = MagicMock()
        deps.get_phase_sequence_repo.return_value = None
        return care_service

    def test_daily_producer_routes_through_factory(self, _mock_dependencies: ModuleType) -> None:
        service = self._wire(_mock_dependencies)

        def _should_generate(profile, rt, **kwargs):  # noqa: ANN001, ANN202
            return rt == ReminderType.FERTILIZING

        service._engine.should_generate_reminder.side_effect = _should_generate
        service._engine.calculate_due_date.return_value = "2026-06-14"
        service._engine.calculate_urgency.return_value = "due_today"

        task_repo = MagicMock()
        task_repo.find_open_care_task.return_value = None
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.care_tasks import generate_due_care_reminders

        built = _record_factory()
        with patch(_FACTORY_PATH, side_effect=built) as spy:
            result = generate_due_care_reminders()

        assert result == {"created": 1, "skipped": 0}
        spy.assert_called_once()
        assert spy.call_args.kwargs["reminder_type"] == ReminderType.FERTILIZING
        # due_today keeps MEDIUM priority (overdue would raise it to HIGH).
        assert spy.call_args.kwargs["priority"] == TaskPriority.MEDIUM
        # The task handed to the repository is exactly the factory's output, and its
        # instruction comes from the single shared source.
        created = task_repo.create.call_args.args[0]
        assert created is built.tasks[0]
        assert created.instruction == care_reminder_instruction(ReminderType.FERTILIZING, "Monstera")
