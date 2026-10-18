"""REQ-053 WP 4.2 (#2412) — tasks on beds: the queue by location and the "for every plant" fan-out (GP-FR-080/081).

Against hand-written doubles (a mock would answer every call and certify nothing, #1155). What the service decides:
which locations a bed queue spans, that a foreign bed is a 404 and never an empty queue, which tasks one fan-out
clones and links, and that every refusal writes nothing. The AQL of the location queue is measured against ArangoDB
in ``tests/integration/test_task_location_queue.py``.
"""

from __future__ import annotations

import pytest

from app.common.enums import TaskStatus
from app.common.exceptions import NotFoundError, ValidationError
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.services.care_event_service import CareEventService
from app.domain.services.task_service import MAX_FAN_OUT, TaskService
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
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)
from tests.support.task_completion_fakes import FakeCompletionRepo, FakeTaskRepo, bed_task


@pytest.fixture
def world():
    sites = FakeSites(make_site(), make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed")
    plan.locations["bed_child"] = make_location("bed_child", name="Row", parent_location_key="bed")
    plan.locations["bed_other"] = make_location("bed_other", name="Other bed")
    plan.locations["loc_foreign"] = make_location("loc_foreign", name="Foreign").model_copy(
        update={"site_key": "site_foreign"}
    )
    plants = {
        "pi_here": (TENANT, "bed"),
        "pi_child": (TENANT, "bed_child"),
        "pi_elsewhere": (TENANT, "bed_other"),
        "pi_foreign": (OTHER_TENANT, "bed"),
    }
    care_repo = FakeCareEventRepo()
    care_repo.plants = dict(plants)
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    tasks = FakeTaskRepo(
        bed_task("t_bed"),
        bed_task("t_child", entity_key="bed_child"),
        bed_task("t_other", entity_key="bed_other"),
        bed_task("t_here", entity_type="plant_instance", entity_key="pi_here"),
        bed_task("t_elsewhere", entity_type="plant_instance", entity_key="pi_elsewhere"),
        bed_task("t_done", status=TaskStatus.COMPLETED),
        bed_task("t_foreign", tenant_key=OTHER_TENANT),
        bed_task("t_run", entity_type="planting_run", entity_key="run_1"),
    )
    tasks.plants = dict(plants)
    completion = FakeCompletionRepo(tasks, plants)
    service = TaskService(tasks, HSTValidator(), DependencyResolver(), completion=completion, care_events=care)
    return service, tasks


def queue(service, **kwargs):
    return sorted(t.key for t in service.get_task_queue(tenant_key=TENANT, **kwargs))


class TestQueueByLocation:
    def test_the_bed_with_its_children_and_the_plants_standing_in_them(self, world):
        service, _ = world

        assert queue(service, location_key="bed") == ["t_bed", "t_child", "t_here"]

    def test_without_children_only_the_bed_itself_and_its_own_plants(self, world):
        service, _ = world

        assert queue(service, location_key="bed", include_children=False) == ["t_bed", "t_here"]

    def test_a_child_bed_does_not_pull_in_its_parent(self, world):
        service, _ = world

        assert queue(service, location_key="bed_child") == ["t_child"]

    def test_other_beds_completed_tasks_and_run_tasks_stay_out(self, world):
        service, _ = world

        found = queue(service, location_key="bed")

        assert not {"t_other", "t_elsewhere", "t_done", "t_run"} & set(found)

    def test_a_foreign_tenants_task_on_the_same_bed_key_never_appears(self, world):
        service, _ = world

        assert "t_foreign" not in queue(service, location_key="bed")

    def test_a_foreign_bed_is_a_404_not_an_empty_queue(self, world):
        service, _ = world

        with pytest.raises(NotFoundError):
            queue(service, location_key="loc_foreign")

    def test_an_unknown_bed_is_the_same_404(self, world):
        service, _ = world

        with pytest.raises(NotFoundError):
            queue(service, location_key="nope")

    def test_the_foreign_tenant_reads_the_bed_as_a_404_too(self, world):
        service, _ = world

        with pytest.raises(NotFoundError):
            service.get_task_queue(tenant_key=OTHER_TENANT, location_key="bed")

    def test_a_plant_and_a_bed_together_are_refused(self, world):
        service, _ = world

        with pytest.raises(ValidationError):
            queue(service, location_key="bed", plant_key="pi_here")

    def test_the_category_narrows_the_query(self, world):
        service, _ = world

        assert queue(service, location_key="bed", category="harvest") == []


class TestFanOutToPlants:
    def test_one_clone_per_plant_of_the_bed_and_its_children(self, world):
        service, tasks = world

        clones = service.fan_out_to_plants("t_bed", tenant_key=TENANT)

        assert sorted(c.entity_key for c in clones) == ["pi_child", "pi_here"]
        assert {c.entity_type for c in clones} == {"plant_instance"}
        assert {c.status for c in clones} == {TaskStatus.PENDING}

    def test_every_clone_is_linked_back_to_its_source(self, world):
        service, tasks = world

        clones = service.fan_out_to_plants("t_bed", tenant_key=TENANT)

        assert sorted(tasks.cloned_from) == sorted((c.key, "t_bed") for c in clones)

    def test_the_bed_task_is_skipped_instead_of_staying_a_duplicate(self, world):
        service, tasks = world

        service.fan_out_to_plants("t_bed", tenant_key=TENANT)

        assert tasks.store["t_bed"].status == TaskStatus.SKIPPED

    def test_keep_source_leaves_the_bed_task_open(self, world):
        service, tasks = world

        service.fan_out_to_plants("t_bed", tenant_key=TENANT, keep_source=True)

        assert tasks.store["t_bed"].status == TaskStatus.PENDING

    def test_without_children_only_the_beds_own_plants(self, world):
        service, _ = world

        clones = service.fan_out_to_plants("t_bed", tenant_key=TENANT, include_children=False)

        assert [c.entity_key for c in clones] == ["pi_here"]

    def test_a_bed_without_plants_clones_nothing_and_keeps_the_task_open(self, world):
        service, tasks = world
        tasks.store["t_empty"] = bed_task("t_empty", entity_key="bed_other").model_copy(
            update={"entity_key": "bed_other"}
        )
        tasks.plants.clear()
        service._completion.plants.clear()

        assert service.fan_out_to_plants("t_empty", tenant_key=TENANT) == []
        assert tasks.store["t_empty"].status == TaskStatus.PENDING
        assert tasks.created == []

    def test_a_foreign_plant_standing_on_the_bed_key_is_not_cloned_onto(self, world):
        service, _ = world

        keys = [c.entity_key for c in service.fan_out_to_plants("t_bed", tenant_key=TENANT)]

        assert "pi_foreign" not in keys

    def test_a_foreign_task_is_a_404_and_writes_nothing(self, world):
        service, tasks = world

        with pytest.raises(NotFoundError):
            service.fan_out_to_plants("t_foreign", tenant_key=TENANT)

        assert tasks.created == [] and tasks.cloned_from == []

    @pytest.mark.parametrize("key", ["t_here", "t_run"])
    def test_only_a_bed_task_can_be_fanned_out(self, world, key):
        service, tasks = world

        with pytest.raises(ValidationError):
            service.fan_out_to_plants(key, tenant_key=TENANT)

        assert tasks.created == []

    def test_a_finished_task_cannot_be_fanned_out(self, world):
        service, tasks = world

        with pytest.raises(ValidationError):
            service.fan_out_to_plants("t_done", tenant_key=TENANT)

        assert tasks.created == []

    def test_a_task_bound_to_a_foreign_bed_is_a_404(self, world):
        service, tasks = world
        tasks.store["t_gone"] = bed_task("t_gone", entity_key="loc_foreign")

        with pytest.raises(NotFoundError):
            service.fan_out_to_plants("t_gone", tenant_key=TENANT)

        assert tasks.created == []

    def test_a_bed_past_the_cap_is_refused_before_anything_is_written(self, world):
        service, tasks = world
        service._completion.plants = {f"pi_{i}": (TENANT, "bed") for i in range(MAX_FAN_OUT + 1)}

        with pytest.raises(ValidationError):
            service.fan_out_to_plants("t_bed", tenant_key=TENANT)

        assert tasks.created == []

    def test_a_retry_after_a_failure_part_way_clones_only_the_missing_plants(self, world):
        service, tasks = world
        first = service.fan_out_to_plants("t_bed", tenant_key=TENANT, keep_source=True)
        assert len(first) == 2
        tasks.store["t_bed"] = tasks.store["t_bed"].model_copy(update={"status": TaskStatus.PENDING})
        service._completion.plants["pi_new"] = (TENANT, "bed")

        retry = service.fan_out_to_plants("t_bed", tenant_key=TENANT)

        assert [c.entity_key for c in retry] == ["pi_new"]
        assert tasks.store["t_bed"].status == TaskStatus.SKIPPED

    def test_a_care_reminder_is_not_fanned_out(self, world):
        service, tasks = world
        tasks.store["t_care"] = bed_task("t_care", "care_reminder")

        with pytest.raises(ValidationError):
            service.fan_out_to_plants("t_care", tenant_key=TENANT)

        assert tasks.created == []

    def test_the_tenant_cannot_be_left_empty(self, world):
        service, _ = world

        with pytest.raises(ValueError, match="tenant_key"):
            service.fan_out_to_plants("t_bed", tenant_key="")


class TestCloneWritesTheEdge:
    def test_a_plain_clone_is_linked_to_its_source_too(self, world):
        service, tasks = world

        clone = service.clone_task("t_bed", tenant_key=TENANT)

        assert tasks.cloned_from == [(clone.key, "t_bed")]
