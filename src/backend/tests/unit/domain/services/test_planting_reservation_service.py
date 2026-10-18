"""REQ-053 WP 3.2 — reservation with a time window, plan-slots, planting states and bed clearing.

The repository is the in-memory double of ``tests/support/planting_reservation_fakes.py``. As in the plan tests,
every refusal asserts that **nothing reached the repository**: a refusal that still wrote is the defect, not the
status code.

Pinned here: GP-ACC-021/039 (V-08, the window and the 409 body), GP-NFR-058 (``slot_keys`` ⊆ the bed, one text for
foreign and absent), the role rules of GP-API-021/022, the layout of GP-FR-064 (ids, geometry, quotas, V-06), and
the clearing of GP-FR-055 (a server-written, server-only ``clearing`` event).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.common.enums import (
    LayoutStrategy,
    PlantingRunStatus,
    PlantingRunType,
    RowDirection,
    SlotRole,
    TenantRole,
    TerminationType,
)
from app.common.exceptions import (
    ForbiddenError,
    InvalidRunStateError,
    NotFoundError,
    PlanError,
    PlanValidationError,
)
from app.domain.engines.slot_reservation_engine import ActivePlant, Reservation
from app.domain.models.planting_reservation import PlantingRow
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.models.site import Slot
from app.domain.services.care_event_service import CareEventService
from app.domain.services.planting_reservation_service import (
    PlantingReservationService,
    PreparedLayout,
    entry_layout_of,
)
from tests.support.care_event_fakes import (
    FakeAttachmentRepo,
    FakeAttachmentService,
    FakeCareEventRepo,
    FakeFertilizers,
    FakeMemberships,
)
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    USER,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)
from tests.support.planting_reservation_fakes import FakeReservationRepo, FakeRuns

GROWER = TenantRole.GROWER
LEAD = TenantRole.LEAD
VIEWER = TenantRole.VIEWER
D = date


def make_run(key: str = "run_b", **overrides) -> PlantingRun:
    data = {
        "_key": key,
        "tenant_key": TENANT,
        "name": "Lamb's lettuce",
        "run_type": PlantingRunType.MONOCULTURE,
        "status": PlantingRunStatus.PLANNED,
        "location_key": "bed",
        "planned_start_date": D(2026, 10, 5),
        **overrides,
    }
    return PlantingRun(**data)


def slot(key: str, slot_id: str, **overrides) -> Slot:
    return Slot(_key=key, slot_id=slot_id, location_key="bed", **overrides)


@pytest.fixture
def world():
    sites = FakeSites(make_site(), make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed 3", geometry=rect(0, 0, 4, 2))
    plan.locations["bed_two"] = make_location("bed_two", name="Bed 4", geometry=rect(5, 0, 2, 2))
    plan.locations["loc_foreign"] = make_location("loc_foreign", name="Foreign").model_copy(
        update={"site_key": "site_foreign"}
    )
    plan.slots = [slot("s1", "BED3_001"), slot("s2", "BED3_002"), slot("s3", "BED3_003")]
    plan.slots.append(Slot(_key="s_other", slot_id="BED4_001", location_key="bed_two"))
    runs = FakeRuns(make_run(), make_run("run_a", planned_start_date=D(2026, 5, 15), planned_until=D(2026, 9, 30)))
    runs.entries["e_b"] = PlantingRunEntry(
        _key="e_b", run_key="run_b", tenant_key=TENANT, species_key="sp_lettuce", quantity=2, id_prefix="LAM"
    )
    runs.entries["e_a"] = PlantingRunEntry(
        _key="e_a", run_key="run_a", tenant_key=TENANT, species_key="sp_tomato", quantity=2, id_prefix="TOM"
    )
    repo = FakeReservationRepo(plan, runs)
    care = CareEventService(
        FakeCareEventRepo(), sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    service = PlantingReservationService(repo, runs, sites, plan, care)
    return type("World", (), {"service": service, "repo": repo, "plan": plan, "runs": runs, "sites": sites})


def reserve(world, run_key: str, slot_key: str, start: date, end: date | None, entry: str = "e_a") -> None:
    world.repo.reservations.append(
        Reservation(slot_key, run_key, entry, "sp", len(world.repo.reservations) + 1, start, end)
    )


class TestPlanSlots:
    def test_a_follow_up_crop_may_take_a_slot_after_the_window(self, world) -> None:
        reserve(world, "run_a", "s1", D(2026, 5, 15), D(2026, 9, 30))

        planned = world.service.plan_slots(
            "run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=["s1", "s2"]
        )

        assert planned.slots == [("s1", 1), ("s2", 2)]
        assert (planned.planned_from, planned.planned_until) == (D(2026, 10, 5), None)
        (write,) = world.repo.reservation_writes
        assert (write.ordered_slot_keys, write.planned_species_key, write.location_key) == (
            ["s1", "s2"],
            "sp_lettuce",
            "bed",
        )

    def test_an_overlapping_window_is_409_and_nothing_is_written(self, world) -> None:
        reserve(world, "run_a", "s1", D(2026, 5, 15), D(2026, 9, 30))
        world.runs.runs["run_b"] = make_run(planned_start_date=D(2026, 8, 1))

        with pytest.raises(PlanError) as caught:
            world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=["s1"])

        error = caught.value
        assert (error.status_code, error.error_code) == (409, "slot.already_planned")
        detail = error.details[0]
        assert detail["conflicting_run_key"] == "run_a"
        assert (detail["overlap_from"], detail["overlap_until"]) == ("2026-08-01", "2026-09-30")
        assert world.repo.reservation_writes == []

    def test_an_active_plant_blocks_a_window_that_starts_before_its_run_ends(self, world) -> None:
        world.repo.plants.append(ActivePlant("s2", "pi_1", "run_a", D(2026, 10, 31)))

        with pytest.raises(PlanError) as caught:
            world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=["s2"])

        assert caught.value.details[0]["conflicting_run_key"] == "run_a"
        assert caught.value.details[0]["overlap_until"] == "2026-10-31"

    def test_the_conflicts_of_all_slots_travel_in_the_body(self, world) -> None:
        reserve(world, "run_a", "s1", D(2026, 5, 15), None)
        reserve(world, "run_a", "s2", D(2026, 5, 15), None)

        with pytest.raises(PlanError) as caught:
            world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=["s1", "s2"])

        assert [c["slot_key"] for c in caught.value.details[0]["conflicts"]] == ["s1", "s2"]

    def test_replacing_a_runs_own_reservation_is_no_conflict(self, world) -> None:
        reserve(world, "run_b", "s1", D(2026, 10, 5), None, entry="e_b")

        world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=["s1", "s3"])

        assert sorted(r.slot_key for r in world.repo.reservations if r.run_key == "run_b") == ["s1", "s3"]

    def test_an_empty_list_releases_the_entrys_reservation(self, world) -> None:
        reserve(world, "run_b", "s1", D(2026, 10, 5), None, entry="e_b")

        world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=[])

        assert world.repo.reservations == []

    @pytest.mark.parametrize("slot_keys", [["s_other"], ["s1", "nope"], ["s1", "s1"]])
    def test_slot_keys_must_be_distinct_slots_of_the_runs_bed(self, world, slot_keys) -> None:
        with pytest.raises(PlanValidationError):
            world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=slot_keys)

        assert world.repo.reservation_writes == []

    def test_an_archived_slot_cannot_be_reserved(self, world) -> None:
        world.plan.slots[0] = slot("s1", "BED3_001", archived_at=datetime(2026, 1, 1, tzinfo=UTC))

        with pytest.raises(PlanValidationError):
            world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=["s1"])

    def test_a_foreign_slot_and_an_absent_one_read_alike(self, world) -> None:
        world.plan.slots.append(Slot(_key="s_foreign", slot_id="FOR_001", location_key="loc_foreign"))
        texts = []
        for key in ("s_foreign", "ghost"):
            with pytest.raises(PlanValidationError) as caught:
                world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=[key])
            texts.append(caught.value.details)
        assert texts[0] == texts[1]

    def test_another_tenants_run_is_404(self, world) -> None:
        with pytest.raises(NotFoundError):
            world.service.plan_slots("run_b", tenant_key=OTHER_TENANT, role=GROWER, entry_key="e_b", slot_keys=["s1"])

        assert world.repo.reservation_writes == []

    @pytest.mark.parametrize("entry_key", ["e_a", "ghost"])
    def test_an_entry_of_another_run_and_an_absent_one_are_422_reference_not_found(self, world, entry_key) -> None:
        with pytest.raises(PlanValidationError) as caught:
            world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key=entry_key, slot_keys=["s1"])

        assert (caught.value.codes, caught.value.details[0]["field"]) == (["reference.not_found"], "entry_key")
        assert world.repo.reservation_writes == []

    def test_a_viewer_may_not_reserve(self, world) -> None:
        with pytest.raises(ForbiddenError):
            world.service.plan_slots("run_b", tenant_key=TENANT, role=VIEWER, entry_key="e_b", slot_keys=["s1"])

    def test_a_run_without_a_location_reserves_nothing(self, world) -> None:
        world.runs.runs["run_b"] = make_run(location_key=None)

        with pytest.raises(PlanError) as caught:
            world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=["s1"])

        assert caught.value.error_code == "run.without_location"

    def test_an_ended_run_reserves_nothing(self, world) -> None:
        world.runs.runs["run_b"] = make_run(status=PlantingRunStatus.COMPLETED)

        with pytest.raises(InvalidRunStateError):
            world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=["s1"])

    def test_the_run_window_defaults_to_the_start_date_then_today(self, world) -> None:
        world.runs.runs["run_b"] = make_run(
            planned_start_date=None, planned_from=D(2026, 11, 1), planned_until=D(2027, 2, 1)
        )
        planned = world.service.plan_slots("run_b", tenant_key=TENANT, role=GROWER, entry_key="e_b", slot_keys=["s1"])
        assert (planned.planned_from, planned.planned_until) == (D(2026, 11, 1), D(2027, 2, 1))


class TestReleaseSlot:
    def test_a_grower_releases_while_the_run_is_planned(self, world) -> None:
        reserve(world, "run_b", "s1", D(2026, 10, 5), None, entry="e_b")

        world.service.release_slot("run_b", "s1", tenant_key=TENANT, role=GROWER)

        assert world.repo.released == [("run_b", "s1")]

    def test_after_the_start_only_the_lead_releases(self, world) -> None:
        world.runs.runs["run_b"] = make_run(status=PlantingRunStatus.ACTIVE)
        reserve(world, "run_b", "s1", D(2026, 10, 5), None, entry="e_b")

        with pytest.raises(ForbiddenError):
            world.service.release_slot("run_b", "s1", tenant_key=TENANT, role=GROWER)
        world.service.release_slot("run_b", "s1", tenant_key=TENANT, role=LEAD)

        assert world.repo.released == [("run_b", "s1")]

    def test_a_slot_that_was_never_reserved_is_404(self, world) -> None:
        with pytest.raises(NotFoundError):
            world.service.release_slot("run_b", "s1", tenant_key=TENANT, role=GROWER)

    def test_a_slot_of_another_bed_is_404_and_nothing_is_released(self, world) -> None:
        with pytest.raises(NotFoundError):
            world.service.release_slot("run_b", "s_other", tenant_key=TENANT, role=GROWER)

        assert world.repo.released == []

    def test_another_tenants_run_is_404(self, world) -> None:
        with pytest.raises(NotFoundError):
            world.service.release_slot("run_b", "s1", tenant_key=OTHER_TENANT, role=LEAD)

        assert world.repo.released == []


class TestListPlantings:
    def rows(self, world) -> None:
        world.repo.rows = [
            PlantingRow(
                state="planned", slot_key="s1", slot_id="BED3_001", species_key="sp", planned_from=D(2026, 10, 5)
            ),
            PlantingRow(state="active", slot_key="s2", slot_id="BED3_002", species_key="sp", planted_on=D(2026, 5, 1)),
            PlantingRow(
                state="harvested",
                slot_key="s3",
                slot_id="BED3_003",
                species_key="sp",
                planted_on=D(2025, 5, 1),
                removed_on=D(2025, 9, 1),
            ),
        ]

    def test_it_filters_by_state_and_year(self, world) -> None:
        self.rows(world)
        page = lambda **kw: world.service.list_plantings(  # noqa: E731
            "bed", tenant_key=TENANT, state=kw.get("state"), year=kw.get("year"), offset=0, limit=50
        )

        assert [r.state for r in page()] == ["planned", "active", "harvested"]
        assert [r.state for r in page(state="active")] == ["active"]
        assert [r.state for r in page(year=2025)] == ["harvested"]

    def test_it_returns_a_window(self, world) -> None:
        self.rows(world)
        rows = world.service.list_plantings("bed", tenant_key=TENANT, state=None, year=None, offset=1, limit=1)
        assert [r.state for r in rows] == ["active"]

    def test_an_unknown_state_is_422(self, world) -> None:
        with pytest.raises(PlanValidationError) as caught:
            world.service.list_plantings("bed", tenant_key=TENANT, state="sown", year=None, offset=0, limit=10)
        assert caught.value.codes == ["plantings.unknown_state"]

    def test_another_tenants_bed_is_404(self, world) -> None:
        with pytest.raises(NotFoundError):
            world.service.list_plantings("loc_foreign", tenant_key=TENANT, state=None, year=None, offset=0, limit=10)
        with pytest.raises(NotFoundError):
            world.service.list_plantings("bed", tenant_key=OTHER_TENANT, state=None, year=None, offset=0, limit=10)


class TestClearBed:
    def test_it_writes_a_server_made_clearing_event_in_the_same_write(self, world) -> None:
        world.service.clear_bed(
            "bed",
            tenant_key=TENANT,
            user_key=USER,
            role=GROWER,
            termination_type=TerminationType.SENESCED,
            reason="  end of season ",
        )

        (write,) = world.repo.clear_writes
        assert write.termination_type == "senesced"
        assert write.removed_on == datetime.now(UTC).date()
        event = write.event
        assert (event.category, event.trigger, event.location_key, event.tenant_key) == (
            "clearing",
            "system",
            "bed",
            TENANT,
        )
        assert event.reason == "end of season"
        assert event.performed_by_user_key == USER

    def test_a_viewer_may_not_clear(self, world) -> None:
        with pytest.raises(ForbiddenError):
            world.service.clear_bed(
                "bed",
                tenant_key=TENANT,
                user_key=USER,
                role=VIEWER,
                termination_type=TerminationType.DIED,
                reason=None,
            )

        assert world.repo.clear_writes == []

    def test_another_tenants_bed_is_404_and_nothing_is_written(self, world) -> None:
        for bed, tenant in (("loc_foreign", TENANT), ("bed", OTHER_TENANT)):
            with pytest.raises(NotFoundError):
                world.service.clear_bed(
                    bed,
                    tenant_key=tenant,
                    user_key=USER,
                    role=LEAD,
                    termination_type=TerminationType.CANCELLED,
                    reason=None,
                )

        assert world.repo.clear_writes == []


class TestEntryLayout:
    def entry(self, **overrides) -> PlantingRunEntry:
        data = {"species_key": "sp", "quantity": 4, "id_prefix": "TOM", "spacing_cm": 50, **overrides}
        return PlantingRunEntry(**data)

    @pytest.mark.parametrize("strategy", [None, LayoutStrategy.FREE])
    def test_no_strategy_and_free_plan_no_layout(self, strategy) -> None:
        assert entry_layout_of(self.entry(layout_strategy=strategy)) is None

    def test_a_strategy_without_spacing_is_422(self) -> None:
        with pytest.raises(PlanError) as caught:
            entry_layout_of(self.entry(layout_strategy=LayoutStrategy.GRID, spacing_cm=None), index=2)
        assert (caught.value.error_code, caught.value.details[0]["field"]) == (
            "layout.spacing_required",
            "entries[2].spacing_cm",
        )

    def test_the_fields_reach_the_calculator(self) -> None:
        layout = entry_layout_of(
            self.entry(layout_strategy=LayoutStrategy.ROWS, row_spacing_cm=60, row_assignment=[0, 2])
        )
        assert (layout.layout_strategy, layout.spacing_cm, layout.row_spacing_cm) == (LayoutStrategy.ROWS, 50, 60)
        assert layout.row_direction is RowDirection.ALONG_LENGTH  # the placeholder default (vector conventions)
        assert layout.row_assignment == (0, 2)


class TestPrepareLayout:
    def entry(self, **overrides) -> PlantingRunEntry:
        data = {
            "species_key": "sp",
            "quantity": 6,
            "id_prefix": "TOM",
            "spacing_cm": 60,
            "row_spacing_cm": 80,
            "layout_strategy": LayoutStrategy.ROWS,
            **overrides,
        }
        return PlantingRunEntry(**data)

    def prepare(self, world, *entries: PlantingRunEntry) -> PreparedLayout | None:
        return world.service.prepare_layout(world.plan.locations["bed"], list(entries), tenant_key=TENANT)

    def test_six_positions_with_ids_geometry_and_sequence(self, world) -> None:
        """GP-ACC-019: six slots, ``slot_role = position``, ``sequence 1..6``."""
        prepared = self.prepare(world, self.entry())

        assert prepared is not None
        assert [p.sequence for p in prepared.slots] == [1, 2, 3, 4, 5, 6]
        assert {p.slot.slot_role for p in prepared.slots} == {SlotRole.POSITION}
        assert {p.slot.geometry_source.value for p in prepared.slots} == {"layout"}
        # the bed already holds BED3_001..003: the new ids continue after them
        assert [p.slot.slot_id for p in prepared.slots] == [f"BED3_{n:03d}" for n in range(4, 10)]
        assert all(p.slot.geometry is not None and p.slot.geometry.kind.value == "point" for p in prepared.slots)

    def test_a_zone_entry_makes_one_zone_slot_with_the_capacity_of_the_layout(self, world) -> None:
        prepared = self.prepare(
            world, self.entry(layout_strategy=LayoutStrategy.ZONE, spacing_cm=10, row_spacing_cm=10, quantity=500)
        )

        (item,) = prepared.slots
        assert item.slot.slot_role is SlotRole.ZONE
        # more than the 20 a position slot holds: the capacity of an area slot is the plants the layout fits
        assert item.slot.capacity_plants == 500

    def test_a_bed_without_geometry_or_an_entry_without_layout_plans_nothing(self, world) -> None:
        assert (
            world.service.prepare_layout(
                world.plan.locations["bed"], [self.entry(layout_strategy=None)], tenant_key=TENANT
            )
            is None
        )
        assert (
            world.service.prepare_layout(
                world.plan.locations["bed"], [self.entry(layout_strategy=LayoutStrategy.FREE)], tenant_key=TENANT
            )
            is None
        )
        world.plan.locations["bed"] = make_location("bed", name="Bed 3")
        assert self.prepare(world, self.entry()) is None

    def test_a_zone_may_not_overlap_a_zone_that_is_live_in_the_bed(self, world) -> None:
        from app.domain.models.geometry import PolygonGeometry

        world.plan.slots.append(
            Slot(
                _key="z1",
                slot_id="BED3_ZONE",
                location_key="bed",
                slot_role=SlotRole.ZONE,
                geometry=PolygonGeometry(points=((0.0, 0.0), (4.0, 0.0), (4.0, 2.0), (0.0, 2.0))),
            )
        )
        zone = self.entry(layout_strategy=LayoutStrategy.ZONE, spacing_cm=20, row_spacing_cm=20, quantity=10)

        with pytest.raises(PlanValidationError) as caught:
            self.prepare(world, zone)
        assert "slot.overlap" in caught.value.codes

    def test_an_archived_zone_does_not_count(self, world) -> None:
        from app.domain.models.geometry import PolygonGeometry

        world.plan.slots.append(
            Slot(
                _key="z1",
                slot_id="BED3_ZONE",
                location_key="bed",
                slot_role=SlotRole.ZONE,
                geometry=PolygonGeometry(points=((0.0, 0.0), (4.0, 0.0), (4.0, 2.0), (0.0, 2.0))),
                archived_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        zone = self.entry(layout_strategy=LayoutStrategy.ZONE, spacing_cm=20, row_spacing_cm=20, quantity=10)

        assert self.prepare(world, zone) is not None  # GP-ACC-040: archived slots block neither V-06 nor V-08

    def test_the_bed_quota_refuses_a_layout_that_does_not_fit(self, world) -> None:
        for n in range(2_000):
            world.plan.slots.append(Slot(_key=f"x{n}", slot_id=f"BED3_X{n}", location_key="bed"))

        with pytest.raises(PlanError) as caught:
            self.prepare(world, self.entry())
        assert (caught.value.error_code, caught.value.details[0]["limit"]) == ("plan.quota_exceeded", 2000)

    def test_a_layout_is_placed_for_the_stored_run_and_entries(self, world) -> None:
        run = make_run("run_new", planned_start_date=D(2026, 5, 15), planned_until=D(2026, 9, 30))
        run.tenant_key = TENANT
        entry = self.entry().model_copy(update={"key": "e_new"})
        prepared = self.prepare(world, entry)

        keys = world.service.place_layout(world.plan.locations["bed"], run, [entry], prepared, tenant_key=TENANT)

        (write,) = world.repo.layout_writes
        assert (write.run_key, write.planned_from, write.planned_until) == ("run_new", D(2026, 5, 15), D(2026, 9, 30))
        assert len(keys) == len(write.slots) == 6
        assert {s.entry_key for s in write.slots} == {"e_new"}
        assert {s.planned_species_key for s in write.slots} == {"sp"}

    def test_a_layout_is_not_placed_for_a_run_of_another_tenant(self, world) -> None:
        run = make_run("run_new").model_copy(update={"tenant_key": OTHER_TENANT})
        entry = self.entry().model_copy(update={"key": "e_new"})
        prepared = self.prepare(world, entry)

        with pytest.raises(NotFoundError):
            world.service.place_layout(world.plan.locations["bed"], run, [entry], prepared, tenant_key=TENANT)

        assert world.repo.layout_writes == []
