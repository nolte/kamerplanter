"""Tenant access to workflow templates spans the hybrid catalog (SEC-B4).

The list query restores global system templates for every tenant; the
detail/instantiate/duplicate routes must then be able to *read* those same
templates through ``get_workflow_template`` — while writes to a system template
stay blocked, and a foreign tenant's template stays invisible.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.task import WorkflowTemplate
from app.domain.services.task_service import TaskService
from tests.conftest import wire_or_raise


def _service(wt: WorkflowTemplate) -> tuple[TaskService, MagicMock]:
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


def _wf(key: str, tenant_key: str, *, is_system: bool = False) -> WorkflowTemplate:
    return WorkflowTemplate(_key=key, tenant_key=tenant_key, name="Workflow", is_system=is_system)


class TestWorkflowTemplateReadAccess:
    def test_system_template_is_readable_by_tenant(self) -> None:
        # The route guard runs get_workflow_template(key, tenant_key=<real>);
        # a globally seeded system template (empty tenant_key) must pass.
        service, _ = _service(_wf("sys1", "", is_system=True))
        result = service.get_workflow_template("sys1", tenant_key="tenant_a")
        assert result.key == "sys1"

    def test_own_template_is_readable(self) -> None:
        service, _ = _service(_wf("a1", "tenant_a"))
        assert service.get_workflow_template("a1", tenant_key="tenant_a").key == "a1"

    def test_foreign_tenant_template_raises_not_found(self) -> None:
        service, _ = _service(_wf("b1", "tenant_b"))
        with pytest.raises(NotFoundError):
            service.get_workflow_template("b1", tenant_key="tenant_a")


class TestWorkflowTemplateWriteGuard:
    def test_update_system_template_is_rejected(self) -> None:
        # Read access is now hybrid-catalog-wide, so the write guard must stop
        # a tenant from mutating a globally seeded system template.
        service, repo = _service(_wf("sys1", "", is_system=True))
        with pytest.raises(ValidationError):
            service.update_workflow_template("sys1", {"name": "Hijacked"})
        repo.update_workflow_template.assert_not_called()

    def test_update_own_template_succeeds(self) -> None:
        service, repo = _service(_wf("a1", "tenant_a"))
        updated = service.update_workflow_template("a1", {"name": "Renamed"})
        assert updated.name == "Renamed"
        repo.update_workflow_template.assert_called_once()


class TestWorkflowTemplateDuplicate:
    def test_duplicate_of_system_template_is_owned_by_duplicating_tenant(self) -> None:
        # A tenant may copy a global system template, but the copy must be a
        # private tenant-scoped template — never inherit the source's empty
        # tenant_key, which would make it globally visible to every tenant.
        service, repo = _service(_wf("sys1", "", is_system=True))

        def _create(clone: WorkflowTemplate) -> WorkflowTemplate:
            clone.key = "clone1"
            return clone

        repo.create_workflow_template.side_effect = _create
        repo.get_phases_for_workflow.return_value = []
        repo.get_task_templates_for_workflow.return_value = []

        result = service.duplicate_workflow_template("sys1", "My Copy", tenant_key="tenant_a")

        assert result.tenant_key == "tenant_a"
        assert result.is_system is False
        assert repo.create_workflow_template.call_args[0][0].tenant_key == "tenant_a"
