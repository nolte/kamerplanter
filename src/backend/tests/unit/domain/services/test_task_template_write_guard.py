"""Task-template writes: the parent anchor and the allow-list (#965).

Two defects sat on the same two methods.

**The reference was never verified.** ``TaskTemplate`` carries no ``tenant_key``
of its own, but its parent ``WorkflowTemplate`` does, so the parent is the
anchor. ``create_task_template`` was a pure pass-through to the repository,
which then builds a ``wf_contains`` edge to whatever key the request body named
— an edge written *across* the isolation boundary rather than a read across it.
``get_task_templates_for_workflow`` filters on the denormalised
``workflow_template_key`` field, so the injected template also shows up in the
foreign workflow's listing and in every task that workflow instantiates.

**The update was mass assignment.** ``update_task_template`` looped over the
request dict and ``setattr``-ed every entry onto the loaded model, so the body
decided which *fields* were written — ``workflow_template_key`` included, which
is the same cross-boundary edge reached from the update side. And since no
domain model sets ``validate_assignment`` (#968), none of those writes was
validated either. The two sibling ``update_*`` methods on this service had the
identical shape and are fixed the same way.

Both directions are pinned: a foreign or unknown parent answers **404, never
403** (no cross-tenant oracle), while the caller's own workflow, a globally
seeded system workflow (the #324 counter-example — a strict filter that hid the
global catalogue) and a standalone template with no parent at all all still
work.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
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
    repo.create_task_template.side_effect = lambda tt: tt
    repo.update_task_template.side_effect = lambda key, tt: tt
    return TaskService(repo, MagicMock(), MagicMock()), repo


def _template(**overrides) -> TaskTemplate:
    return TaskTemplate(_key="tt-1", name="Giessen", **overrides)


class TestCreateTaskTemplateVerifiesItsParentWorkflow:
    def test_a_foreign_workflow_is_not_found_and_writes_nothing(self) -> None:
        service, repo = _service()

        with pytest.raises(NotFoundError):
            service.create_task_template(
                _template(workflow_template_key=FOREIGN_WORKFLOW),
                tenant_key=TENANT_KEY,
            )

        repo.create_task_template.assert_not_called()

    def test_an_unknown_workflow_looks_exactly_the_same(self) -> None:
        """No oracle: 'belongs to another tenant' and 'does not exist' are one answer."""
        service, _ = _service()

        with pytest.raises(NotFoundError) as foreign:
            service.create_task_template(
                _template(workflow_template_key=FOREIGN_WORKFLOW),
                tenant_key=TENANT_KEY,
            )
        with pytest.raises(NotFoundError) as unknown:
            service.create_task_template(
                _template(workflow_template_key="does-not-exist"),
                tenant_key=TENANT_KEY,
            )

        assert foreign.value.status_code == unknown.value.status_code == 404
        assert foreign.value.error_code == unknown.value.error_code

    def test_the_callers_own_workflow_still_accepts_a_template(self) -> None:
        service, repo = _service()

        created = service.create_task_template(
            _template(workflow_template_key=OWN_WORKFLOW),
            tenant_key=TENANT_KEY,
        )

        assert created.workflow_template_key == OWN_WORKFLOW
        repo.create_task_template.assert_called_once()

    def test_a_globally_seeded_system_workflow_stays_referenceable(self) -> None:
        """#324's counter-example: the strict direction would hide the global catalogue."""
        service, repo = _service()

        created = service.create_task_template(
            _template(workflow_template_key=SYSTEM_WORKFLOW),
            tenant_key=TENANT_KEY,
        )

        assert created.workflow_template_key == SYSTEM_WORKFLOW
        repo.create_task_template.assert_called_once()

    def test_a_standalone_template_without_a_parent_is_still_creatable(self) -> None:
        """A template with no workflow is a supported state — it has nothing to anchor on."""
        service, repo = _service()

        created = service.create_task_template(_template(), tenant_key=TENANT_KEY)

        assert created.workflow_template_key is None
        repo.create_task_template.assert_called_once()


