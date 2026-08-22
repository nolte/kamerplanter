"""Unit tests for care reminder Celery tasks (REQ-022).

Mocks ``app.common.dependencies`` before the task runs so the ArangoDB import
chain is never triggered. The CareReminderService is doubled with a MagicMock
whose ``_repo`` and ``_engine`` collaborators are configured per test. Tests
assert observable behaviour: the result dict and which service/repo methods
are invoked.
"""

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _mock_dependencies(monkeypatch):
    """Install a mock ``app.common.dependencies`` module."""
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

    yield mock_deps


def _wire(deps, *, profiles, plants_with_schedule=None):
    """Wire up the common collaborator graph and return the service double."""
    care_service = MagicMock()
    care_service._repo.get_all_profiles.return_value = profiles
    care_service._repo.get_last_confirmation.return_value = None
    # Default: never generate a reminder unless a test overrides it.
    care_service._engine.should_generate_reminder.return_value = False
    care_service.ensure_next_watering_task.return_value = None
    deps.get_care_reminder_service.return_value = care_service

    run_repo = MagicMock()
    run_repo.get_plant_keys_with_active_schedule.return_value = plants_with_schedule or set()
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
    deps.get_task_repo.return_value = MagicMock()

    return care_service


class TestGenerateDueCareReminders:
    def test_no_profiles(self, _mock_dependencies):
        _wire(_mock_dependencies, profiles=[])

        from app.tasks.care_tasks import generate_due_care_reminders

        result = generate_due_care_reminders()

        assert result == {"created": 0, "skipped": 0}

    def test_skips_profile_without_plant_key(self, _mock_dependencies):
        service = _wire(_mock_dependencies, profiles=[SimpleNamespace(plant_key=None)])

        from app.tasks.care_tasks import generate_due_care_reminders

        result = generate_due_care_reminders()

        assert result == {"created": 0, "skipped": 0}
        service.ensure_next_watering_task.assert_not_called()

    def test_skips_removed_plant(self, _mock_dependencies):
        """A removed plant's care profile must not spawn any tasks."""
        from datetime import date

        service = _wire(_mock_dependencies, profiles=[SimpleNamespace(plant_key="plant_1")])
        _mock_dependencies.get_plant_repo.return_value.get_by_key.return_value = SimpleNamespace(
            current_phase_key=None,
            plant_name="Monstera",
            instance_id="m1",
            tenant_key="tenant_1",
            removed_on=date(2026, 6, 1),
            site_key=None,
        )

        from app.tasks.care_tasks import generate_due_care_reminders

        result = generate_due_care_reminders()

        assert result == {"created": 0, "skipped": 1}
        service.ensure_next_watering_task.assert_not_called()
        service._engine.should_generate_reminder.assert_not_called()

    def test_skips_when_plant_missing(self, _mock_dependencies):
        """A care profile pointing at a non-existent plant is skipped."""
        service = _wire(_mock_dependencies, profiles=[SimpleNamespace(plant_key="ghost")])
        _mock_dependencies.get_plant_repo.return_value.get_by_key.return_value = None

        from app.tasks.care_tasks import generate_due_care_reminders

        result = generate_due_care_reminders()

        assert result == {"created": 0, "skipped": 1}
        service.ensure_next_watering_task.assert_not_called()

    def test_creates_auto_watering_task_when_no_active_plan(self, _mock_dependencies):
        service = _wire(_mock_dependencies, profiles=[SimpleNamespace(plant_key="plant_1")])
        created_task = SimpleNamespace(due_date="2026-06-15")
        service.ensure_next_watering_task.return_value = created_task

        from app.tasks.care_tasks import generate_due_care_reminders

        result = generate_due_care_reminders()

        assert result == {"created": 1, "skipped": 0}
        # Verify the profile and the phase-interval keyword are forwarded, not
        # just that the method was called — guards against a dropped argument.
        call = service.ensure_next_watering_task.call_args
        assert call.args[0].plant_key == "plant_1"
        assert call.kwargs["phase_watering_interval"] is None
        # The periodic producer closes no task itself, so it keeps the #509 recency
        # rule: no ``just_completed_task`` opt-out here, or it would re-materialize a
        # reminder the user already confirmed earlier today (#761).
        assert "just_completed_task" not in call.kwargs

    def test_producer_keeps_the_completed_today_dedup(self, _mock_dependencies):
        """#768 guard — the nightly producer must NOT suppress the completed-today branch.

        The complete-then-schedule callers pass ``include_completed_today=False``
        because they have just closed a task themselves in the same operation. The
        producer closes nothing, so it must keep the default: a watering task
        completed earlier today still satisfies the reminder. Inheriting the flag
        here would mint a duplicate watering task every night for every plant that
        was watered that day (regression against #509).
        """
        service = _wire(_mock_dependencies, profiles=[SimpleNamespace(plant_key="plant_1")])

        from app.tasks.care_tasks import generate_due_care_reminders

        generate_due_care_reminders()

        call = service.ensure_next_watering_task.call_args
        assert call.kwargs.get("include_completed_today", True) is True
        # ...and it is not smuggled in positionally either.
        assert len(call.args) == 1

    def test_resolves_phase_interval_from_phase_sequence(self, _mock_dependencies):
        service = _wire(_mock_dependencies, profiles=[SimpleNamespace(plant_key="plant_1")])

        # Plant sits in a phase whose PhaseSequence definition carries an interval.
        _mock_dependencies.get_plant_repo.return_value.get_by_key.return_value = SimpleNamespace(
            current_phase_key="phase_veg",
            plant_name="Monstera",
            instance_id="m1",
            tenant_key="tenant_1",
            removed_on=None,
            species_key="species_1",
            cultivar_key=None,
            site_key=None,
        )
        phase_seq_repo = MagicMock()
        phase_seq_repo.get_entry_by_key.return_value = SimpleNamespace(phase_definition_key="def_1")
        phase_seq_repo.get_definition_by_key.return_value = SimpleNamespace(watering_interval_days=5)
        _mock_dependencies.get_phase_sequence_repo.return_value = phase_seq_repo

        from app.tasks.care_tasks import generate_due_care_reminders

        generate_due_care_reminders()

        # The resolved interval is forwarded to the service.
        _, kwargs = service.ensure_next_watering_task.call_args
        assert kwargs["phase_watering_interval"] == 5

    def test_falls_back_to_lifecycle_interval(self, _mock_dependencies):
        service = _wire(_mock_dependencies, profiles=[SimpleNamespace(plant_key="plant_1")])

        _mock_dependencies.get_plant_repo.return_value.get_by_key.return_value = SimpleNamespace(
            current_phase_key="phase_veg",
            plant_name="Monstera",
            instance_id="m1",
            tenant_key="tenant_1",
            removed_on=None,
            species_key="species_1",
            cultivar_key=None,
            site_key=None,
        )
        # No PhaseSequence repo -> fall back to LifecycleConfig.
        _mock_dependencies.get_phase_sequence_repo.return_value = None
        lifecycle_repo = MagicMock()
        lifecycle_repo.get_phase_by_key.return_value = SimpleNamespace(watering_interval_days=9)
        _mock_dependencies.get_lifecycle_repo.return_value = lifecycle_repo

        from app.tasks.care_tasks import generate_due_care_reminders

        generate_due_care_reminders()

        _, kwargs = service.ensure_next_watering_task.call_args
        assert kwargs["phase_watering_interval"] == 9

    def test_skips_auto_watering_when_run_has_schedule(self, _mock_dependencies):
        service = _wire(
            _mock_dependencies,
            profiles=[SimpleNamespace(plant_key="plant_1")],
            plants_with_schedule={"plant_1"},
        )

        from app.tasks.care_tasks import generate_due_care_reminders

        result = generate_due_care_reminders()

        assert result == {"created": 0, "skipped": 0}
        service.ensure_next_watering_task.assert_not_called()

    def test_creates_reminder_task_when_due_today(self, _mock_dependencies):
        from app.common.enums import ReminderType

        service = _wire(_mock_dependencies, profiles=[SimpleNamespace(plant_key="plant_1")])

        # Generate exactly one reminder (FERTILIZING), due today, no existing task.
        def _should_generate(profile, rt, **kwargs):
            return rt == ReminderType.FERTILIZING

        service._engine.should_generate_reminder.side_effect = _should_generate
        service._engine.calculate_due_date.return_value = "2026-06-14"
        service._engine.calculate_urgency.return_value = "due_today"

        task_repo = MagicMock()
        task_repo.find_open_care_task.return_value = None
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.care_tasks import generate_due_care_reminders

        result = generate_due_care_reminders()

        assert result == {"created": 1, "skipped": 0}
        task_repo.create.assert_called_once()
        created = task_repo.create.call_args.args[0]
        assert created.name.endswith("— fertilizing")
        assert created.entity_key == "plant_1"
        assert created.tenant_key == "tenant_1"

    def test_creates_winter_protection_task_and_forwards_context(self, _mock_dependencies):
        """B1 — the daily producer must forward the overwintering context so a
        winter-protection reminder can actually spawn a task."""
        from app.common.enums import ReminderType

        service = _wire(_mock_dependencies, profiles=[SimpleNamespace(plant_key="plant_1")])

        sentinel_owp = object()
        service.resolve_overwintering_profile.return_value = sentinel_owp
        service._resolve_species.return_value = SimpleNamespace(frost_sensitivity="sensitive")
        service._resolve_cultivar_traits.return_value = None

        def _should_generate(profile, rt, **kwargs):
            return rt == ReminderType.WINTER_PROTECTION

        service._engine.should_generate_reminder.side_effect = _should_generate
        service._engine.calculate_due_date.return_value = "2026-10-14"
        service._engine.calculate_urgency.return_value = "due_today"

        task_repo = MagicMock()
        task_repo.find_open_care_task.return_value = None
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.care_tasks import generate_due_care_reminders

        result = generate_due_care_reminders()

        assert result == {"created": 1, "skipped": 0}
        created = task_repo.create.call_args.args[0]
        assert created.name.endswith("— winter_protection")

        # The overwintering context must reach both engine calls (B1).
        gen_kwargs = service._engine.should_generate_reminder.call_args.kwargs
        assert gen_kwargs["overwintering_profile"] is sentinel_owp
        assert gen_kwargs["frost_sensitivity"] == "sensitive"
        due_kwargs = service._engine.calculate_due_date.call_args.kwargs
        assert due_kwargs["overwintering_profile"] is sentinel_owp

    def test_skips_reminder_when_not_urgent(self, _mock_dependencies):
        from app.common.enums import ReminderType

        service = _wire(_mock_dependencies, profiles=[SimpleNamespace(plant_key="plant_1")])

        def _should_generate(profile, rt, **kwargs):
            return rt == ReminderType.FERTILIZING

        service._engine.should_generate_reminder.side_effect = _should_generate
        service._engine.calculate_due_date.return_value = "2026-06-20"
        service._engine.calculate_urgency.return_value = "upcoming"

        task_repo = MagicMock()
        task_repo.find_open_care_task.return_value = None
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.care_tasks import generate_due_care_reminders

        result = generate_due_care_reminders()

        assert result == {"created": 0, "skipped": 0}
        task_repo.create.assert_not_called()

    def test_idempotent_skip_when_pending_task_exists(self, _mock_dependencies):
        from app.common.enums import ReminderType, TaskCategory, TaskStatus
        from app.domain.models.task import Task

        service = _wire(_mock_dependencies, profiles=[SimpleNamespace(plant_key="plant_1")])

        def _should_generate(profile, rt, **kwargs):
            return rt == ReminderType.FERTILIZING

        service._engine.should_generate_reminder.side_effect = _should_generate
        service._engine.calculate_due_date.return_value = "2026-06-14"
        service._engine.calculate_urgency.return_value = "due_today"

        task_repo = MagicMock()
        # The single tenant-aware dedup helper reports the still-open task (#509),
        # so the daily producer must skip re-creating it.
        task_repo.find_open_care_task.return_value = Task(
            name="Monstera — fertilizing",
            instruction="Fertilize Monstera according to care profile.",
            category=TaskCategory.CARE_REMINDER,
            entity_key="plant_1",
            entity_type="plant_instance",
            tenant_key="tenant_1",
            status=TaskStatus.PENDING,
        )
        _mock_dependencies.get_task_repo.return_value = task_repo

        from app.tasks.care_tasks import generate_due_care_reminders

        result = generate_due_care_reminders()

        assert result == {"created": 0, "skipped": 1}
        task_repo.create.assert_not_called()


