""" "Cannot modify system workflow templates" extends to their children (#965 item 3).

``update_workflow_template`` and ``delete_workflow_template`` refuse a globally
seeded system template outright. One level down the rule stopped: the parent
reference added in #964 resolved through ``get_workflow_template``, whose read
access deliberately spans the hybrid catalog (``tenant_key == ""`` passes, the
#324 counter-example being a strict filter that hid the global catalogue). So a
tenant could attach a task template — or a phase — to "Tomato Standard", and
because ``get_task_templates_for_workflow`` filters on the denormalised parent
field, that child then appeared for **every** tenant and in every task their
next instantiation generated. The codebase contradicted a rule it already
enforced one level up.

The refusal deliberately does **not** collapse into the 404 a foreign or unknown
key produces. Those two are one answer on purpose (no cross-tenant oracle), but a
system workflow is a third case: it exists, the caller may read it, they simply
may not write into it. That is exactly the case the parent's own guard already
answers with ``ValidationError`` (HTTP 422, ``VALIDATION_ERROR``), so the child
guard raises the same thing rather than inventing a convention.

Both directions are pinned. The strict direction must not eat the legitimate
uses of a system workflow that the UI depends on — reading it, duplicating it
into an owned copy, instantiating it — nor the tenant's own workflows, which
still accept children.

The rule covers a child that is *already* inside a system workflow, not only one
being attached: editing a seeded task template in place, or deleting it, is the
same modification arriving by a different verb. That half needs no anchor
decision — the parent is read off the child's own ``workflow_template_key`` and
only its ``is_system`` flag is consulted, never the caller's tenant. What stays
deliberately open is #965 item 1, the *foreign-tenant* half of the same two
routes: a template belonging to another tenant's workflow is still reachable,
because closing that needs the orphan-ownership field and backfill rather than a
guard bolted onto the delete path. Two tests below pin that boundary so this file
cannot be misread as having closed item 1.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.task import TaskTemplate, WorkflowPhase, WorkflowTemplate
from app.domain.services.task_service import TaskService
from tests.conftest import wire_or_raise

TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_WORKFLOW = "wf-a1"
FOREIGN_WORKFLOW = "wf-b1"
SYSTEM_WORKFLOW = "wf-sys"

WORKFLOWS: dict[str, WorkflowTemplate] = {
    OWN_WORKFLOW: WorkflowTemplate(_key=OWN_WORKFLOW, tenant_key=TENANT_KEY, name="Eigener Workflow"),
    FOREIGN_WORKFLOW: WorkflowTemplate(_key=FOREIGN_WORKFLOW, tenant_key=FOREIGN_TENANT_KEY, name="Fremd"),
    SYSTEM_WORKFLOW: WorkflowTemplate(_key=SYSTEM_WORKFLOW, tenant_key="", name="Tomato Standard", is_system=True),
}

PHASES: dict[str, WorkflowPhase] = {
    "ph-own": WorkflowPhase(_key="ph-own", workflow_template_key=OWN_WORKFLOW, name="Vegetativ"),
    "ph-sys": WorkflowPhase(_key="ph-sys", workflow_template_key=SYSTEM_WORKFLOW, name="Vegetativ"),
    "ph-orphan": WorkflowPhase(_key="ph-orphan", workflow_template_key="", name="Ohne Workflow"),
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
    wire_or_raise(repo, "WorkflowPhase", by_key="get_phase_by_key", or_raise="get_phase_or_raise")
    repo.get_workflow_template_by_key.side_effect = lambda key: WORKFLOWS.get(key)
    repo.get_phase_by_key.side_effect = lambda key: PHASES.get(key)
    repo.get_task_template_by_key.return_value = template
    repo.create_task_template.side_effect = lambda tt: tt
    repo.update_task_template.side_effect = lambda key, tt: tt
    repo.create_phase.side_effect = lambda phase: phase
    repo.update_phase.side_effect = lambda key, phase: phase
    repo.delete_phase.return_value = True
    return TaskService(repo, MagicMock(), MagicMock()), repo


def _template(**overrides) -> TaskTemplate:
    return TaskTemplate(_key="tt-1", name="Giessen", **overrides)


class TestASystemWorkflowRefusesTaskTemplateChildren:
    def test_creating_a_task_template_in_a_system_workflow_is_refused(self) -> None:
        service, repo = _service()

        with pytest.raises(ValidationError):
            service.create_task_template(
                _template(workflow_template_key=SYSTEM_WORKFLOW),
                tenant_key=TENANT_KEY,
            )

        repo.create_task_template.assert_not_called()

    def test_re_pointing_a_task_template_into_a_system_workflow_is_refused(self) -> None:
        service, repo = _service(_template(workflow_template_key=OWN_WORKFLOW))

        with pytest.raises(ValidationError):
            service.update_task_template(
                "tt-1",
                {"workflow_template_key": SYSTEM_WORKFLOW},
                tenant_key=TENANT_KEY,
            )

        repo.update_task_template.assert_not_called()

    def test_the_refusal_is_the_one_the_parents_own_write_guard_already_raises(self) -> None:
        """Not a third convention: the same error the parent-level guard raises."""
        service, _ = _service()

        with pytest.raises(ValidationError) as child:
            service.create_task_template(
                _template(workflow_template_key=SYSTEM_WORKFLOW),
                tenant_key=TENANT_KEY,
            )
        with pytest.raises(ValidationError) as parent:
            service.update_workflow_template(SYSTEM_WORKFLOW, {"name": "Hijacked"})

        assert child.value.status_code == parent.value.status_code == 422
        assert child.value.error_code == parent.value.error_code == "VALIDATION_ERROR"

    def test_a_system_workflow_is_not_answered_as_a_foreign_one(self) -> None:
        """404 stays reserved for "you may not even read this"; 422 says "read yes, write no"."""
        service, _ = _service()

        with pytest.raises(NotFoundError) as foreign:
            service.create_task_template(
                _template(workflow_template_key=FOREIGN_WORKFLOW),
                tenant_key=TENANT_KEY,
            )
        with pytest.raises(ValidationError) as system:
            service.create_task_template(
                _template(workflow_template_key=SYSTEM_WORKFLOW),
                tenant_key=TENANT_KEY,
            )

        assert foreign.value.status_code == 404
        assert system.value.status_code == 422


class TestASystemWorkflowRefusesPhaseChildren:
    """``POST/PUT/DELETE`` on phases resolve the same parent and carry the same consequence."""

    def test_creating_a_phase_in_a_system_workflow_is_refused(self) -> None:
        service, repo = _service()

        with pytest.raises(ValidationError):
            service.create_workflow_phase(
                WorkflowPhase(workflow_template_key=SYSTEM_WORKFLOW, name="Neue Phase"),
            )

        repo.create_phase.assert_not_called()

    def test_updating_a_system_workflows_phase_is_refused(self) -> None:
        service, repo = _service()

        with pytest.raises(ValidationError):
            service.update_workflow_phase("ph-sys", {"name": "Umbenannt"})

        repo.update_phase.assert_not_called()

    def test_deleting_a_system_workflows_phase_is_refused(self) -> None:
        service, repo = _service()

        with pytest.raises(ValidationError):
            service.delete_workflow_phase("ph-sys")

        repo.delete_phase.assert_not_called()


class TestASystemWorkflowsExistingTaskTemplatesAreAlsoOffLimits:
    """The rule reaches the children already inside, not only the ones arriving.

    ``PUT``/``DELETE /tasks/templates/{key}`` never looked at the parent at all,
    so a tenant could rename, re-time or delete a seeded template of "Tomato
    Standard" — for everyone. That is the same modification as attaching one,
    arriving by a different verb, and it closes without the orphan-ownership
    decision: the parent comes off the child's own ``workflow_template_key`` and
    only ``is_system`` is consulted.
    """

    def test_editing_a_task_template_of_a_system_workflow_in_place_is_refused(self) -> None:
        service, repo = _service(_template(workflow_template_key=SYSTEM_WORKFLOW))

        with pytest.raises(ValidationError):
            service.update_task_template("tt-1", {"name": "Umbenannt"}, tenant_key=TENANT_KEY)

        repo.update_task_template.assert_not_called()

    def test_deleting_a_task_template_of_a_system_workflow_is_refused(self) -> None:
        service, repo = _service(_template(workflow_template_key=SYSTEM_WORKFLOW))

        with pytest.raises(ValidationError):
            service.delete_task_template("tt-1")

        repo.delete_task_template.assert_not_called()

    def test_both_refusals_carry_the_shared_shape(self) -> None:
        service, _ = _service(_template(workflow_template_key=SYSTEM_WORKFLOW))

        with pytest.raises(ValidationError) as edit:
            service.update_task_template("tt-1", {"name": "Umbenannt"}, tenant_key=TENANT_KEY)
        with pytest.raises(ValidationError) as removal:
            service.delete_task_template("tt-1")

        assert edit.value.status_code == removal.value.status_code == 422
        assert edit.value.error_code == removal.value.error_code == "VALIDATION_ERROR"


class TestItem1StaysOpen:
    """The foreign-tenant half of the same two routes is deliberately untouched.

    Guarding it means anchoring on the parent's *tenant*, which is exactly the
    step that needs the orphan-ownership field and its backfill. These two tests
    exist so a later reader cannot mistake the ``is_system`` guard for that fix —
    if someone closes item 1, they should be replaced, not silently satisfied.
    """

    def test_a_foreign_tenants_task_template_is_still_editable(self) -> None:
        service, repo = _service(_template(workflow_template_key=FOREIGN_WORKFLOW))

        updated = service.update_task_template("tt-1", {"name": "Umbenannt"}, tenant_key=TENANT_KEY)

        assert updated.name == "Umbenannt"
        repo.update_task_template.assert_called_once()

    def test_a_foreign_tenants_task_template_is_still_deletable(self) -> None:
        service, repo = _service(_template(workflow_template_key=FOREIGN_WORKFLOW))

        service.delete_task_template("tt-1")

        repo.delete_task_template.assert_called_once()


class TestTheTenantsOwnWorkflowStillAcceptsChildren:
    """The positive direction — #324 is what over-strictness costs."""

    def test_a_task_template_still_lands_in_the_callers_own_workflow(self) -> None:
        service, repo = _service()

        created = service.create_task_template(
            _template(workflow_template_key=OWN_WORKFLOW),
            tenant_key=TENANT_KEY,
        )

        assert created.workflow_template_key == OWN_WORKFLOW
        repo.create_task_template.assert_called_once()

    def test_a_standalone_template_without_a_parent_is_still_creatable(self) -> None:
        service, repo = _service()

        created = service.create_task_template(_template(), tenant_key=TENANT_KEY)

        assert created.workflow_template_key is None
        repo.create_task_template.assert_called_once()

    def test_a_phase_still_lands_in_the_callers_own_workflow(self) -> None:
        service, repo = _service()

        created = service.create_workflow_phase(
            WorkflowPhase(workflow_template_key=OWN_WORKFLOW, name="Neue Phase"),
        )

        assert created.workflow_template_key == OWN_WORKFLOW
        repo.create_phase.assert_called_once()

    def test_the_callers_own_phase_is_still_editable_and_deletable(self) -> None:
        service, repo = _service()

        assert service.update_workflow_phase("ph-own", {"name": "Umbenannt"}).name == "Umbenannt"
        assert service.delete_workflow_phase("ph-own") is True
        repo.update_phase.assert_called_once()
        repo.delete_phase.assert_called_once()

    def test_the_callers_own_task_template_is_still_editable_and_deletable(self) -> None:
        service, repo = _service(_template(workflow_template_key=OWN_WORKFLOW))

        assert service.update_task_template("tt-1", {"name": "Umbenannt"}, tenant_key=TENANT_KEY).name == "Umbenannt"
        service.delete_task_template("tt-1")
        repo.update_task_template.assert_called_once()
        repo.delete_task_template.assert_called_once()

    def test_a_task_template_with_no_parent_workflow_is_left_alone(self) -> None:
        """A standalone template has no anchor — this guard must not become an
        orphan-ownership decision by the back door.

        Orphans do have an owner now (global, decided on #965), but that belongs
        to items 1/2/4 with their own field and backfill; refusing one here would
        settle it in the wrong place and break a template that is editable today.
        """
        service, repo = _service(_template())

        assert service.update_task_template("tt-1", {"name": "Umbenannt"}, tenant_key=TENANT_KEY).name == "Umbenannt"
        service.delete_task_template("tt-1")
        repo.update_task_template.assert_called_once()
        repo.delete_task_template.assert_called_once()

    def test_a_phase_with_no_parent_workflow_is_left_alone(self) -> None:
        """An unparented phase has nothing to anchor on; the guard must not 404 it."""
        service, repo = _service()

        assert service.update_workflow_phase("ph-orphan", {"name": "Umbenannt"}).name == "Umbenannt"
        assert service.delete_workflow_phase("ph-orphan") is True
        repo.update_phase.assert_called_once()
        repo.delete_phase.assert_called_once()


