"""REQ-053 WP 7.4 (#2470) - the technical coupling of a zone: actuator, Home Assistant flow rate, consumption.

Acceptance (negative tests): a grower without the ``technical`` scope -> 403; a flow entity that is not granted ->
422 ``HA_ENTITY_NOT_GRANTED``; a foreign actuator -> 422 ``reference.not_found``. Beside them: the entity must be a
flow sensor, Home Assistant down means "not bound", a lead with the scope may bind, the entity id is neither logged
nor returned, and the consumption carries the provenance of its rate (GP-FR-114: logged litres plus actuator
runtime x flow rate).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import structlog

from app.common.enums import AdminScope, FlowRateSource, TenantRole
from app.common.exceptions import ForbiddenError, PlanError, PlanValidationError, ValidationError
from app.domain.calculators.irrigation_zone_consumption_calculator import StateChange
from app.domain.interfaces.flow_rate_sensor import FlowReading, FlowSensorUnavailableError
from app.domain.models.irrigation_zone import IrrigationZone, IrrigationZoneInput, IrrigationZonePatch
from app.domain.models.site import Site
from app.domain.services.irrigation_zone_service import (
    ERROR_FLOW_DEVICE_CLASS,
    ERROR_FLOW_SOURCE_MISMATCH,
    ERROR_FLOW_UNVERIFIABLE,
    IrrigationZoneService,
)
from tests.support.care_event_fakes import FakeCareEventRepo
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)
from tests.support.ha_entity_grants import grant_service
from tests.support.irrigation_zone_fakes import FakeZones

ENTITY = "sensor.south_flow"
OTHER_SITE = "site_other"
TECH = (AdminScope.TECHNICAL,)
NOW = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)


class FakeFlowSensor:
    def __init__(self) -> None:
        self.device_classes: dict[str, str | None] = {ENTITY: "volume_flow_rate"}
        self.readings: dict[str, FlowReading | None] = {}
        self.down = False
        self.asked: list[str] = []

    def device_class(self, entity_id: str) -> str | None:
        self.asked.append(entity_id)
        if self.down:
            raise FlowSensorUnavailableError
        return self.device_classes.get(entity_id)

    def read(self, entity_id: str) -> FlowReading | None:
        if self.down:
            raise FlowSensorUnavailableError
        return self.readings.get(entity_id)


class World:
    def __init__(self) -> None:
        sites = FakeSites(
            make_site(),
            Site(_key=OTHER_SITE, tenant_key=TENANT, name="Allotment", type="outdoor"),
            Site(_key="site_foreign", tenant_key=OTHER_TENANT, name="Theirs", type="outdoor"),
        )
        self.plan = FakePlanRepo(sites)
        self.plan.locations["bed"] = make_location("bed", name="Bed")
        self.plan.locations["bed_other_site"] = make_location("bed_other_site").model_copy(
            update={"site_key": OTHER_SITE}
        )
        self.plan.locations["bed_foreign"] = make_location("bed_foreign").model_copy(
            update={"site_key": "site_foreign"}
        )
        self.zones = FakeZones(self.plan)
        self.zones.add(IrrigationZone(_key="z", tenant_key=TENANT, site_key=SITE, name="South", irrigation_type="drip"))
        self.zones.replace_zone_locations("z", ["bed"], tenant_key=TENANT)
        self.zones.actuators = {
            "act_ok": (TENANT, "bed"),
            "act_other_site": (TENANT, "bed_other_site"),
            "act_foreign": (OTHER_TENANT, "bed_foreign"),
        }
        self.sensor = FakeFlowSensor()
        self.gate = grant_service({TENANT: [ENTITY]})
        self.service = IrrigationZoneService(
            self.zones,
            sites,
            _NoObjects(),  # type: ignore[arg-type]
            FakeCareEventRepo(),
            ha_entity_gate=self.gate,
            flow_sensor=self.sensor,
        )

    def patch(self, role=TenantRole.LEAD, scopes=TECH, **fields):
        return self.service.patch_zone(
            "z", tenant_key=TENANT, role=role, patch=IrrigationZonePatch(**fields), admin_scopes=scopes
        )


class _NoObjects:
    def get_garden_object_by_key(self, key, *, tenant_key):  # pragma: no cover - no water source in this module
        return None


@pytest.fixture
def world() -> World:
    return World()


def _code(exc: PlanValidationError | ValidationError) -> str:
    return str((exc.details or [{}])[0].get("code"))


class TestScope:
    @pytest.mark.parametrize(
        "fields",
        [
            {"actuator_key": "act_ok"},
            {"flow_rate_source": FlowRateSource.HA_ENTITY, "flow_rate_ha_entity_id": ENTITY},
        ],
    )
    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.LEAD])
    def test_no_technical_scope_is_403_and_nothing_is_written(self, world, fields, role) -> None:
        with pytest.raises(ForbiddenError):
            world.patch(role=role, scopes=(AdminScope.MANAGEMENT,), **fields)
        assert world.zones.updates == [] and world.sensor.asked == []

    def test_the_scope_is_checked_before_any_reference(self, world) -> None:
        with pytest.raises(ForbiddenError):  # 403 even though the actuator does not exist
            world.patch(scopes=(), actuator_key="act_nowhere")

    def test_a_grower_with_the_scope_may_bind_the_actuator_the_scope_is_independent_of_the_rank(self, world) -> None:
        view = world.patch(role=TenantRole.GROWER, actuator_key="act_ok")

        assert view.zone.actuator_key == "act_ok"
        assert world.zones.updates == [("z", {"actuator_key": "act_ok"})]

    def test_a_viewer_is_still_refused_by_the_role(self, world) -> None:
        with pytest.raises(ForbiddenError):
            world.patch(role=TenantRole.VIEWER, scopes=TECH, actuator_key="act_ok")

    def test_the_manual_flow_rate_needs_no_scope(self, world) -> None:
        view = world.patch(role=TenantRole.GROWER, scopes=(), flow_rate_l_per_min=7.5)

        assert view.zone.flow_rate_l_per_min == 7.5

    def test_an_unchanged_coupling_value_needs_no_scope(self, world) -> None:
        world.patch(actuator_key="act_ok")

        view = world.patch(role=TenantRole.GROWER, scopes=(), actuator_key="act_ok", name="South 2")

        assert view.zone.name == "South 2"

    def test_the_scope_is_needed_on_create_too(self, world) -> None:
        with pytest.raises(ForbiddenError):
            world.service.create_zone(
                SITE, tenant_key=TENANT, role=TenantRole.LEAD, data=IrrigationZoneInput(name="Z", actuator_key="act_ok")
            )
        view = world.service.create_zone(
            SITE,
            tenant_key=TENANT,
            role=TenantRole.LEAD,
            data=IrrigationZoneInput(name="Z", actuator_key="act_ok"),
            admin_scopes=TECH,
        )
        assert view.zone.actuator_key == "act_ok"


class TestActuator:
    @pytest.mark.parametrize("actuator", ["act_foreign", "act_other_site", "act_nowhere"])
    def test_a_foreign_other_site_or_absent_actuator_is_reference_not_found(self, world, actuator) -> None:
        with pytest.raises(PlanValidationError) as refused:
            world.patch(actuator_key=actuator)

        assert [(d["field"], d["code"]) for d in refused.value.details or []] == [
            ("actuator_key", "reference.not_found")
        ]
        assert world.zones.updates == []

    def test_the_actuator_can_be_unbound(self, world) -> None:
        world.patch(actuator_key="act_ok")

        view = world.patch(actuator_key=None)

        assert view.zone.actuator_key is None


class TestFlowEntity:
    def _bind(self, world, **extra):
        return world.patch(flow_rate_source=FlowRateSource.HA_ENTITY, flow_rate_ha_entity_id=ENTITY, **extra)

    def test_a_granted_flow_sensor_is_bound(self, world) -> None:
        view = self._bind(world)

        assert view.zone.flow_rate_ha_entity_id == ENTITY and view.zone.flow_rate_source is FlowRateSource.HA_ENTITY

    def test_an_entity_the_tenant_is_not_granted_is_422_and_home_assistant_is_not_asked(self, world) -> None:
        world.sensor.device_classes["sensor.other_flow"] = "water"

        with pytest.raises(ValidationError) as refused:
            world.patch(flow_rate_source=FlowRateSource.HA_ENTITY, flow_rate_ha_entity_id="sensor.other_flow")

        assert _code(refused.value) == "HA_ENTITY_NOT_GRANTED"
        assert world.sensor.asked == [] and "sensor.other_flow" not in str(refused.value.details)

    @pytest.mark.parametrize("device_class", ["water", "volume_flow_rate"])
    def test_both_flow_device_classes_are_accepted(self, world, device_class) -> None:
        world.sensor.device_classes[ENTITY] = device_class

        assert self._bind(world).zone.flow_rate_ha_entity_id == ENTITY

    @pytest.mark.parametrize("device_class", ["temperature", "power", "", None])
    def test_another_device_class_is_422(self, world, device_class) -> None:
        world.sensor.device_classes[ENTITY] = device_class

        with pytest.raises(PlanError) as refused:
            self._bind(world)

        assert (refused.value.error_code, refused.value.status_code) == (ERROR_FLOW_DEVICE_CLASS, 422)
        assert world.zones.updates == []

    def test_when_home_assistant_cannot_be_asked_the_entity_is_not_bound(self, world) -> None:
        world.sensor.down = True

        with pytest.raises(PlanError) as refused:
            self._bind(world)

        assert refused.value.error_code == ERROR_FLOW_UNVERIFIABLE and world.zones.updates == []

    def test_a_source_and_an_entity_belong_together(self, world) -> None:
        with pytest.raises(PlanError) as only_source:
            world.patch(flow_rate_source=FlowRateSource.HA_ENTITY)
        with pytest.raises(PlanError) as only_entity:
            world.patch(flow_rate_ha_entity_id=ENTITY)
        assert {only_source.value.error_code, only_entity.value.error_code} == {ERROR_FLOW_SOURCE_MISMATCH}

    def test_clearing_the_entity_puts_the_source_back_to_manual(self, world) -> None:
        self._bind(world)

        view = world.patch(flow_rate_ha_entity_id=None)

        assert view.zone.flow_rate_ha_entity_id is None and view.zone.flow_rate_source is FlowRateSource.MANUAL

    def test_a_malformed_entity_id_is_refused_by_the_shape(self) -> None:
        for bad in ("light.kitchen", "sensor.", "sensor.UPPER", "sensor.a b", "sensor." + "x" * 65):
            with pytest.raises(ValueError, match=r"."):
                IrrigationZonePatch(flow_rate_ha_entity_id=bad)

    def test_the_entity_id_is_never_logged(self, world) -> None:
        with structlog.testing.capture_logs() as logs:
            self._bind(world)
            world.service.zone_status("z", tenant_key=TENANT, now=NOW)

        assert ENTITY not in repr(logs)


class TestConsumption:
    def _run(self, world, *, minutes: int) -> None:
        start = NOW - timedelta(days=2)
        world.zones.switches["act_ok"] = [
            StateChange(start, "on"),
            StateChange(start + timedelta(minutes=minutes), "off"),
        ]

    def test_the_manual_rate_gives_actuator_litres_with_that_provenance(self, world) -> None:
        world.patch(actuator_key="act_ok", flow_rate_l_per_min=6.0)
        self._run(world, minutes=20)

        status = world.service.zone_status("z", tenant_key=TENANT, now=NOW)

        assert [(p.source, p.liters) for p in status.consumption] == [("actuator_runtime_manual_rate", 120.0)]
        assert status.consumption_liters_30d == 120.0

    def test_a_fresh_home_assistant_reading_overrides_the_manual_rate(self, world) -> None:
        world.patch(actuator_key="act_ok", flow_rate_l_per_min=6.0)
        world.patch(flow_rate_source=FlowRateSource.HA_ENTITY, flow_rate_ha_entity_id=ENTITY)
        world.sensor.readings[ENTITY] = FlowReading(10.0, NOW - timedelta(hours=2))
        self._run(world, minutes=20)

        status = world.service.zone_status("z", tenant_key=TENANT, now=NOW)

        assert [(p.source, p.liters) for p in status.consumption] == [("actuator_runtime_ha_rate", 200.0)]

    @pytest.mark.parametrize("reading", [None, FlowReading(10.0, NOW - timedelta(hours=25))])
    def test_a_stale_or_missing_reading_falls_back_to_the_manual_rate(self, world, reading) -> None:
        world.patch(actuator_key="act_ok", flow_rate_l_per_min=6.0)
        world.patch(flow_rate_source=FlowRateSource.HA_ENTITY, flow_rate_ha_entity_id=ENTITY)
        world.sensor.readings[ENTITY] = reading
        self._run(world, minutes=20)

        parts = world.service.zone_status("z", tenant_key=TENANT, now=NOW).consumption

        assert [(p.source, p.liters) for p in parts] == [("actuator_runtime_manual_rate", 120.0)]

    def test_home_assistant_being_down_degrades_to_the_manual_rate(self, world) -> None:
        world.patch(actuator_key="act_ok", flow_rate_l_per_min=6.0)
        world.patch(flow_rate_source=FlowRateSource.HA_ENTITY, flow_rate_ha_entity_id=ENTITY)
        world.sensor.down = True
        self._run(world, minutes=20)

        parts = world.service.zone_status("z", tenant_key=TENANT, now=NOW).consumption

        assert [p.source for p in parts] == ["actuator_runtime_manual_rate"]

    def test_a_withdrawn_grant_means_the_entity_is_not_read(self, world) -> None:
        world.patch(actuator_key="act_ok")
        world.patch(flow_rate_source=FlowRateSource.HA_ENTITY, flow_rate_ha_entity_id=ENTITY)
        world.sensor.readings[ENTITY] = FlowReading(10.0, NOW - timedelta(hours=1))
        world.gate._repo.revoke(TENANT, ENTITY)  # type: ignore[attr-defined]
        self._run(world, minutes=20)

        assert world.service.zone_status("z", tenant_key=TENANT, now=NOW).consumption == ()

    def test_an_actuator_without_any_rate_adds_nothing_not_a_guess(self, world) -> None:
        world.patch(actuator_key="act_ok")
        self._run(world, minutes=20)

        assert world.service.zone_status("z", tenant_key=TENANT, now=NOW).consumption_liters_30d == 0.0

    def test_a_zone_without_an_actuator_reports_only_what_was_logged(self, world) -> None:
        world.zones.facts = world.zones.facts.__class__(last_watering=None, next_planned=None, consumption_liters=42.0)

        status = world.service.zone_status("z", tenant_key=TENANT, now=NOW)

        assert [(p.source, p.liters) for p in status.consumption] == [("manual_log", 42.0)]

    def test_logged_and_runtime_litres_add_up_with_both_provenances(self, world) -> None:
        world.patch(actuator_key="act_ok", flow_rate_l_per_min=6.0)
        world.zones.facts = world.zones.facts.__class__(last_watering=None, next_planned=None, consumption_liters=40.0)
        self._run(world, minutes=10)

        status = world.service.zone_status("z", tenant_key=TENANT, now=NOW)

        assert [p.source for p in status.consumption] == ["manual_log", "actuator_runtime_manual_rate"]
        assert status.consumption_liters_30d == 100.0


class TestGrantOnUse:
    """#2522: a bind that fails the device-class check leaves no grant behind (light mode grants on use)."""

    def _light(self, world):
        world.gate = grant_service({}, grant_on_use=True)
        world.service = IrrigationZoneService(
            world.zones,
            world.service._sites,
            _NoObjects(),  # type: ignore[arg-type]
            FakeCareEventRepo(),
            ha_entity_gate=world.gate,
            flow_sensor=world.sensor,
        )

    def _bind(self, world):
        return world.patch(flow_rate_source=FlowRateSource.HA_ENTITY, flow_rate_ha_entity_id=ENTITY)

    def test_a_non_flow_entity_is_refused_and_not_granted(self, world) -> None:
        self._light(world)
        world.sensor.device_classes[ENTITY] = "temperature"

        with pytest.raises(PlanError):
            self._bind(world)

        assert world.gate.granted_entity_ids(TENANT) == frozenset()

    def test_an_unverifiable_entity_is_not_granted_either(self, world) -> None:
        self._light(world)
        world.sensor.down = True

        with pytest.raises(PlanError):
            self._bind(world)

        assert world.gate.granted_entity_ids(TENANT) == frozenset()

    def test_a_flow_entity_is_granted_on_use_once_it_passed(self, world) -> None:
        self._light(world)

        self._bind(world)

        assert world.gate.granted_entity_ids(TENANT) == frozenset({ENTITY})


