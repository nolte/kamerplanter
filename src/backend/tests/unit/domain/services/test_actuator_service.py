"""REQ-018 ActuatorService unit tests — dispatch, HA degradation, isolation.

Uses lightweight in-memory fakes for the repository, HA client and task
repository so the service's control-flow (HA success, HA failure -> fallback
task + offline, manual actuator -> fallback task, tenant isolation, emergency
stop) is verified without a database.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import (
    ActionCommand,
    ActuatorType,
    ConditionOperator,
    ControlEventSource,
    RuleType,
    ScheduleType,
)
from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.actuator import (
    Actuator,
    ControlEvent,
    ControlRule,
    ControlSchedule,
    HysteresisConfig,
    ManualOverride,
    PhaseControlProfile,
    RuleAction,
    RuleCondition,
    ScheduleEntry,
)
from app.domain.models.site import Location
from app.domain.models.task import Task
from app.domain.services.actuator_service import ActuatorService


class FakeActuatorRepo:
    def __init__(self):
        self.actuators: dict[str, Actuator] = {}
        self.events: list[ControlEvent] = []
        self.overrides: dict[str, ManualOverride] = {}
        self.schedules: dict[str, ControlSchedule] = {}
        self.rules: dict[str, ControlRule] = {}
        self.profiles: dict[str, PhaseControlProfile] = {}
        self.applied_profiles: list[tuple[str, str]] = []
        self.active_rules: list[ControlRule] = []
        self.active_schedules: list[ControlSchedule] = []
        self.active_override: ManualOverride | None = None
        self.location = Location(_key="loc1", tenant_key="t1", name="Zelt 1", area_m2=2.0)
        self._seq = 0

    def _next(self, prefix):
        self._seq += 1
        return f"{prefix}{self._seq}"

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

    def list_events(self, actuator_key, tenant_key, offset=0, limit=50):
        matches = [e for e in self.events if e.actuator_key == actuator_key]
        return matches[offset : offset + limit]

    def list_events_for_location(self, location_key, tenant_key, offset=0, limit=50):
        matches = [e for e in self.events if e.location_key == location_key]
        return matches[offset : offset + limit]

    def deactivate_overrides_for_actuator(self, key):
        self.active_override = None
        return 0

    def create_override(self, override):
        override.key = "ov1"
        self.overrides[override.key] = override
        return override

    def get_active_override(self, key):
        return self.active_override

    # control-loop helpers
    def list_active_rules(self, key):
        return self.active_rules

    def list_active_schedules(self, key):
        return self.active_schedules

    # schedules
    def create_schedule(self, schedule):
        schedule.key = self._next("sch")
        self.schedules[schedule.key] = schedule
        return schedule

    def list_schedules(self, actuator_key, tenant_key):
        return [s for s in self.schedules.values() if s.actuator_key == actuator_key]

    def get_schedule_or_raise(self, key):
        sch = self.schedules.get(key)
        if sch is None:
            raise NotFoundError("ControlSchedule", key)
        return sch

    def update_schedule(self, key, schedule):
        self.schedules[key] = schedule
        return schedule

    def delete_schedule(self, key):
        self.schedules.pop(key, None)

    # rules
    def create_rule(self, rule):
        rule.key = self._next("rl")
        self.rules[rule.key] = rule
        return rule

    def list_rules(self, actuator_key, tenant_key):
        return [r for r in self.rules.values() if r.actuator_key == actuator_key]

    def list_rules_for_tenant(self, tenant_key, *a, **k):
        return [r for r in self.rules.values() if r.tenant_key == tenant_key]

    def get_rule_or_raise(self, key):
        rule = self.rules.get(key)
        if rule is None:
            raise NotFoundError("ControlRule", key)
        return rule

    def update_rule(self, key, rule):
        self.rules[key] = rule
        return rule

    def delete_rule(self, key):
        self.rules.pop(key, None)

    # profiles
    def create_profile(self, profile):
        profile.key = self._next("pr")
        self.profiles[profile.key] = profile
        return profile

    def list_profiles(self, tenant_key, is_template=None):
        return [p for p in self.profiles.values() if p.tenant_key == tenant_key]

    def get_profile_or_raise(self, key):
        profile = self.profiles.get(key)
        if profile is None:
            raise NotFoundError("PhaseControlProfile", key)
        return profile

    def update_profile(self, key, profile):
        self.profiles[key] = profile
        return profile

    def delete_profile(self, key):
        self.profiles.pop(key, None)

    def apply_profile_to_location(self, key, location_key):
        self.applied_profiles.append((key, location_key))


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

    def test_expired_override_is_rejected(self, repo):
        # SEC (REQ-018): an override whose window lies entirely in the past must
        # not be applied — the model only enforces expires_at > started_at.
        repo.actuators["act1"] = _ha_actuator(state="off")
        ha = FakeHaClient()
        service = _service(repo, ha=ha, task_repo=FakeTaskRepo())
        now = datetime.now(UTC)
        override = ManualOverride(
            tenant_key="t1",
            actuator_key="act1",
            started_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
            override_value=100,
            created_by="u1",
        )
        with pytest.raises(ValidationError):
            service.set_override("act1", "t1", override, "u1")
        assert not ha.calls  # nothing dispatched for an expired override

    def test_override_value_is_clamped_to_max(self, repo):
        # SEC (REQ-018): an override value beyond the actuator's envelope is clamped.
        actuator = _ha_actuator(state="off")
        actuator = actuator.model_copy(update={"min_value": 0.0, "max_value": 100.0})
        repo.actuators["act1"] = actuator
        ha = FakeHaClient()
        service = _service(repo, ha=ha, task_repo=FakeTaskRepo())
        now = datetime.now(UTC)
        override = ManualOverride(
            tenant_key="t1",
            actuator_key="act1",
            started_at=now,
            expires_at=now + timedelta(hours=1),
            override_value=5000,
            created_by="u1",
        )
        service.set_override("act1", "t1", override, "u1")
        assert repo.actuators["act1"].current_value == 100.0
        assert repo.events[-1].value == 100.0


class TestValueClamping:
    """SEC (REQ-018): every dispatched command is clamped to [min_value, max_value]."""

    def _bounded_actuator(self):
        return _ha_actuator(state="off").model_copy(update={"min_value": 0.0, "max_value": 100.0})

    def test_command_above_max_is_clamped(self, repo):
        repo.actuators["act1"] = self._bounded_actuator()
        ha = FakeHaClient()
        service = _service(repo, ha=ha, task_repo=FakeTaskRepo())
        event = service.send_command("act1", "t1", "set_value", 5000.0, user="u1")
        assert event.value == 100.0
        assert repo.actuators["act1"].current_value == 100.0
        # The HA service call also received the clamped value, not 5000.
        assert ha.calls[-1][2].get("brightness_pct") == 100.0

    def test_command_below_min_is_clamped(self, repo):
        actuator = self._bounded_actuator().model_copy(update={"min_value": 20.0})
        repo.actuators["act1"] = actuator
        ha = FakeHaClient()
        service = _service(repo, ha=ha, task_repo=FakeTaskRepo())
        event = service.send_command("act1", "t1", "set_value", -10.0, user="u1")
        assert event.value == 20.0

    def test_command_inside_bounds_passes_through(self, repo):
        repo.actuators["act1"] = self._bounded_actuator()
        ha = FakeHaClient()
        service = _service(repo, ha=ha, task_repo=FakeTaskRepo())
        event = service.send_command("act1", "t1", "set_value", 60.0, user="u1")
        assert event.value == 60.0

    def test_unbounded_actuator_not_clamped(self, repo):
        repo.actuators["act1"] = _ha_actuator(state="off")  # no min/max configured
        ha = FakeHaClient()
        service = _service(repo, ha=ha, task_repo=FakeTaskRepo())
        event = service.send_command("act1", "t1", "set_value", 250.0, user="u1")
        assert event.value == 250.0


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


def _humidifier(state="off"):
    return Actuator(
        _key="act1",
        tenant_key="t1",
        location_key="loc1",
        name="Humidifier",
        actuator_type=ActuatorType.HUMIDIFIER,
        protocol="home_assistant",
        ha_entity_id="humidifier.zelt",
        current_state=state,
    )


def _vpd_rule():
    return ControlRule(
        tenant_key="t1",
        actuator_key="act1",
        name="VPD rule",
        rule_type=RuleType.THRESHOLD,
        sensor_parameter="vpd",
        condition=RuleCondition(operator=ConditionOperator.GT, threshold=1.5),
        action=RuleAction(command=ActionCommand.TURN_ON),
        hysteresis=HysteresisConfig(
            on_threshold=1.5, off_threshold=1.2, min_on_duration_seconds=0, min_off_duration_seconds=0
        ),
    )


def _schedule():
    return ControlSchedule(
        tenant_key="t1",
        actuator_key="act1",
        name="Lights",
        schedule_type=ScheduleType.DAILY,
        entries=[ScheduleEntry(time_on="06:00", time_off="00:00")],
    )


def _profile():
    return PhaseControlProfile(
        tenant_key="t1",
        name="Veg",
        target_photoperiod_hours=18.0,
        target_light_ppfd=600,
        target_temperature_day_c=24.0,
        target_temperature_night_c=20.0,
        target_humidity_day_percent=65,
        target_humidity_night_percent=60,
    )


class TestControlLoop:
    """REQ-018 sensor -> actuator loop: a firing sensor rule dispatches a command."""

    def test_evaluate_dispatches_when_rule_fires(self, repo):
        repo.actuators["act1"] = _humidifier(state="off")
        repo.active_rules = [_vpd_rule()]
        ha = FakeHaClient()
        service = _service(repo, ha=ha, task_repo=FakeTaskRepo())
        event = service.evaluate_actuator(repo.actuators["act1"], {"vpd": 1.7})
        assert event is not None
        assert event.event_source == ControlEventSource.RULE
        assert repo.actuators["act1"].current_state == "on"

    def test_evaluate_no_change_returns_none(self, repo):
        repo.actuators["act1"] = _humidifier(state="off")
        repo.active_rules = [_vpd_rule()]
        service = _service(repo, ha=FakeHaClient(), task_repo=FakeTaskRepo())
        # VPD below the on-threshold and already off -> no state change.
        assert service.evaluate_actuator(repo.actuators["act1"], {"vpd": 1.0}) is None


class TestScheduleCrud:
    def test_create_list_update_toggle_delete(self, repo):
        repo.actuators["act1"] = _humidifier()
        service = _service(repo, ha=FakeHaClient())
        created = service.create_schedule("act1", "t1", _schedule())
        assert created.actuator_key == "act1"
        assert len(service.list_schedules("act1", "t1")) == 1
        updated = service.update_schedule("act1", created.key, "t1", {"name": "Renamed"})
        assert updated.name == "Renamed"
        toggled = service.toggle_schedule("act1", created.key, "t1")
        assert toggled.is_active is False
        service.delete_schedule("act1", created.key, "t1")
        assert service.list_schedules("act1", "t1") == []

    def test_schedule_of_other_actuator_rejected(self, repo):
        repo.actuators["act1"] = _humidifier()
        repo.actuators["act2"] = _humidifier(state="on").model_copy(update={"key": "act2"})
        service = _service(repo, ha=FakeHaClient())
        created = service.create_schedule("act1", "t1", _schedule())
        with pytest.raises(ValidationError):
            service.update_schedule("act2", created.key, "t1", {"name": "x"})


class TestRuleCrud:
    def test_create_list_toggle_delete_and_test_rule(self, repo):
        repo.actuators["act1"] = _humidifier(state="off")
        service = _service(repo, ha=FakeHaClient())
        created = service.create_rule("act1", "t1", _vpd_rule())
        assert len(service.list_rules("act1", "t1")) == 1
        assert len(service.list_rules_for_tenant("t1")) == 1
        toggled = service.toggle_rule("act1", created.key, "t1")
        assert toggled.is_active is False
        dry = service.test_rule(created.key, "t1", {"vpd": 1.7})
        assert dry["would_trigger"] is True
        service.delete_rule("act1", created.key, "t1")
        assert service.list_rules("act1", "t1") == []


class TestProfileCrud:
    def test_create_list_get_update_apply_delete(self, repo):
        repo.actuators["act1"] = _humidifier()
        service = _service(repo, ha=FakeHaClient())
        created = service.create_profile("t1", _profile())
        assert service.get_profile(created.key, "t1").name == "Veg"
        assert len(service.list_profiles("t1")) == 1
        updated = service.update_profile(created.key, "t1", {"name": "Flower"})
        assert updated.name == "Flower"
        result = service.apply_profile(created.key, "t1", "loc1")
        assert result["applied"] is True
        assert repo.applied_profiles == [(created.key, "loc1")]
        service.delete_profile(created.key, "t1")
        assert service.list_profiles("t1") == []


class TestStatsAndEnergy:
    def test_state_stats_and_energy(self, repo):
        actuator = _humidifier(state="on").model_copy(update={"current_value": 100.0, "power_watts": 50.0})
        repo.actuators["act1"] = actuator
        service = _service(repo, ha=FakeHaClient(), task_repo=FakeTaskRepo())
        service.send_command("act1", "t1", "turn_on", None, user="u1")
        state = service.get_state("act1", "t1")
        assert state["current_state"] == "on"
        assert state["has_override"] is False
        stats = service.get_event_stats("act1", "t1")
        assert stats["total_events"] >= 1
        energy = service.get_location_energy("loc1", "t1", hours_per_day=12.0)
        assert energy["total_kwh_per_day"] > 0
        assert energy["actuators"][0]["power_watts"] == 50.0

    def test_clear_override_and_list_events(self, repo):
        repo.actuators["act1"] = _humidifier(state="on")
        service = _service(repo, ha=FakeHaClient(), task_repo=FakeTaskRepo())
        service.send_command("act1", "t1", "turn_off", None, user="u1")
        service.clear_override("act1", "t1")
        assert len(service.list_events("act1", "t1")) == 1
        assert service.list_location_events("loc1", "t1") == service.list_events("act1", "t1")
