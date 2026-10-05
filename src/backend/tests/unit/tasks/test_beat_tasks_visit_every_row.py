"""Every all-tenant beat task must visit every row, not the first page (#2012).

Nine reads in ``app/tasks`` called ``repo.get_all(offset=0, limit=<N>, all_tenants=True)``
once and iterated the result as if it were the whole collection. Past ``N`` rows the
rest were silently ignored — for ``notification_tasks`` that means a care task beyond
the page never produced a reminder.

Each test drives the **real task function** with a repository double that holds one
row more than the page the task used to ask for, and that pages like the real
``BaseArangoRepository.get_all``: ``_key`` order, ``offset``/``limit`` honoured, the
full ``total`` reported, and the same ``ValueError`` for a tenant-scoped collection
read without ``tenant_key``/``all_tenants``.
"""

import sys
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.enums import TaskCategory, TaskStatus
from app.domain.models.task import Task
from app.domain.models.tenant import Tenant
from tests.support.ha_entity_grants import EverythingGrantedTo


class PagingRepo:
    """A ``get_all`` that behaves like the real one (sorted by ``_key``, paged, total)."""

    def __init__(self, rows, *, tenant_scoped: bool = True, **extra):
        self._rows = sorted(rows, key=_row_key)
        self._tenant_scoped = tenant_scoped
        self.calls: list[tuple[int, int]] = []
        for name, value in extra.items():
            setattr(self, name, value)

    def get_all(self, offset=0, limit=50, tenant_key=None, *, all_tenants=False):
        if self._tenant_scoped and not tenant_key and not all_tenants:
            raise ValueError("tenant-scoped: pass a tenant_key or all_tenants=True")
        if limit < 1 or offset < 0:
            raise ValueError("bad paging window")
        self.calls.append((offset, limit))
        return list(self._rows[offset : offset + limit]), len(self._rows)


def _row_key(row) -> str:
    key = getattr(row, "key", None)
    return f"{key}" if key is not None else str(row)


def _keys(n: int, prefix: str) -> list[str]:
    # zero-padded so lexicographic ``_key`` order equals creation order
    return [f"{prefix}{i:05d}" for i in range(n)]


@pytest.fixture
def deps(monkeypatch):
    """A stand-in ``app.common.dependencies`` carrying every getter the tasks import lazily."""
    module = ModuleType("app.common.dependencies")
    for name in (
        "get_plant_repo",
        "get_species_repo",
        "get_lifecycle_repo",
        "get_phase_sequence_repo",
        "get_phase_service",
        "get_site_repo",
        "get_quarter_climate_service",
        "get_actuator_repo",
        "get_actuator_service",
        "get_sensor_repo",
        "get_ha_client",
        "get_tank_repo",
        "get_task_repo",
        "get_notification_service",
        "get_tenant_repo",
        "get_membership_repo",
    ):
        setattr(module, name, MagicMock(name=name))
    # MT-015 (#2112): every actuator here is t1's and its entity granted to t1 — these
    # tests are about paging; the allowlist has its own tests.
    module.get_ha_entity_grant_service = lambda: SimpleNamespace(snapshot=lambda: EverythingGrantedTo("t1"))  # type: ignore[attr-defined]
    # #2114 — the notification beat asks the stored membership of (user, tenant); these tests are about
    # paging, so everyone is an active member (the membership rule has its own tests).
    module.get_membership_repo.return_value = SimpleNamespace(
        get_by_user_and_tenant=lambda *_args: SimpleNamespace(is_active=True)
    )
    monkeypatch.setitem(sys.modules, "app.common.dependencies", module)
    return module


def _repoint(monkeypatch, task_module, deps, **getters) -> None:
    """Point a getter on the deps stand-in and, when the task imported it at module level, on the task."""
    for name, value in getters.items():
        getattr(deps, name).return_value = value
        if hasattr(task_module, name):
            monkeypatch.setattr(task_module, name, getattr(deps, name))


def _plants(n: int, **extra):
    return [
        SimpleNamespace(
            key=k, removed_on=None, current_phase_key="phase_veg", species_key="sp1", site_key=None, **extra
        )
        for k in _keys(n, "plant")
    ]


