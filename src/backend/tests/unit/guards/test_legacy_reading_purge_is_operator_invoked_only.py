"""The legacy-reading purge is reachable from the operator command and from nowhere else (#2077).

``purge_legacy_series`` deletes a sensor's rows under the empty tenant key from
every readings table. The operator decided (2026-10-04) that this happens only
after a human confirmed the count a dry run printed: no migration, no beat task,
no request path may call it. The class is "a caller of the purge, or an importer
of the command / its service". It is derived from the syntax tree of ``app/``; the
non-vacuity tests prove the predicate sees a caller and an importer.
"""

from __future__ import annotations

import ast
import pathlib

APP_ROOT = pathlib.Path(__file__).resolve().parents[3] / "app"

_PURGE = "purge_legacy_series"
#: The definition, the one service that drives it behind the confirmation, and its command.
_ALLOWED_CALLERS = frozenset({"domain/services/legacy_reading_cleanup.py"})
_DEFINITIONS = frozenset({"domain/interfaces/legacy_reading_store.py", "data_access/timescale/legacy_reading_store.py"})
#: Modules only the operator command may import (the command itself is run with ``python -m``).
_OPERATOR_ONLY = ("app.migrations.purge_orphan_ha_readings", "app.domain.services.legacy_reading_cleanup")
_ALLOWED_IMPORTERS = frozenset({"migrations/purge_orphan_ha_readings.py"})


def _purge_calls(tree: ast.AST) -> list[int]:
    return [
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == _PURGE
    ]


def _operator_imports(tree: ast.AST) -> list[int]:
    lines: list[int] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module is not None:
            names = {n.module, *(f"{n.module}.{a.name}" for a in n.names)}
            if names & set(_OPERATOR_ONLY):
                lines.append(n.lineno)
        elif isinstance(n, ast.Import) and any(a.name in _OPERATOR_ONLY for a in n.names):
            lines.append(n.lineno)
    return lines


def _scan() -> tuple[list[str], int]:
    problems: list[str] = []
    seen = 0
    for path in sorted(APP_ROOT.rglob("*.py")):
        relative = path.relative_to(APP_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = _purge_calls(tree) if relative not in _DEFINITIONS else []
        seen += len(calls)
        if calls and relative not in _ALLOWED_CALLERS:
            problems.extend(f"{relative}:{line} calls {_PURGE}" for line in calls)
        imports = _operator_imports(tree)
        if imports and relative not in _ALLOWED_IMPORTERS:
            problems.extend(f"{relative}:{line} imports the operator-only cleanup" for line in imports)
    return problems, seen


def test_the_purge_is_called_by_the_confirmed_cleanup_only() -> None:
    problems, seen = _scan()
    assert not problems, "the legacy-reading purge must stay operator-invoked (#2077):\n" + "\n".join(problems)
    assert seen == 1, f"the sweep saw {seen} purge calls; the cleanup service has exactly one"


def _code_tokens(tree: ast.AST) -> set[str]:
    """Names, attributes and string constants of the executable code — never a comment or a docstring's prose."""
    tokens: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            tokens.add(n.id)
        elif isinstance(n, ast.Attribute):
            tokens.add(n.attr)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            tokens.add(n.value)
        elif isinstance(n, ast.alias):
            tokens.add(n.name)
    return tokens


def test_the_beat_schedule_names_no_legacy_cleanup() -> None:
    schedules = 0
    for path in sorted(APP_ROOT.rglob("*.py")):
        tokens = _code_tokens(ast.parse(path.read_text(encoding="utf-8")))
        if "beat_schedule" not in tokens:
            continue
        schedules += 1
        text = " ".join(tokens)
        assert "purge_orphan_ha_readings" not in text and "legacy_reading_cleanup" not in text, path.name
    assert schedules, "the sweep found no beat schedule at all"


# ── non-vacuity ─────────────────────────────────────────────────────


def test_the_predicate_sees_a_caller() -> None:
    assert _purge_calls(ast.parse("def f(store):\n    store.purge_legacy_series('k')\n")) == [2]
    assert _purge_calls(ast.parse("def f(store):\n    store.purge_other('k')\n")) == []


def test_the_predicate_sees_an_importer() -> None:
    assert _operator_imports(ast.parse("from app.migrations import purge_orphan_ha_readings\n")) == [1]
    assert _operator_imports(ast.parse("from app.domain.services.legacy_reading_cleanup import X\n")) == [1]
    assert _operator_imports(ast.parse("import app.migrations.purge_orphan_ha_readings\n")) == [1]
    assert _operator_imports(ast.parse("from app.domain.services import observation_service\n")) == []


def test_the_token_reader_ignores_prose_and_sees_code() -> None:
    prose = ast.parse("# beat_schedule\nx = 1\n")
    code = ast.parse("app.conf.beat_schedule = {'a': 1}\n")
    assert "beat_schedule" not in _code_tokens(prose)
    assert "beat_schedule" in _code_tokens(code)
