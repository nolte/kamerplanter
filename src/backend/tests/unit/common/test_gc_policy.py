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
    gc.unfreeze()
    cycle = _Node()
    gone = weakref.ref(cycle)
    del cycle  # a cycle only a collection frees
    try:
        frozen = freeze_startup_heap()

        assert gone() is None  # collected before the freeze, not frozen with the heap
        assert frozen == gc.get_freeze_count() > 0
    finally:
        gc.unfreeze()


def test_the_lifespan_freezes_right_before_it_yields() -> None:
    from app import main

    tree = ast.parse(textwrap.dedent(inspect.getsource(main.lifespan)))
    body = tree.body[0].body  # type: ignore[attr-defined]
    statements = [node for node in body if isinstance(node, ast.Expr)]
    yield_at = next(i for i, node in enumerate(statements) if isinstance(node.value, ast.Yield))
    before = statements[yield_at - 1].value

    assert isinstance(before, ast.Call) and isinstance(before.func, ast.Name)
    assert before.func.id == "freeze_startup_heap"
