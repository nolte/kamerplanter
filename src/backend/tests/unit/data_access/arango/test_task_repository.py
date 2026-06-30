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
