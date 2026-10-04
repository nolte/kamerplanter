"""#2039 — every ``get_*`` provider in ``app/common/dependencies.py`` declares what it returns.

An unannotated provider makes every receiver built from it untyped: measured
2026-10-04, 115 of the ~200 providers had no return annotation and fed the
unresolved-receiver tripwire (``tests/unit/api/test_write_route_gates.py``) and
mypy alike. This keeps them annotated.

Scope, named so silence is not read as more: module-level ``def get_*`` in
``dependencies.py`` and the two private helpers listed in ``_PRIVATE_HELPERS``;
other private ``_get_*`` helpers and nested functions are not read. ``Any`` is
not an annotation in this sense.

``_get_redis_client`` is annotated with a Protocol and a ``cast`` (the redis-py
stubs type every reply ``bytes | str | None`` and cannot express
``decode_responses=True``, so ``redis.Redis`` satisfies none of the stores'
``str``-typed protocols — measured with mypy); ``_resolve_substrate_batch``
returns ``SubstrateBatch``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import app.common.dependencies as dependencies_module

_MIN_PROVIDERS = 150
_PRIVATE_HELPERS = ("_get_redis_client", "_resolve_substrate_batch")


def unannotated_providers(source: str) -> tuple[int, list[str]]:
    """Return ``(providers seen, names without a usable return annotation)``."""

    seen = 0
    missing: list[str] = []
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            node.name.startswith("get_") or node.name in _PRIVATE_HELPERS
        ):
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


def test_the_scan_reads_the_two_named_private_helpers():
    source = (
        "def _get_redis_client(): return 1\n"
        "def _resolve_substrate_batch(k) -> int: return 1\n"
        "def _get_other(): return 1\n"
    )

    assert unannotated_providers(source) == (2, ["_get_redis_client"])
    present = {
        node.name for node in ast.parse(Path(dependencies_module.__file__).read_text()).body if hasattr(node, "name")
    }
    assert set(_PRIVATE_HELPERS) <= present, "a helper this guard names was renamed; the scan would stop reading it"
