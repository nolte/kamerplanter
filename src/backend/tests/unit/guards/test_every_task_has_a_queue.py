"""MT-032 (#2128) class guard: every Celery task is routed to a queue a worker consumes.

Until #2128 the worker had one queue and nothing to decide. With three
(``app/tasks/routing.py``) two failure modes appear, and both are silent:

* a task routed to a queue no worker consumes waits in Redis forever — the
  stranded-task mode; Celery reports nothing, the beat keeps publishing;
* a new task nobody classified lands wherever the default sends it, which is
  correct only by luck.

So, measured against the live registry (``celery_app.tasks`` after importing every
``include`` module) and the live configuration:

1. every registered task is in exactly one of ``CRITICAL_TASKS``, ``DEFAULT_TASKS``,
   ``BULK_TASKS`` — and every name there is registered (no stale entry routing a
   task that was renamed);
2. Celery's router really sends each task to its queue (``celery_app.amqp.router``,
   the code ``apply_async`` runs), and every target queue is declared in
   ``task_queues`` — a worker without ``-Q`` consumes exactly the declared set;
3. every beat entry routes to a declared queue;
4. every worker container in every chart values profile consumes every queue:
   either it passes no queue selection (then it consumes ``task_queues``) or its
   ``-Q``/``--queues`` list covers :data:`QUEUES` and it excludes none;
5. the Redis ``visibility_timeout`` is longer than the longest hard time limit any
   task can have, so a message reserved behind a running task is not handed out
   twice.

Spellings this does NOT see: a task published by name with an explicit
``queue=`` option at the call site (``send_task(..., queue="x")``), and a worker
started outside the chart (a GitOps overlay that replaces ``args`` is read only
if it is one of this repository's values files).
"""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

import pytest
import yaml

from app.tasks import celery_app
from app.tasks.routing import (
    BULK_TASKS,
    CRITICAL_TASKS,
    DEFAULT_TASKS,
    LONG_TIME_LIMIT_SECONDS,
    QUEUE_DEFAULT,
    QUEUES,
    TIME_LIMIT_SECONDS,
    VISIBILITY_TIMEOUT_SECONDS,
)

_CHART = Path(__file__).resolve().parents[5] / "helm" / "kamerplanter"
_BASE = _CHART / "values.yaml"
_WORKER_CONTROLLERS_PREFIX = "celery-worker"


def _registered() -> dict[str, Any]:
    celery_app.loader.import_default_modules()
    return {name: task for name, task in celery_app.tasks.items() if not name.startswith("celery.")}


def _declared_queues() -> set[str]:
    return {queue.name for queue in celery_app.conf.task_queues}


def test_every_registered_task_is_classified_exactly_once() -> None:
    registered = set(_registered())
    assert len(registered) >= 60, "the registry is derived; a near-empty one would pass vacuously"
    sets = {"critical": CRITICAL_TASKS, "default": DEFAULT_TASKS, "bulk": BULK_TASKS}
    twice = sorted(name for name in registered if sum(name in members for members in sets.values()) > 1)
    unclassified = sorted(registered - CRITICAL_TASKS - DEFAULT_TASKS - BULK_TASKS)
    stale = sorted((CRITICAL_TASKS | DEFAULT_TASKS | BULK_TASKS) - registered)
    assert not twice, f"tasks in more than one queue set: {twice}"
    assert not unclassified, f"tasks without a queue decision in app/tasks/routing.py: {unclassified}"
    assert not stale, f"queue sets name tasks that are not registered: {stale}"


def test_the_default_queue_keeps_its_name_and_every_queue_is_declared() -> None:
    assert celery_app.conf.task_default_queue == QUEUE_DEFAULT == "celery"
    assert _declared_queues() == set(QUEUES)


@pytest.mark.parametrize(
    ("members", "queue"),
    [(CRITICAL_TASKS, "critical"), (DEFAULT_TASKS, "celery"), (BULK_TASKS, "bulk")],
    ids=["critical", "default", "bulk"],
)
def test_the_router_sends_each_task_to_its_queue(members: frozenset[str], queue: str) -> None:
    router = celery_app.amqp.router
    wrong = {}
    for name in sorted(members):
        routed = router.route({}, name, (), {})["queue"].name
        if routed != queue:
            wrong[name] = routed
    assert not wrong, f"routed elsewhere than declared (expected {queue!r}): {wrong}"
    assert queue in _declared_queues()


