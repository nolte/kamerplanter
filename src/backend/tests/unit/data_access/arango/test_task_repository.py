"""Unit tests for ArangoTaskRepository task-listing queries.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O
boundary and is doubled with MagicMock. No real ArangoDB connection. Assertions
target the AQL the repository builds — specifically the defensive guard that
keeps tasks of removed (soft-deleted) or missing plant_instances out of every
task listing, including the queue.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.models.task import Task


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoTaskRepository(mock_db)


def _list_and_count(items, total):
    """Side-effect for get_all_tasks: first the list cursor, then the count."""
    return [iter(items), iter([total])]


class TestRemovedPlantGuard:
    def test_get_all_tasks_filters_removed_plant_instances(self, repo, mock_db):
        mock_db.aql.execute.side_effect = _list_and_count([], 0)

        repo.get_all_tasks()

        list_query = mock_db.aql.execute.call_args_list[0].args[0]
        assert "doc.entity_type == 'plant_instance'" in list_query
        assert "DOCUMENT(CONCAT('plant_instances/', doc.entity_key))" in list_query
        assert "_plant.removed_on == null" in list_query

    def test_count_query_applies_the_same_guard(self, repo, mock_db):
        # The count must match the list so the total never includes orphans.
        mock_db.aql.execute.side_effect = _list_and_count([], 0)

        repo.get_all_tasks()

        count_query = mock_db.aql.execute.call_args_list[1].args[0]
        assert "_plant.removed_on == null" in count_query
        assert "COLLECT WITH COUNT INTO total" in count_query

    def test_get_pending_tasks_carries_the_guard(self, repo, mock_db):
        mock_db.aql.execute.side_effect = _list_and_count([], 0)

        repo.get_pending_tasks()

        list_query = mock_db.aql.execute.call_args_list[0].args[0]
        assert "doc.status == @val0" in list_query
        assert "_plant.removed_on == null" in list_query

    def test_guard_does_not_drop_non_plant_tasks(self, repo, mock_db):
        # Tasks not tied to a plant_instance (e.g. planting_run / tank) must pass
        # the guard via the ``entity_type != 'plant_instance'`` branch.
        mock_db.aql.execute.side_effect = _list_and_count([], 0)

        repo.get_all_tasks()

        list_query = mock_db.aql.execute.call_args_list[0].args[0]
        assert "doc.entity_type != 'plant_instance'" in list_query


class TestGetTasksForRun:
    def test_filters_on_planting_run_key(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.get_tasks_for_run("run-1")

        query = mock_db.aql.execute.call_args.args[0]
        bind = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert "doc.planting_run_key == @run_key" in query
        assert bind["run_key"] == "run-1"

    def test_optional_status_filter(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.get_tasks_for_run("run-1", status="pending")

        query = mock_db.aql.execute.call_args.args[0]
        bind = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert "doc.status == @status" in query
        assert bind["status"] == "pending"


class TestPlantingRunKeyPersisted:
    """Regression guard: ``planting_run_key`` must be a declared model field.

    It used to be missing, so Pydantic's default ``extra='ignore'`` silently
    dropped it on construction and it was never written to the document — which
    left watering/feeding tasks unattributable to their run.
    """

    def test_field_survives_model_dump(self):
        task = Task(name="watering", planting_run_key="run-1")

        assert task.planting_run_key == "run-1"
        assert task.model_dump(by_alias=True)["planting_run_key"] == "run-1"
