"""Every handler for ArangoDB's 1210 also answers its 1200 (#1458).

`DuplicateError` (ArangoDB ``1210``, *unique constraint violated*) and
`WriteConflictError` (``1200``, *conflict*) are the two answers the server may
give the loser of the same race. Which one arrives is the server's decision about
how far the winner's transaction had got, not a property of the code — so a
handler that resolves a lost race by catching only ``DuplicateError`` is still a
500 under exactly the load it was written for.

That was the shape of #1458: the mapping existed in `_insert_doc` (#1436) and
`create_edge` (#1292), the sibling call sites had never been served, and nothing
said so. **This is the guard for the class**, not for the three sites — it asks
the whole services and data-access surface.

**What the pattern must NOT miss** (the question MEMORY.md makes the sweep
answer: *name a spelling of the same thing my pattern does not match*). Three
spellings of "this try catches both", all of which must pass:

* one tuple handler, parenthesised — ``except (DuplicateError, WriteConflictError):``
* one tuple handler, PEP 758 bare — ``except DuplicateError, WriteConflictError:``
  (Python 3.14; ``ruff format`` rewrites the parenthesised form into this one, so
  it is what the repository actually contains)
* **two sibling handlers on the same ``try``** — which is how
  ``care_reminder_service`` spells it, because the two codes get *different*
  resolutions there: 1210 means the winner's task is committed and visible, 1200
  means it may not exist at all and has to be re-read. A guard that demanded a
  tuple would report that correct code as a defect.

And one spelling it must not accept: ``WriteConflictError`` caught in a
*different* ``try`` in the same function. That is not the same race being
handled; the checks below therefore reason per ``ast.Try`` node, never per
function.
"""

from __future__ import annotations

import ast
import pathlib
import textwrap

import pytest

APP_ROOT = pathlib.Path(__file__).resolve().parents[3] / "app"

#: Where a lost insert race is resolved. The domain services own the
#: read-then-insert windows and the repositories own the raise sites; the API
#: layer never catches either (it lets the typed error become a 409), and a
#: handler appearing there would be a layering finding of its own.
_SCANNED = ("domain/services", "data_access")

_DUPLICATE = "DuplicateError"
_CONFLICT = "WriteConflictError"

#: Handlers that may catch 1210 alone, with the reason 1200 cannot reach them.
#:
#: Empty, and that is the measurement rather than an aspiration: every handler in
#: the tree today resolves a race on a **unique index**, and the server may answer
#: either code on any of them. An entry here has to name a raise path that cannot
#: produce 1200 at all — not merely one where it has not been observed, because
#: "not observed" is what #1292's four-way race disproved after a year.
_ALLOWED_WITHOUT_CONFLICT: dict[str, str] = {}


def _caught_names(handler: ast.ExceptHandler) -> set[str]:
    """Every exception name one ``except`` clause names.

    Handles the bare name, the parenthesised tuple and the PEP 758 bare tuple
    identically, because at the AST level ``except A, B:`` and ``except (A, B):``
    are the same ``ast.Tuple``.
    """
    node = handler.type
    if node is None:
        return set()
    parts = node.elts if isinstance(node, ast.Tuple) else [node]
    names: set[str] = set()
    for part in parts:
        if isinstance(part, ast.Name):
            names.add(part.id)
        elif isinstance(part, ast.Attribute):
            names.add(part.attr)
    return names


def _python_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for area in _SCANNED:
        files.extend(sorted((APP_ROOT / area).rglob("*.py")))
    return files


def _findings(tree: ast.Module, label: str) -> list[str]:
    """Every ``try`` that answers 1210 without answering 1200."""
    problems: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        caught = [(_caught_names(handler), handler) for handler in node.handlers]
        if not any(_DUPLICATE in names for names, _ in caught):
            continue
        # The whole ``try``, not the one handler: two sibling handlers on the
        # same statement are one decision about one race.
        if any(_CONFLICT in names for names, _ in caught):
            continue
        site = f"{label}:{node.lineno}"
        if site in _ALLOWED_WITHOUT_CONFLICT:
            continue
        problems.append(site)
    return problems


