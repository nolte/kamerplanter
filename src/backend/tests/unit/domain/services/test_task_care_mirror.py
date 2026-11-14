"""#2960 - every path that completes or skips a care-reminder task mirrors it into the plant's care state.

The mirror (``CareReminderService.record_care_task_completion`` / ``record_care_task_skip``: confirmation, care
event, next occurrence) used to run in the single-task route only, so ``POST /tasks/batch/status`` closed a care
reminder without a confirmation and the schedule never advanced. It now runs in :class:`TaskService`, the one place
the single completion, the batch, a replay and both skips go through. Pinned here against the hand-written
repository doubles of the completion tests; the care-state behaviour behind the mirror is pinned with the real
``CareReminderService`` in ``tests/unit/api/test_task_complete_care_followup.py``.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.common.enums import TaskCategory, TaskStatus, TenantRole
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.models.client_event import batch_item_client_event_id
from app.domain.models.task import Task
from app.domain.models.task_completion import CompletionActor
from app.domain.services.care_event_service import CareEventService
from app.domain.services.task_service import TaskService
from tests.support.care_event_fakes import (
    FakeAttachmentRepo,
    FakeAttachmentService,
    FakeCareEventRepo,
    FakeFertilizers,
    FakeMemberships,
)
from tests.support.garden_plan_fakes import TENANT, USER, FakePlanRepo, FakeSites, make_location, make_site
from tests.support.task_completion_fakes import FakeCompletionRepo, FakeHarvests, FakeTaskRepo, bed_task

GROWER = CompletionActor(user_key=USER, role=TenantRole.GROWER)


class RecordingMirror:
    """Records every bridge call; ``fail_next`` makes the next completion mirror raise (a crashed process)."""

    def __init__(self) -> None:
        self.completions: list[tuple[str, str, str, str | None]] = []
        self.skips: list[tuple[str, str]] = []
        self.fail_next = False

    def record_care_task_completion(self, task, *, tenant_key, user_key, completion_client_event_id=None):
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("the process died between the commit and the mirror")
        self.completions.append((task.key, tenant_key, user_key, completion_client_event_id))

    def record_care_task_skip(self, task, *, tenant_key):
        self.skips.append((task.key, tenant_key))


def _reminder(key: str) -> Task:
    return bed_task(key, TaskCategory.CARE_REMINDER, entity_type="plant_instance", entity_key="pi_here")


@pytest.fixture
def world():
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed")
    plants = {"pi_here": (TENANT, "bed")}
    care_repo = FakeCareEventRepo()
    care_repo.plants = dict(plants)
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    tasks = FakeTaskRepo(_reminder("r1"), _reminder("r2"), bed_task("plain"), bed_task("plain2"))
    mirror = RecordingMirror()
    built: list[int] = []

    def factory() -> RecordingMirror:
        built.append(1)
        return mirror

    service = TaskService(
        tasks,
        HSTValidator(),
        DependencyResolver(),
        completion=FakeCompletionRepo(tasks, plants),
        care_events=care,
        harvests=FakeHarvests(),
        fertilizers=FakeFertilizers(),
        care_mirror=factory,
    )
    return service, tasks, mirror, built


class TestCompletion:
    def test_the_single_completion_mirrors_a_care_reminder_with_the_caller_as_performer(self, world):
        service, _tasks, mirror, _built = world

        service.complete_task_once("r1", tenant_key=TENANT, client_event_id=None, actor=GROWER)

        assert mirror.completions == [("r1", TENANT, USER, None)]

    def test_the_batch_mirrors_every_care_reminder_it_completes_and_nothing_else(self, world):
        service, _tasks, mirror, built = world

        succeeded, failed = service.batch_status_change(
            ["r1", "plain", "r2"], "complete", tenant_key=TENANT, actor=GROWER
        )

        assert (sorted(succeeded), failed) == (["plain", "r1", "r2"], [])
        assert sorted(mirror.completions) == [("r1", TENANT, USER, None), ("r2", TENANT, USER, None)]
        assert len(built) == 2  # built for the two reminders only, never for the plain task

    def test_a_buffered_batch_mirrors_each_task_with_its_own_derived_id(self, world):
        service, _tasks, mirror, _built = world
        batch_id = uuid4()

        service.batch_status_change(["r1", "r2"], "complete", tenant_key=TENANT, actor=GROWER, client_event_id=batch_id)

        assert sorted(mirror.completions) == [
            ("r1", TENANT, USER, batch_item_client_event_id(batch_id, "r1")),
            ("r2", TENANT, USER, batch_item_client_event_id(batch_id, "r2")),
        ]

    def test_a_failing_mirror_of_one_batch_task_does_not_fail_the_batch_or_starve_the_rest(self, world):
        service, tasks, mirror, _built = world
        mirror.fail_next = True

        succeeded, _failed = service.batch_status_change(["r1", "r2"], "complete", tenant_key=TENANT, actor=GROWER)

        assert sorted(succeeded) == ["r1", "r2"]
        assert {tasks.store[k].status for k in ("r1", "r2")} == {TaskStatus.COMPLETED}
        assert len(mirror.completions) == 1  # the second task was still mirrored

    def test_a_plain_task_and_a_completion_without_a_caller_mirror_nothing(self, world):
        service, _tasks, mirror, built = world

        service.complete_task_once("plain", tenant_key=TENANT, client_event_id=None, actor=GROWER)
        service.complete_task_once("r1", tenant_key=TENANT, client_event_id=None, actor=None)

        assert mirror.completions == []
        assert built == []


class TestReplay:
    def test_a_replay_runs_the_mirror_a_crashed_first_attempt_lost(self, world):
        service, tasks, mirror, _built = world
        client_id = uuid4()
        mirror.fail_next = True

        with pytest.raises(RuntimeError):
            service.complete_task_once("r1", tenant_key=TENANT, client_event_id=client_id, actor=GROWER)
        assert tasks.store["r1"].status == TaskStatus.COMPLETED  # committed before the mirror died
        assert mirror.completions == []

        outcome = service.complete_task_once("r1", tenant_key=TENANT, client_event_id=client_id, actor=GROWER)

        assert outcome.replayed
        # the same id each time: the care service dedups the confirmation per id
        assert mirror.completions == [("r1", TENANT, USER, str(client_id))]

    def test_a_replay_of_a_reopened_task_mirrors_nothing(self, world):
        service, tasks, mirror, _built = world
        client_id = uuid4()
        service.complete_task_once("r1", tenant_key=TENANT, client_event_id=client_id, actor=GROWER)
        tasks.store["r1"] = tasks.store["r1"].model_copy(update={"status": TaskStatus.PENDING})
        mirror.completions.clear()

        outcome = service.complete_task_once("r1", tenant_key=TENANT, client_event_id=client_id, actor=GROWER)

        assert outcome.replayed
        assert mirror.completions == []

    def test_a_replayed_batch_task_is_mirrored_again_with_its_id(self, world):
        service, _tasks, mirror, _built = world
        batch_id = uuid4()
        service.batch_status_change(["r1"], "complete", tenant_key=TENANT, actor=GROWER, client_event_id=batch_id)

        succeeded, _ = service.batch_status_change(
            ["r1"], "complete", tenant_key=TENANT, actor=GROWER, client_event_id=batch_id
        )

        assert succeeded == ["r1"]
        expected = ("r1", TENANT, USER, batch_item_client_event_id(batch_id, "r1"))
        assert mirror.completions == [expected, expected]


class TestSkip:
    def test_the_single_skip_and_the_batch_skip_both_mirror_a_care_reminder(self, world):
        service, _tasks, mirror, _built = world

        service.skip_task("r1", tenant_key=TENANT)
        succeeded, failed = service.batch_status_change(["r2", "plain"], "skip", tenant_key=TENANT)

        assert (sorted(succeeded), failed) == (["plain", "r2"], [])
        assert mirror.skips == [("r1", TENANT), ("r2", TENANT)]
