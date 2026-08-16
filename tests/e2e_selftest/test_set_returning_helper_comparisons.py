"""A set-returning helper compared with ``==`` is a permanently false assertion.

This closes a defect this suite produced on itself. `_day` in the TC-004-092
scenario used to return one ``(d, m, y)`` tuple. A run that straddled midnight
made that wrong — the row was written at 23:59 and the day was read at 00:01 —
so it became a *set* of the days the action could legitimately have landed on,
and the three assertions that consume it had to move from ``==`` to ``in``.

Two of the three moved. The third and fourth kept comparing a tuple against a
set, which is never equal, so they failed on every profile in the next nightly
with a message that contained its own refutation::

    cell='16.8.2026, 00:40:23', expected={(16, 8, 2026)}

The cell holds exactly the day the assertion wanted. Read by a human that is
obvious; nothing in the toolchain says a word, because comparing a tuple to a
set is a legal expression that is simply always ``False``. Type checkers do not
run over ``tests/e2e/`` here, and a green local run proves nothing — the bug
only surfaces once the assertion is *reached*, which in this scenario needs the
whole browser stack.

Note the direction of the damage. Had the helper been widened in the other
order — assertions first, helper second — the same mistake would have made the
comparisons silently *true* against a set that always contains the value. That
is the far worse half of this failure class, and it is the reason this guard
rejects ``==`` and ``!=`` rather than merely warning about them.

Scope and honesty about it: the analysis is per-file, so it only sees helpers
defined in the same module as their caller. A set-returning helper imported
from elsewhere is not caught. That is a real gap, not an oversight — resolving
imports would mean importing `tests/e2e/`, which needs Selenium and a browser
and is exactly what this browser-free selftest tier exists to avoid.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

_E2E = pathlib.Path(__file__).resolve().parents[1] / "e2e"

#: Return annotations whose value must never be compared with ``==``/``!=``.
_SET_TYPES = frozenset({"set", "frozenset", "AbstractSet", "Set"})


def _annotation_root(node: ast.expr | None) -> str | None:
    """The outermost name of a return annotation, e.g. ``set`` in ``set[int]``."""
    if isinstance(node, ast.Subscript):
        node = node.value
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _set_returning_helpers(tree: ast.AST) -> set[str]:
    """Names of functions in this module annotated as returning a set."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if _annotation_root(node.returns) in _SET_TYPES:
                found.add(node.name)
    return found


def _names_bound_to(tree: ast.AST, helpers: set[str]) -> dict[str, str]:
    """Local variables assigned straight from a call to one of ``helpers``.

    Maps variable name → helper it came from, so the failure message can name
    both. Only the direct ``x = helper(...)`` shape is tracked; anything that
    launders the value through another expression is out of scope, and saying so
    is better than pretending to a completeness this cannot have.
    """
    bound: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        call = node.value
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)):
            continue
        if call.func.id not in helpers:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                bound[target.id] = call.func.id
    return bound


def _equality_comparisons_on(tree: ast.AST, bound: dict[str, str]) -> list[tuple[int, str, str]]:
    """``(line, variable, helper)`` for every ``==``/``!=`` touching a bound name."""
    offenders: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, ast.Eq | ast.NotEq) for op in node.ops):
            continue
        for side in [node.left, *node.comparators]:
            if isinstance(side, ast.Name) and side.id in bound:
                offenders.append((node.lineno, side.id, bound[side.id]))
    return offenders


def _e2e_modules() -> list[pathlib.Path]:
    return sorted(path for path in _E2E.rglob("*.py") if path.name != "__init__.py")


def test_the_scan_finds_a_set_returning_helper() -> None:
    """Loud when it finds nothing to check.

    Every assertion below is a no-op over an empty helper set. If `_day` is
    renamed, loses its annotation, or the suite moves, this file would keep
    reporting green while checking nothing — the vacuous-pass shape, in a guard
    written to close one.
    """
    total = sum(
        len(_set_returning_helpers(ast.parse(p.read_text("utf-8")))) for p in _e2e_modules()
    )

    assert total > 0, (
        f"no set-returning helper found under {_E2E}. Either they all lost their return "
        "annotations or this guard stopped being able to see them."
    )


@pytest.mark.parametrize("path", _e2e_modules(), ids=lambda p: p.name)
def test_no_equality_comparison_against_a_set_returning_helper(path: pathlib.Path) -> None:
    """A tuple is never equal to a set holding it — so the assertion is dead."""
    tree = ast.parse(path.read_text("utf-8"))
    helpers = _set_returning_helpers(tree)
    if not helpers:
        pytest.skip("no set-returning helper defined in this module")

    offenders = _equality_comparisons_on(tree, _names_bound_to(tree, helpers))

    assert offenders == [], "\n".join(
        [
            f"{path.name} compares a set-returning helper's result with `==`/`!=`:",
            *(
                f"  line {line}: `{var}` comes from `{helper}()`, which returns a set"
                for line, var, helper in offenders
            ),
            "",
            "Membership is the operation you want here — `x in " + "result` — because the",
            "helper returns the set of acceptable values, not one value. An equality",
            "comparison against it is not merely unusual: it can never hold, so the",
            "assertion it guards is inert and the test passes on nothing.",
            "",
            "This is exactly how TC-004-092 came to fail on all six E2E profiles at once.",
        ]
    )