class TestPlantTasks:
    def test_dormancy_checks_visit_every_plant(self, monkeypatch, deps):
        import app.tasks.dormancy_checks as module

        plant_repo = PagingRepo(_plants(1001), resolve_phase_name=lambda _key: "vegetative")
        _repoint(
            monkeypatch,
            module,
            deps,
            get_plant_repo=plant_repo,
            get_species_repo=MagicMock(),
            get_lifecycle_repo=MagicMock(),
            get_phase_sequence_repo=MagicMock(),
        )
        trigger = MagicMock()
        trigger.should_trigger_dormancy.return_value = False

        with patch.object(module, "DormancyTrigger", return_value=trigger):
            module.check_dormancy_triggers(5.0, 8.0)

        assert trigger.should_trigger_dormancy.call_count == 1001

    def test_phase_transitions_visit_every_plant(self, monkeypatch, deps):
        import app.tasks.phase_transitions as module

        plant_repo = PagingRepo(_plants(1001))
        phase_service = MagicMock()
        phase_service.get_current_phase.return_value = {"days_in_phase": 1}
        phase_service.get_transition_rules.return_value = []
        _repoint(
            monkeypatch,
            module,
            deps,
            get_plant_repo=plant_repo,
            get_phase_service=phase_service,
            get_lifecycle_repo=MagicMock(),
            get_site_repo=MagicMock(),
        )

        module.check_auto_transitions()

        assert phase_service.get_current_phase.call_count == 1001

    def test_quarter_climate_evaluates_every_plant(self, monkeypatch, deps):
        import app.tasks.season_tasks as module

        monkeypatch.setattr(module.settings, "season_state_eval_enabled", True, raising=False)
        service = MagicMock()
        service.evaluate_plant.return_value = None
        _repoint(
            monkeypatch, module, deps, get_plant_repo=PagingRepo(_plants(1001)), get_quarter_climate_service=service
        )

        result = module.evaluate_quarter_climate()

        assert result["evaluated"] == 1001
        assert service.evaluate_plant.call_count == 1001


def _actuators(n: int):
    return [
        SimpleNamespace(key=k, tenant_key="t1", location_key="loc1", ha_entity_id="switch.x", is_online=True)
        for k in _keys(n, "act")
    ]


class TestActuatorTasks:
    def test_control_rules_evaluate_every_actuator(self, monkeypatch, deps):
        import app.tasks.actuator_tasks as module

        monkeypatch.setattr(module.settings, "actuator_control_loop_enabled", True, raising=False)
        service = MagicMock()
        service.evaluate_actuator.return_value = None
        _repoint(
            monkeypatch,
            module,
            deps,
            get_actuator_repo=PagingRepo(_actuators(5001)),
            get_actuator_service=service,
            get_sensor_repo=MagicMock(),
            get_ha_client=MagicMock(),
        )
        monkeypatch.setattr(module, "_resolve_location_readings", lambda *_a, **_k: {})

        result = module.evaluate_control_rules()

        assert result["evaluated"] == 5001
        assert service.evaluate_actuator.call_count == 5001

    def test_state_sync_polls_every_actuator(self, monkeypatch, deps):
        import app.tasks.actuator_tasks as module

        monkeypatch.setattr(module.settings, "actuator_control_loop_enabled", True, raising=False)
        ha_client = MagicMock()
        ha_client.get_state.return_value = {"state": "on"}
        _repoint(monkeypatch, module, deps, get_actuator_repo=PagingRepo(_actuators(5001)), get_ha_client=ha_client)

        module.sync_actuator_states()

        assert ha_client.get_state.call_count == 5001


class TestTankTasks:
    def test_state_sync_visits_every_tank(self, monkeypatch, deps):
        import app.tasks.tank_maintenance_tasks as module

        sensor_repo = MagicMock()
        sensor_repo.find_by_tank.return_value = []
        tanks = [SimpleNamespace(key=k, name=k) for k in _keys(1001, "tank")]
        _repoint(
            monkeypatch,
            module,
            deps,
            get_tank_repo=PagingRepo(tanks),
            get_sensor_repo=sensor_repo,
            get_ha_client=MagicMock(),
        )

        result = module.sync_tank_states_from_ha()

        assert result["skipped"] == 1001

    def test_alert_check_visits_every_tank(self, monkeypatch, deps):
        import app.tasks.tank_maintenance_tasks as module

        latest_state = MagicMock(return_value=None)
        tanks = [SimpleNamespace(key=k, name=k) for k in _keys(1001, "tank")]
        _repoint(monkeypatch, module, deps, get_tank_repo=PagingRepo(tanks, get_latest_state=latest_state))

        module.check_tank_alerts()

        assert latest_state.call_count == 1001


def _care_tasks(n: int, *, user: str = "user1") -> list[Task]:
    """Open care reminders due today, as the real repository returns them: ``Task`` models."""
    now = datetime.now(UTC)
    due = datetime(now.year, now.month, now.day, 12, 0, tzinfo=UTC)
    return [
        Task(
            _key=k,
            tenant_key=f"tenant{i % 3}",
            name=f"Plant {i} — watering",
            category=TaskCategory.CARE_REMINDER,
            status=TaskStatus.PENDING,
            due_date=due,
            assigned_to_user_key=user,
            entity_type="plant_instance",
            entity_key=f"plant{i}",
        )
        for i, k in enumerate(_keys(n, "task"))
    ]


