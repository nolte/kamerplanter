"""#2039 — every ``get_*`` provider in ``app/common/dependencies.py`` declares what it returns.

An unannotated provider makes every receiver built from it untyped: measured
2026-10-04, 115 of the ~200 providers had no return annotation and fed the
unresolved-receiver tripwire (``tests/unit/api/test_write_route_gates.py``) and
mypy alike. This keeps them annotated.

Scope, named so silence is not read as more: only module-level ``def get_*`` in
``dependencies.py``; private ``_get_*`` helpers and nested functions are not
read. ``Any`` is not an annotation in this sense.
"""

from __future__ import annotations

import ast
from pathlib import Path

import app.common.dependencies as dependencies_module

_MIN_PROVIDERS = 150


def unannotated_providers(source: str) -> tuple[int, list[str]]:
    """Return ``(providers seen, names without a usable return annotation)``."""

    seen = 0
    missing: list[str] = []
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("get_"):
            seen += 1
            returns = node.returns
            if returns is None or (isinstance(returns, ast.Name) and returns.id == "Any"):
                missing.append(node.name)
    return seen, missing


def test_every_provider_declares_its_return_type():
    seen, missing = unannotated_providers(Path(dependencies_module.__file__).read_text())

    assert seen >= _MIN_PROVIDERS, f"only {seen} providers found; the scan stopped seeing the file"
    assert missing == []


def test_the_scan_flags_an_unannotated_and_an_any_provider():
    source = (
        "def get_a(): return 1\n"
        "def get_b() -> Any: return 1\n"
        "def get_c() -> int: return 1\n"
        "def _get_d(): return 1\n"
        "async def get_e(): return 1\n"
    )

    assert unannotated_providers(source) == (4, ["get_a", "get_b", "get_e"])
