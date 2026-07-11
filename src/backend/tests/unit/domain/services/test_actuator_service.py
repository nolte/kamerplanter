"""REQ-018 ActuatorService unit tests — dispatch, HA degradation, isolation.

Uses lightweight in-memory fakes for the repository, HA client and task
repository so the service's control-flow (HA success, HA failure -> fallback
task + offline, manual actuator -> fallback task, tenant isolation, emergency
stop) is verified without a database.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import ActuatorType, ControlEventSource
from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.actuator import Actuator, ControlEvent, ManualOverride
from app.domain.models.site import Location
from app.domain.models.task import Task
from app.domain.services.actuator_service import ActuatorService


class FakeActuatorRepo:
    def __init__(self):
        self.actuators: dict[str, Actuator] = {}
        self.events: list[ControlEvent] = []
        self.overrides: dict[str, ManualOverride] = {}
        self.location = Location(_key="loc1", tenant_key="t1", name="Zelt 1", area_m2=2.0)

    # location
    def get_location(self, key):
        return self.location if key == "loc1" else None

    # actuator
    def get_or_raise(self, key):
        act = self.actuators.get(key)
        if act is None:
            raise NotFoundError("Actuator", key)
        return act

    def update_actuator(self, key, actuator):
        self.actuators[key] = actuator
        return actuator

    def list_for_tenant(self, tenant_key, *a, **k):
        return [a for a in self.actuators.values() if a.tenant_key == tenant_key]

    def list_for_location(self, location_key, tenant_key):
        return [a for a in self.actuators.values() if a.location_key == location_key]

    # events / overrides
    def create_event(self, event):
        event.key = f"ev{len(self.events)}"
        self.events.append(event)
        return event

    def deactivate_overrides_for_actuator(self, key):
        return 0

    def create_override(self, override):
        override.key = "ov1"
        self.overrides[override.key] = override
        return override

    def get_active_override(self, key):
        return None

    # control-loop helpers
    def list_active_rules(self, key):
        return []

    def list_active_schedules(self, key):
        return []


class FakeHaClient:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls: list[tuple] = []

    async def call_service(self, domain, service, data):
        if self.fail:
            raise ConnectionError("HA not reachable")
        self.calls.append((domain, service, data))
        return {"ok": True}

    def list_sensor_entities(self):
        if self.fail:
            raise ConnectionError("HA not reachable")
        return [{"entity_id": "sensor.vpd", "state": "1.2"}]

    def get_state(self, entity_id):
        return {"value": 1.0} if not self.fail else None


class FakeTaskRepo:
    def __init__(self):
        self.tasks: list[Task] = []

    def create_task(self, task):
        self.tasks.append(task)
        return task


def _ha_actuator(key="act1", state="off"):
    return Actuator(
        _key=key,
        tenant_key="t1",
        location_key="loc1",
        name="Light",
        actuator_type=ActuatorType.LIGHT,
        protocol="home_assistant",
        ha_entity_id="light.zelt",
        current_state=state,
    )


@pytest.fixture
def repo():
    return FakeActuatorRepo()


def _service(repo, ha=None, task_repo=None):
    return ActuatorService(
        repo,
        ha_client_factory=(lambda: ha) if ha is not None else None,
        task_repo=task_repo,
    )


class TestDispatchHomeAssistant:
    def test_ha_success_updates_state_and_logs_event(self, repo):
        repo.actuators["act1"] = _ha_actuator()
        ha = FakeHaClient(fail=False)
        service = _service(repo, ha=ha, task_repo=FakeTaskRepo())
        event = service.send_command("act1", "t1", "turn_on", None, user="u1")
        assert event.success is True
        assert event.event_source == ControlEventSource.MANUAL
        assert repo.actuators["act1"].current_state == "on"
        assert repo.actuators["act1"].is_online is True
        assert ha.calls  # HA service actually called

    def test_ha_failure_creates_fallback_task_and_marks_offline(self, repo):
        repo.actuators["act1"] = _ha_actuator()
        ha = FakeHaClient(fail=True)
        task_repo = FakeTaskRepo()
        service = _service(repo, ha=ha, task_repo=task_repo)
        event = service.send_command("act1", "t1", "turn_on", None, user="u1")
        assert event.success is False
        assert event.event_source == ControlEventSource.FALLBACK_TASK
        assert event.error_message is not None
        assert repo.actuators["act1"].is_online is False
        assert len(task_repo.tasks) == 1
        assert task_repo.tasks[0].priority.value == "high"

    def test_manual_actuator_only_creates_task(self, repo):
        manual = Actuator(
            _key="act2",
            tenant_key="t1",
            location_key="loc1",
            name="Manual fan",
            actuator_type=ActuatorType.CIRCULATION_FAN,
            protocol="manual",
        )
        repo.actuators["act2"] = manual
        task_repo = FakeTaskRepo()
        service = _service(repo, ha=FakeHaClient(), task_repo=task_repo)
        event = service.send_command("act2", "t1", "turn_on", None)
        assert event.event_source == ControlEventSource.FALLBACK_TASK
        assert len(task_repo.tasks) == 1


class TestTenantIsolation:
    def test_cross_tenant_access_returns_not_found(self, repo):
        repo.actuators["act1"] = _ha_actuator()
        service = _service(repo, ha=FakeHaClient())
        with pytest.raises(NotFoundError):
            service.get_actuator("act1", "other-tenant")

    def test_create_on_foreign_location_rejected(self, repo):
        repo.location = Location(_key="loc1", tenant_key="foreign", name="x", area_m2=1.0)
        service = _service(repo, ha=FakeHaClient())
        actuator = _ha_actuator()
        with pytest.raises(NotFoundError):
            service.create_actuator("loc1", "t1", actuator)


class TestOverride:
    def test_set_override_dispatches_immediately(self, repo):
        repo.actuators["act1"] = _ha_actuator(state="off")
        ha = FakeHaClient()
        service = _service(repo, ha=ha, task_repo=FakeTaskRepo())
        override = ManualOverride(
            tenant_key="t1",
            actuator_key="act1",
            started_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            override_value=100,
            created_by="u1",
        )
        created = service.set_override("act1", "t1", override, "u1")
        assert created.key == "ov1"
        assert ha.calls  # immediate dispatch happened


class TestEmergencyStop:
    def test_water_leak_stops_pumps(self, repo):
        repo.actuators["p1"] = Actuator(
            _key="p1",
            tenant_key="t1",
            location_key="loc1",
            name="Pump",
            actuator_type=ActuatorType.PUMP,
            protocol="home_assistant",
            ha_entity_id="switch.pump",
            current_state="on",
        )
        repo.actuators["l1"] = _ha_actuator(key="l1", state="on")
        service = _service(repo, ha=FakeHaClient(), task_repo=FakeTaskRepo())
        result = service.emergency_stop("t1", "water_leak", "u1")
        assert "p1" in result["stopped"]
        assert "l1" not in result["stopped"]  # a light is not affected by water leak

    def test_unknown_scenario_raises(self, repo):
        service = _service(repo, ha=FakeHaClient())
        with pytest.raises(ValidationError):
            service.emergency_stop("t1", "nonsense", "u1")


class TestControlLoopEvaluation:
    def test_ha_status_degrades_gracefully(self, repo):
        service = _service(repo, ha=FakeHaClient(fail=True))
        status = service.ha_status()
        assert status["configured"] is True
        assert status["reachable"] is False

    def test_ha_status_not_configured(self, repo):
        service = _service(repo, ha=None)
        status = service.ha_status()
        assert status["configured"] is False
