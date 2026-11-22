"""The adjacency dispatch is wired where it matters (REQ-053 GP-NFR-016, #2393).

A dispatcher that is injected and optional is inert in exactly the place nobody tests: the production
factory that forgot to pass it. These tests read the factories' source and the dispatcher's call.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import app.common.dependencies as dependencies
from app.tasks.adjacency import TASK_NAME

_SOURCE = Path(dependencies.__file__)


def _constructor_keywords(class_name: str) -> list[set[str]]:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    return [
        {kw.arg for kw in node.keywords if kw.arg}
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == class_name
    ]


@pytest.mark.parametrize("service", ["GardenResourceService", "PlantingReservationService"])
def test_the_production_factory_passes_the_dispatcher(service: str) -> None:
    constructions = _constructor_keywords(service)
    assert constructions, f"{service} is no longer built in app/common/dependencies.py"
    assert all("dispatch_adjacency" in keywords for keywords in constructions)


def test_the_dispatcher_queues_the_registered_task_with_only_the_bed_key() -> None:
    celery = MagicMock()
    with patch("app.tasks.celery_app", celery):
        dependencies.dispatch_adjacency_recompute("bed_1")
    celery.send_task.assert_called_once()
    args, kwargs = celery.send_task.call_args
    assert args == (TASK_NAME,)
    assert kwargs["args"] == ("bed_1",)
    assert set(kwargs) <= {"args", "retry", "retry_policy"}


def test_the_task_name_the_dispatcher_sends_is_the_one_the_worker_registers() -> None:
    from app.tasks import celery_app

    source = ast.unparse(ast.parse(_SOURCE.read_text(encoding="utf-8")))
    assert f"'{TASK_NAME}'" in source
    assert TASK_NAME in celery_app.tasks
