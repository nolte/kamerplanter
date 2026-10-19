"""REQ-053 WP 7.3-7.5 (#2469-#2471) - the zone status, the watering round, the demand and the coupling on ArangoDB.

What no double can decide, measured here against the production schema:

* the watering round writes one ``care_event`` per bed in one transaction, marked with its ``allocation``;
* the status reads only the tenant's own records: care events (voided or superseded ones do not count),
  ``watering_events`` of the beds' slots, the oldest open ``watering`` task (a suggestion is none), the REQ-037
  demand of the day, and the actuator's successful switches;
* the plan read model carries ``last_watered_at`` per bed;
* the coupling writes the ``zone_actuated_by`` edge, refuses another tenant's actuator, and an actuator that is
  deleted takes itself out of the zone.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from arango import ArangoClient

from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import PlanValidationError
from app.data_access.arango import collections as col
from app.data_access.arango.actuator_repository import ArangoActuatorRepository
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.garden_object_repository import ArangoGardenObjectRepository
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.data_access.arango.irrigation_zone_repository import ArangoIrrigationZoneRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.irrigation_zone import IrrigationZoneInput, IrrigationZonePatch, ZoneWateringInput
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.irrigation_zone_service import IrrigationZoneService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("irrigation_zone_wave7")
A, B = "ten_a", "ten_b"
USER = "u_sabine"
NOW = datetime.now(UTC)
_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 20, "length_m": 20, "rotation_deg": 0}
TECH = (AdminScope.TECHNICAL,)


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


def _bed(key: str, site: str, x: float, area: float = 2.0) -> dict[str, Any]:
    return {
        "_key": key,
        "site_key": site,
        "name": key,
        "location_type_key": "bed",
        "area_m2": area,
        "depth": 0,
        "path": key,
        "bed_status": "active",
        "geometry": {"kind": "rect", "origin": [x, 1], "width_m": area, "length_m": 1, "rotation_deg": 0},
    }


_TOUCHED = (
    col.SITES,
    col.LOCATIONS,
    col.SLOTS,
    col.IRRIGATION_ZONES,
    col.CARE_EVENTS,
    col.WATERING_EVENTS,
    col.TASKS,
    col.IRRIGATION_DEMANDS,
    col.PLANTING_RUNS,
    col.ACTUATORS,
    col.CONTROL_EVENTS,
    col.LOCATION_TYPES,
    col.USERS,
    col.CONTAINS,
    col.HAS_IRRIGATION_ZONE,
    col.ZONE_COVERS,
    col.ZONE_SUPPLIED_BY,
    col.ZONE_ACTUATED_BY,
    col.CARE_EVENT_AT,
)


@pytest.fixture
def db(database):
    for name in _TOUCHED:
        database.collection(name).truncate()
    database.collection(col.USERS).insert({"_key": USER, "display_name": "Sabine"})
    database.collection(col.LOCATION_TYPES).insert({"_key": "bed", "name": "Bed", "is_bed": True})
    for key, tenant in (("site_a", A), ("site_b", B)):
        database.collection(col.SITES).insert(
            {
                "_key": key,
                "tenant_key": tenant,
                "name": key,
                "type": "outdoor",
                "total_area_m2": 0.0,
                "timezone": "UTC",
                "plan": {"boundary": _BOUNDARY, "plan_revision": 3, "north_angle_deg": 0.0},
            }
        )
    for index, (key, area) in enumerate((("bed_1", 6.0), ("bed_2", 2.0))):
        database.collection(col.LOCATIONS).insert(_bed(key, "site_a", 1 + index * 8, area))
        database.collection(col.CONTAINS).insert({"_from": "sites/site_a", "_to": f"locations/{key}"})
    database.collection(col.LOCATIONS).insert(_bed("bed_b", "site_b", 1))
    database.collection(col.SLOTS).insert(
        {"_key": "slot_1", "slot_id": "BED1_P1", "location_key": "bed_1", "capacity_plants": 1, "archived_at": None}
    )
    return database


def _service(db) -> IrrigationZoneService:
    return IrrigationZoneService(
        ArangoIrrigationZoneRepository(db),
        ArangoSiteRepository(db),
        ArangoGardenObjectRepository(db),
        ArangoCareEventRepository(db),
    )


def _zone(db, **data: Any) -> str:
    service = _service(db)
    view = service.create_zone(
        "site_a", tenant_key=A, role=TenantRole.GROWER, data=IrrigationZoneInput(name="South", **data)
    )
    key = view.zone.key or ""
    service.replace_locations(key, tenant_key=A, role=TenantRole.GROWER, location_keys=["bed_1", "bed_2"])
    return key


def _status(db, zone: str):
    return _service(db).zone_status(zone, tenant_key=A, now=datetime.now(UTC))


class TestWateringRound:
    def test_one_event_per_bed_marked_with_the_allocation_and_the_status_reads_them_back(self, db) -> None:
        zone = _zone(db)

        result = _service(db).log_watering(
            zone,
            tenant_key=A,
            user_key=USER,
            role=TenantRole.GROWER,
            data=ZoneWateringInput(volume_liters=40, allocation="by_area"),
        )

        stored = list(db.collection(col.CARE_EVENTS).all())
        assert {(e["location_key"], e["quantity"], e["allocation"]) for e in stored} == {
            ("bed_1", 30.0, "by_area"),
            ("bed_2", 10.0, "by_area"),
        }
        assert len(db.collection(col.CARE_EVENT_AT).all()) == 2 and len(result.event_keys) == 2
        status = _status(db, zone)
        assert status.consumption_liters_30d == 40.0
        assert status.last_watering is not None and status.last_watering.allocation == "by_area"
        assert status.last_watering.source == "care_event"

    def test_a_voided_event_is_no_watering(self, db) -> None:
        zone = _zone(db)
        _service(db).log_watering(
            zone,
            tenant_key=A,
            user_key=USER,
            role=TenantRole.GROWER,
            data=ZoneWateringInput(volume_liters=8, allocation="equal"),
        )
        for event in db.collection(col.CARE_EVENTS).all():
            db.collection(col.CARE_EVENTS).update({"_key": event["_key"], "voided_at": NOW.isoformat()})

        status = _status(db, zone)

        assert status.last_watering is None and status.consumption_liters_30d == 0.0

    def test_another_tenants_event_at_the_same_bed_key_is_not_counted(self, db) -> None:
        zone = _zone(db)
        db.collection(col.CARE_EVENTS).insert(
            {
                "tenant_key": B,
                "site_key": "site_a",
                "location_key": "bed_1",
                "category": "watering",
                "performed_at": NOW.isoformat(),
                "trigger": "manual",
                "unit": "l",
                "quantity": 99.0,
            }
        )

        assert _status(db, zone).consumption_liters_30d == 0.0


class TestStatusReads:
    def test_a_watering_event_of_the_beds_slots_counts_and_can_be_the_last_watering(self, db) -> None:
        zone = _zone(db)
        db.collection(col.WATERING_EVENTS).insert(
            {
                "tenant_key": A,
                "slot_keys": ["slot_1"],
                "volume_liters": 5.0,
                "watered_at": (NOW - timedelta(hours=2)).isoformat(),
            }
        )

        status = _status(db, zone)

        assert status.consumption_liters_30d == 5.0
        assert status.last_watering is not None and status.last_watering.source == "watering_event"
        assert status.last_watering.location_key == "bed_1" and status.last_watering.allocation == "measured"

    def test_the_oldest_open_watering_task_is_next_and_a_suggestion_is_not(self, db) -> None:
        zone = _zone(db)
        past = (NOW - timedelta(days=3)).isoformat()
        for key, extra in (
            ("t_old", {"due_date": past}),
            ("t_suggested", {"due_date": (NOW - timedelta(days=9)).isoformat(), "suggested": True}),
            ("t_done", {"due_date": (NOW - timedelta(days=8)).isoformat(), "status": "completed"}),
            ("t_other_tenant", {"due_date": (NOW - timedelta(days=7)).isoformat(), "tenant_key": B}),
            ("t_other_category", {"due_date": (NOW - timedelta(days=6)).isoformat(), "category": "pruning"}),
        ):
            db.collection(col.TASKS).insert(
                {
                    "_key": key,
                    "tenant_key": A,
                    "status": "pending",
                    "category": "watering",
                    "entity_type": "location",
                    "entity_key": "bed_2",
                    **extra,
                }
            )

        planned = _status(db, zone).next_planned

        assert planned is not None and (planned.task_key, planned.location_key) == ("t_old", "bed_2")
        assert planned.overdue is True

    def test_the_demand_of_today_is_net_and_gross_by_the_type_default(self, db) -> None:
        zone = _zone(db, irrigation_type="drip")
        db.collection(col.PLANTING_RUNS).insert(
            {"_key": "run_1", "tenant_key": A, "name": "R", "location_key": "bed_1"}
        )
        db.collection(col.IRRIGATION_DEMANDS).insert(
            {
                "tenant_key": A,
                "site_key": "site_a",
                "run_key": "run_1",
                "demand_date": datetime.now(UTC).date().isoformat(),
                "net_demand_mm": 2.0,
                "area_m2": 6.0,
            }
        )
        db.collection(col.IRRIGATION_DEMANDS).insert(  # yesterday's is no demand for today
            {
                "tenant_key": A,
                "site_key": "site_a",
                "run_key": "run_1",
                "demand_date": (datetime.now(UTC).date() - timedelta(days=1)).isoformat(),
                "net_demand_mm": 50.0,
                "area_m2": 6.0,
            }
        )

        status = _status(db, zone)

        assert status.demand_liters_today == 12.0
        assert (status.demand_gross_liters_today, status.efficiency_source) == (13.64, "type_default")

    def test_the_plan_read_model_carries_the_last_watering_per_bed(self, db) -> None:
        zone = _zone(db)
        _service(db).log_watering(
            zone,
            tenant_key=A,
            user_key=USER,
            role=TenantRole.GROWER,
            data=ZoneWateringInput(volume_liters=10, allocation="equal"),
        )
        plans = GardenPlanService(
            ArangoSiteRepository(db), ArangoGardenPlanRepository(db), ArangoIrrigationZoneRepository(db)
        )

        view = plans.get_plan("site_a", tenant_key=A)

        assert set(view.last_watered) == {"bed_1", "bed_2"}
        assert [zone_row["key"] for zone_row in view.zones] == [zone]
        assert plans.get_plan("site_a", tenant_key=A, include=frozenset({"plants"})).last_watered == {}


class TestCoupling:
    def _actuator(self, db, key: str, tenant: str, location: str) -> None:
        db.collection(col.ACTUATORS).insert(
            {"_key": key, "tenant_key": tenant, "location_key": location, "name": key, "actuator_type": "pump"}
        )

    def test_the_actuator_gets_its_edge_and_a_foreign_one_is_refused(self, db) -> None:
        zone = _zone(db)
        self._actuator(db, "act_a", A, "bed_1")
        self._actuator(db, "act_b", B, "bed_b")
        service = _service(db)

        view = service.patch_zone(
            zone,
            tenant_key=A,
            role=TenantRole.GROWER,
            patch=IrrigationZonePatch(actuator_key="act_a"),
            admin_scopes=TECH,
        )
        with pytest.raises(PlanValidationError):
            service.patch_zone(
                zone,
                tenant_key=A,
                role=TenantRole.GROWER,
                patch=IrrigationZonePatch(actuator_key="act_b"),
                admin_scopes=TECH,
            )

        assert view.zone.actuator_key == "act_a"
        assert [(e["_from"], e["_to"]) for e in db.collection(col.ZONE_ACTUATED_BY).all()] == [
            (f"irrigation_zones/{zone}", "actuators/act_a")
        ]

    def test_a_deleted_actuator_leaves_no_dead_key_on_the_zone(self, db) -> None:
        zone = _zone(db)
        self._actuator(db, "act_a", A, "bed_1")
        _service(db).patch_zone(
            zone,
            tenant_key=A,
            role=TenantRole.GROWER,
            patch=IrrigationZonePatch(actuator_key="act_a"),
            admin_scopes=TECH,
        )

        ArangoActuatorRepository(db).delete_actuator("act_a")

        assert "actuator_key" not in db.collection(col.IRRIGATION_ZONES).get(zone)
        assert list(db.collection(col.ZONE_ACTUATED_BY).all()) == []

    def test_the_actuators_switches_are_read_with_the_state_before_the_window(self, db) -> None:
        repo = ArangoIrrigationZoneRepository(db)
        events = db.collection(col.CONTROL_EVENTS)
        base = {"tenant_key": A, "actuator_key": "act_a", "success": True}
        events.insert({**base, "timestamp": (NOW - timedelta(days=40)).isoformat(), "new_state": "on"})
        events.insert({**base, "timestamp": (NOW - timedelta(days=5)).isoformat(), "new_state": "off"})
        events.insert({**base, "success": False, "timestamp": (NOW - timedelta(days=4)).isoformat(), "new_state": "on"})
        events.insert({**base, "tenant_key": B, "timestamp": (NOW - timedelta(days=3)).isoformat(), "new_state": "on"})

        changes = repo.actuator_state_changes("act_a", tenant_key=A, since=NOW - timedelta(days=30), until=NOW)

        assert [change.new_state for change in changes] == ["on", "off"]  # the state at the start, then the switch
