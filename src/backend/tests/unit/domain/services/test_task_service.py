"""Tests for TaskService.instantiate_workflow with entity-agnostic support."""

from unittest.mock import MagicMock

import pytest

from app.domain.models.task import (
    ChecklistItem,
    Task,
    TaskTemplate,
    WorkflowExecution,
    WorkflowTemplate,
)
from app.domain.services.task_service import TaskService


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def mock_hst():
    return MagicMock()


@pytest.fixture
def mock_deps():
    return MagicMock()


@pytest.fixture
def service(mock_repo, mock_hst, mock_deps):
    return TaskService(mock_repo, mock_hst, mock_deps)


def _make_task_template(
    key: str = "tt1",
    name: str = "Topping",
    trigger_phase: str | None = None,
    trigger_type: str = "manual",
    days_offset: int = 0,
) -> TaskTemplate:
    return TaskTemplate(
        key=key,
        name=name,
        instruction="Cut the main stem",
        category="training",
        trigger_phase=trigger_phase,
        trigger_type=trigger_type,
        days_offset=days_offset,
        stress_level="medium",
        skill_level="intermediate",
        default_checklist=[ChecklistItem(text="Sterilize scissors", done=False, order=0)],
    )


def _make_workflow_template(key: str = "wf1") -> WorkflowTemplate:
    return WorkflowTemplate(
        key=key,
        name="Cannabis Indoor Workflow",
        description="Standard workflow",
        species_compatible=["cannabis"],
    )


def _setup_workflow_mocks(mock_repo, templates=None, entity_type="plant_instance"):
    wf = _make_workflow_template()
    templates = templates or [_make_task_template()]
    execution = WorkflowExecution(
        key="we1",
        workflow_template_key="wf1",
        entity_key="entity1",
        entity_type=entity_type,
    )

    mock_repo.get_workflow_template_by_key.return_value = wf
    mock_repo.get_task_templates_for_workflow.return_value = templates
    mock_repo.create_workflow_execution.return_value = execution
    mock_repo.create_task.side_effect = lambda t: t
    return wf, execution


class TestInstantiateWorkflowEntityAgnostic:
    """Verify entity_key/entity_type are set correctly for all entity types."""

    def test_plant_instance_entity_key(self, service, mock_repo):
        """Direct call with entity_key/entity_type for plant_instance."""
        _setup_workflow_mocks(mock_repo)

        service.instantiate_workflow("wf1", entity_key="plant1", entity_type="plant_instance")

        created_task = mock_repo.create_task.call_args[0][0]
        assert created_task.entity_key == "plant1"
        assert created_task.entity_type == "plant_instance"

    def test_entity_key_entity_type_used_directly(self, service, mock_repo):
        _setup_workflow_mocks(mock_repo, entity_type="tank")

        service.instantiate_workflow(
            "wf1",
            entity_key="tank1",
            entity_type="tank",
        )

        created_task = mock_repo.create_task.call_args[0][0]
        assert created_task.entity_key == "tank1"
        assert created_task.entity_type == "tank"

    def test_location_entity_type(self, service, mock_repo):
        _setup_workflow_mocks(mock_repo, entity_type="location")

        service.instantiate_workflow(
            "wf1",
            entity_key="loc1",
            entity_type="location",
        )

        created_task = mock_repo.create_task.call_args[0][0]
        assert created_task.entity_key == "loc1"
        assert created_task.entity_type == "location"

    def test_planting_run_entity_type(self, service, mock_repo):
        _setup_workflow_mocks(mock_repo, entity_type="planting_run")

        service.instantiate_workflow(
            "wf1",
            entity_key="run1",
            entity_type="planting_run",
        )

        created_task = mock_repo.create_task.call_args[0][0]
        assert created_task.entity_key == "run1"
        assert created_task.entity_type == "planting_run"

    def test_non_plant_entity_no_dormant_tasks(self, service, mock_repo):
        """Phase-based dormant tasks should only be created for plant_instance."""
        templates = [
            _make_task_template(
                key="tt1",
                name="Check pH",
                trigger_phase="vegetative",
                trigger_type="phase_entry",
            ),
        ]
        _setup_workflow_mocks(mock_repo, templates, entity_type="tank")

        service.instantiate_workflow(
            "wf1",
            entity_key="tank1",
            entity_type="tank",
        )

        created_task = mock_repo.create_task.call_args[0][0]
        assert created_task.status == "pending"

    def test_plant_instance_creates_dormant_tasks(self, service, mock_repo):
        """Phase-based tasks for plant_instance should be dormant."""
        templates = [
            _make_task_template(
                key="tt1",
                name="LST Bend",
                trigger_phase="vegetative",
                trigger_type="phase_entry",
            ),
        ]
        _setup_workflow_mocks(mock_repo, templates)

        service.instantiate_workflow("wf1", entity_key="plant1", entity_type="plant_instance")

        created_task = mock_repo.create_task.call_args[0][0]
        assert created_task.status == "dormant"

    def test_execution_has_entity_fields(self, service, mock_repo):
        _setup_workflow_mocks(mock_repo, entity_type="tank")

        service.instantiate_workflow(
            "wf1",
            entity_key="tank1",
            entity_type="tank",
        )

        execution_arg = mock_repo.create_workflow_execution.call_args[0][0]
        assert execution_arg.entity_key == "tank1"
        assert execution_arg.entity_type == "tank"

    def test_multiple_task_templates_all_get_entity_fields(self, service, mock_repo):
        templates = [
            _make_task_template(key="tt1", name="Topping"),
            _make_task_template(key="tt2", name="LST Bend", trigger_phase="vegetative", trigger_type="phase_entry"),
        ]
        _setup_workflow_mocks(mock_repo, templates)

        service.instantiate_workflow("wf1", entity_key="plant1", entity_type="plant_instance")

        assert mock_repo.create_task.call_count == 2
        for call in mock_repo.create_task.call_args_list:
            task = call[0][0]
            assert task.entity_key == "plant1"
            assert task.entity_type == "plant_instance"


class TestCloneTaskEntityAgnostic:
    """Verify clone_task handles entity fields correctly."""

    def test_clone_with_target_entity(self, service, mock_repo):
        source = Task(
            key="t1",
            tenant_key="tenant1",
            name="Clean tank",
            entity_key="tank1",
            entity_type="tank",
        )
        mock_repo.get_task_by_key.return_value = source
        mock_repo.create_task.side_effect = lambda t: t

        cloned = service.clone_task(
            "t1",
            target_entity_key="tank2",
            target_entity_type="tank",
        )

        assert cloned.entity_key == "tank2"
        assert cloned.entity_type == "tank"

    def test_clone_falls_back_to_source_entity(self, service, mock_repo):
        source = Task(
            key="t1",
            tenant_key="tenant1",
            name="Clean tank",
            entity_key="tank1",
            entity_type="tank",
        )
        mock_repo.get_task_by_key.return_value = source
        mock_repo.create_task.side_effect = lambda t: t

        cloned = service.clone_task("t1")

        assert cloned.entity_key == "tank1"
        assert cloned.entity_type == "tank"


class TestListTasksWithEntityFilter:
    """Verify the filter dict is correctly passed to the repository."""

    def test_entity_type_filter_passed_to_repo(self, service, mock_repo):
        mock_repo.get_all_tasks.return_value = ([], 0)

        service.list_tasks(0, 50, {"entity_type": "planting_run", "entity_key": "run1"}, tenant_key="t1")

        mock_repo.get_all_tasks.assert_called_once_with(
            0,
            50,
            {"entity_type": "planting_run", "entity_key": "run1"},
            tenant_key="t1",
        )