class TestTenantScope:
    """#1204 — a scoped run writes only in the tenant it was addressed to.

    These tests wire ``get_by_key`` with a per-key ``side_effect`` rather than
    widening ``_wire``: that helper answers every key with one plant, which is
    exactly what a cross-tenant assertion must not do, and twelve callers
    depend on its current shape.

    The predicate under test hangs on the PLANT. ``CareProfile`` has no
    ``tenant_key``, so a test that gave profiles one would be asserting against
    a data shape the product cannot produce.
    """

    @staticmethod
    def _plant(tenant_key):
        return SimpleNamespace(
            current_phase_key=None,
            plant_name="Monstera",
            instance_id="m1",
            tenant_key=tenant_key,
            removed_on=None,
            species_key="species_1",
            cultivar_key=None,
            site_key=None,
        )

    def _wire_two_tenants(self, deps, *, tenant_b="tenant_b"):
        """One profile in ``tenant_a``, one in ``tenant_b``; both want a watering task."""
        care_service = MagicMock()
        care_service._repo.get_all_profiles.return_value = [
            SimpleNamespace(plant_key="plant_a"),
            SimpleNamespace(plant_key="plant_b"),
        ]
        care_service._repo.get_last_confirmation.return_value = None
        care_service._engine.should_generate_reminder.return_value = False
        # Every considered plant yields exactly one watering task, so the
        # created-count equals the number of plants the run actually reached.
        care_service.ensure_next_watering_task.side_effect = lambda profile, **kw: SimpleNamespace(
            due_date="2026-08-22"
        )
        deps.get_care_reminder_service.return_value = care_service

        plants = {"plant_a": self._plant("tenant_a"), "plant_b": self._plant(tenant_b)}
        plant_repo = MagicMock()
        plant_repo.get_by_key.side_effect = plants.get
        deps.get_plant_repo.return_value = plant_repo

        run_repo = MagicMock()
        run_repo.get_plant_keys_with_active_schedule.return_value = set()
        deps.get_planting_run_repo.return_value = run_repo

        nutrient_plan_repo = MagicMock()
        nutrient_plan_repo.get_plant_plan.return_value = None
        deps.get_nutrient_plan_repo.return_value = nutrient_plan_repo

        deps.get_lifecycle_repo.return_value = MagicMock()
        deps.get_phase_sequence_repo.return_value = None
        deps.get_task_repo.return_value = MagicMock()
        return care_service

    def test_a_scoped_run_reaches_only_its_own_tenants_plants(self, _mock_dependencies):
        service = self._wire_two_tenants(_mock_dependencies)

        from app.tasks.care_tasks import generate_due_care_reminders

        generate_due_care_reminders(tenant_key="tenant_a")

        reached = [call.args[0].plant_key for call in service.ensure_next_watering_task.call_args_list]
        assert reached == ["plant_a"]

    def test_the_returned_counts_describe_only_the_callers_tenant(self, _mock_dependencies):
        """The count is the information-leak half of #1204, not just the writes."""
        self._wire_two_tenants(_mock_dependencies)

        from app.tasks.care_tasks import generate_due_care_reminders

        assert generate_due_care_reminders(tenant_key="tenant_a") == {"created": 1, "skipped": 0}

    def test_a_foreign_plant_is_not_counted_as_skipped(self, _mock_dependencies):
        """``skipped`` reports work this tenant declined, not work it never had.

        This does NOT falsify the #1204 defect — it is green against the
        unscoped code too, because that code creates the task instead of
        skipping it. What it discriminates is the obvious wrong repair:
        ``skipped_count += 1; continue`` on the tenant predicate, which would
        put the other tenants' volume straight back into the response the fix
        removes it from. Kept as an implementation guard, and labelled as one
        so nobody reads it as evidence the scope works.
        """
        self._wire_two_tenants(_mock_dependencies)

        from app.tasks.care_tasks import generate_due_care_reminders

        assert generate_due_care_reminders(tenant_key="tenant_a")["skipped"] == 0

    def test_a_tenantless_plant_is_excluded_from_a_scoped_run(self, _mock_dependencies):
        """It belongs to no tenant, therefore not to this one."""
        service = self._wire_two_tenants(_mock_dependencies, tenant_b=None)

        from app.tasks.care_tasks import generate_due_care_reminders

        generate_due_care_reminders(tenant_key="tenant_a")

        reached = [call.args[0].plant_key for call in service.ensure_next_watering_task.call_args_list]
        assert reached == ["plant_a"]

    def test_the_unscoped_sweep_still_covers_every_tenant(self, _mock_dependencies):
        """The Celery beat calls this with no argument and must not narrow."""
        service = self._wire_two_tenants(_mock_dependencies)

        from app.tasks.care_tasks import generate_due_care_reminders

        result = generate_due_care_reminders()

        reached = [call.args[0].plant_key for call in service.ensure_next_watering_task.call_args_list]
        assert reached == ["plant_a", "plant_b"]
        assert result == {"created": 2, "skipped": 0}

    def test_the_sweep_still_covers_a_tenantless_plant(self, _mock_dependencies):
        """Unchanged from before #1204: only a SCOPED run excludes it."""
        service = self._wire_two_tenants(_mock_dependencies, tenant_b=None)

        from app.tasks.care_tasks import generate_due_care_reminders

        generate_due_care_reminders()

        reached = [call.args[0].plant_key for call in service.ensure_next_watering_task.call_args_list]
        assert reached == ["plant_a", "plant_b"]