class TestUpdateTaskTemplateVerifiesItsParentWorkflow:
    def test_the_update_path_cannot_re_point_a_template_into_a_foreign_workflow(self) -> None:
        service, repo = _service(_template(workflow_template_key=OWN_WORKFLOW))

        with pytest.raises(NotFoundError):
            service.update_task_template(
                "tt-1",
                {"workflow_template_key": FOREIGN_WORKFLOW},
                tenant_key=TENANT_KEY,
            )

        repo.update_task_template.assert_not_called()

    def test_an_unknown_workflow_looks_exactly_the_same(self) -> None:
        service, _ = _service(_template(workflow_template_key=OWN_WORKFLOW))

        with pytest.raises(NotFoundError) as foreign:
            service.update_task_template(
                "tt-1",
                {"workflow_template_key": FOREIGN_WORKFLOW},
                tenant_key=TENANT_KEY,
            )
        with pytest.raises(NotFoundError) as unknown:
            service.update_task_template(
                "tt-1",
                {"workflow_template_key": "does-not-exist"},
                tenant_key=TENANT_KEY,
            )

        assert foreign.value.status_code == unknown.value.status_code == 404
        assert foreign.value.error_code == unknown.value.error_code

    def test_moving_a_template_between_the_callers_own_workflows_still_works(self) -> None:
        service, repo = _service(_template(workflow_template_key=SYSTEM_WORKFLOW))

        updated = service.update_task_template(
            "tt-1",
            {"workflow_template_key": OWN_WORKFLOW},
            tenant_key=TENANT_KEY,
        )

        assert updated.workflow_template_key == OWN_WORKFLOW
        repo.update_task_template.assert_called_once()


class TestUpdateTaskTemplateIsAllowListed:
    def test_the_body_cannot_reach_an_unexposed_reference_field(self) -> None:
        """``activity_key`` is on no request schema and is verified nowhere."""
        service, _ = _service(_template(activity_key="act-own"))

        updated = service.update_task_template(
            "tt-1",
            {"name": "Umbenannt", "activity_key": "act-foreign"},
            tenant_key=TENANT_KEY,
        )

        assert updated.name == "Umbenannt"
        assert updated.activity_key == "act-own"

    def test_the_body_cannot_reach_identity_or_audit_fields(self) -> None:
        service, _ = _service(_template())

        updated = service.update_task_template(
            "tt-1",
            {"key": "tt-hijacked", "created_at": "2020-01-01T00:00:00Z"},
            tenant_key=TENANT_KEY,
        )

        assert updated.key == "tt-1"
        assert updated.created_at is None

    def test_an_exposed_field_is_still_written(self) -> None:
        service, _ = _service(_template(days_offset=0))

        updated = service.update_task_template("tt-1", {"days_offset": 7}, tenant_key=TENANT_KEY)

        assert updated.days_offset == 7


class TestTheSiblingUpdatesAreAllowListedToo:
    """``update_workflow_template`` and ``update_workflow_phase`` had the same shape."""

    def _workflow_service(self, wt: WorkflowTemplate) -> tuple[TaskService, MagicMock]:
        repo = MagicMock()
        wire_or_raise(
            repo,
            "WorkflowTemplate",
            by_key="get_workflow_template_by_key",
            or_raise="get_workflow_template_or_raise",
        )
        repo.get_workflow_template_by_key.return_value = wt
        repo.update_workflow_template.side_effect = lambda key, template: template
        return TaskService(repo, MagicMock(), MagicMock()), repo

    def test_a_workflow_template_cannot_be_handed_to_another_tenant(self) -> None:
        service, _ = self._workflow_service(WorkflowTemplate(_key="wf-1", tenant_key=TENANT_KEY, name="Meiner"))

        updated = service.update_workflow_template(
            "wf-1",
            {"name": "Umbenannt", "tenant_key": FOREIGN_TENANT_KEY},
        )

        assert updated.name == "Umbenannt"
        assert updated.tenant_key == TENANT_KEY

    def test_a_workflow_template_cannot_declare_itself_a_system_template(self) -> None:
        """``is_system`` is the flag the write guard itself reads."""
        service, _ = self._workflow_service(WorkflowTemplate(_key="wf-1", tenant_key=TENANT_KEY, name="Meiner"))

        updated = service.update_workflow_template("wf-1", {"is_system": True})

        assert updated.is_system is False

    def test_a_phase_cannot_be_moved_into_another_workflow(self) -> None:
        repo = MagicMock()
        wire_or_raise(repo, "WorkflowPhase", by_key="get_phase_by_key", or_raise="get_phase_or_raise")
        repo.get_phase_by_key.return_value = WorkflowPhase(
            _key="ph-1",
            workflow_template_key=OWN_WORKFLOW,
            name="Vegetativ",
        )
        repo.update_phase.side_effect = lambda key, phase: phase
        service = TaskService(repo, MagicMock(), MagicMock())

        updated = service.update_workflow_phase(
            "ph-1",
            {"name": "Bluete", "workflow_template_key": FOREIGN_WORKFLOW},
        )

        assert updated.name == "Bluete"
        assert updated.workflow_template_key == OWN_WORKFLOW
