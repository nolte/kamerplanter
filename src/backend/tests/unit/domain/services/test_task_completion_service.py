"""REQ-053 WP 4.3 (#2413) — the atomic completion transition of a task, at the service (GP-FR-083/088/149).

What the service decides, against hand-written doubles of the repository (a mock would answer every call and
certify nothing, #1155): which task is a bed task, what care event and specialist document one completion writes,
that every refusal leaves nothing written, that a batch is all-or-nothing with a 404 for the whole batch on a foreign
key, and that the undo predicate is the one of ``POST /care-events/{key}/void``. The transaction itself — that the
task, the event and the document really are one commit — is measured against ArangoDB in
``tests/integration/test_task_completion_repository.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import TaskCategory, TaskStatus, TenantRole
from app.common.exceptions import (
    ForbiddenError,
    KarenzViolationError,
    NotFoundError,
    PlanError,
    PlanValidationError,
    ValidationError,
)
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.models.care_event import CareEvent
from app.domain.models.task import Task
from app.domain.models.task_completion import CompletionActor, TaskCompletionDetails
from app.domain.services.care_event_service import CareEventService
from app.domain.services.task_service import TaskService
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
from tests.support.task_completion_fakes import FakeCompletionRepo, FakeHarvests, FakeTaskRepo, bed_task

GROWER = CompletionActor(user_key=USER, role=TenantRole.GROWER)
LEAD = CompletionActor(user_key="u_lead", role=TenantRole.LEAD)
BED_AREA = 2.5


@pytest.fixture
def world():
    site = make_site()
    sites = FakeSites(site, make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed", geometry=rect(1, 1, 2, 1)).model_copy(
        update={"area_m2": BED_AREA}
    )
    plan.locations["bed_child"] = make_location("bed_child", name="Row", parent_location_key="bed")
    plan.locations["bed_other"] = make_location("bed_other", name="Other bed")
    foreign = make_location("loc_foreign", name="Foreign").model_copy(update={"site_key": "site_foreign"})
    plan.locations["loc_foreign"] = foreign
    care_repo = FakeCareEventRepo()
    plants = {
        "pi_here": (TENANT, "bed"),
        "pi_child": (TENANT, "bed_child"),
        "pi_elsewhere": (TENANT, "bed_other"),
        "pi_foreign": (OTHER_TENANT, "bed"),
    }
    care_repo.plants = dict(plants)
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    tasks = FakeTaskRepo(
        bed_task("t1"),
        bed_task("t2"),
        bed_task("t_plant", entity_type="plant_instance", entity_key="pi_here"),
        bed_task("t_run", entity_type="planting_run", entity_key="run_1"),
        bed_task("t_reminder", TaskCategory.CARE_REMINDER, entity_type="plant_instance", entity_key="pi_here"),
        bed_task("t_gone", entity_key="loc_foreign"),
        bed_task("t_done", status=TaskStatus.COMPLETED),
        bed_task("t_foreign", tenant_key=OTHER_TENANT),
        bed_task("t_feed", TaskCategory.FEEDING),
        bed_task("t_harvest", TaskCategory.HARVEST),
    )
    completion = FakeCompletionRepo(tasks, plants)
    harvests = FakeHarvests()
    service = TaskService(
        tasks,
        HSTValidator(),
        DependencyResolver(),
        completion=completion,
        care_events=care,
        harvests=harvests,
        fertilizers=FakeFertilizers(),
    )
    return service, tasks, completion, care_repo, harvests


def complete(service, key="t1", *, actor=GROWER, tenant=TENANT, **details):
    return service.complete_task(
        key,
        tenant_key=tenant,
        details=TaskCompletionDetails(**details) if details else None,
        actor=actor,
    )


class TestOneTransition:
    def test_a_bed_task_is_closed_and_logged_in_one_write(self, world):
        service, tasks, completion, *_ = world

        completed = complete(service, "t1")

        assert completed.status == TaskStatus.COMPLETED
        assert completion.calls == 1
        (write,) = completion.completed
        assert write.task_key == "t1"
        assert write.task_patch["status"] == "completed"
        event = write.event
        assert event is not None
        assert (event.trigger, event.task_key, event.category, event.location_key) == ("task", "t1", "watering", "bed")
        assert (event.tenant_key, event.performed_by_user_key, event.created_by) == (TENANT, USER, USER)
        assert event.summary == "Bed 3"
        assert write.domain is None

    def test_a_plant_task_is_logged_in_the_bed_the_plant_stands_in(self, world):
        service, _, completion, *_ = world

        complete(service, "t_plant")

        assert completion.completed[0].event.location_key == "bed"

    def test_the_performer_is_the_token_never_the_body(self, world):
        service, _, completion, *_ = world

        complete(service, "t1", actor=CompletionActor(user_key="u_tom", role=TenantRole.GROWER))

        event = completion.completed[0].event
        assert (event.performed_by_user_key, event.created_by) == ("u_tom", "u_tom")

    def test_the_care_fields_reach_the_event(self, world):
        service, _, completion, *_ = world

        complete(
            service,
            "t1",
            plant_keys=["pi_here"],
            reason="Dry week",
            quantity=8,
            unit="l",
            observed_outcome="soaked in",
            outcome_rating="positive",
        )

        event = completion.completed[0].event
        assert event.plant_keys == ["pi_here"]
        assert (event.reason, event.quantity, event.unit) == ("Dry week", 8, "l")
        assert (event.observed_outcome, event.outcome_rating) == ("soaked in", "positive")

    def test_the_completion_note_is_the_outcome_text_when_the_client_gave_none(self, world):
        service, _, completion, *_ = world

        service.complete_task("t1", "went fine", tenant_key=TENANT, actor=GROWER)

        assert completion.completed[0].event.observed_outcome == "went fine"

    def test_performed_at_is_the_completion_instant(self, world):
        service, _, completion, *_ = world
        when = datetime.now(UTC) - timedelta(days=3)

        complete(service, "t1", performed_at=when)

        assert completion.completed[0].event.performed_at == when
        assert completion.completed[0].task_patch["completed_at"].startswith(when.strftime("%Y-%m-%dT%H:%M"))

    def test_a_task_without_a_bed_closes_alone(self, world):
        service, _, completion, *_ = world

        complete(service, "t_run")

        assert completion.completed[0].event is None
        assert completion.completed[0].domain is None

    def test_a_care_reminder_is_not_logged_twice(self, world):
        # GP-FR-106: the reminder confirmation is the line of that strand.
        service, _, completion, *_ = world

        complete(service, "t_reminder")

        assert completion.completed[0].event is None

    def test_a_caller_without_an_actor_closes_the_task_alone(self, world):
        service, _, completion, *_ = world

        service.complete_task("t1", tenant_key=TENANT)

        assert completion.completed[0].event is None

    def test_a_service_built_without_the_transition_keeps_the_plain_update(self):
        tasks = FakeTaskRepo(bed_task("t1"))
        service = TaskService(tasks, HSTValidator(), DependencyResolver())

        completed = service.complete_task("t1", tenant_key=TENANT, actor=GROWER)

        assert completed.status == TaskStatus.COMPLETED

    def test_a_bed_that_is_gone_does_not_keep_the_task_open(self, world):
        service, _, completion, *_ = world

        complete(service, "t_gone")

        assert completion.completed[0].event is None

    def test_a_bed_that_is_gone_cannot_take_care_fields(self, world):
        service, tasks, completion, *_ = world

        with pytest.raises(NotFoundError):
            complete(service, "t_gone", plant_keys=["pi_here"])
        assert completion.completed == [] and tasks.store["t_gone"].status == TaskStatus.PENDING


class TestSpecialistDocuments:
    def test_a_feeding_writes_one_feeding_event_with_the_area_dose_total(self, world):
        # GP-ACC-024: 2 l/m² of fertilizer X on p1, p2 → quantity_total = 2 × area_m2, one document, event → document.
        service, _, completion, *_ = world

        complete(
            service,
            "t_feed",
            product_ref={"kind": "fertilizer", "key": "fert_global"},
            quantity=2,
            unit="l_per_m2",
            plant_keys=["pi_here", "pi_child"],
        )

        write = completion.completed[0]
        assert write.event.quantity_total == 2 * BED_AREA
        assert write.event.quantity_total_unit == "l"
        assert write.domain.collection == "feeding_events"
        assert write.domain.document["quantity_total"] == 2 * BED_AREA
        assert write.domain.document["plant_keys"] == ["pi_here", "pi_child"]

    def test_a_whole_bed_dose_is_attributed_to_the_plants_standing_in_the_bed(self, world):
        service, _, completion, *_ = world

        complete(service, "t1", quantity=6, unit="l")

        domain = completion.completed[0].domain
        assert domain.collection == "watering_events"
        assert domain.document["plant_keys"] == ["pi_child", "pi_here"]  # the bed and the row below it, not the rest
        assert completion.completed[0].event.plant_keys == []  # the care event itself says "whole bed"

    def test_a_harvest_passes_the_karenz_gate_and_gets_a_batch_id(self, world):
        service, _, completion, _, harvests = world

        complete(service, "t_harvest", quantity=2, unit="kg", plant_keys=["pi_here"])

        domain = completion.completed[0].domain
        assert domain.collection == "harvest_batches"
        assert domain.document["batch_id"] == "HARVEST-pi_here-1"
        assert harvests.checked == [["pi_here"]]

    def test_a_karenz_violation_refuses_the_whole_completion(self, world):
        service, tasks, completion, _, harvests = world
        harvests.refuse = True

        with pytest.raises(KarenzViolationError):
            complete(service, "t_harvest", quantity=2, unit="kg", plant_keys=["pi_here"])

        assert completion.completed == [] and tasks.store["t_harvest"].status == TaskStatus.PENDING

    def test_a_failure_in_the_transaction_leaves_the_task_pending(self, world):
        # The service hands the whole write to ONE repository call; whatever fails there leaves the task as it was
        # (the real transaction is measured in the integration tier).
        service, tasks, completion, *_ = world
        completion.fail_with = RuntimeError("feeding_event insert failed")

        with pytest.raises(RuntimeError):
            complete(service, "t_feed", quantity=1, unit="l", product_ref={"kind": "fertilizer", "key": "fert_global"})

        assert tasks.store["t_feed"].status == TaskStatus.PENDING


class TestRefusalsWriteNothing:
    def test_performed_at_in_the_future_is_422(self, world):
        # GP-ACC-025
        service, tasks, completion, *_ = world

        with pytest.raises(PlanError) as exc:
            complete(service, "t1", performed_at=datetime.now(UTC) + timedelta(minutes=10))

        assert exc.value.details[0]["code"] == "care_event.performed_in_future"
        assert completion.calls == 0 and tasks.store["t1"].status == TaskStatus.PENDING

    def test_performed_at_400_days_back_is_422(self, world):
        service, _, completion, *_ = world

        with pytest.raises(PlanError) as exc:
            complete(service, "t1", performed_at=datetime.now(UTC) - timedelta(days=400))

        assert exc.value.details[0]["code"] == "care_event.too_old"
        assert completion.calls == 0

    @pytest.mark.parametrize("offset", [timedelta(minutes=10), -timedelta(days=400)])
    def test_the_window_holds_a_task_outside_the_care_log_too(self, world, offset):
        service, _, completion, *_ = world

        with pytest.raises(PlanError):
            complete(service, "t_run", performed_at=datetime.now(UTC) + offset)

        assert completion.calls == 0

    def test_a_plant_outside_the_bed_is_422_reference_not_found(self, world):
        service, tasks, completion, *_ = world

        with pytest.raises(PlanValidationError) as exc:
            complete(service, "t1", plant_keys=["pi_elsewhere"])

        assert exc.value.codes == ["reference.not_found"]
        assert completion.calls == 0 and tasks.store["t1"].status == TaskStatus.PENDING

    def test_another_tenants_plant_is_refused_alike(self, world):
        service, _, completion, *_ = world

        with pytest.raises(PlanValidationError) as exc:
            complete(service, "t1", plant_keys=["pi_foreign"])

        assert exc.value.codes == ["reference.not_found"]
        assert completion.calls == 0

    def test_care_fields_on_a_task_without_a_bed_are_422(self, world):
        service, _, completion, *_ = world

        with pytest.raises(PlanError) as exc:
            complete(service, "t_run", quantity=2, unit="l")

        assert exc.value.details[0]["code"] == "task.no_bed_context"
        assert completion.calls == 0

    def test_measurements_on_a_watering_are_422(self, world):
        service, _, completion, *_ = world

        with pytest.raises(ValidationError):
            complete(service, "t1", measurements=[{"parameter": "ph", "value": 6.5, "unit": "pH"}])

        assert completion.calls == 0

    def test_a_task_that_is_not_open_cannot_be_completed(self, world):
        service, *_ = world

        with pytest.raises(ValidationError):
            complete(service, "t_done")

    def test_another_tenants_task_is_404_and_untouched(self, world):
        # Cross-tenant negative: a foreign key answers like an absent one and nothing is written.
        service, tasks, completion, *_ = world

        with pytest.raises(NotFoundError):
            complete(service, "t_foreign")

        assert completion.calls == 0 and tasks.store["t_foreign"].status == TaskStatus.PENDING

    def test_a_viewer_cannot_log_care(self, world):
        service, _, completion, *_ = world

        with pytest.raises(ForbiddenError):
            complete(service, "t1", actor=CompletionActor(user_key=USER, role=TenantRole.VIEWER))

        assert completion.calls == 0


class TestBatch:
    def test_every_task_gets_its_own_event_in_one_transaction(self, world):
        service, _, completion, *_ = world

        succeeded, failed = service.batch_status_change(
            ["t1", "t2"],
            "complete",
            tenant_key=TENANT,
            details=TaskCompletionDetails(quantity=5, unit="l"),
            actor=GROWER,
        )

        assert succeeded == ["t1", "t2"] and failed == []
        assert completion.calls == 1
        assert [w.event.task_key for w in completion.completed] == ["t1", "t2"]

    def test_a_foreign_key_is_404_for_the_whole_batch(self, world):
        service, tasks, completion, *_ = world

        with pytest.raises(NotFoundError):
            service.batch_status_change(["t1", "t_foreign"], "complete", tenant_key=TENANT, actor=GROWER)

        assert completion.calls == 0
        assert tasks.store["t1"].status == TaskStatus.PENDING  # the caller's own task is not completed either

    def test_an_unknown_key_is_the_same_404(self, world):
        service, _, completion, *_ = world

        with pytest.raises(NotFoundError):
            service.batch_status_change(["t1", "nope"], "complete", tenant_key=TENANT, actor=GROWER)

        assert completion.calls == 0

    def test_a_task_that_is_not_open_is_reported_and_the_rest_completes(self, world):
        service, _, completion, *_ = world

        succeeded, failed = service.batch_status_change(["t1", "t_done"], "complete", tenant_key=TENANT, actor=GROWER)

        assert succeeded == ["t1"]
        assert [item["key"] for item in failed] == ["t_done"]
        assert completion.calls == 1

    def test_more_than_200_tasks_are_refused_before_anything_is_read(self, world):
        service, _, completion, *_ = world

        with pytest.raises(ValidationError):
            service.batch_status_change([f"t{i}" for i in range(201)], "complete", tenant_key=TENANT, actor=GROWER)

        assert completion.calls == 0

    def test_two_harvest_batches_of_one_write_get_different_ids(self, world):
        service, tasks, completion, *_ = world
        tasks.store["t_h2"] = bed_task("t_h2", TaskCategory.HARVEST)

        service.batch_status_change(
            ["t_harvest", "t_h2"],
            "complete",
            tenant_key=TENANT,
            details=TaskCompletionDetails(quantity=1, unit="kg", plant_keys=["pi_here"]),
            actor=GROWER,
        )

        ids = [w.domain.document["batch_id"] for w in completion.completed]
        assert len(set(ids)) == 2

    def test_a_harvest_inside_its_karenz_is_reported_and_the_rest_completes(self, world):
        service, tasks, completion, _, harvests = world
        harvests.refuse = True

        succeeded, failed = service.batch_status_change(
            ["t1", "t_harvest"],
            "complete",
            tenant_key=TENANT,
            details=TaskCompletionDetails(quantity=1, unit="kg", plant_keys=["pi_here"]),
            actor=GROWER,
        )

        assert succeeded == ["t1"]
        assert [item["key"] for item in failed] == ["t_harvest"]
        assert tasks.store["t_harvest"].status == TaskStatus.PENDING

    def test_care_fields_belong_to_complete_only(self, world):
        service, _, completion, *_ = world

        with pytest.raises(ValidationError):
            service.batch_status_change(
                ["t1"], "skip", tenant_key=TENANT, details=TaskCompletionDetails(plant_keys=["pi_here"]), actor=GROWER
            )
        with pytest.raises(ValidationError):
            service.batch_status_change(
                ["t1"],
                "start",
                tenant_key=TENANT,
                details=TaskCompletionDetails(performed_at=datetime.now(UTC)),
                actor=GROWER,
            )

        assert completion.calls == 0

    def test_a_follow_up_that_fails_after_the_commit_does_not_turn_the_batch_into_an_error(self, world):
        # The transaction is committed; the next-occurrence spawn of task 1 raising must not hide that both are done.
        service, tasks, completion, *_ = world
        tasks.store["t1"] = tasks.store["t1"].model_copy(update={"recurrence_rule": "FREQ=DAILY"})

        def boom(_task):
            raise RuntimeError("spawn failed")

        service._create_next_recurring_task = boom  # noqa: SLF001 — the follow-up under test

        succeeded, failed = service.batch_status_change(["t1", "t2"], "complete", tenant_key=TENANT, actor=GROWER)

        assert succeeded == ["t1", "t2"] and failed == []
        assert len(completion.completed) == 2

    def test_a_duplicated_key_completes_once(self, world):
        service, _, completion, *_ = world

        succeeded, _ = service.batch_status_change(["t1", "t1"], "complete", tenant_key=TENANT, actor=GROWER)

        assert succeeded == ["t1"] and len(completion.completed) == 1


class TestReCompletion:
    """A task reopened without an undo and completed again: the earlier line is replaced only by who could void it."""

    @pytest.fixture
    def reopened(self, world):
        service, tasks, completion, *_ = world
        completion.open_event = CareEvent(
            _key="ce_old",
            tenant_key=TENANT,
            site_key="site_1",
            location_key="bed",
            category="watering",
            summary="x",
            performed_at=datetime.now(UTC) - timedelta(days=1),
            trigger="task",
            task_key="t1",
            created_by=USER,
            created_at=datetime.now(UTC) - timedelta(days=1),
        )
        return service, completion

    def test_the_author_replaces_their_own_line(self, reopened):
        service, completion = reopened

        complete(service, "t1", actor=GROWER)

        assert completion.completed[0].replaces_event_key == "ce_old"

    def test_a_lead_replaces_any_line(self, reopened):
        service, completion = reopened

        complete(service, "t1", actor=LEAD)

        assert completion.completed[0].replaces_event_key == "ce_old"

    def test_another_grower_adds_a_line_and_leaves_the_authors_alone(self, reopened):
        service, completion = reopened

        complete(service, "t1", actor=CompletionActor(user_key="u_tom", role=TenantRole.GROWER))

        assert completion.completed[0].replaces_event_key is None

    def test_a_first_completion_replaces_nothing(self, world):
        service, _, completion, *_ = world

        complete(service, "t1")

        assert completion.completed[0].replaces_event_key is None


class TestUndo:
    @pytest.fixture
    def completed(self, world):
        service, tasks, completion, *_ = world
        tasks.store["t1"] = tasks.store["t1"].model_copy(update={"status": TaskStatus.COMPLETED})
        completion.open_event = CareEvent(
            _key="ce_1",
            tenant_key=TENANT,
            site_key="site_1",
            location_key="bed",
            category="watering",
            summary="x",
            performed_at=datetime.now(UTC),
            trigger="task",
            task_key="t1",
            created_by=USER,
            created_at=datetime.now(UTC) - timedelta(seconds=30),
        )
        return service, tasks, completion

    def test_the_author_takes_the_completion_back_in_one_write(self, completed):
        service, tasks, completion = completed

        reopened = service.reopen_task("t1", tenant_key=TENANT, undo=True, actor=GROWER)

        assert reopened.status == TaskStatus.PENDING
        (write,) = completion.reopened
        assert (write.event_key, write.void_reason, write.voided_by) == ("ce_1", "undo", USER)
        assert write.task_patch["status"] == "pending"
        assert write.task_patch["completed_at"] is None

    def test_another_grower_cannot_undo_someone_elses_line(self, completed):
        service, tasks, completion = completed

        with pytest.raises(ForbiddenError):
            service.reopen_task("t1", tenant_key=TENANT, undo=True, actor=CompletionActor("u_tom", TenantRole.GROWER))

        assert completion.reopened == [] and tasks.store["t1"].status == TaskStatus.COMPLETED

    def test_the_author_cannot_undo_after_ten_minutes(self, completed):
        service, _, completion = completed
        completion.open_event = completion.open_event.model_copy(
            update={"created_at": datetime.now(UTC) - timedelta(minutes=11)}
        )

        with pytest.raises(ForbiddenError):
            service.reopen_task("t1", tenant_key=TENANT, undo=True, actor=GROWER)

        assert completion.reopened == []

    def test_a_lead_undoes_any_line(self, completed):
        service, _, completion = completed
        completion.open_event = completion.open_event.model_copy(
            update={"created_at": datetime.now(UTC) - timedelta(days=2)}
        )

        service.reopen_task("t1", tenant_key=TENANT, undo=True, actor=LEAD)

        assert completion.reopened[0].event_key == "ce_1"

    def test_a_task_that_logged_nothing_is_just_reopened(self, completed):
        service, _, completion = completed
        completion.open_event = None

        service.reopen_task("t1", tenant_key=TENANT, undo=True, actor=GROWER)

        assert completion.reopened[0].event_key is None

    def test_a_plain_reopen_leaves_the_care_line_alone(self, completed):
        service, tasks, completion = completed

        service.reopen_task("t1", tenant_key=TENANT)

        assert completion.reopened == []
        assert tasks.store["t1"].status == TaskStatus.PENDING

    def test_undo_needs_the_actor(self, completed):
        service, *_ = completed

        with pytest.raises(ValueError, match="actor"):
            service.reopen_task("t1", tenant_key=TENANT, undo=True)

    def test_another_tenants_task_cannot_be_reopened(self, world):
        service, tasks, completion, *_ = world
        tasks.store["t_foreign"] = tasks.store["t_foreign"].model_copy(update={"status": TaskStatus.COMPLETED})

        with pytest.raises(NotFoundError):
            service.reopen_task("t_foreign", tenant_key=TENANT, undo=True, actor=GROWER)

        assert completion.reopened == []


class TestParkedRecurrence:
    """#2411 item 4: a new RRULE answers what the migration parked."""

    RULE = "FREQ=WEEKLY;BYDAY=MO"

    def service(self, task: Task) -> tuple[TaskService, FakeTaskRepo]:
        repo = FakeTaskRepo(task)
        return TaskService(repo, HSTValidator(), DependencyResolver()), repo

    def test_setting_a_new_rule_clears_the_parked_value(self):
        task = bed_task("t1")
        service, repo = self.service(task)
        edited = task.model_copy(update={"recurrence_rule": self.RULE})

        service.update_task("t1", edited, previous=task)

        assert repo.cleared_parked == ["t1"]

    def test_an_edit_that_leaves_the_rule_alone_does_not_touch_it(self):
        task = bed_task("t1", recurrence_rule=self.RULE)
        service, repo = self.service(task)

        service.update_task("t1", task.model_copy(update={"name": "Renamed"}), previous=task)

        assert repo.cleared_parked == []

    def test_clearing_the_rule_does_not_clear_the_parked_value(self):
        task = bed_task("t1", recurrence_rule=self.RULE)
        service, repo = self.service(task)

        service.update_task("t1", task.model_copy(update={"recurrence_rule": None}), previous=task)

        assert repo.cleared_parked == []