def test_every_duplicate_handler_also_answers_a_write_conflict():
    """The sweep. One entry per ``try`` that would 500 on the other code."""
    problems: list[str] = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        problems.extend(_findings(tree, str(path.relative_to(APP_ROOT.parent))))

    assert not problems, (
        "These handlers resolve a lost insert race but answer only ArangoDB's 1210. The server may "
        "answer 1200 for the same race — it depends on how far the winner's transaction had got — and "
        "that path is a raw driver exception, i.e. a 500 (#1458). Catch both, either in one tuple or "
        "as two handlers on the same `try` when the resolutions differ:\n  " + "\n  ".join(problems)
    )


def test_the_sweep_actually_reaches_the_handlers():
    """The control. A sweep over an empty file set certifies nothing.

    Measured on 2026-09-18: five ``try`` statements across the scanned areas
    catch ``DuplicateError``. A refactor that moved them out of
    ``domain/services`` / ``data_access`` would otherwise turn this file green by
    looking at nothing.
    """
    found = 0
    for path in _python_files():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Try) and any(_DUPLICATE in _caught_names(h) for h in node.handlers):
                found += 1

    assert found >= 4, (
        f"only {found} DuplicateError handlers found under {_SCANNED}; the sweep above is nearly "
        "vacuous. Either they moved, or the scanned areas are wrong."
    )


def test_the_allowlist_entries_still_exist():
    """An entry naming a site that is gone excuses nothing and hides the next one."""
    live = set()
    for path in _python_files():
        label = str(path.relative_to(APP_ROOT.parent))
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Try) and any(_DUPLICATE in _caught_names(h) for h in node.handlers):
                live.add(f"{label}:{node.lineno}")

    stale = sorted(set(_ALLOWED_WITHOUT_CONFLICT) - live)
    assert not stale, "Obsolete _ALLOWED_WITHOUT_CONFLICT entries:\n  " + "\n  ".join(stale)


# ── the guard can fail, and does not fail on the correct spellings ───────────


def _probe(source: str) -> list[str]:
    return _findings(ast.parse(textwrap.dedent(source)), "probe.py")


class TestTheGuardCanFail:
    """An assertion nobody has seen fail proves nothing — and neither does one
    that fires on correct code. Both directions are driven here, over the three
    spellings this codebase really uses."""

    def test_a_lone_duplicate_handler_is_reported(self):
        assert _probe("""
            try:
                repo.create(thing)
            except DuplicateError:
                return None
        """)

    def test_a_parenthesised_tuple_passes(self):
        assert not _probe("""
            try:
                repo.create(thing)
            except (DuplicateError, WriteConflictError):
                return None
        """)

    def test_a_bare_pep758_tuple_passes(self):
        """What `ruff format` leaves behind, and therefore what the tree contains."""
        assert not _probe("""
            try:
                repo.create(thing)
            except DuplicateError, WriteConflictError:
                return None
        """)

    def test_two_sibling_handlers_on_one_try_pass(self):
        """`care_reminder_service`'s spelling: same race, two different answers."""
        assert not _probe("""
            try:
                repo.create(thing)
            except DuplicateError:
                return None
            except WriteConflictError:
                if reread() is None:
                    raise
                return None
        """)

    def test_a_conflict_handler_on_another_try_does_not_count(self):
        """The spelling the guard must not accept: it is not the same race."""
        assert _probe("""
            try:
                repo.create(thing)
            except DuplicateError:
                return None

            try:
                repo.update(key, thing)
            except WriteConflictError:
                raise
        """)

    def test_a_dotted_exception_name_is_recognised(self):
        """`except exceptions.DuplicateError:` is the same handler, spelled longer."""
        assert _probe("""
            try:
                repo.create(thing)
            except exceptions.DuplicateError:
                return None
        """)

    def test_an_unrelated_handler_is_not_reported(self):
        assert not _probe("""
            try:
                repo.create(thing)
            except NotFoundError:
                return None
        """)


@pytest.mark.parametrize("area", _SCANNED)
def test_every_scanned_area_exists(area: str):
    """A typo in a scanned path would silently shrink the sweep to nothing."""
    assert (APP_ROOT / area).is_dir(), f"{area} is not a directory under {APP_ROOT}"
