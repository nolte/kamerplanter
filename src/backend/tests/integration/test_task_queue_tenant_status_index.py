"""#1534 — the tenant's task queue reads its own pending tasks, measured on a real ArangoDB.

``GET /t/{slug}/tasks/queue`` reaches ``ArangoTaskRepository.get_pending_tasks``, which
sends two queries (the window and its count) filtering ``doc.tenant_key == @tenant_key
AND doc.status == @val0``. With only the single-field ``status`` index the optimizer took
that one and filtered the tenant afterwards, so every tenant's queue read every pending
task of the installation (533 680 entries, ~1.4 s per query at 970 k tasks —
``spec/analysis/task-queue-index-measurement-2026-10.md``). The plans asserted here:

* on a bootstrapped volume both queue queries plan an ``IndexNode`` on
  ``(tenant_key, status)``, never ``status`` alone and never a collection scan;
* on a volume that predates the index they plan on ``status`` (the measured defect —
  which is also what makes the first assertion falsifiable), and after v0092 they plan
  on the new index again.

The AQL is not written down here: it is captured from the real repository method, so a
change of the query shape is measured, not a copy of it.

Run with: pytest tests/integration/test_task_queue_tenant_status_index.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import pytest
from arango.aql import AQL
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.models.task import Task, TaskStatus
from app.migrations.versions.v0092_task_tenant_status_index import migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#1534 asserts the optimizer's plan for the task queue on a real ArangoDB"),
]

_DB_NAME = run_database_name("task_queue_tenant_status_index")

#: Many tenants of similar size, mostly ``pending`` — the shape where the ``status``
#: index is the poor choice: it narrows to about half of the installation, the
#: compound one to one tenant's pending tasks.
_TENANTS = 40
_TASKS_PER_TENANT = 30
_MEASURED_TENANT = "tenant-07"
_STATUSES = (TaskStatus.PENDING, TaskStatus.PENDING, TaskStatus.COMPLETED, TaskStatus.SKIPPED)


def _tasks(repo: ArangoTaskRepository) -> Iterator[dict[str, Any]]:
    now = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
    for t in range(_TENANTS):
        for i in range(_TASKS_PER_TENANT):
            task = Task(
                tenant_key=f"tenant-{t:02d}",
                name=f"Task {i}",
                due_date=now + timedelta(days=i - 15),
                status=_STATUSES[i % len(_STATUSES)],
            )
            yield repo._to_doc(task)


@pytest.fixture(scope="module")
def db() -> Iterator[StandardDatabase]:
    system, database = create_database(_DB_NAME)
    database.collection(col.TASKS).import_bulk(
        list(_tasks(ArangoTaskRepository(database))), on_duplicate="error", halt_on_error=True
    )
    try:
        yield database
    finally:
        system.delete_database(_DB_NAME)


def _queue_queries(db: StandardDatabase) -> list[tuple[str, dict[str, Any]]]:
    """The AQL the queue sends for the measured tenant, as the repository sends it."""
    executed: list[tuple[str, dict[str, Any]]] = []
    original = AQL.execute

    def spy(self: AQL, query: str, *args: Any, **kwargs: Any) -> Any:
        executed.append((query, dict(kwargs.get("bind_vars") or {})))
        return original(self, query, *args, **kwargs)

    with patch.object(AQL, "execute", spy):
        items, total = ArangoTaskRepository(db).get_pending_tasks(0, 200, tenant_key=_MEASURED_TENANT)

    # Reading exactly the tenant's own pending tasks proves the captured queries are
    # the ones that answered, not a neighbouring call.
    pending = sum(1 for i in range(_TASKS_PER_TENANT) if _STATUSES[i % len(_STATUSES)] is TaskStatus.PENDING)
    assert (len(items), total) == (pending, pending)
    assert len(executed) == 2, [q for q, _ in executed]
    assert any("LIMIT @offset, @limit" in q for q, _ in executed)
    return executed


def _plan(db: StandardDatabase, query: str, bind_vars: dict[str, Any]) -> tuple[list[str], list[list[str]]]:
    """Node types of the chosen plan and the distinct field lists of the indexes its IndexNodes use.

    One IndexNode can list the same index once per condition branch (measured: the
    queue window lists ``(tenant_key, status)`` twice); the plan uses it once, so it is
    reported once.
    """
    plan = db.aql.explain(query, bind_vars=bind_vars)
    assert isinstance(plan, dict)
    nodes = plan["nodes"]
    index_fields: list[list[str]] = []
    for node in nodes:
        for index in node.get("indexes", []) if node["type"] == "IndexNode" else []:
            if list(index["fields"]) not in index_fields:
                index_fields.append(list(index["fields"]))
    return [node["type"] for node in nodes], index_fields


def _compound_indexes(db: StandardDatabase) -> list[dict[str, Any]]:
    rows = db.collection(col.TASKS).indexes()
    assert isinstance(rows, list)
    return [row for row in rows if row.get("fields") == col.TASK_TENANT_STATUS_INDEX_FIELDS]


def test_the_queue_plans_on_the_tenant_status_index(db: StandardDatabase) -> None:
    for query, bind_vars in _queue_queries(db):
        node_types, index_fields = _plan(db, query, bind_vars)

        assert "IndexNode" in node_types, (query, node_types)
        assert "EnumerateCollectionNode" not in node_types, (query, node_types)
        assert index_fields == [col.TASK_TENANT_STATUS_INDEX_FIELDS], (query, index_fields)


def test_the_bootstrap_keeps_the_single_field_status_index(db: StandardDatabase) -> None:
    rows = db.collection(col.TASKS).indexes()
    assert isinstance(rows, list)
    fields = [row.get("fields") for row in rows if row.get("type") == "persistent"]

    assert ["status"] in fields
    assert col.TASK_TENANT_STATUS_INDEX_FIELDS in fields
    assert ["tenant_key", "status", "due_date"] not in fields
    (compound,) = _compound_indexes(db)
    assert (compound["unique"], compound["sparse"]) == (False, False)


def test_without_the_index_the_queue_reads_status_and_v0092_restores_it(db: StandardDatabase) -> None:
    tasks = db.collection(col.TASKS)
    for row in _compound_indexes(db):
        tasks.delete_index(row["id"])
    try:
        before = [_plan(db, query, bind_vars)[1] for query, bind_vars in _queue_queries(db)]

        report = migration.up(db)
        second = migration.up(db)
    finally:
        if not _compound_indexes(db):  # leave the module database bootstrapped for the other tests
            col.ensure_collections(db)

    # A volume that predates the index: the queue walks every pending task of the installation.
    assert before == [[["status"]], [["status"]]]
    assert (report.changed, second.changed) == (1, 0)
    (created,) = _compound_indexes(db)
    assert (created["unique"], created["sparse"]) == (False, False)
    for query, bind_vars in _queue_queries(db):
        assert _plan(db, query, bind_vars)[1] == [col.TASK_TENANT_STATUS_INDEX_FIELDS], query
