"""Unit tests for ArangoTaskRepository task-listing queries.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O
boundary and is doubled with MagicMock. No real ArangoDB connection. Assertions
target the AQL the repository builds — specifically the defensive guard that
keeps tasks of removed (soft-deleted) or missing plant_instances out of every
task listing, including the queue.
"""

import re
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


class FakeTaskDb:
    """Minimal ArangoDB double that evaluates the ``get_all_tasks`` query semantics.

    The real repository builds a parametrised AQL string and hands it to
    ``aql.execute``. This double parses the equality ``FILTER`` clauses and the
    removed-plant defensive guard out of that very string and applies them to an
    in-memory task collection, so a test can prove that ``entity_type``/
    ``entity_key``/``tenant_key`` filtering genuinely returns the seeded task
    (#578) — without a running ArangoDB and without re-hardcoding the query.
    """

    _EQ_RE = re.compile(r"doc\.(\w+) == @(\w+)")

    def __init__(self, tasks: list[dict], plants: dict[str, dict]) -> None:
        self._tasks = tasks
        self._plants = plants
        self.aql = self  # execute() lives on this object

    def execute(self, query: str, bind_vars: dict | None = None):
        bind_vars = bind_vars or {}
        docs = list(self._tasks)
        for field, bind in self._EQ_RE.findall(query):
            expected = bind_vars[bind]
            docs = [d for d in docs if d.get(field) == expected]
        if "_plant.removed_on == null" in query:
            docs = [
                d
                for d in docs
                if d.get("entity_type") != "plant_instance"
                or ((plant := self._plants.get(d.get("entity_key"))) is not None and plant.get("removed_on") is None)
            ]
        if "COLLECT WITH COUNT INTO total" in query:
            return iter([len(docs)])
        docs = sorted(docs, key=lambda d: d.get("due_date") or "")
        offset = bind_vars.get("offset", 0)
        limit = bind_vars.get("limit", 50)
        return iter(docs[offset : offset + limit])


def _task_doc(key: str, *, category: str, entity_key: str, tenant_key: str, status: str = "pending") -> dict:
    return {
        "_key": key,
        "name": f"task-{key}",
        "category": category,
        "entity_type": "plant_instance",
        "entity_key": entity_key,
        "tenant_key": tenant_key,
        "status": status,
        "due_date": None,
    }


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


class TestEntityFilterQuery:
    """#578 — the plant-instance Tasks tab filters via entity_type + entity_key."""

    def test_builds_entity_and_tenant_equality_clauses(self, repo, mock_db):
        mock_db.aql.execute.side_effect = _list_and_count([], 0)

        repo.get_all_tasks(
            filters={"entity_type": "plant_instance", "entity_key": "219579"},
            tenant_key="tenant-A",
        )

        list_query = mock_db.aql.execute.call_args_list[0].args[0]
        bind = mock_db.aql.execute.call_args_list[0].kwargs["bind_vars"]
        assert "doc.tenant_key == @tenant_key" in list_query
        assert "doc.entity_type == @val0" in list_query
        assert "doc.entity_key == @val1" in list_query
        assert bind["tenant_key"] == "tenant-A"
        assert bind["val0"] == "plant_instance"
        assert bind["val1"] == "219579"


class TestEntityFilterSemantics:
    """The exact filter the Tasks tab issues returns the instance's tasks (#578).

    Root cause hunt: care-reminder, workflow and manual tasks are all stored with
    ``entity_type='plant_instance'`` and ``entity_key=<plant _key>``; the filter
    must return every one of them, tenant-scoped, while excluding foreign-tenant
    rows, rows of a different instance, and tasks of a soft-deleted plant.
    """

    PLANT_KEY = "219579"
    TENANT = "tenant-A"

    def _repo_with(self, tasks: list[dict]) -> ArangoTaskRepository:
        plants = {self.PLANT_KEY: {"_key": self.PLANT_KEY, "removed_on": None}}
        return ArangoTaskRepository(FakeTaskDb(tasks, plants))

    def test_returns_tasks_across_all_categories(self):
        tasks = [
            _task_doc("t-care", category="care_reminder", entity_key=self.PLANT_KEY, tenant_key=self.TENANT),
            _task_doc("t-maint", category="maintenance", entity_key=self.PLANT_KEY, tenant_key=self.TENANT),
            _task_doc("t-harvest", category="harvest", entity_key=self.PLANT_KEY, tenant_key=self.TENANT),
            _task_doc("t-obs", category="observation", entity_key=self.PLANT_KEY, tenant_key=self.TENANT),
        ]
        repo = self._repo_with(tasks)

        result, total = repo.get_all_tasks(
            filters={"entity_type": "plant_instance", "entity_key": self.PLANT_KEY},
            tenant_key=self.TENANT,
        )

        assert total == 4
        assert {t.key for t in result} == {"t-care", "t-maint", "t-harvest", "t-obs"}
        # No implicit category/status narrowing leaked into the query.
        assert {t.category.value for t in result} == {"care_reminder", "maintenance", "harvest", "observation"}

    def test_excludes_foreign_tenant_and_other_instance(self):
        tasks = [
            _task_doc("mine", category="care_reminder", entity_key=self.PLANT_KEY, tenant_key=self.TENANT),
            _task_doc("foreign", category="care_reminder", entity_key=self.PLANT_KEY, tenant_key="tenant-B"),
            _task_doc("other", category="care_reminder", entity_key="999999", tenant_key=self.TENANT),
        ]
        repo = self._repo_with(tasks)

        result, total = repo.get_all_tasks(
            filters={"entity_type": "plant_instance", "entity_key": self.PLANT_KEY},
            tenant_key=self.TENANT,
        )

        assert total == 1
        assert [t.key for t in result] == ["mine"]

    def test_excludes_tasks_of_removed_plant(self):
        tasks = [_task_doc("gone", category="care_reminder", entity_key="removed-1", tenant_key=self.TENANT)]
        plants = {"removed-1": {"_key": "removed-1", "removed_on": "2024-06-01T00:00:00Z"}}
        repo = ArangoTaskRepository(FakeTaskDb(tasks, plants))

        result, total = repo.get_all_tasks(
            filters={"entity_type": "plant_instance", "entity_key": "removed-1"},
            tenant_key=self.TENANT,
        )

        assert total == 0
        assert result == []


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