class TestOrdering:
    def test_a_caller_without_the_scope_gets_403_before_the_422_of_a_mismatched_source(self, world) -> None:
        with pytest.raises(ForbiddenError):
            world.patch(scopes=(), flow_rate_source=FlowRateSource.HA_ENTITY)  # source without an entity

    def test_a_caller_with_the_scope_still_gets_the_422(self, world) -> None:
        with pytest.raises(PlanError) as refused:
            world.patch(flow_rate_source=FlowRateSource.HA_ENTITY)

        assert refused.value.error_code == ERROR_FLOW_SOURCE_MISMATCH


class TestReadingCache:
    """#2522: every member opens the status; Home Assistant is asked at most once per window."""

    def _count_reads(self, world) -> list[str]:
        asked: list[str] = []
        original = world.sensor.read

        def counting(entity_id):
            asked.append(entity_id)
            return original(entity_id)

        world.sensor.read = counting
        return asked

    def _setup(self, world) -> list[str]:
        world.patch(actuator_key="act_ok", flow_rate_l_per_min=6.0)
        world.patch(flow_rate_source=FlowRateSource.HA_ENTITY, flow_rate_ha_entity_id=ENTITY)
        world.sensor.readings[ENTITY] = FlowReading(10.0, NOW - timedelta(hours=1))
        return self._count_reads(world)

    def test_repeated_status_reads_ask_home_assistant_once(self, world) -> None:
        asked = self._setup(world)

        for _ in range(5):
            world.service.zone_status("z", tenant_key=TENANT, now=NOW)

        assert asked == [ENTITY]

    def test_the_answer_expires(self, world, monkeypatch) -> None:
        import app.domain.services.irrigation_zone_service as module

        asked = self._setup(world)
        clock = [1000.0]
        monkeypatch.setattr(module, "monotonic", lambda: clock[0])

        world.service.zone_status("z", tenant_key=TENANT, now=NOW)
        clock[0] += module.READING_TTL_SECONDS + 1
        world.service.zone_status("z", tenant_key=TENANT, now=NOW)

        assert asked == [ENTITY, ENTITY]

    def test_an_unreachable_home_assistant_is_remembered_too(self, world) -> None:
        asked = self._setup(world)
        world.sensor.down = True

        for _ in range(3):
            world.service.zone_status("z", tenant_key=TENANT, now=NOW)

        assert asked == [ENTITY]


