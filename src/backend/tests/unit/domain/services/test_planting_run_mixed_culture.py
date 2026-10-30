"""#2463 — ``PlantingRunService.create_mixed_culture``: the per-species runs of a mixed culture in **one** write.

Pinned: one repository write for all runs (nothing is stored run by run, so there is nothing to take back), every
refusal leaves nothing behind, one slot-id sequence across the species, hand-set points reserved with the run,
and the tenant rules (a foreign bed is 404, a viewer is 403, the tenant is the caller's, never the body's).
"""

from __future__ import annotations

from datetime import date

import pytest

from app.common.enums import LayoutStrategy, PlanRole, PlantingRunStatus, PlantingRunType, SlotRole, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.domain.models.planting_reservation import MixedRunDraft
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT
from tests.support.planting_reservation_fakes import build_world

D = date
GROWER = TenantRole.GROWER


@pytest.fixture
def world():
    return build_world()


def draft(species: str = "sp_tomato", *, rows: list[int] | None = None, name: str = "Run", **entry_overrides):
    entry = {
        "species_key": species,
        "quantity": 4,
        "id_prefix": "TOM",
        "spacing_cm": 50,
        "row_spacing_cm": 80,
        "layout_strategy": LayoutStrategy.ROWS,
        "row_assignment": rows,
        **entry_overrides,
    }
    run = PlantingRun(
        name=name,
        run_type=PlantingRunType.MONOCULTURE,
        location_key="bed",
        planned_start_date=D(2026, 5, 20),
        rotation_override_reason="shared reason",
    )
    return MixedRunDraft(run=run, entry=PlantingRunEntry(**entry))


def create(world, drafts, *, location="bed", tenant=TENANT, role=GROWER):
    return world.service.create_mixed_culture(location, drafts, tenant_key=tenant, role=role)


class TestOneTransaction:
    def test_all_runs_reach_the_repository_in_one_write(self, world) -> None:
        runs = create(world, [draft(rows=[0], name="Tomato"), draft("sp_phacelia", rows=[1], name="Phacelia")])

        (write,) = world.repo.mixed_writes
        assert [item.run.name for item in write.runs] == ["Tomato", "Phacelia"]
        assert [run.name for run in runs] == ["Tomato", "Phacelia"]
        # nothing went through the one-run-at-a-time path whose rollback needs the lead role
        assert world.repo.layout_writes == [] and world.runs.deleted == []

    def test_the_runs_are_planned_monocultures_of_the_callers_tenant_on_the_bed(self, world) -> None:
        create(world, [draft(), draft("sp_phacelia", name="Phacelia")])

        (write,) = world.repo.mixed_writes
        for item in write.runs:
            assert item.run.status is PlantingRunStatus.PLANNED
            assert item.run.run_type is PlantingRunType.MONOCULTURE
            assert (item.run.tenant_key, item.entry.tenant_key, item.run.location_key) == (TENANT, TENANT, "bed")
            assert item.run.planned_quantity == item.entry.quantity
            assert item.planned_from == D(2026, 5, 20)

    def test_the_tenant_of_the_body_is_never_trusted(self, world) -> None:
        forged = draft()
        forged.run.tenant_key = OTHER_TENANT

        create(world, [forged])

        assert world.repo.mixed_writes[0].runs[0].run.tenant_key == TENANT

    def test_every_species_gets_its_own_slots_with_one_id_sequence(self, world) -> None:
        create(world, [draft(rows=[0]), draft("sp_phacelia", rows=[1], id_prefix="PHA")])

        (write,) = world.repo.mixed_writes
        first, second = write.runs
        ids = [s.slot.slot_id for s in first.slots] + [s.slot.slot_id for s in second.slots]
        assert len(ids) == len(set(ids)) == 8
        assert [s.sequence for s in first.slots] == [1, 2, 3, 4]
        assert [s.sequence for s in second.slots] == [1, 2, 3, 4]


