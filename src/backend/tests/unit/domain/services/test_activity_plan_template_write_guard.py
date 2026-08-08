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

Since #1003 the last of those writes **forks**: the shared generated plan stays
a template and the write lands on a private copy owned by the caller. The #992
assertion that it stays writable is unchanged and still here — that is the #324
half — with the landing site asserted alongside it. The end-to-end semantics of
the fork live in ``tests/api/test_activity_plan_copy_on_write.py``.
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
COPIED_WORKFLOW = "wf-plan-copy"
UNGENERATED_SHARED_WORKFLOW = "wf-shared-but-not-a-plan"
SPECIES_KEY = "solanum_lycopersicum"

WORKFLOWS: dict[str, WorkflowTemplate] = {
    OWN_WORKFLOW: WorkflowTemplate(_key=OWN_WORKFLOW, tenant_key=TENANT_KEY, name="Eigener Workflow"),
    FOREIGN_WORKFLOW: WorkflowTemplate(_key=FOREIGN_WORKFLOW, tenant_key=FOREIGN_TENANT_KEY, name="Fremd"),
    SYSTEM_WORKFLOW: WorkflowTemplate(_key=SYSTEM_WORKFLOW, tenant_key="", name="Tomato Standard", is_system=True),
    GLOBAL_PLAN_WORKFLOW: WorkflowTemplate(
        _key=GLOBAL_PLAN_WORKFLOW,
        tenant_key="",
        name="Tomate",
        auto_generated=True,
        species_key=SPECIES_KEY,
    ),
}


def _service(template: TaskTemplate | None = None) -> tuple[TaskService, MagicMock]:
    """A repo double that can actually *fork*, not only read (#1003).

    The copy-on-write path composes six repository calls (lookup, workflow
    create, phase read/create, template read/create), so a double that answers
    the read and shrugs at the writes would let the fork "succeed" without
    producing anything. This one keeps a small store instead, which is what makes
    "the write landed on a different row" assertable rather than assumed.

    ``get_task_templates_for_workflow`` hands out **deep copies** on purpose: the
    copier mutates what it is given (``key = None``, re-pointed parent), and a
    double returning the stored objects would let it rewrite the source it is
    supposed to be copying — the fixture would then agree with a broken copier.
    """
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
    templates: dict[str, TaskTemplate] = {template.key or "tt-1": template} if template else {}

    def _create_workflow(workflow: WorkflowTemplate) -> WorkflowTemplate:
        workflow.key = COPIED_WORKFLOW
        return workflow

    def _create_template(created: TaskTemplate) -> TaskTemplate:
        created.key = f"tt-copy-{len(templates)}"
        templates[created.key] = created
        return created

    repo.get_workflow_template_by_key.side_effect = lambda key: WORKFLOWS.get(key)
    repo.get_task_template_by_key.side_effect = templates.get
    repo.update_task_template.side_effect = lambda key, tt: tt
    repo.delete_task_template.return_value = True
    # No private copy exists yet: the first write of the test is the fork.
    repo.get_auto_generated_workflow_for_species.return_value = None
    repo.create_workflow_template.side_effect = _create_workflow
    repo.create_task_template.side_effect = _create_template
    repo.get_phases_for_workflow.return_value = []
    repo.get_task_templates_for_workflow.side_effect = lambda wf_key: [
        tt.model_copy(deep=True) for tt in templates.values() if tt.workflow_template_key == wf_key
    ]
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
        """Every plan the generator persists is global — a strict filter would kill the feature.

        **Changed for #1003, on purpose.** This assertion was written for #992 to
        pin that such a plan stays writable, and it still is: the write succeeds
        and carries the caller's value. What #1003 changed is *where* it lands,
        so that is now asserted too — on a row in the caller's own copy, never on
        the shared one, which is the whole of #1003 in one line.
        """
        service, repo = _service(_template(GLOBAL_PLAN_WORKFLOW))

        updated = service.update_activity_plan_task_template("tt-1", {"days_offset": 9}, tenant_key=TENANT_KEY)

        assert updated.days_offset == 9
        repo.update_task_template.assert_called_once()
        assert repo.update_task_template.call_args.args[0] != "tt-1"
        assert updated.workflow_template_key == COPIED_WORKFLOW
        assert updated.source_template_key == "tt-1"

    def test_the_fork_leaves_the_shared_plan_alone(self) -> None:
        """The copy is the caller's, and nothing about the source is rewritten."""
        source = _template(GLOBAL_PLAN_WORKFLOW)
        service, repo = _service(source)

        service.update_activity_plan_task_template("tt-1", {"days_offset": 9}, tenant_key=TENANT_KEY)

        copy = repo.create_workflow_template.call_args.args[0]
        assert (copy.tenant_key, copy.auto_generated, copy.is_system) == (TENANT_KEY, True, False)
        assert copy.source_workflow_key == GLOBAL_PLAN_WORKFLOW
        assert copy.species_key == SPECIES_KEY
        assert (source.days_offset, source.workflow_template_key) == (3, GLOBAL_PLAN_WORKFLOW)

    def test_a_delete_forks_too_and_removes_the_copied_row(self) -> None:
        """Copy-then-delete, not refusal: removing an activity is what the editor is for."""
        service, repo = _service(_template(GLOBAL_PLAN_WORKFLOW))

        assert service.delete_activity_plan_task_template("tt-1", tenant_key=TENANT_KEY) is True

        repo.create_workflow_template.assert_called_once()
        repo.delete_task_template.assert_called_once()
        assert repo.delete_task_template.call_args.args[0] != "tt-1"

    def test_a_shared_workflow_that_is_not_a_generated_plan_cannot_be_forked(self) -> None:
        """It would be forked into a copy no lookup can find — refused loudly instead."""
        WORKFLOWS[UNGENERATED_SHARED_WORKFLOW] = WorkflowTemplate(
            _key=UNGENERATED_SHARED_WORKFLOW,
            tenant_key="",
            name="Ownerless",
        )
        try:
            service, repo = _service(_template(UNGENERATED_SHARED_WORKFLOW))

            with pytest.raises(NotFoundError):
                service.update_activity_plan_task_template("tt-1", {"enabled": False}, tenant_key=TENANT_KEY)

            repo.update_task_template.assert_not_called()
            repo.create_workflow_template.assert_not_called()
        finally:
            del WORKFLOWS[UNGENERATED_SHARED_WORKFLOW]

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
