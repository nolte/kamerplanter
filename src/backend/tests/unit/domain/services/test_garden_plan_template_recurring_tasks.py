"""REQ-053 GP-FR-087 (#2897) - the recurring tasks a bed template brings, created when the template is placed.

Operator decision 2026-11-11: placing a bed from a template creates its recurring tasks **directly** (RRULE,
ADR-008), as an **opt-in** at placing time. Pinned here against the real ``GardenPlanService`` and ``TaskService``
over hand-written doubles: without the opt-in nothing is created; with it one yearly task per task template lands
on the new bed; a task template of another tenant (or an absent one) refuses the placement before the bed is
written; a failed task write leaves the committed bed standing and says so.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest

from app.common.enums import TaskOrigin, TaskStatus, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanValidationError
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.engines.recurrence_engine import RecurrenceEngine
from app.domain.models.bed_template import BedTemplate
from app.domain.models.site import SitePlan
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.task_service import TaskService
from tests.support.bed_template_fakes import FakeTemplates
from tests.support.garden_plan_fakes import OTHER_TENANT, SITE, TENANT, USER, FakePlanRepo, FakeSites, make_site
from tests.support.template_task_fakes import TemplateTaskRepo, task_template

_RECT_2X1 = {"kind": "rect", "origin": [0, 0], "width_m": 2, "length_m": 1, "rotation_deg": 0}


def _bed_template(key: str, tenant: str | None, task_keys: list[str]) -> BedTemplate:
    return BedTemplate(
        _key=key,
        tenant_key=tenant,
        name="Raised bed",
        location_type_key="raised_bed",
        default_geometry=_RECT_2X1,
        recurring_task_templates=task_keys,
    )


class World:
    def __init__(self) -> None:
        site = make_site()
        site.plan = SitePlan(
            boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0},
            plan_revision=5,
        )
        self.sites = FakeSites(site)
        self.repo = FakePlanRepo(self.sites)
        self.task_repo = TemplateTaskRepo(
            task_template("tt_refill", "", name="Refill soil", activity_key="act_soil"),
            task_template("tt_own", TENANT, name="Cover for winter", days_offset=30),
            task_template("tt_theirs", OTHER_TENANT, name="Their task"),
        )
        self.templates = FakeTemplates()
        self.templates.task_templates = {"tt_refill": "", "tt_own": TENANT, "tt_theirs": OTHER_TENANT}
        self.templates.add(_bed_template("own", TENANT, ["tt_refill", "tt_own"]))
        self.templates.add(_bed_template("sys_raised", None, ["tt_refill"]))
        self.templates.add(_bed_template("bare", TENANT, []))
        self.tasks = TaskService(self.task_repo, HSTValidator(), DependencyResolver())
        self.plans = GardenPlanService(self.sites, self.repo, template_repo=self.templates, tasks=lambda: self.tasks)

    def place(self, template: str = "own", **overrides: Any):
        arguments: dict[str, Any] = {
            "tenant_key": TENANT,
            "user_key": USER,
            "role": TenantRole.GROWER,
            "template_key": template,
            "origin": (4.0, 1.0),
            "rotation_deg": 0.0,
            "expected_revision": 5,
        } | overrides
        return self.plans.place_template(SITE, **arguments)


@pytest.fixture
def world() -> World:
    return World()


class TestOptIn:
    def test_without_the_opt_in_no_task_is_created(self, world: World) -> None:
        result = world.place()

        assert len(world.repo.applied) == 1  # the bed is placed
        assert world.task_repo.created == [] and world.task_repo.atomic_batches == []
        assert (result.created_task_keys, result.recurring_tasks_failed) == ([], False)

    def test_with_the_opt_in_one_yearly_task_per_task_template_lands_on_the_new_bed(self, world: World) -> None:
        before = datetime.now(UTC)
        result = world.place(create_recurring_tasks=True)
        after = datetime.now(UTC)

        bed_key = result.key_map["template_bed"]
        assert world.task_repo.atomic_batches == [2]  # one transaction for both tasks
        by_template = {task.template_key: task for task in world.task_repo.created}
        assert set(by_template) == {"tt_refill", "tt_own"}
        assert result.created_task_keys == [task.key for task in world.task_repo.created]
        for key, offset in (("tt_refill", 0), ("tt_own", 30)):
            task = by_template[key]
            assert (task.entity_type, task.entity_key, task.tenant_key) == ("location", bed_key, TENANT)
            assert (task.status, task.origin, task.suggested) == (TaskStatus.PENDING, TaskOrigin.USER, False)
            assert task.due_date is not None
            assert before + timedelta(days=offset) <= task.due_date <= after + timedelta(days=offset)
            due = task.due_date.date()
            assert task.recurrence_rule == f"FREQ=YEARLY;BYMONTH={due.month};BYMONTHDAY={due.day}"
        assert by_template["tt_refill"].name == "Refill soil"
        assert world.task_repo.activity_edges == [(by_template["tt_refill"].key, "act_soil")]

    def test_a_system_template_brings_its_global_task_templates(self, world: World) -> None:
        result = world.place("sys_raised", create_recurring_tasks=True)

        (task,) = world.task_repo.created
        assert (task.template_key, task.tenant_key, task.entity_key) == (
            "tt_refill",
            TENANT,
            result.key_map["template_bed"],
        )

    def test_a_template_without_task_templates_creates_nothing_with_the_opt_in(self, world: World) -> None:
        result = world.place("bare", create_recurring_tasks=True)

        assert len(world.repo.applied) == 1
        assert world.task_repo.atomic_batches == [] and result.created_task_keys == []


class TestRefusals:
    @pytest.mark.parametrize("foreign", ["tt_theirs", "tt_absent"])
    def test_a_foreign_or_absent_task_template_refuses_before_the_bed_is_written(
        self, world: World, foreign: str
    ) -> None:
        world.templates.add(_bed_template("own", TENANT, ["tt_refill", foreign]))

        with pytest.raises(PlanValidationError) as refused:
            world.place(create_recurring_tasks=True)

        assert refused.value.codes == ["reference.not_found"]
        assert refused.value.details[0]["field"] == "recurring_task_templates[1]"
        assert world.repo.applied == [] and world.task_repo.created == []

    def test_without_the_opt_in_a_stale_task_template_key_does_not_block_the_bed(self, world: World) -> None:
        world.templates.add(_bed_template("own", TENANT, ["tt_absent"]))

        world.place()

        assert len(world.repo.applied) == 1 and world.task_repo.created == []

    def test_a_viewer_is_refused_before_any_task_template_is_read(self, world: World) -> None:
        with pytest.raises(ForbiddenError):
            world.place(role=TenantRole.VIEWER, create_recurring_tasks=True)

        assert world.repo.applied == [] and world.task_repo.created == []

    def test_a_failed_task_write_leaves_the_bed_and_reports_it(self, world: World) -> None:
        world.task_repo.fail_atomic = True

        result = world.place(create_recurring_tasks=True)

        assert len(world.repo.applied) == 1 and result.key_map["template_bed"]
        assert (result.created_task_keys, result.recurring_tasks_failed) == ([], True)
        assert world.task_repo.created == []


class TestTheTaskPath:
    def test_a_task_template_of_another_tenant_is_a_404_and_nothing_is_written(self, world: World) -> None:
        with pytest.raises(NotFoundError):
            world.tasks.create_recurring_tasks_for_bed(["tt_refill", "tt_theirs"], bed_key="bed", tenant_key=TENANT)

        assert world.task_repo.created == []

    def test_a_repeated_key_creates_one_task(self, world: World) -> None:
        created = world.tasks.create_recurring_tasks_for_bed(
            ["tt_refill", "tt_refill"], bed_key="bed", tenant_key=TENANT
        )

        assert [task.template_key for task in created] == ["tt_refill"]

    def test_an_empty_tenant_is_refused(self, world: World) -> None:
        with pytest.raises(ValueError, match="tenant_key"):
            world.tasks.create_recurring_tasks_for_bed(["tt_refill"], bed_key="bed", tenant_key="")


class TestTheYearlyRule:
    def test_the_rule_pins_month_and_day_and_the_next_occurrence_is_a_year_on(self) -> None:
        rule = RecurrenceEngine.yearly_rule_on(date(2026, 3, 1))

        assert rule == "FREQ=YEARLY;BYMONTH=3;BYMONTHDAY=1"
        # completed late, on 20 March: the next one is still 1 March, a year on
        completed = datetime(2026, 3, 20, 9, 0, tzinfo=UTC)
        assert RecurrenceEngine.next_occurrence(rule, completed) == datetime(2027, 3, 1, 9, 0, tzinfo=UTC)

    def test_29_february_is_pinned_to_the_28th(self) -> None:
        rule = RecurrenceEngine.yearly_rule_on(date(2028, 2, 29))

        assert rule == "FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=28"
        next_due = RecurrenceEngine.next_occurrence(rule, datetime(2028, 3, 1, tzinfo=UTC))
        assert next_due == datetime(2029, 2, 28, tzinfo=UTC)