class TestFreePoints:
    def test_hand_set_points_become_reserved_positions_of_the_run(self, world) -> None:
        item = draft(layout_strategy=LayoutStrategy.FREE, quantity=2, row_spacing_cm=None, spacing_cm=40)
        item = MixedRunDraft(
            run=item.run, entry=item.entry, free_points=((0.5, 0.5), (1.0, 0.8)), container_volume_l=12
        )

        create(world, [item])

        (write,) = world.repo.mixed_writes
        slots = write.runs[0].slots
        assert [s.sequence for s in slots] == [1, 2]
        assert {s.slot.slot_role for s in slots} == {SlotRole.POSITION}
        assert {s.slot.container_volume_l for s in slots} == {12}
        assert {s.slot.planned_spacing_cm for s in slots} == {40}

    def test_a_point_outside_the_bed_is_refused_and_nothing_is_written(self, world) -> None:
        item = draft(layout_strategy=LayoutStrategy.FREE, quantity=1, row_spacing_cm=None)
        item = MixedRunDraft(run=item.run, entry=item.entry, free_points=((50.0, 50.0),))

        with pytest.raises(PlanValidationError):
            create(world, [item])

        assert world.repo.mixed_writes == [] and world.runs.runs == {}

    def test_points_on_a_bed_without_a_frame_are_refused(self, world) -> None:
        item = draft(layout_strategy=LayoutStrategy.FREE, quantity=1, row_spacing_cm=None)
        item.run.location_key = "bed_nogeo"
        item = MixedRunDraft(run=item.run, entry=item.entry, free_points=((1.0, 1.0),))

        with pytest.raises(PlanValidationError):
            create(world, [item], location="bed_nogeo")

        assert world.repo.mixed_writes == []


class TestNonFinitePoints:
    def test_an_infinite_point_is_422_not_an_arithmetic_error(self, world) -> None:
        item = draft(layout_strategy=LayoutStrategy.FREE, quantity=1, row_spacing_cm=None)
        item = MixedRunDraft(run=item.run, entry=item.entry, free_points=((float("inf"), 1.0),))

        with pytest.raises(PlanValidationError):
            create(world, [item])

        assert world.repo.mixed_writes == []


class TestRefusalsLeaveNothingBehind:
    def test_a_layout_refusal_of_one_species_stores_none_of_the_runs(self, world) -> None:
        with pytest.raises(PlanError) as caught:
            create(world, [draft(), draft("sp_phacelia", spacing_cm=None)])

        assert caught.value.error_code == "layout.spacing_required"
        assert world.repo.mixed_writes == [] and world.runs.runs == {}

    def test_an_unreadable_species_stores_none_of_the_runs(self, world) -> None:
        with pytest.raises(PlanValidationError):
            create(world, [draft(), draft("sp_unknown")])

        assert world.repo.mixed_writes == [] and world.runs.runs == {}

    def test_a_failed_write_surfaces_and_nothing_else_is_attempted(self, world) -> None:
        def explode(write):
            raise RuntimeError("write conflict")

        world.repo.create_mixed_runs = explode

        with pytest.raises(RuntimeError):
            create(world, [draft(), draft("sp_phacelia")])

        assert world.runs.runs == {} and world.runs.deleted == []

    def test_green_manure_needs_a_species_suited_as_green_manure(self, world) -> None:
        item = draft()
        item.run.plan_role = PlanRole.GREEN_MANURE

        with pytest.raises(PlanError) as caught:
            create(world, [item])

        assert caught.value.error_code == "run.species_not_green_manure"
        assert world.repo.mixed_writes == []


class TestTenantRules:
    def test_another_tenants_bed_is_404_and_nothing_is_written(self, world) -> None:
        with pytest.raises(NotFoundError):
            create(world, [draft()], location="loc_foreign")

        assert world.repo.mixed_writes == [] and world.runs.runs == {}

    def test_an_empty_tenant_is_refused(self, world) -> None:
        with pytest.raises(ValueError):
            create(world, [draft()], tenant="")

        assert world.repo.mixed_writes == []

    def test_a_viewer_may_not_plant(self, world) -> None:
        with pytest.raises(ForbiddenError):
            create(world, [draft()], role=TenantRole.VIEWER)

        assert world.repo.mixed_writes == []


