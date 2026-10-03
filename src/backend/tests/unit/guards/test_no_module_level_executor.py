"""#1995 — no thread or process pool is built at module scope under ``app/``.

The defect class of #1995: a module-wide ``ThreadPoolExecutor`` shared by every
request (``_resolver_pool`` in ``url_safety``). Its queue is unbounded and a task
that blocks holds its thread for good, so one caller can occupy the pool for
every other. A pool a request path needs belongs behind something that bounds
it per caller and refuses instead of queueing (``url_safety._ResolverLane``),
built inside that wrapper — never as a bare module-level executor.

Sweep: every ``*Executor(...)`` call from ``concurrent.futures`` under ``app/``,
however imported (``ThreadPoolExecutor``, an alias, ``concurrent.futures.X``,
``futures.X``), whose nearest enclosing scope is the module itself — a module
level assignment, a default argument, a class body. A call inside a function or
method is per call or per instance and is not this class.

Blind spot, stated: a module-level *instance* of a class that builds a pool in
its ``__init__`` is not flagged (that is how the bounded lane is built); nor is a
pool obtained through a factory function called at module scope.
"""

from __future__ import annotations

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[3] / "app"
EXECUTOR_NAMES = frozenset({"ThreadPoolExecutor", "ProcessPoolExecutor", "InterpreterPoolExecutor"})


def _executor_aliases(tree: ast.Module) -> tuple[set[str], set[str]]:
    """``(names, module_aliases)`` bound to the executor classes / ``concurrent.futures``."""
    names: set[str] = set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in {"concurrent.futures", "concurrent"}:
            for alias in node.names:
                if node.module == "concurrent.futures" and alias.name in EXECUTOR_NAMES:
                    names.add(alias.asname or alias.name)
                if node.module == "concurrent" and alias.name == "futures":
                    modules.add(alias.asname or "futures")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "concurrent.futures":
                    modules.add(alias.asname or "concurrent.futures")
                elif alias.name == "concurrent":
                    modules.add("concurrent.futures")
    return names, modules


def _dotted(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def module_level_executors(source: str) -> list[int]:
    """Line numbers of executor constructions at module scope in *source* (pure)."""
    tree = ast.parse(source)
    names, modules = _executor_aliases(tree)
    hits: list[int] = []

    def visit(node: ast.AST, in_function: bool) -> None:
        if isinstance(node, ast.Call) and not in_function:
            callee = _dotted(node.func)
            if callee is not None and (
                callee in names or any(callee == f"{m}.{n}" for m in modules for n in EXECUTOR_NAMES)
            ):
                hits.append(node.lineno)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                # Defaults and decorators are evaluated at definition time: module scope.
                for expr in [*child.args.defaults, *[d for d in child.args.kw_defaults if d is not None]]:
                    visit(expr, in_function)
                for decorator in getattr(child, "decorator_list", []):
                    visit(decorator, in_function)
                body = child.body if isinstance(child.body, list) else [child.body]
                for stmt in body:
                    visit(stmt, True)
            else:
                visit(child, in_function)

    visit(tree, False)
    return hits


def test_the_sweep_finds_every_spelling_at_module_scope():
    cases = {
        "from concurrent.futures import ThreadPoolExecutor\npool = ThreadPoolExecutor(8)\n": [2],
        "from concurrent.futures import ThreadPoolExecutor as TPE\npool = TPE(8)\n": [2],
        "import concurrent.futures\npool = concurrent.futures.ThreadPoolExecutor(8)\n": [2],
        "import concurrent.futures as cf\npool = cf.ProcessPoolExecutor()\n": [2],
        "from concurrent import futures\npool = futures.ThreadPoolExecutor()\n": [2],
        "from concurrent.futures import ThreadPoolExecutor\nclass A:\n    pool = ThreadPoolExecutor()\n": [3],
        "from concurrent.futures import ThreadPoolExecutor\ndef f(p=ThreadPoolExecutor()):\n    pass\n": [2],
    }
    for source, expected in cases.items():
        assert module_level_executors(source) == expected, source


def test_the_sweep_leaves_per_call_and_per_instance_pools_alone():
    source = (
        "from concurrent.futures import ThreadPoolExecutor\n"
        "def f():\n    with ThreadPoolExecutor(1) as p:\n        pass\n"
        "class Lane:\n    def __init__(self):\n        self.pool = ThreadPoolExecutor(8)\n"
        "g = lambda: ThreadPoolExecutor(1)\n"
    )
    assert module_level_executors(source) == []


def test_no_module_level_executor_under_app():
    files = sorted(APP_ROOT.rglob("*.py"))
    assert len(files) > 100, f"the sweep found too few files under {APP_ROOT}"
    offenders = [
        f"{path.relative_to(APP_ROOT.parent)}:{line}"
        for path in files
        for line in module_level_executors(path.read_text(encoding="utf-8"))
    ]
    assert offenders == [], (
        "A module-level executor is shared by every caller with an unbounded queue (#1995); "
        "build it inside a per-caller bounded wrapper such as url_safety._ResolverLane: " + ", ".join(offenders)
    )
