"""#1661 — no module of the integration tier may bootstrap a database by a fixed name.

Two sessions of ``tests/integration/`` on one ArangoDB — two worktrees on one
machine, which is this repository's documented working mode — dropped each
other's database mid-test: ``[HTTP 404][ERR 1228] database not found``,
``[HTTP 409][ERR 1207] duplicate name``, 60-odd errors per side, all of them
looking like defects in the change under review. Measured 2026-09-23 on three
deliberately concurrent pairs; the record is
``spec/dev-tooling/INTEGRATION-DB-ISOLATION.md``. The repair is
``tests.support.arango_integration.run_database_name``, which scopes every
name to the session.

This file pins the repair from both ends, and — because the sweep that
enumerated the 21 offending modules on 2026-09-23 is itself the thing most
likely to have a blind spot — it enumerates the **class**, not the spellings
found that day:

* **absence** — a database name reaching ``create_database`` /
  ``delete_database`` / ``has_database``, ``Settings(arangodb_database=…)`` or
  ``client.db(…)`` must not be a fixed string. Read from the syntax tree:
  a literal at the call, a module-level name bound to a literal (the
  ``_DB_NAME = "…"`` shape every offender used), an f-string whose every
  interpolation is itself fixed, or two literals concatenated. ``"_system"`` is the one fixed
  name the tier legitimately addresses and is exempt by value.
* **presence** — a floor on how many modules of the tier call
  ``run_database_name(...)`` in *executable* text, so the helper cannot be
  quietly retired module by module. The floor is deliberately below today's
  count (21) so a module that stops needing a database can be deleted without
  touching this file; it exists to catch the class going away, not to census
  it. Executable text comes from ``scripts/source_text.py``: a docstring that
  *mentions* the helper — every module's does — must not count.
* the helper's own contract: names are inside the sweep's namespace, distinct
  across processes, stable within one, and the staleness boundary is where the
  constant says it is.

Both sweeps are proven able to go red on planted files, including one whose
only spelling of each pattern is in a comment or docstring.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.support import arango_integration as support
from tests.support.execution_guards import find_project_root
from tests.support.repo_scripts import load_repo_script

_source_text = load_repo_script("source_text")

#: ``src/backend`` — the checkout these tests belong to.
_PROJECT_ROOT = find_project_root(Path(__file__))

_INTEGRATION_DIR = _PROJECT_ROOT / "tests" / "integration"

#: How many modules of the tier must name their database through the helper.
#: 21 did on 2026-09-23; the gap is headroom for deleting modules, not for
#: adding fixed names — those are caught by the absence sweep regardless.
_RUN_SCOPED_FLOOR = 15

#: The calls through which a database name reaches the server.
_NAME_TAKING_CALLS = frozenset({"create_database", "delete_database", "has_database", "db"})

#: The one fixed name the tier may address: the server's own database.
_EXEMPT_NAMES = frozenset({support.SYSTEM_DATABASE})

_HELPER_CALL = re.compile(r"\brun_database_name\s*\(")


def _tier_sources() -> list[Path]:
    """Every module of the tier except the conftest that holds the contract."""
    return sorted(path for path in _INTEGRATION_DIR.glob("*.py") if path.name != "conftest.py")


def _fixed_string(node: ast.expr, bindings: dict[str, str]) -> str | None:
    """The fixed value *node* evaluates to, or ``None`` when it is not fixed.

    Fixed means: a string literal; a module-level name bound to one; an f-string
    whose every interpolation is itself fixed; or a concatenation of fixed parts. Anything else — a
    call, an attribute, a name bound elsewhere — is treated as not fixed, which
    is the sweep's stated blind spot: a fixed name imported from another module
    would pass here. ``SYSTEM_DATABASE`` is exactly such an import, and exempt.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return bindings.get(node.id)
    if isinstance(node, ast.JoinedStr):
        parts = [_fixed_string(value, bindings) for value in node.values]
        return None if any(part is None for part in parts) else "".join(parts)
    if isinstance(node, ast.FormattedValue):
        # ``f"{PREFIX}suffix"`` wraps the name in a FormattedValue; the first
        # draft of this sweep missed exactly that, and the planted file caught it.
        return None if node.format_spec is not None or node.conversion != -1 else _fixed_string(node.value, bindings)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _fixed_string(node.left, bindings), _fixed_string(node.right, bindings)
        return None if left is None or right is None else left + right
    return None