class TestWhatTheUiLegitimatelyDoesWithSystemWorkflowsStillWorks:
    """Reading, duplicating and instantiating a system workflow are untouched."""

    def test_a_system_workflow_is_still_readable(self) -> None:
        service, _ = _service()

        assert service.get_workflow_template(SYSTEM_WORKFLOW, tenant_key=TENANT_KEY).key == SYSTEM_WORKFLOW

    def test_duplicating_a_system_workflow_still_copies_its_phases_and_templates(self) -> None:
        """The escape hatch the refusal points at — the copy is the tenant's own."""
        service, repo = _service()
        repo.create_workflow_template.side_effect = lambda clone: clone.model_copy(update={"key": "clone-1"})
        repo.get_phases_for_workflow.return_value = [
            WorkflowPhase(_key="ph-sys", workflow_template_key=SYSTEM_WORKFLOW, name="Vegetativ"),
        ]
        repo.get_task_templates_for_workflow.return_value = [
            _template(workflow_template_key=SYSTEM_WORKFLOW, workflow_phase_key="ph-sys"),
        ]
        repo.create_phase.side_effect = lambda phase: phase.model_copy(update={"key": "ph-clone"})

        clone = service.duplicate_workflow_template(SYSTEM_WORKFLOW, "Meine Kopie", tenant_key=TENANT_KEY)

        assert clone.tenant_key == TENANT_KEY
        assert clone.is_system is False
        assert repo.create_phase.call_count == 1
        assert repo.create_task_template.call_count == 1
        copied_template = repo.create_task_template.call_args[0][0]
        assert copied_template.workflow_template_key == "clone-1"
        assert copied_template.workflow_phase_key == "ph-clone"

    def test_instantiating_a_system_workflow_still_generates_tasks(self) -> None:
        service, repo = _service()
        repo.get_task_templates_for_workflow.return_value = [_template(workflow_template_key=SYSTEM_WORKFLOW)]
        repo.create_workflow_execution.side_effect = lambda execution: execution.model_copy(
            update={"key": "exec-1"},
        )
        repo.create_task.side_effect = lambda task: task.model_copy(update={"key": "task-1"})

        execution = service.instantiate_workflow(SYSTEM_WORKFLOW, "plant-1", "plant_instance")

        assert execution.workflow_template_key == SYSTEM_WORKFLOW
        repo.create_task.assert_called_once()