class TestZoneCap:
    def _fill(self, world, count: int) -> None:
        for index in range(count):
            world.zones.add(
                IrrigationZone(
                    _key=f"fill{index}", tenant_key=TENANT, site_key=SITE, name=f"Z{index}", irrigation_type="drip"
                )
            )

    def test_the_501st_zone_of_a_site_is_422_with_a_clear_code(self, world) -> None:
        from app.domain.models.garden_plan import ERROR_ZONE_QUOTA, MAX_PLAN_ZONES

        self._fill(world, MAX_PLAN_ZONES - 1)  # plus the zone "z" of the world = the cap

        with pytest.raises(PlanError) as refused:
            world.service.create_zone(
                SITE, tenant_key=TENANT, role=TenantRole.LEAD, data=IrrigationZoneInput(name="One too many")
            )

        assert (refused.value.error_code, refused.value.status_code) == (ERROR_ZONE_QUOTA, 422)

    def test_the_last_zone_under_the_cap_is_created(self, world) -> None:
        from app.domain.models.garden_plan import MAX_PLAN_ZONES

        self._fill(world, MAX_PLAN_ZONES - 2)

        view = world.service.create_zone(
            SITE, tenant_key=TENANT, role=TenantRole.LEAD, data=IrrigationZoneInput(name="Last")
        )

        assert view.zone.name == "Last"

    def test_another_sites_zones_do_not_count(self, world) -> None:
        from app.domain.models.garden_plan import MAX_PLAN_ZONES

        for index in range(MAX_PLAN_ZONES):
            world.zones.add(
                IrrigationZone(
                    _key=f"o{index}", tenant_key=TENANT, site_key=OTHER_SITE, name=f"Z{index}", irrigation_type="drip"
                )
            )

        view = world.service.create_zone(
            SITE, tenant_key=TENANT, role=TenantRole.LEAD, data=IrrigationZoneInput(name="Fine")
        )

        assert view.zone.name == "Fine"
