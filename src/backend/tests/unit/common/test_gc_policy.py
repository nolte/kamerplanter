"""#2526: the start-up heap is frozen out of the collector, and the lifespan does it as its last step."""

from __future__ import annotations

import ast
import gc
import inspect
import textwrap
import weakref

from app.common.gc_policy import freeze_startup_heap


class _Node:
    def __init__(self) -> None:
        self.me = self


def test_freeze_collects_first_then_moves_what_is_alive_out_of_the_collector() -> None:
    """With the automatic collector off, only the policy's own collect can free the cycle - and only before the
    freeze: a cycle frozen first would survive every later collection."""
    gc.unfreeze()
    gc.disable()
    cycle = _Node()
    gone = weakref.ref(cycle)
    del cycle
    try:
        frozen = freeze_startup_heap()

        assert gone() is None
        assert frozen == gc.get_freeze_count() > 0
    finally:
        gc.unfreeze()
        gc.enable()


def _yield_statement(body: list[ast.stmt]) -> int:
    for index, node in enumerate(body):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Yield):
            return index
    raise AssertionError("the lifespan has no top-level `yield`; move the freeze to the statement before it")


def test_the_lifespan_freezes_in_the_statement_right_before_it_yields() -> None:
    """Any statement between the freeze and ``yield`` would allocate start-up state the freeze misses."""
    from app import main

    tree = ast.parse(textwrap.dedent(inspect.getsource(main.lifespan)))
    function = tree.body[0]
    assert isinstance(function, ast.AsyncFunctionDef)
    before = function.body[_yield_statement(function.body) - 1]

    assert isinstance(before, ast.Expr) and isinstance(before.value, ast.Call), ast.dump(before)
    assert isinstance(before.value.func, ast.Name) and before.value.func.id == "freeze_startup_heap"
