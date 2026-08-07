"""The activity-plan task-template writes, at the service boundary (#992).

The router half is pinned end to end in
``tests/api/test_activity_plan_template_tenant_scope.py``. This file pins the
service contract the router now depends on, which the old API-layer code had no
equivalent of at all — it went straight to the repository with the document key
as the entire authorisation.

``TaskTemplate`` carries no ``tenant_key``, so the predicate hangs on the parent
``WorkflowTemplate``. Both directions are pinned, because a predicate on the
wrong anchor matches nothing and refuses everybody while looking like a working
guard: a foreign parent answers **404, never 403** (no cross-tenant oracle), a
system workflow answers **422** ("you may read this, you may not write it"), a
parentless template answers 404 — and the caller's own workflow *and* the global
auto-generated activity plan (``tenant_key == ""``, ``is_system == False``, what
``ActivityPlanService`` actually persists) both still write.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.task import TaskTemplate, WorkflowTemplate
from app.domain.services.task_service import TaskService
from tests.conftest import wire_or_raise

TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_WORKFLOW = "wf-a1"
FOREIGN_WORKFLOW = "wf-b1"
SYSTEM_WORKFLOW = "wf-sys"
GLOBAL_PLAN_WORKFLOW = "wf-plan"

WORKFLOWS: dict[str, WorkflowTemplate] = {
    OWN_WORKFLOW: WorkflowTemplate(_key=OWN_WORKFLOW, tenant_key=TENANT_KEY, name="Eigener Workflow"),
    FOREIGN_WORKFLOW: WorkflowTemplate(_key=FOREIGN_WORKFLOW, tenant_key=FOREIGN_TENANT_KEY, name="Fremd"),
    SYSTEM_WORKFLOW: WorkflowTemplate(_key=SYSTEM_WORKFLOW, tenant_key="", name="Tomato Standard", is_system=True),
    GLOBAL_PLAN_WORKFLOW: WorkflowTemplate(
        _key=GLOBAL_PLAN_WORKFLOW,
        tenant_key="",
        name="Tomate",
        auto_generated=True,
    ),
}


def _service(template: TaskTemplate | None = None) -> tuple[TaskService, MagicMock]:
    repo = MagicMock()
    wire_or_raise(
        repo,
        "WorkflowTemplate",
        by_key="get_workflow_template_by_key",
        or_raise="get_workflow_template_or_raise",
    )
    wire_or_raise(
        repo,
        "TaskTemplate",
        by_key="get_task_template_by_key",
        or_raise="get_task_template_or_raise",
    )
    repo.get_workflow_template_by_key.side_effect = lambda key: WORKFLOWS.get(key)
    repo.get_task_template_by_key.return_value = template
    repo.update_task_template.side_effect = lambda key, tt: tt
    repo.delete_task_template.return_value = True
    return TaskService(repo, MagicMock(), MagicMock()), repo


def _template(parent: str | None) -> TaskTemplate:
    return TaskTemplate(
        _key="tt-1",
        name="Giessen",
        enabled=True,
        days_offset=3,
        workflow_template_key=parent,
    )


class TestAForeignTenantsTemplate:
    def test_update_is_not_found_and_writes_nothing(self) -> None:
        service, repo = _service(_template(FOREIGN_WORKFLOW))

        with pytest.raises(NotFoundError):
            service.update_activity_plan_task_template("tt-1", {"enabled": False}, tenant_key=TENANT_KEY)

        repo.update_task_template.assert_not_called()

    def test_delete_is_not_found_and_removes_nothing(self) -> None:
        service, repo = _service(_template(FOREIGN_WORKFLOW))

        with pytest.raises(NotFoundError):
            service.delete_activity_plan_task_template("tt-1", tenant_key=TENANT_KEY)

        repo.delete_task_template.assert_not_called()

    def test_an_unknown_parent_looks_exactly_the_same(self) -> None:
        """No oracle: 'belongs to another tenant' and 'does not exist' are one answer."""
        foreign_service, _ = _service(_template(FOREIGN_WORKFLOW))
        unknown_service, _ = _service(_template("does-not-exist"))

        with pytest.raises(NotFoundError) as foreign:
            foreign_service.update_activity_plan_task_template("tt-1", {"enabled": False}, tenant_key=TENANT_KEY)
        with pytest.raises(NotFoundError) as unknown:
            unknown_service.update_activity_plan_task_template("tt-1", {"enabled": False}, tenant_key=TENANT_KEY)

        assert foreign.value.status_code == unknown.value.status_code == 404
        assert foreign.value.error_code == unknown.value.error_code


class TestASystemWorkflowsTemplate:
    def test_update_is_refused_with_422_and_writes_nothing(self) -> None:
        service, repo = _service(_template(SYSTEM_WORKFLOW))

        with pytest.raises(ValidationError) as refusal:
            service.update_activity_plan_task_template("tt-1", {"enabled": False}, tenant_key=TENANT_KEY)

        assert refusal.value.status_code == 422
        repo.update_task_template.assert_not_called()

    def test_delete_is_refused_with_422_and_removes_nothing(self) -> None:
        service, repo = _service(_template(SYSTEM_WORKFLOW))

        with pytest.raises(ValidationError) as refusal:
            service.delete_activity_plan_task_template("tt-1", tenant_key=TENANT_KEY)

        assert refusal.value.status_code == 422
        repo.delete_task_template.assert_not_called()


class TestATemplateWithNoParentWorkflowIsRefused:
    """The parentless decision, stated in the class name.

    ``ActivityPlanService.generate_plan`` sets ``workflow_template_key`` on every
    template it persists, so this state is unreachable from the legitimate flow —
    and it has no owner, so on a write route "no anchor, so no refusal" would
    mean "writable by anyone". Refused with the 404 rather than a 422 because the
    ownership question has no answer to report and a 422 would confirm the key.
    """

    def test_update_is_not_found_and_writes_nothing(self) -> None:
        service, repo = _service(_template(None))

        with pytest.raises(NotFoundError) as refusal:
            service.update_activity_plan_task_template("tt-1", {"enabled": False}, tenant_key=TENANT_KEY)

        assert refusal.value.status_code == 404
        repo.update_task_template.assert_not_called()

    def test_delete_is_not_found_and_removes_nothing(self) -> None:
        service, repo = _service(_template(None))

        with pytest.raises(NotFoundError):
            service.delete_activity_plan_task_template("tt-1", tenant_key=TENANT_KEY)

        repo.delete_task_template.assert_not_called()


class TestTheEditorItselfStillWorks:
    """#324: the guard must not pass its negatives by refusing everyone."""

    def test_the_callers_own_template_is_still_updatable(self) -> None:
        service, repo = _service(_template(OWN_WORKFLOW))

        updated = service.update_activity_plan_task_template("tt-1", {"enabled": False}, tenant_key=TENANT_KEY)

        assert updated.enabled is False
        repo.update_task_template.assert_called_once()

    def test_the_callers_own_template_is_still_deletable(self) -> None:
        service, repo = _service(_template(OWN_WORKFLOW))

        assert service.delete_activity_plan_task_template("tt-1", tenant_key=TENANT_KEY) is True
        repo.delete_task_template.assert_called_once_with("tt-1")

    def test_a_globally_generated_activity_plans_template_is_still_writable(self) -> None:
        """Every plan the generator persists is global — a strict filter would kill the feature."""
        service, repo = _service(_template(GLOBAL_PLAN_WORKFLOW))

        updated = service.update_activity_plan_task_template("tt-1", {"days_offset": 9}, tenant_key=TENANT_KEY)

        assert updated.days_offset == 9
        repo.update_task_template.assert_called_once()

    def test_all_three_fields_the_editor_exposes_survive_the_allow_list(self) -> None:
        """``enabled`` is the activity-plan editor's main control and is not in the workflow editor's set."""
        service, _ = _service(_template(OWN_WORKFLOW))

        updated = service.update_activity_plan_task_template(
            "tt-1",
            {"enabled": False, "days_offset": 12, "trigger_phase": "flowering"},
            tenant_key=TENANT_KEY,
        )

        assert (updated.enabled, updated.days_offset, updated.trigger_phase) == (False, 12, "flowering")


class TestTheAllowListStillBoundsTheWrite:
    def test_the_body_cannot_re_point_the_template_into_another_workflow(self) -> None:
        """``workflow_template_key`` is not in the editor's set — the anchor cannot be moved."""
        service, _ = _service(_template(OWN_WORKFLOW))

        updated = service.update_activity_plan_task_template(
            "tt-1",
            {"enabled": False, "workflow_template_key": FOREIGN_WORKFLOW},
            tenant_key=TENANT_KEY,
        )

        assert updated.workflow_template_key == OWN_WORKFLOW