def _module_bindings(tree: ast.Module) -> dict[str, str]:
    """Module-level names bound to a fixed string, resolved in source order."""
    bindings: dict[str, str] = {}
    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        if value is None:
            continue
        fixed = _fixed_string(value, bindings)
        for target in targets:
            if isinstance(target, ast.Name):
                if fixed is None:
                    bindings.pop(target.id, None)
                else:
                    bindings[target.id] = fixed
    return bindings


def _database_name_argument(call: ast.Call) -> ast.expr | None:
    """The expression a name-taking call passes as the database name, if any."""
    func = call.func
    if isinstance(func, ast.Attribute) and func.attr in _NAME_TAKING_CALLS:
        return call.args[0] if call.args else None
    for keyword in call.keywords:
        if keyword.arg == "arangodb_database":
            return keyword.value
    return None


def fixed_database_names(paths: list[Path]) -> list[str]:
    """``file:line name`` for every fixed database name that reaches the server."""
    findings = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        bindings = _module_bindings(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            argument = _database_name_argument(node)
            if argument is None:
                continue
            fixed = _fixed_string(argument, bindings)
            if fixed is not None and fixed not in _EXEMPT_NAMES:
                findings.append((path.name, node.lineno, fixed))
    return [f"{name}:{line} {fixed!r}" for name, line, fixed in sorted(findings)]


def run_scoped_modules(paths: list[Path]) -> list[str]:
    """Modules that call ``run_database_name(...)`` in executable text."""
    return [
        path.name
        for path in paths
        if _HELPER_CALL.search(_source_text.executable_source(path.read_text(encoding="utf-8"), language="python"))
    ]


class TestTheTierIsRunScoped:
    """The 21 fixed names may not come back, one module at a time."""

    def test_no_module_hands_the_server_a_fixed_database_name(self) -> None:
        findings = fixed_database_names(_tier_sources())

        assert findings == [], (
            "These modules bootstrap a database by a fixed name, so two sessions on one "
            "server drop it out from under each other (#1661):\n  "
            + "\n  ".join(findings)
            + "\nName it through tests.support.arango_integration.run_database_name(base) instead."
        )

    def test_enough_modules_name_their_database_through_the_helper(self) -> None:
        modules = run_scoped_modules(_tier_sources())

        assert len(modules) >= _RUN_SCOPED_FLOOR, (
            f"Only {len(modules)} modules of the integration tier call run_database_name(); "
            f"the floor is {_RUN_SCOPED_FLOOR}. Either the helper is being retired module by "
            "module — which re-opens #1661 — or modules were deleted, in which case lower the "
            f"floor here deliberately. Found: {modules}"
        )


class TestTheSweepsCanGoRed:
    """A measuring tool that cannot fail measures nothing."""

    def test_every_fixed_spelling_is_a_finding(self, tmp_path: Path) -> None:
        planted = tmp_path / "test_planted.py"
        planted.write_text(
            "from app.config.settings import Settings\n"
            '_DB_NAME = "kamerplanter_fixed_test"\n'
            'PREFIX = "kp_"\n'
            'JOINED = f"{PREFIX}suffix"\n'
            'CONCAT = PREFIX + "other"\n'
            "def f(system, client):\n"
            "    system.create_database(_DB_NAME)\n"
            '    system.delete_database("literal_name")\n'
            "    system.has_database(JOINED)\n"
            "    client.db(CONCAT, username='u')\n"
            "    Settings(arangodb_database=_DB_NAME)\n"
            '    system.has_database("_system")\n',
            encoding="utf-8",
        )

        findings = fixed_database_names([planted])

        assert findings == [
            "test_planted.py:7 'kamerplanter_fixed_test'",
            "test_planted.py:8 'literal_name'",
            "test_planted.py:9 'kp_suffix'",
            "test_planted.py:10 'kp_other'",
            "test_planted.py:11 'kamerplanter_fixed_test'",
        ]

    def test_a_run_scoped_spelling_is_not_a_finding(self, tmp_path: Path) -> None:
        clean = tmp_path / "test_clean.py"
        clean.write_text(
            "from tests.support.arango_integration import run_database_name\n"
            '_DB_NAME = run_database_name("clean")\n'
            "def f(system):\n"
            "    system.create_database(_DB_NAME)\n"
            '    system.has_database("_system")\n',
            encoding="utf-8",
        )

        assert fixed_database_names([clean]) == []
        assert run_scoped_modules([clean]) == ["test_clean.py"]

    def test_a_name_that_was_rebound_to_something_dynamic_is_not_a_finding(self, tmp_path: Path) -> None:
        """The last binding wins, as it does at runtime."""
        rebound = tmp_path / "test_rebound.py"
        rebound.write_text(
            "import os\n"
            '_DB_NAME = "fixed"\n'
            '_DB_NAME = os.environ["X"]\n'
            "def f(system):\n"
            "    system.create_database(_DB_NAME)\n",
            encoding="utf-8",
        )

        assert fixed_database_names([rebound]) == []

    def test_prose_satisfies_neither_sweep(self, tmp_path: Path) -> None:
        """A comment or docstring is not code, in either direction (#1456).

        The absence sweep must not go red over a docstring that *names* a fixed
        database (the tier's docstrings discuss the retired names), and the
        presence sweep must not count a module whose only ``run_database_name(``
        is in a comment — that is the spelling a retirement would leave behind.
        """
        prose = tmp_path / "test_prose.py"
        prose.write_text(
            '"""Used to be kamerplanter_prose_test; system.create_database("kamerplanter_prose_test")."""\n'
            "# _DB_NAME = run_database_name('prose')\n"
            "def f(system):\n"
            "    # system.create_database('kamerplanter_prose_test')\n"
            "    pass\n",
            encoding="utf-8",
        )

        assert fixed_database_names([prose]) == []
        assert run_scoped_modules([prose]) == []


class TestTheHelperContract:
    """What ``run_database_name`` promises the sweeps in the conftest."""

    def test_a_name_is_inside_the_namespace_the_sweeps_recognise(self) -> None:
        name = support.run_database_name("contract")

        assert name.startswith(support.RUN_DATABASE_PREFIX)
        assert support.is_run_database(name)
        assert support.belongs_to_this_run(name)
        assert len(name) <= 64, "ArangoDB refuses traditional names longer than 64 characters"

    def test_a_name_is_stable_within_one_process(self) -> None:
        assert support.run_database_name("stable") == support.run_database_name("stable")

    def test_two_processes_get_two_names(self) -> None:
        """The property the whole repair rests on, measured across a real process boundary."""
        script = "from tests.support.arango_integration import run_database_name; print(run_database_name('twins'))"
        names = {
            subprocess.run(  # noqa: S603 - fixed argv, no shell
                [sys.executable, "-c", script],
                cwd=_PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
                env={**os.environ, "PYTHONPATH": str(_PROJECT_ROOT)},
            ).stdout.strip()
            for _ in range(2)
        }

        assert len(names) == 2, f"two processes derived the same name: {names}"
        assert all(support.is_run_database(name) for name in names)
        assert not any(support.belongs_to_this_run(name) for name in names), (
            "a child process must not land in its parent's namespace — that is how a child "
            "pytest session would collide with the session that spawned it"
        )

    @pytest.mark.parametrize("base", ["Upper", "1leading", "has-hyphen", "x" * 39, ""])
    def test_a_base_outside_the_namespace_is_refused(self, base: str) -> None:
        with pytest.raises(ValueError, match="must match"):
            support.run_database_name(base)

    def test_the_longest_permitted_base_still_fits_the_server_limit(self) -> None:
        assert len(support.run_database_name("x" * 38)) <= 64

    def test_names_outside_the_namespace_are_never_run_databases(self) -> None:
        for name in ("kamerplanter", "kamerplanter_e2e", "kamerplanter_test", "_system", "kp_it_x", "kp_it_x__12_abc"):
            assert not support.is_run_database(name), name
            assert not support.is_stale_run_database(name, now=10**12), name

    def test_staleness_is_the_constant_and_not_a_second_number(self) -> None:
        started = 1_700_000_000
        name = f"{support.RUN_DATABASE_PREFIX}stale__{started:010d}_abcdef"

        assert not support.is_stale_run_database(name, now=started + support.STALE_AFTER_SECONDS)
        assert support.is_stale_run_database(name, now=started + support.STALE_AFTER_SECONDS + 1)

    def test_this_sessions_own_name_is_not_stale(self) -> None:
        assert not support.is_stale_run_database(support.run_database_name("fresh"))
