"""Unit tests for external-source enrichment Celery tasks (REQ-011).

The task module imports its dependency getter (``get_enrichment_engine``),
``AdapterRegistry`` and ``SyncTrigger`` at module level. Both the getter and
``AdapterRegistry`` are therefore module attributes of ``enrichment_tasks``
and are patched in place per test — the module is imported once and its
identity kept stable, so the Celery task instance bound to ``self`` at call
time is the same object the tests patch.

``sync_source_task`` is ``bind=True``; calling ``.run(...)`` invokes the
underlying function with the bound task instance as ``self``, so the task's
own ``retry`` is patched to make the retry branch observable.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def _task_module():
    import app.tasks.enrichment_tasks as module

    # ``get_enrichment_engine`` is imported into the task module's namespace,
    # so patch it there rather than re-importing the module (which would create
    # a fresh task instance and break the ``self.retry`` patch in the full
    # suite). ``deps`` exposes the patched getter for backwards compatibility.
    with patch.object(module, "get_enrichment_engine") as get_engine:
        yield module, SimpleNamespace(get_enrichment_engine=get_engine)


class TestSyncSourceTask:
    def test_returns_run_summary(self, _task_module):
        module, deps = _task_module
        run = SimpleNamespace(
            status=SimpleNamespace(value="success"),
            total_processed=10,
            new_mappings=4,
            updated_mappings=2,
        )
        engine = MagicMock()
        engine.sync_source.return_value = run
        deps.get_enrichment_engine.return_value = engine

        with patch.object(module, "AdapterRegistry") as registry:
            registry.get.return_value = MagicMock()

            result = module.sync_source_task.run("gbif", full_sync=False)

        assert result == {
            "source_key": "gbif",
            "status": "success",
            "total_processed": 10,
            "new_mappings": 4,
            "updated_mappings": 2,
        }
        engine.sync_source.assert_called_once()

    def test_retries_on_failure(self, _task_module):
        module, deps = _task_module
        deps.get_enrichment_engine.return_value = MagicMock()

        with (
            patch.object(module, "AdapterRegistry") as registry,
            patch.object(module.sync_source_task, "retry") as retry,
        ):
            registry.get.side_effect = RuntimeError("adapter boom")
            retry.side_effect = RuntimeError("retry-raised")

            with pytest.raises(RuntimeError, match="retry-raised"):
                module.sync_source_task.run("gbif")

            retry.assert_called_once()


class TestSyncAllSourcesTask:
    def test_dispatches_each_source(self, _task_module, monkeypatch):
        module, _deps = _task_module
        dispatch_mock = MagicMock()

        with patch.object(module, "AdapterRegistry") as registry:
            registry.all_keys.return_value = ["gbif", "perenual"]
            # Patch via monkeypatch so the substitution is reverted after the
            # test and does not leak into the rest of the suite.
            monkeypatch.setattr(module, "sync_source_task", dispatch_mock)

            result = module.sync_all_sources_task.run(full_sync=True)

        assert result == {"dispatched": ["gbif", "perenual"]}
        assert dispatch_mock.delay.call_count == 2
        dispatch_mock.delay.assert_any_call("gbif", full_sync=True)
