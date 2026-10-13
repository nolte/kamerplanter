"""#2150 class guard: under ``app/`` a database connection is built only by its provider.

Six Celery retention tasks built ``ArangoConnection()`` themselves, without the
settings its constructor requires, and raised ``TypeError`` on every run for three
months (measured on a real worker, 2026-10-05). A seventh (``security_audit``) passed
the settings and worked, but opened a private client per run next to the process-wide
one. The supported way is the provider in ``app/common/dependencies.py``
(``get_connection()`` / ``get_db()`` for ArangoDB, ``get_timescale_connection()`` for
TimescaleDB): one constructor call per process, with the settings, reached by the API
and the worker alike — so a constructor change is exercised by every request.

**The rule.** Anywhere under ``app/``, any *use* of ``ArangoConnection``,
``TimescaleConnection`` or ``ArangoClient`` as a value — a call, an alias assignment, an
argument (``partial(ArangoConnection, ...)``), a return — is a violation unless
:data:`ALLOWED` names the enclosing function with a reason. Uses are found by AST, so
these spellings are all seen: the bare name, a ``from … import X as Y`` alias, a
module attribute (``connection.ArangoConnection(...)``, ``arango.ArangoClient(...)``),
a call split over lines. Type annotations (parameters, returns, annotated assignments,
string annotations) are not uses and pass, and so do imports.

**The registry half.** The AST sweep only covers files under ``app/``. Every task the
worker registers is checked to be defined in a module under ``app/``, so no task can
build its connection in a file the sweep does not read.

Spellings this does NOT see: a class reached through ``getattr(module, "ArangoConnection")``
or ``importlib``; a subclass of one of the classes defined and instantiated elsewhere
(the subclass name is not tracked); a connection built by a third-party helper.
"""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

import pytest

from app.tasks import celery_app

APP = Path(__file__).resolve().parents[3] / "app"

#: The classes whose construction belongs to the provider.
CONNECTION_CLASSES = frozenset({"ArangoConnection", "TimescaleConnection", "ArangoClient"})

#: ``(path relative to app/, enclosing function)`` -> why this construction is correct.
ALLOWED: dict[tuple[str, str], str] = {
    ("common/dependencies.py", "get_connection"): "the ArangoDB provider: the one construction, with the settings",
    ("common/dependencies.py", "get_timescale_connection"): "the TimescaleDB provider",
    ("common/dependencies.py", "check_database_access"): (
        "#2154 worker start gate: a throwaway connection that proves the login and is closed again, so the "
        "prefork parent never holds the process-wide client its children would inherit"
    ),
    ("data_access/arango/connection.py", "connect"): "the connection class building its own HTTP client",
    ("migrations/purge_orphan_ha_readings.py", "__init__"): (
        "an operator-invoked purge that must NOT create a missing database, which ArangoConnection.connect() does"
    ),
    ("migrations/audit_legacy_stamps.py", "_connect"): (
        "the operator-invoked, read-only v0004 stamp audit (MT-052): must NOT create a missing database, which "
        "ArangoConnection.connect() does — an empty one would measure nothing and report it as clean"
    ),
}


def _annotation_nodes(tree: ast.AST) -> set[int]:
    """``id()`` of every node that sits inside a type annotation."""
    roots: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                roots.append(node.returns)
            all_args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            all_args += [a for a in (node.args.vararg, node.args.kwarg) if a is not None]
            roots.extend(a.annotation for a in all_args if a.annotation is not None)
        elif isinstance(node, ast.AnnAssign):
            roots.append(node.annotation)
    return {id(inner) for root in roots for inner in ast.walk(root)}


def _bound_names(tree: ast.AST) -> set[str]:
    """Local names bound to one of the classes by ``from … import X [as Y]``."""
    names = set(CONNECTION_CLASSES)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in CONNECTION_CLASSES:
                    names.add(alias.asname or alias.name)
    return names


def _enclosing_functions(tree: ast.AST) -> dict[int, str]:
    """``id(node)`` -> name of the innermost function containing it (``<module>`` at top level)."""
    owner: dict[int, str] = {}

    def visit(node: ast.AST, current: str) -> None:
        for child in ast.iter_child_nodes(node):
            name = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else current
            owner[id(child)] = name
            visit(child, name)

    visit(tree, "<module>")
    return owner


