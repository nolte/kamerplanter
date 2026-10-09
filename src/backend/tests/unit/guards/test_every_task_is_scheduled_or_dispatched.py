"""MT-051 (#2144): every Celery task is scheduled, dispatched, or a reviewed exception.

The audit found three tasks — ``check_auto_transitions``, ``check_dormancy_triggers``
and ``update_vernalization_progress`` — that were registered, routed to a queue
(``app/tasks/routing.py``, #2128) and described as running, but that nothing ever
started: no beat entry, no ``.delay``/``.apply_async`` anywhere. "Implemented but
inert", the shape the queue guard (``test_every_task_has_a_queue``) cannot see,
because a routed task that nobody publishes is perfectly routed.

Measured against the live registry (``celery_app.tasks`` after importing every
``include`` module), each task is one of:

1. **scheduled** — named by a ``"task": "<name>"`` entry anywhere in
   ``app/tasks/__init__.py``, including the entries behind a feature flag (read
   from the source, not from ``beat_schedule``, so a flag that is off in the test
   environment does not make a scheduled task look inert);
2. **dispatched** — some module under ``app/`` calls ``.delay``, ``.apply_async``,
   ``.s``, ``.si`` or ``.signature`` on it (directly, or on a local variable bound
   from an expression naming it), or ``send_task("<name>")``;
3. **listed** in :data:`_NOT_STARTED_BY_THE_APP` with the reason it is neither.

A listed task that becomes scheduled or dispatched fails (the entry must go), so
the list cannot keep excusing a task that no longer needs it.

Spellings this does not see: a task started from outside ``app/`` (a script, the
chart, ``celery call`` by an operator — which is exactly what the operator-only
entries below say), a dispatch through ``getattr``/a registry lookup by string
other than ``send_task``, and a receiver bound in another function than the call.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from app.tasks import celery_app

APP = Path(__file__).resolve().parents[3] / "app"
_BEAT_SOURCE = APP / "tasks" / "__init__.py"
_DISPATCH = {"delay", "apply_async", "s", "si", "signature"}

#: Decision record per task, operator-overturnable (MT-051, #2144). Each reason says
#: why the task is not scheduled *and* what would have to change for it to be.
_NOT_STARTED_BY_THE_APP: dict[str, str] = {
    "check_auto_transitions": (
        "inert since it was written (MT-051). Not scheduled on purpose: it reads every plant of every "
        "tenant (get_all_pages(all_tenants=True)) and runs several queries per plant — the unchunked "
        "all-tenant beat read #2128 is reworking. Schedule it (daily) once that chunking lands; until then "
        "phase transitions are manual, as they have been in production all along."
    ),
    "check_dormancy_triggers": (
        "inert since it was written (MT-051). Not schedulable as it stands: its signature takes ONE "
        "installation-wide temperature and day length (current_temp_c, day_length_hours), while dormancy "
        "depends on each plant's site weather — a beat entry has no value to pass. Needs a per-site input "
        "(REQ-046 weather) and the #2128 chunking before it can run."
    ),
    "update_vernalization_progress": (
        "inert since it was written (MT-051). Not schedulable as it stands: one installation-wide "
        "avg_temp_c for every plant; chill days are per site. Same prerequisite as "
        "check_dormancy_triggers (per-site weather input + #2128 chunking)."
    ),
    "glossary.invalidate_after_reingest": (
        "documented as 'chained after ai.knowledge_service_ingest' but nothing chains it (found by this "
        "guard, #2144). Not wired here on purpose: it drops the whole glossary cache and queues a warm-up "
        "of one LLM call per term and variant — wiring it to the weekly reingest is a cost decision "
        "(REQ-035 §4.3, AI budget #2110) for the operator. Until then the cache expires by its TTL."
    ),
    "app.tasks.storage_tasks.migrate_storage": (
        "operator-invoked one-off (NFR-013 §7.3 AC-07): moves object storage between backends with "
        "explicit source/target arguments; started by hand (celery call), never scheduled."
    ),
    "app.tasks.storage_tasks.migrate_photo_refs": (
        "operator-invoked one-off (NFR-013 §2.2 AC-09): dry-run by default since #1438, applied by an "
        "explicit dry_run=False from an operator; never scheduled."
    ),
}


def _registered() -> dict[str, Any]:
    celery_app.loader.import_default_modules()
    return {name: task for name, task in celery_app.tasks.items() if not name.startswith("celery.")}


def _scheduled() -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(_BEAT_SOURCE.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=True):
                if (
                    isinstance(key, ast.Constant)
                    and key.value == "task"
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                ):
                    names.add(value.value)
    return names


def _identifiers(node: ast.AST) -> set[str]:
    found: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            found.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            found.add(sub.attr)
    return found


def _dispatched() -> tuple[set[str], set[str]]:
    """(function identifiers a dispatch call reaches, task names passed to ``send_task``)."""
    identifiers: set[str] = set()
    sent: set[str] = set()
    for path in sorted(APP.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        scopes = [tree, *(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef))]
        for scope in scopes:
            bound: dict[str, list[ast.expr]] = {}
            for node in ast.walk(scope):
                if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    bound.setdefault(node.targets[0].id, []).append(node.value)
            for node in ast.walk(scope):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                    continue
                if node.func.attr in _DISPATCH:
                    reached = _identifiers(node.func.value)
                    for name in list(reached):
                        for value in bound.get(name, []):
                            reached |= _identifiers(value)
                    identifiers |= reached
                elif node.func.attr == "send_task" and node.args and isinstance(node.args[0], ast.Constant):
                    sent.add(str(node.args[0].value))
    return identifiers, sent


def _started() -> dict[str, str]:
    """Registered task name -> how the app starts it (``""`` when it does not)."""
    scheduled = _scheduled()
    identifiers, sent = _dispatched()
    how: dict[str, str] = {}
    for name, task in _registered().items():
        function = getattr(getattr(task, "run", None), "__name__", "")
        if name in scheduled:
            how[name] = "scheduled"
        elif name in sent or function in identifiers:
            how[name] = "dispatched"
        else:
            how[name] = ""
    return how


def test_every_task_is_scheduled_dispatched_or_a_reviewed_exception() -> None:
    how = _started()
    assert len(how) >= 60, "the registry is derived; a near-empty one would pass vacuously"
    print(f"tasks: {len(how)}; not started by the app: {sorted(n for n, h in how.items() if not h)}")  # noqa: T201

    inert = sorted(name for name, started in how.items() if not started and name not in _NOT_STARTED_BY_THE_APP)

    assert inert == [], (
        "Celery tasks that nothing schedules or dispatches (MT-051) — schedule them, dispatch them, delete "
        "them, or list them in _NOT_STARTED_BY_THE_APP with the reason:\n  " + "\n  ".join(inert)
    )


def test_no_listed_task_is_started_or_gone() -> None:
    how = _started()

    gone = sorted(name for name in _NOT_STARTED_BY_THE_APP if name not in how)
    started = sorted(f"{name} ({how[name]})" for name in _NOT_STARTED_BY_THE_APP if how.get(name))

    assert gone == [], f"listed tasks that are not registered any more: {gone}"
    assert started == [], f"listed tasks that the app now starts — remove their entry: {started}"


def test_the_sweep_sees_both_ways_in() -> None:
    """A predicate that found nothing would be green over nothing — pin one of each kind."""
    how = _started()

    assert how["retention.purge_expired_consent_records"] == "scheduled"
    assert how["app.tasks.storage_tasks.generate_thumbnails"] == "dispatched"
    # Behind a feature flag: read from the source, not from the live beat_schedule.
    assert how["app.tasks.weather_tasks.fetch_weather_forecasts"] == "scheduled"
