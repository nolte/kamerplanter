"""#2489 W-1: ``get_phase_names`` — the names of many growth phases in one statement.

The print needs the name of every distinct phase of a site; it used to read one growth phase per key. The AQL
itself is measured on the server in ``tests/integration/test_lifecycle_phase_names.py``.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository


class _AnsweringAql:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.calls: list[dict[str, Any]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.calls.append({"query": query, "bind_vars": bind_vars or {}})
        return iter([dict(row) for row in self.rows])


class _Db:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.aql = _AnsweringAql(rows)

    def collection(self, _name: str) -> object:
        return object()


def test_four_hundred_keys_are_one_statement_bound_to_the_growth_phases() -> None:
    keys = [f"ph-{index:04d}" for index in range(400)]
    db = _Db([{"key": "ph-0001", "name": "flowering"}])

    names = ArangoLifecycleRepository(db).get_phase_names([*keys, "ph-0001", ""])  # type: ignore[arg-type]

    assert names == {"ph-0001": "flowering"}
    assert len(db.aql.calls) == 1
    (call,) = db.aql.calls
    assert call["bind_vars"] == {"phases": col.GROWTH_PHASES, "keys": keys}
    assert "DOCUMENT(@phases, k)" in call["query"]


def test_no_key_no_statement() -> None:
    db = _Db([])

    assert ArangoLifecycleRepository(db).get_phase_names(["", ""]) == {}  # type: ignore[arg-type]
    assert db.aql.calls == []
