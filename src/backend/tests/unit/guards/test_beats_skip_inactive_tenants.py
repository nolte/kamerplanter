"""REQ-056 §5.2 (AK-07) — every beat is classified, and every tenant-writing beat asks the tenant's state.

The defect class: the ``ActiveTenants`` gate (#2166) is opt-in at the call site. #2166 put it
into the care, watering, notification, frost and three tank beats; measured on develop
afterwards, 13 more beats that write into a tenant or notify about one went on processing a
``suspended`` or ``pending_deletion`` tenant (tank alerts, the e-mail digest, Home Assistant
ingestion, the weather, climate-normal and hardiness refreshes, irrigation demand, both season
beats, both InvenTree syncs, two actuator beats). A hand list of gated tasks cannot notice the
next beat nobody gated, so this guard starts from the **schedule**:

* every ``"task": "<name>"`` in a dict literal of ``app/tasks/__init__.py`` — the
  unconditional ``beat_schedule`` *and* the entries added behind a feature flag, read from
  the source so a flag that is off in the test environment hides nothing — is in exactly one
  of :data:`~app.tasks.tenant_gate.TENANT_WRITING_BEATS` and
  :data:`~app.tasks.tenant_gate.TENANT_AGNOSTIC_BEATS` (a classification naming no scheduled
  task fails too, so the lists cannot go stale);
* the function of every tenant-writing beat reaches the gate: its body, or a function or
  class of the same module it names (transitively), names ``ActiveTenants`` or compares
  with ``TenantStatus.ACTIVE``.

**Spellings this predicate cannot see:** a gate in another module the task calls (the
predicate follows same-module names only — move the gate into the task module), a gate that
is constructed but never asked (the per-beat behaviour tests in
``tests/unit/tasks/test_beats_skip_inactive_tenants.py`` and
``test_care_beats_skip_closed_tenants.py`` hold what each beat does), and a beat registered
outside ``app/tasks/__init__.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.tasks.tenant_gate import TENANT_AGNOSTIC_BEATS, TENANT_WRITING_BEATS

TASKS = Path(__file__).resolve().parents[3] / "app" / "tasks"

_Def = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


def _scheduled_task_names() -> set[str]:
    tree = ast.parse((TASKS / "__init__.py").read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values, strict=True):
            if isinstance(key, ast.Constant) and key.value == "task":
                assert isinstance(value, ast.Constant), "a beat task name must be a literal"
                names.add(value.value)
    return names


def _registered_name(module: str, func: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """The Celery name a decorator gives *func*: ``name=`` or the default ``app.tasks.<module>.<func>``."""
    for decorator in func.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        is_task = (isinstance(target, ast.Attribute) and target.attr == "task") or (
            isinstance(target, ast.Name) and target.id == "run_async_task"
        )
        if not is_task:
            continue
        for keyword in getattr(decorator, "keywords", []):
            if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                return str(keyword.value.value)
        return f"app.tasks.{module}.{func.name}"
    return None


def _task_index() -> dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, dict[str, _Def]]]:
    index: dict[str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, dict[str, _Def]]] = {}
    for path in sorted(TASKS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        defs: dict[str, _Def] = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        }
        for node in defs.values():
            if isinstance(node, ast.ClassDef):
                continue
            name = _registered_name(path.stem, node)
            if name is not None:
                index[name] = (node, defs)
    return index


def _asks_the_tenant_state(node: _Def, defs: dict[str, _Def], seen: set[str] | None = None) -> bool:
    seen = seen if seen is not None else {node.name}
    for inner in ast.walk(node):
        if isinstance(inner, ast.Name) and inner.id == "ActiveTenants":
            return True
        if (
            isinstance(inner, ast.Attribute)
            and inner.attr == "ACTIVE"
            and isinstance(inner.value, ast.Name)
            and inner.value.id == "TenantStatus"
        ):
            return True
        named = inner.id if isinstance(inner, ast.Name) else None
        if named in defs and named not in seen:
            seen.add(named)
            if _asks_the_tenant_state(defs[named], defs, seen):
                return True
    return False


def test_every_scheduled_beat_is_classified_exactly_once() -> None:
    scheduled = _scheduled_task_names()
    classified = TENANT_WRITING_BEATS | set(TENANT_AGNOSTIC_BEATS)

    assert TENANT_WRITING_BEATS.isdisjoint(TENANT_AGNOSTIC_BEATS), "a beat is classified twice"
    assert sorted(scheduled - classified) == [], "a scheduled beat is in neither TENANT_*_BEATS list"
    assert sorted(classified - scheduled) == [], "a classification names no scheduled beat any more"
    assert all(reason.strip() for reason in TENANT_AGNOSTIC_BEATS.values())


def test_the_schedule_read_covers_the_flagged_beats_too() -> None:
    """The source read sees the entries behind a feature flag (off in the test environment)."""
    scheduled = _scheduled_task_names()

    assert {
        "inventree.sync_stock_levels",
        "app.tasks.sensor_ingestion_tasks.ingest_ha_readings",
        "app.tasks.weather_tasks.fetch_weather_forecasts",
        "app.tasks.actuator_tasks.evaluate_control_rules",
        "app.tasks.season_tasks.evaluate_quarter_climate",
    } <= scheduled
    assert len(scheduled) == len(TENANT_WRITING_BEATS) + len(TENANT_AGNOSTIC_BEATS) == 49


def test_every_tenant_writing_beat_asks_the_tenant_state() -> None:
    index = _task_index()

    unresolved = sorted(TENANT_WRITING_BEATS - set(index))
    ungated = sorted(name for name in TENANT_WRITING_BEATS & set(index) if not _asks_the_tenant_state(*index[name]))

    assert unresolved == [], "a tenant-writing beat whose function the index cannot find"
    assert ungated == [], "a tenant-writing beat that never asks ActiveTenants (REQ-056 §5.2)"


def test_the_predicate_tells_an_ungated_beat_from_a_gated_one() -> None:
    """Negative control: the predicate is not satisfied by any function at all."""
    tree = ast.parse(
        "def _helper():\n"
        "    return ActiveTenants(repo)\n"
        "def gated():\n"
        "    gate = _helper()\n"
        "def by_status(doc):\n"
        "    return doc.status == TenantStatus.ACTIVE\n"
        "def ungated():\n"
        "    return [t for t in get_all_pages(repo, all_tenants=True)]\n"
        "def other_status(doc):\n"
        "    return doc.status == TenantStatus.SUSPENDED\n"
    )
    defs: dict[str, _Def] = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}

    assert _asks_the_tenant_state(defs["gated"], defs)
    assert _asks_the_tenant_state(defs["by_status"], defs)
    assert not _asks_the_tenant_state(defs["ungated"], defs)
    assert not _asks_the_tenant_state(defs["other_status"], defs)