class TestRowAssignmentsAreDisjoint:
    """GP-ACC-054 / GP-FR-070: the ``row_assignment`` sets of the species of one mixed culture are disjoint.

    The bed ``bed`` is 4 m x 2 m; at a row spacing of 40 cm five rows fit (indices 0-4, 0-based like the API).
    """

    @staticmethod
    def five_row_draft(species: str, rows: list[int] | None, prefix: str, quantity: int = 24) -> MixedRunDraft:
        return draft(species, rows=rows, name=species, id_prefix=prefix, row_spacing_cm=40, quantity=quantity)

    def test_overlapping_sets_are_refused_before_anything_is_written(self, world) -> None:
        with pytest.raises(PlanError) as caught:
            create(world, [draft(rows=[1, 2]), draft("sp_phacelia", rows=[2, 3], id_prefix="PHA")])

        assert caught.value.status_code == 422
        assert caught.value.error_code == "layout.row_assignment_overlap"
        (detail,) = caught.value.details
        assert detail["field"] == "runs[1].entry.row_assignment"
        assert detail["conflicts"] == [{"runs": [0, 1], "rows": [2]}]
        assert world.repo.mixed_writes == [] and world.runs.runs == {} and world.plan.slots == []

    def test_every_overlapping_pair_is_named(self, world) -> None:
        with pytest.raises(PlanError) as caught:
            create(
                world,
                [
                    draft(rows=[0, 1]),
                    draft("sp_phacelia", rows=[2], id_prefix="PHA"),
                    draft("sp_tomato", rows=[1, 2, 4], id_prefix="TOB"),
                ],
            )

        assert caught.value.details[0]["conflicts"] == [{"runs": [0, 2], "rows": [1]}, {"runs": [1, 2], "rows": [2]}]
        assert caught.value.details[0]["field"] == "runs[2].entry.row_assignment"

    def test_disjoint_sets_are_planted(self, world) -> None:
        create(world, [draft(rows=[0]), draft("sp_phacelia", rows=[1], id_prefix="PHA")])

        assert len(world.repo.mixed_writes) == 1

    def test_entries_without_a_row_assignment_are_not_part_of_the_check(self, world) -> None:
        create(
            world,
            [
                draft(rows=[0, 1]),
                draft("sp_phacelia", rows=None, id_prefix="PHA", layout_strategy=LayoutStrategy.ZONE),
                draft("sp_tomato", rows=None, id_prefix="TOB", layout_strategy=None),
            ],
        )

        assert len(world.repo.mixed_writes) == 1

    def test_gp_acc_054_every_slot_of_a_row_carries_the_entry_the_row_is_assigned_to(self, world) -> None:
        """GP-ACC-054: tomato on rows 0/2/4 and basil on 1/3 of a five-row bed; each slot belongs to its row's entry."""
        create(
            world,
            [
                self.five_row_draft("sp_tomato", [0, 2, 4], "TOM"),
                self.five_row_draft("sp_phacelia", [1, 3], "PHA", quantity=16),
            ],
        )

        (write,) = world.repo.mixed_writes
        rows_of = {item.entry.species_key: sorted({s.slot.row_index for s in item.slots}) for item in write.runs}
        assert rows_of == {"sp_tomato": [0, 2, 4], "sp_phacelia": [1, 3]}
        owner_of_row = {s.slot.row_index: item.entry.species_key for item in write.runs for s in item.slots}
        assert owner_of_row == {0: "sp_tomato", 1: "sp_phacelia", 2: "sp_tomato", 3: "sp_phacelia", 4: "sp_tomato"}
        assert [len(item.slots) for item in write.runs] == [24, 16]
