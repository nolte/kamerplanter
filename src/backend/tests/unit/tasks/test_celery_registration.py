"""Guard test: every task module under app/tasks must be registered with Celery.

Regression guard for the DINOv2 acquisition run silently failing with
``Received unregistered task ...`` because ``app.tasks.reference_image_tasks``
was missing from the Celery ``include`` list. A task module that is never
imported by a worker is never registered, so ``.delay()`` enqueues a message
no worker can execute.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import app.tasks as tasks_pkg
from app.tasks import celery_app

# Helper modules under app/tasks that hold no Celery tasks and must not be on
# the include list (e.g. the run_async_task bridge decorator, AP-18).
_NON_TASK_MODULES = {"__init__", "task_bridge"}


def _task_module_names() -> set[str]:
    """All importable task modules under app/tasks (excluding non-task helpers)."""
    pkg_dir = Path(tasks_pkg.__file__).parent
    return {f"app.tasks.{path.stem}" for path in pkg_dir.glob("*.py") if path.stem not in _NON_TASK_MODULES}


def test_all_task_modules_are_included():
    """Every task module is in the Celery include list (else its tasks are unregistered)."""
    included = set(celery_app.conf.include)
    missing = _task_module_names() - included
    assert not missing, f"Task modules not registered with Celery: {sorted(missing)}"


def test_acquire_all_reference_images_task_is_registered():
    """The UI-dispatched acquisition task must be a registered Celery task."""
    from app.tasks import reference_image_tasks  # noqa: F401  (import triggers registration)

    assert "app.tasks.reference_image_tasks.acquire_all_reference_images_task" in celery_app.tasks


def test_redispatch_stale_pending_exports_task_is_registered():
    """NFR-011 GAP-B5 safety-net task must be registered (else its .delay is a no-op)."""
    from app.tasks import retention_tasks  # noqa: F401  (import triggers registration)

    assert "retention.redispatch_stale_pending_exports" in celery_app.tasks


def test_redispatch_stale_exports_beat_entry_present():
    """The hourly re-dispatch safety net must be on the beat schedule."""
    entry = celery_app.conf.beat_schedule["retention-redispatch-stale-exports-hourly"]
    assert entry["task"] == "retention.redispatch_stale_pending_exports"


def test_worker_entrypoint_registers_weather_adapters():
    """Guard: booting the worker via ``app.tasks`` must populate the adapter registry.

    The Celery worker/beat boot with ``celery -A app.tasks`` and never import
    ``app.main``. The weather adapters register only as an import side effect of
    ``@WeatherAdapterRegistry.register``; if that import never runs in the worker
    process the REQ-046 fetch fails with ``weather_source_unknown`` and writes
    nothing. Run in a *fresh* subprocess so it mirrors a real worker boot and is
    immune to modules the test session already imported.
    """
    code = textwrap.dedent(
        """
        import app.tasks  # noqa: F401  worker entry point (NOT app.main)
        from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

        names = set(WeatherAdapterRegistry.all())
        required = {"open-meteo", "dwd", "openweathermap", "ha_weather"}
        missing = required - names
        assert not missing, f"weather adapters unregistered in worker process: {sorted(missing)}"
        print("REGISTRY_OK")
        """
    )
    backend_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    assert "REGISTRY_OK" in result.stdout
