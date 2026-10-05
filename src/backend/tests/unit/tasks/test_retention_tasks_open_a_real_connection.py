"""#2150 — every database-backed retention task builds its connection the way the worker can.

Six tasks (``ai.cleanup_expired_conversations``, ``ai.cleanup_expired_audit_log``,
``glossary.cleanup_expired_cache``, ``glossary.invalidate_after_reingest``,
``mcp.cleanup_expired_audit_log``, ``mcp.cleanup_expired_idempotency``) called
``ArangoConnection()`` although the constructor has required the settings since the
first commit of the class. Measured on a real worker (2026-10-05): each run ended in
``TypeError: ArangoConnection.__init__() missing 1 required positional argument:
'settings'`` — since the tasks were added (2026-07-11/12), no run of these sweeps ever
reached the database. Their unit tests replaced the class with a bare ``MagicMock``,
which accepts any call, so they stayed green.

These tests do not replace the connection class. They replace only the one method a
unit test must not run — ``ArangoConnection.connect``, which opens the HTTP client
(the tier's ``db_guard`` blocks it) — and let the real constructor and the real
provider (``app.common.dependencies.get_db``) run. A wrong constructor call raises
here exactly as it raised in the worker. The task is
run through ``Task.apply()``, the path a worker takes (signals, request context).
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from app.common import dependencies
from app.data_access.arango.connection import ArangoConnection
from app.tasks import celery_app

#: task name -> (module, repository class name, repository method the task calls)
TASKS: dict[str, tuple[str, str, str]] = {
    "ai.cleanup_expired_conversations": ("ai_tasks", "ArangoAiConversationRepository", "delete_expired"),
    "ai.cleanup_expired_audit_log": ("ai_tasks", "ArangoAiAuditRepository", "delete_older_than"),
    "glossary.cleanup_expired_cache": ("glossary_tasks", "ArangoGlossaryTermCacheRepository", "delete_expired"),
    "glossary.invalidate_after_reingest": ("glossary_tasks", "ArangoGlossaryTermCacheRepository", "invalidate_all"),
    "mcp.cleanup_expired_audit_log": ("mcp_tasks", "ArangoMcpAuditRepository", "delete_expired"),
    "mcp.cleanup_expired_idempotency": ("mcp_tasks", "ArangoMcpIdempotencyRepository", "delete_expired"),
    "security_audit.purge_expired": ("security_audit_tasks", "ArangoSecurityAuditRepository", "delete_expired"),
}


@pytest.fixture
def arango_boundary(monkeypatch: pytest.MonkeyPatch) -> Iterator[MagicMock]:
    """A fresh provider singleton whose ``connect`` hands out a database double; yields that double."""
    monkeypatch.setattr(dependencies, "_connection", None)
    database = MagicMock(name="database")
    with patch.object(ArangoConnection, "connect", autospec=True, return_value=database):
        yield database


@pytest.mark.parametrize("task_name", sorted(TASKS))
def test_the_task_runs_on_the_provider_connection(task_name: str, arango_boundary: MagicMock) -> None:
    module_name, repo_name, method = TASKS[task_name]
    module = __import__(f"app.tasks.{module_name}", fromlist=[repo_name])
    repo = MagicMock()
    getattr(repo, method).return_value = 3
    repo.count_undated.return_value = 0

    with (
        patch.object(module, repo_name, return_value=repo) as repo_cls,
        patch("app.tasks.glossary_tasks.warm_glossary_cache"),
    ):
        result = celery_app.tasks[task_name].apply()

    assert result.successful(), f"{task_name} failed in the worker path: {result.result!r}"
    assert result.result == 3
    # The repository got the database the provider opened — not a second, private client.
    repo_cls.assert_called_once_with(arango_boundary)
    assert dependencies.get_connection().db is arango_boundary


def test_the_table_covers_every_task_in_these_modules() -> None:
    """A new database task in one of the four modules must be added above, or it is not exercised."""
    modules = {f"app.tasks.{module}" for module, _, _ in TASKS.values()}
    celery_app.loader.import_default_modules()
    registered = {
        name
        for name, task in celery_app.tasks.items()
        if task.__module__ in modules and name not in {"ai.knowledge_service_ingest", "glossary.warm_cache"}
    }
    assert registered == set(TASKS)