def test_every_beat_entry_routes_to_a_declared_queue() -> None:
    router = celery_app.amqp.router
    declared = _declared_queues()
    entries = celery_app.conf.beat_schedule
    assert len(entries) >= 20
    undeclared = {
        key: router.route({}, entry["task"], (), {})["queue"].name
        for key, entry in entries.items()
        if router.route({}, entry["task"], (), {})["queue"].name not in declared
    }
    assert not undeclared, f"beat entries routed to a queue no worker declares: {undeclared}"


def test_no_task_outlives_the_visibility_timeout() -> None:
    longest = max(
        [TIME_LIMIT_SECONDS, LONG_TIME_LIMIT_SECONDS]
        + [task.time_limit for task in _registered().values() if task.time_limit]
    )
    assert celery_app.conf.broker_transport_options["visibility_timeout"] == VISIBILITY_TIMEOUT_SECONDS
    assert longest < VISIBILITY_TIMEOUT_SECONDS, (
        f"visibility_timeout {VISIBILITY_TIMEOUT_SECONDS}s <= longest hard limit {longest}s: a reserved message "
        "would be redelivered while the task ahead of it still runs"
    )


# --- the chart ---------------------------------------------------------------


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _helm_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if value is None:
            merged.pop(key, None)
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _helm_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def consumed_queues(args: list[str]) -> set[str] | None:
    """Queues a ``celery … worker`` command line consumes; ``None`` = every declared queue.

    Raises ``ValueError`` for an exclusion (``-X``/``--exclude-queues``): a worker that
    excludes a queue strands it unless another worker consumes it, which the chart
    cannot show.
    """
    tokens = [token for arg in args for token in shlex.split(arg)]
    selected: set[str] | None = None
    for index, token in enumerate(tokens):
        value: str | None = None
        if token in {"-Q", "--queues"} and index + 1 < len(tokens):
            value = tokens[index + 1]
        elif token.startswith("--queues="):
            value = token.split("=", 1)[1]
        elif token.startswith("-Q") and len(token) > 2:
            value = token[2:]
        elif token in {"-X", "--exclude-queues"} or token.startswith(("--exclude-queues=", "-X")):
            raise ValueError(f"queue exclusion in worker args: {args}")
        if value is not None:
            selected = (selected or set()) | {queue for queue in value.split(",") if queue}
    return selected


def _worker_commands() -> list[tuple[str, str, list[str]]]:
    files = sorted(_CHART.glob("values*.yaml"))
    assert _BASE in files
    found = []
    for path in files:
        values = _load(_BASE) if path == _BASE else _helm_merge(_load(_BASE), _load(path))
        for name, controller in (values.get("controllers") or {}).items():
            if not name.startswith(_WORKER_CONTROLLERS_PREFIX) or controller.get("enabled") is False:
                continue
            for container_name, container in (controller.get("containers") or {}).items():
                args = [str(arg) for arg in (container.get("command") or []) + (container.get("args") or [])]
                if "worker" in args:
                    found.append((path.name, f"{name}/{container_name}", args))
    return found


def test_every_chart_worker_consumes_every_queue() -> None:
    commands = _worker_commands()
    assert any(profile == "values.yaml" for profile, _, _ in commands), "the base chart runs no worker"
    missing = {}
    for profile, container, args in commands:
        consumed = consumed_queues(args)
        if consumed is not None and not set(QUEUES) <= consumed:
            missing[f"{profile}:{container}"] = sorted(set(QUEUES) - consumed)
    assert not missing, f"worker containers that do not consume every queue (tasks there would strand): {missing}"


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["-A", "app.tasks", "worker"], None),
        (["-A", "app.tasks", "worker", "-Q", "critical,celery,bulk"], {"critical", "celery", "bulk"}),
        (["-A", "app.tasks", "worker", "--queues=critical,celery"], {"critical", "celery"}),
        (["-A", "app.tasks", "worker", "-Qbulk"], {"bulk"}),
        (["-A app.tasks worker --queues critical -Q bulk"], {"critical", "bulk"}),
    ],
)
def test_the_queue_parser_reads_every_spelling(args: list[str], expected: set[str] | None) -> None:
    assert consumed_queues(args) == expected


@pytest.mark.parametrize("flag", ["-X", "--exclude-queues", "--exclude-queues=bulk", "-Xbulk"])
def test_the_queue_parser_refuses_exclusions(flag: str) -> None:
    with pytest.raises(ValueError, match="exclusion"):
        consumed_queues(["-A", "app.tasks", "worker", flag, "bulk"])
