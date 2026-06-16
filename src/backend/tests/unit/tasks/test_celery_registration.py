"""Guard test: every task module under app/tasks must be registered with Celery.

Regression guard for the DINOv2 acquisition run silently failing with
``Received unregistered task ...`` because ``app.tasks.reference_image_tasks``
was missing from the Celery ``include`` list. A task module that is never
imported by a worker is never registered, so ``.delay()`` enqueues a message
no worker can execute.
"""

from pathlib import Path

import app.tasks as tasks_pkg
from app.tasks import celery_app


def _task_module_names() -> set[str]:
    """All importable task modules under app/tasks (excluding the package init)."""
    pkg_dir = Path(tasks_pkg.__file__).parent
    return {f"app.tasks.{path.stem}" for path in pkg_dir.glob("*.py") if path.stem != "__init__"}


def test_all_task_modules_are_included():
    """Every task module is in the Celery include list (else its tasks are unregistered)."""
    included = set(celery_app.conf.include)
    missing = _task_module_names() - included
    assert not missing, f"Task modules not registered with Celery: {sorted(missing)}"


def test_acquire_all_reference_images_task_is_registered():
    """The UI-dispatched acquisition task must be a registered Celery task."""
    from app.tasks import reference_image_tasks  # noqa: F401  (import triggers registration)

    assert "app.tasks.reference_image_tasks.acquire_all_reference_images_task" in celery_app.tasks
