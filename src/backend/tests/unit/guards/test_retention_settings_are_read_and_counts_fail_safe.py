"""#1955/#1800 class guard: a retention period is enforced, and a report never fails the enforcement.

Two rules over the retention surface of ``app/``.

**Every ``retention_*`` setting has a reader.** A ``Settings`` field named
``retention_*`` that no code under ``app/`` (outside ``config/settings.py``) reads as an
attribute is inert: the operator can set it and nothing changes (#1800 measured
``RETENTION_INVITATION_RETENTION_DAYS`` and the sensor settings in that state). The
field set is derived from ``Settings.model_fields``, the readers from an AST walk, so a
new setting joins the rule without an edit here.

**A report-only counter never runs bare.** Any ``<x>.count_*(...)`` call in
``domain/services/privacy_service.py``, ``tasks/retention_tasks.py``,
``tasks/auth_tasks.py`` or ``tasks/tenant_tasks.py`` (the retention beat) must sit inside
``held_undated_count(...)`` (``app/common/held_count.py``). The count runs after the
deletion; a bare call that raises fails the task although the work is done, and the
retry repeats it (#1955). A method *reference* (``held_undated_count(repo.count_x, ...)``)
is not a call and passes.

Spellings this does NOT see: a counter whose name does not start with ``count_``; a
counter reached through ``getattr``; a counter called in a module outside the four
files above (the care and dashboard counters are not retention work).
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.config.settings import Settings

APP = Path(__file__).resolve().parents[3] / "app"
GUARDED_FILES = [
    APP / "domain" / "services" / "privacy_service.py",
    *(APP / "tasks" / f"{name}.py" for name in ("retention_tasks", "auth_tasks", "tenant_tasks")),
]
WRAPPER = "held_undated_count"


def attribute_names(source: str) -> set[str]:
    """Every attribute name read anywhere in ``source``."""
    return {n.attr for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Attribute)}


def bare_count_calls(source: str) -> list[int]:
    """Line numbers of ``<x>.count_*(...)`` calls that are not inside a ``held_undated_count(...)`` call."""
    tree = ast.parse(source)
    bare: list[int] = []

    def visit(node: ast.AST, wrapped: bool) -> None:
        for child in ast.iter_child_nodes(node):
            child_wrapped = wrapped
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Attribute) and func.attr.startswith("count_") and not wrapped:
                    bare.append(child.lineno)
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
                if name == WRAPPER:
                    child_wrapped = True
            visit(child, child_wrapped)

    visit(tree, False)
    return bare


def test_every_retention_setting_has_a_reader():
    readers: set[str] = set()
    for path in APP.rglob("*.py"):
        if path == APP / "config" / "settings.py":
            continue
        readers |= attribute_names(path.read_text(encoding="utf-8"))
    fields = [name for name in Settings.model_fields if name.startswith("retention_")]
    assert len(fields) >= 14, "the field set is derived from Settings; an empty set would pass vacuously"
    inert = sorted(name for name in fields if name not in readers)
    assert not inert, f"retention settings nothing reads (inert): {inert}"


def test_a_retention_count_is_never_called_bare():
    offenders: list[str] = []
    for path in GUARDED_FILES:
        offenders += [f"{path.relative_to(APP)}:{line}" for line in bare_count_calls(path.read_text(encoding="utf-8"))]
    assert not offenders, f"report-only counts must go through {WRAPPER}: {offenders}"


class TestTheGuardsAreNotVacuous:
    def test_a_setting_nobody_reads_is_seen(self):
        assert "retention_x" not in attribute_names("settings.retention_y + 1")
        assert "retention_y" in attribute_names("settings.retention_y + 1")

    def test_a_bare_count_is_seen(self):
        assert bare_count_calls("def f():\n    return repo.count_held(1)\n") == [2]

    def test_a_wrapped_count_and_a_reference_pass(self):
        wrapped = "x = held_undated_count(lambda: repo.count_held(1), task='t')\n"
        reference = "x = held_undated_count(repo.count_held, task='t')\n"
        assert bare_count_calls(wrapped) == []
        assert bare_count_calls(reference) == []

    def test_the_scan_reaches_the_known_wrapped_site(self):
        text = (APP / "domain" / "services" / "privacy_service.py").read_text(encoding="utf-8")
        assert "count_completed_without_tombstone_before" in attribute_names(text)
        assert bare_count_calls(text) == []