def uses_in_source(source: str) -> list[tuple[str, int, str]]:
    """``(enclosing function, line, spelling)`` of every value use of a connection class."""
    tree = ast.parse(source)
    annotations = _annotation_nodes(tree)
    names = _bound_names(tree)
    owner = _enclosing_functions(tree)
    found: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if id(node) in annotations:
            continue
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in names:
            found.append((owner.get(id(node), "<module>"), node.lineno, node.id))
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load) and node.attr in CONNECTION_CLASSES:
            found.append((owner.get(id(node), "<module>"), node.lineno, node.attr))
    return found


def _violations() -> list[str]:
    out: list[str] = []
    for path in sorted(APP.rglob("*.py")):
        relative = path.relative_to(APP).as_posix()
        for function, line, spelling in uses_in_source(path.read_text(encoding="utf-8")):
            if (relative, function) not in ALLOWED:
                out.append(f"app/{relative}:{line} {function}() uses {spelling}")
    return out


def test_no_code_outside_the_provider_builds_a_database_connection() -> None:
    violations = _violations()
    assert not violations, (
        "Build database connections through app.common.dependencies (get_db() / get_connection() / "
        "get_timescale_connection()), not by hand (#2150):\n  " + "\n  ".join(violations)
    )


def test_every_allowed_entry_still_exists() -> None:
    """A stale entry would silently allow a future use in a function of the same name."""
    present = {
        (path.relative_to(APP).as_posix(), function)
        for path in APP.rglob("*.py")
        for function, _, _ in uses_in_source(path.read_text(encoding="utf-8"))
    }
    stale = sorted(set(ALLOWED) - present)
    assert not stale, f"ALLOWED names functions that no longer build a connection: {stale}"


def test_every_registered_task_lives_where_the_sweep_reads() -> None:
    celery_app.loader.import_default_modules()
    tasks = {name: task for name, task in celery_app.tasks.items() if not name.startswith("celery.")}
    assert len(tasks) >= 60, "the registry is derived; a near-empty one would pass vacuously"
    outside = sorted(
        name
        for name, task in tasks.items()
        if APP not in Path(inspect.getfile(sys.modules[task.__module__])).resolve().parents
    )
    assert not outside, f"tasks defined outside app/, where the connection sweep does not look: {outside}"


# ---------------------------------------------------------------------------
# Self-test: the selector sees every spelling the docstring claims, and lets
# the non-uses through. Each source below is a spelling found in, or one edit
# away from, the tree this guard was written against.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "source",
    [
        # the #2150 defect, verbatim
        "from app.data_access.arango.connection import ArangoConnection\ndef task():\n    db = ArangoConnection().db\n",
        # the security_audit spelling: correct arguments, private client
        "from app.data_access.arango.connection import ArangoConnection\n"
        "def task():\n    return Repo(ArangoConnection(settings).db)\n",
        "from app.data_access.arango.connection import ArangoConnection as Conn\ndef task():\n    Conn(settings)\n",
        "import app.data_access.arango.connection as c\ndef task():\n    c.ArangoConnection(settings)\n",
        "from app.data_access.arango.connection import ArangoConnection\nmake = ArangoConnection\n",
        "import functools\nfrom app.data_access.arango.connection import ArangoConnection\n"
        "def task():\n    functools.partial(ArangoConnection, settings)()\n",
        "import arango\ndef task():\n    arango.ArangoClient(hosts='http://x')\n",
        "from app.data_access.timescale.connection import TimescaleConnection\n"
        "def task():\n    TimescaleConnection(\n        settings,\n    )\n",
    ],
)
def test_the_selector_sees_every_construction_spelling(source: str) -> None:
    assert uses_in_source(source), f"not seen:\n{source}"


@pytest.mark.parametrize(
    "source",
    [
        "from __future__ import annotations\nfrom app.data_access.arango.connection import ArangoConnection\n"
        "def get(c: ArangoConnection) -> ArangoConnection:\n    return c\n",
        "from app.data_access.arango.connection import ArangoConnection\n_c: ArangoConnection | None = None\n",
        "def f(c: 'ArangoConnection') -> None:\n    pass\n",
        "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
        "    from app.data_access.arango.connection import ArangoConnection\n",
        "from app.common.dependencies import get_db\ndef task():\n    return get_db()\n",
    ],
)
def test_the_selector_lets_non_uses_through(source: str) -> None:
    assert not uses_in_source(source), f"flagged although not a construction:\n{source}"


def test_the_function_owner_is_the_innermost_function() -> None:
    source = "def outer():\n    def inner():\n        ArangoConnection(s)\n    ArangoClient()\n"
    assert sorted(uses_in_source(source)) == [("inner", 3, "ArangoConnection"), ("outer", 4, "ArangoClient")]