class TestNotificationTasks:
    def test_due_care_reminder_beyond_the_first_page_is_sent(self, monkeypatch, deps):
        import app.tasks.notification_tasks as module

        service = MagicMock()
        service.send_care_notifications = AsyncMock(return_value={"users_notified": 1, "total_sent": 1})
        _repoint(
            monkeypatch, module, deps, get_task_repo=PagingRepo(_care_tasks(501)), get_notification_service=service
        )

        result = module.dispatch_due_care_notifications()

        sent = [t for call in service.send_care_notifications.await_args_list for t in call.args[1]]
        assert result["tasks_found"] == 501
        assert len(sent) == 501
        assert {t["plant_key"] for t in sent} >= {"plant0", "plant500"}
        assert {t["user_key"] for t in sent} == {"user1"}

    def test_daily_summary_counts_every_open_task(self, monkeypatch, deps):
        import app.tasks.notification_tasks as module

        service = MagicMock()
        service.get_preferences.return_value = SimpleNamespace(daily_summary=SimpleNamespace(enabled=True))
        service.send_notification = AsyncMock()
        _repoint(
            monkeypatch, module, deps, get_task_repo=PagingRepo(_care_tasks(1001)), get_notification_service=service
        )

        module.send_daily_summary()

        # One summary per (user, tenant) since #2114; every open task beyond the first page is in one of them.
        summaries = [call.kwargs for call in service.send_notification.await_args_list]
        assert sum(s["data"]["due_today_count"] for s in summaries) == 1001
        assert len({s["tenant_key"] for s in summaries}) == len(summaries) > 1

    def test_escalation_visits_every_tenant(self, monkeypatch, deps):
        import app.tasks.notification_tasks as module

        tenants = [Tenant(_key=k, name=k, slug=k, owner_user_key="u1") for k in _keys(1001, "tenant")]
        service = MagicMock()
        service._engine.escalate_overdue = AsyncMock(return_value={"escalated": 0})
        _repoint(
            monkeypatch,
            module,
            deps,
            get_tenant_repo=PagingRepo(tenants, tenant_scoped=False),
            get_notification_service=service,
        )

        result = module.escalate_overdue_notifications()

        assert result["tenants_processed"] == 1001


class TestVernalization:
    def test_vernalization_visits_every_plant(self, monkeypatch, deps):
        import app.tasks.vernalization_updates as module

        lifecycle_repo = MagicMock()
        lifecycle_repo.get_lifecycle_by_species.return_value = SimpleNamespace(vernalization_required=False)
        plant_repo = PagingRepo(_plants(1001, chill_days_accumulated=0))
        _repoint(monkeypatch, module, deps, get_plant_repo=plant_repo, get_lifecycle_repo=lifecycle_repo)

        module.update_vernalization_progress(2.0)

        assert lifecycle_repo.get_lifecycle_by_species.call_count == 1001


class TestBeatCalledReads:
    """Same shape one call deeper: the task reaches the single-window read through a service."""

    def test_full_enrichment_sync_visits_every_species(self):
        from app.domain.engines.enrichment_engine import EnrichmentEngine

        species = [SimpleNamespace(key=k, scientific_name=k) for k in _keys(10001, "sp")]
        adapter = MagicMock()
        adapter.enrich_species.return_value = None
        engine = EnrichmentEngine(PagingRepo(species, tenant_scoped=False), MagicMock(), MagicMock())

        result = engine._full_sync(adapter)

        assert result.total_processed == 10001

    def test_care_profile_reader_returns_every_profile(self):
        from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository

        profiles = [SimpleNamespace(key=k) for k in _keys(10001, "profile")]
        repo = ArangoCareReminderRepository.__new__(ArangoCareReminderRepository)
        double = PagingRepo(profiles, tenant_scoped=False)
        with patch.object(ArangoCareReminderRepository, "get_all", double.get_all):
            assert len(repo.get_all_profiles()) == 10001


def test_a_task_due_date_stored_without_an_offset_does_not_abort_the_dispatch(monkeypatch, deps):
    import app.tasks.notification_tasks as module

    now = datetime.now(UTC)
    naive_due = datetime(now.year, now.month, now.day, 12, 0)  # no tzinfo
    task = _care_tasks(1)[0].model_copy(update={"due_date": naive_due})
    service = MagicMock()
    service.send_care_notifications = AsyncMock(return_value={"users_notified": 1, "total_sent": 1})
    _repoint(monkeypatch, module, deps, get_task_repo=PagingRepo([task]), get_notification_service=service)

    result = module.dispatch_due_care_notifications()

    assert result["tasks_found"] == 1
