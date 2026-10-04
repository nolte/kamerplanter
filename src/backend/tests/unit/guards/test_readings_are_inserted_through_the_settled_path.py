"""A sensor reading is written only through the path that asks again afterwards (#1944).

A reading stored for a sensor or tenant whose erasure ran between the ownership
check and the insert re-creates a raw row and, once the continuous aggregates
refresh, buckets for an owner nothing reaches again. The one path that closes it
is ``ObservationService``: it resolves whose a sensor is, inserts, asks again
(``_settle_after_insert``) and purges what it just wrote when the sensor went
meanwhile. The Home Assistant poll used to bypass it — it stored readings through
the repository directly, under ``tenant_key = ''``.

The class is "a caller of the readings store's insert". It is derived here from the
syntax tree of ``app/``: every ``insert`` / ``insert_batch`` call on an
observation repository must sit in ``ObservationService`` and in a function that
also calls ``_settle_after_insert``. The non-vacuity tests prove the predicate
flags a direct caller and sees today's sites.
"""

from __future__ import annotations

import ast
import pathlib
import textwrap

APP_ROOT = pathlib.Path(__file__).resolve().parents[3] / "app"

_SERVICE_FILE = "domain/services/observation_service.py"
_INSERTS = frozenset({"insert", "insert_batch"})
_SETTLE = "_settle_after_insert"
#: The repository's own definition site is not a caller.
_DEFINITIONS = ("data_access/timescale/", "domain/interfaces/")


def _receiver(call: ast.Call) -> str:
    func = call.func
    if not isinstance(func, ast.Attribute):
        return ""
    value = func.value
    if isinstance(value, ast.Attribute):
        return value.attr
    if isinstance(value, ast.Name):
        return value.id
    return ""


def _insert_calls(node: ast.AST) -> list[ast.Call]:
    return [
        c
        for c in ast.walk(node)
        if isinstance(c, ast.Call)
        and isinstance(c.func, ast.Attribute)
        and c.func.attr in _INSERTS
        and _receiver(c).endswith(("obs_repo", "observation_repo"))
    ]


def _settles(node: ast.AST) -> bool:
    return any(
        isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == _SETTLE for c in ast.walk(node)
    )


def _findings(tree: ast.Module, label: str, *, is_service: bool) -> tuple[list[str], int]:
    problems: list[str] = []
    sites = 0
    for function in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)):
        calls = _insert_calls(function)
        if not calls:
            continue
        sites += len(calls)
        if is_service and _settles(function):
            continue
        problems.extend(f"{label}:{c.lineno} ({function.name})" for c in calls)
    return problems, sites


def _scan() -> tuple[list[str], int]:
    problems: list[str] = []
    sites = 0
    for path in sorted(APP_ROOT.rglob("*.py")):
        relative = path.relative_to(APP_ROOT).as_posix()
        if relative.startswith(_DEFINITIONS):
            continue
        found, count = _findings(
            ast.parse(path.read_text(encoding="utf-8")), relative, is_service=relative == _SERVICE_FILE
        )
        problems.extend(found)
        sites += count
    return problems, sites


def test_every_reading_is_inserted_through_a_function_that_settles_afterwards():
    problems, sites = _scan()
    assert not problems, (
        "a sensor reading is inserted without ObservationService._settle_after_insert — it can re-create a series "
        "for an owner whose erasure already ran (#1944):\n" + "\n".join(problems)
    )
    assert sites >= 2, f"the sweep saw {sites} insert calls; record_reading and record_readings_batch exist today"


# ── non-vacuity ─────────────────────────────────────────────────────


def test_the_sweep_flags_a_direct_caller_outside_the_service():
    tree = ast.parse(
        textwrap.dedent(
            """
            def poll(obs_repo, readings):
                return obs_repo.insert_batch(readings)
            """
        )
    )
    problems, sites = _findings(tree, "task.py", is_service=False)
    assert (sites, problems) == (1, ["task.py:3 (poll)"])


def test_the_sweep_flags_a_service_function_that_does_not_settle():
    tree = ast.parse(
        textwrap.dedent(
            """
            class S:
                def record(self, r):
                    self._obs_repo.insert(r)
            """
        )
    )
    problems, _ = _findings(tree, _SERVICE_FILE, is_service=True)
    assert problems == [f"{_SERVICE_FILE}:4 (record)"]


def test_the_sweep_accepts_a_service_function_that_settles():
    tree = ast.parse(
        textwrap.dedent(
            """
            class S:
                def record(self, r):
                    self._obs_repo.insert(r)
                    self._settle_after_insert(r.sensor_key, tenant_key="t")
            """
        )
    )
    assert _findings(tree, _SERVICE_FILE, is_service=True) == ([], 1)


def test_the_sweep_ignores_an_unrelated_insert():
    tree = ast.parse("def f(db, doc):\n    db.insert(doc)\n    self.collection.insert(doc)\n")
    assert _findings(tree, "x.py", is_service=False) == ([], 0)
