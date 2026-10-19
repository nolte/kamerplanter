"""REQ-053 WP 7.3 (#2469) - the status of a zone and its watering round (GP-API-052/053, GP-FR-112/117).

Pinned here: the order of the checks (tenant 404 -> role 403 -> body), the all-or-nothing round, the shares that
add up to the total, the `allocation` on every event, the beds without an area, and that the status reads only the
beds of the zone it was asked about.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import CareEventAllocation, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError
from app.domain.models.irrigation_zone import (
    IrrigationZone,
    LastWatering,
    NextPlannedWatering,
    ZoneWateringFacts,
    ZoneWateringInput,
)
from app.domain.models.site import Site
from app.domain.services.irrigation_zone_service import (
    ERROR_NO_BED_AREA,
    ERROR_NO_BEDS,
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
from tests.support.irrigation_zone_fakes import FakeZones

USER = "u_sabine"
NOW = datetime(2026, 10, 19, 9, 30, tzinfo=UTC)


class _NoObjects:
    def get_garden_object_by_key(self, key, *, tenant_key):  # pragma: no cover - not reached here
        return None


class World:
    def __init__(self) -> None:
        sites = FakeSites(
            make_site(), Site(_key="site_foreign", tenant_key=OTHER_TENANT, name="Theirs", type="outdoor")
        )
        self.plan = FakePlanRepo(sites)
        for key, area in (("bed_1", 6.0), ("bed_2", 2.0), ("bed_flat", 0.0)):
            self.plan.locations[key] = make_location(key, name=key).model_copy(update={"area_m2": area})
        self.zones = FakeZones(self.plan)
        self.zones.add(IrrigationZone(_key="z", tenant_key=TENANT, site_key=SITE, name="South", irrigation_type="drip"))
        self.zones.add(IrrigationZone(_key="z_empty", tenant_key=TENANT, site_key=SITE, name="Empty"))
        self.zones.add(IrrigationZone(_key="z_foreign", tenant_key=OTHER_TENANT, site_key="site_foreign", name="X"))
        self.zones.replace_zone_locations("z", ["bed_1", "bed_2", "bed_flat"], tenant_key=TENANT)
        self.care = FakeCareEventRepo()
        self.service = IrrigationZoneService(self.zones, sites, _NoObjects(), self.care)  # type: ignore[arg-type]

    def log(self, **data):
        body = {"volume_liters": 40.0, "allocation": "by_area"} | data
        return self.service.log_watering(
            "z", tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER, data=ZoneWateringInput(**body)
        )


@pytest.fixture
def world() -> World:
    return World()


class TestLogWatering:
    def test_by_area_divides_the_total_over_the_beds_with_an_area_and_names_the_rest(self, world) -> None:
        result = world.log()

        assert {s.location_key: s.liters for s in result.shares} == {"bed_1": 30.0, "bed_2": 10.0}
        assert sum(s.liters for s in result.shares) == pytest.approx(40.0, abs=0.01)
        assert result.skipped_location_keys == ("bed_flat",)
        assert result.allocation is CareEventAllocation.BY_AREA

    def test_one_watering_event_per_bed_each_marked_with_the_allocation(self, world) -> None:
        world.log(summary="Morning round")

        events = world.care.inserted
        assert sorted(e.location_key for e in events) == ["bed_1", "bed_2"]
        for event in events:
            assert (event.category, event.trigger, event.unit) == ("watering", "manual", "l")
            assert event.allocation is CareEventAllocation.BY_AREA  # never stored as measured
            assert (event.tenant_key, event.site_key, event.performed_by_user_key) == (TENANT, SITE, USER)
            assert event.summary == "Morning round"
        assert len({e.performed_at for e in events}) == 1  # one round, one instant

    def test_equal_gives_every_bed_the_same_share_even_one_without_an_area(self, world) -> None:
        result = world.log(allocation="equal", volume_liters=30.0)

        assert sorted(s.liters for s in result.shares) == [10.0, 10.0, 10.0]
        assert result.skipped_location_keys == ()
        assert all(e.allocation is CareEventAllocation.EQUAL for e in world.care.inserted)

    def test_a_round_that_cannot_be_written_writes_nothing(self, world) -> None:
        world.care.fail_insert_many = True

        with pytest.raises(RuntimeError):
            world.log()

        assert world.care.inserted == []

    def test_by_area_without_any_bed_area_is_refused_and_equal_still_works(self, world) -> None:
        for key in ("bed_1", "bed_2"):
            world.plan.locations[key] = world.plan.locations[key].model_copy(update={"area_m2": 0.0})

        with pytest.raises(PlanError) as refused:
            world.log()
        assert (refused.value.error_code, refused.value.status_code) == (ERROR_NO_BED_AREA, 422)
        assert world.care.inserted == []
        assert len(world.log(allocation="equal").shares) == 3

    def test_a_zone_without_beds_is_refused(self, world) -> None:
        with pytest.raises(PlanError) as refused:
            world.service.log_watering(
                "z_empty",
                tenant_key=TENANT,
                user_key=USER,
                role=TenantRole.GROWER,
                data=ZoneWateringInput(volume_liters=5, allocation="equal"),
            )
        assert refused.value.error_code == ERROR_NO_BEDS and world.care.inserted == []

    def test_a_viewer_is_refused_after_the_tenant_anchor_and_a_foreign_zone_is_a_404(self, world) -> None:
        data = ZoneWateringInput(volume_liters=5, allocation="equal")
        with pytest.raises(ForbiddenError):
            world.service.log_watering("z", tenant_key=TENANT, user_key=USER, role=TenantRole.VIEWER, data=data)
        for role in (TenantRole.VIEWER, TenantRole.LEAD):
            with pytest.raises(NotFoundError):
                world.service.log_watering("z_foreign", tenant_key=TENANT, user_key=USER, role=role, data=data)
        assert world.care.inserted == []

    def test_the_instant_follows_the_care_log_window(self, world) -> None:
        with pytest.raises(PlanError) as future:
            world.log(performed_at=datetime.now(UTC) + timedelta(hours=1))
        with pytest.raises(PlanError) as old:
            world.log(performed_at=datetime.now(UTC) - timedelta(days=400))
        assert future.value.error_code == "care_event.performed_in_future"
        assert old.value.error_code == "care_event.too_old"
        assert world.care.inserted == []

    @pytest.mark.parametrize(
        "bad",
        [
            {"allocation": "measured"},
            {"allocation": "by_demand"},
            {"volume_liters": 0},
            {"volume_liters": -3},
            {"volume_liters": 1_000_000},
            {"surprise": 1},
        ],
    )
    def test_the_body_refuses_what_is_not_a_divided_total(self, bad) -> None:
        with pytest.raises(ValueError, match=r"."):
            ZoneWateringInput(**({"volume_liters": 5, "allocation": "equal"} | bad))


class TestStatus:
    def test_it_reads_the_beds_of_the_zone_and_maps_the_facts(self, world) -> None:
        world.zones.facts = ZoneWateringFacts(
            last_watering=LastWatering(
                at=NOW - timedelta(days=1), source="care_event", location_key="bed_1", allocation="by_area"
            ),
            next_planned=NextPlannedWatering(
                task_key="t1", location_key="bed_2", due_date=datetime(2026, 10, 18, 23, 59, tzinfo=UTC)
            ),
            consumption_liters=480.0,
        )

        status = world.service.zone_status("z", tenant_key=TENANT, now=NOW)

        assert world.zones.facts_asked == [["bed_1", "bed_2", "bed_flat"]]
        assert status.last_watering is not None and status.last_watering.allocation == "by_area"
        assert status.next_planned is not None and status.next_planned.overdue is True  # due day < today (#2461)
        assert (status.demand_liters_today, status.consumption_liters_30d) == (None, 480.0)

    def test_a_task_due_today_is_not_overdue_whatever_the_time(self, world) -> None:
        world.zones.facts = ZoneWateringFacts(
            last_watering=None,
            next_planned=NextPlannedWatering(task_key="t", location_key="bed_1", due_date=NOW.replace(hour=0)),
            consumption_liters=0.0,
        )

        status = world.service.zone_status("z", tenant_key=TENANT, now=NOW)

        assert status.next_planned is not None and status.next_planned.overdue is False
        assert status.last_watering is None

    def test_a_foreign_zone_is_a_404_and_nothing_is_read(self, world) -> None:
        with pytest.raises(NotFoundError):
            world.service.zone_status("z_foreign", tenant_key=TENANT, now=NOW)
        assert world.zones.facts_asked == []
