"""#2709: every read of a document by key under ``app/data_access`` goes through ``get_document``.

``StandardCollection.get(".")`` and ``get("..")`` raise ``DocumentGetError`` [ERR 1203] instead of answering
``None`` (measured against ArangoDB 3.12, see :mod:`app.data_access.arango.document_reads`), and both reach a
route as ``%2E`` / ``%2E%2E``: every keyed garden-plan route answered them with a 500. The fix is one place,
:func:`~app.data_access.arango.document_reads.get_document`; this guard holds that no repository reads past it.

The predicate: no call ``<x>.collection(...).get(...)`` and no call ``<x>.collection.get(...)`` in a module under
``app/data_access`` other than ``document_reads.py``.

Spellings this does not see: a collection handle bound to a local name first (``edges = db.collection(c)``
then ``edges.get(key)`` - none reads by key today), a stream-transaction handle, and ``app/migrations`` (its
keys come from the database itself, not from a client).
"""

from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"
DATA_ACCESS = APP / "data_access"
_EXEMPT = {"arango/document_reads.py"}


def _is_collection_handle(node: ast.expr) -> bool:
    """``x.collection(...)`` or ``x.collection``."""
    if isinstance(node, ast.Call):
        node = node.func
    return isinstance(node, ast.Attribute) and node.attr == "collection"


def _direct_reads(source: str) -> list[int]:
    """Line numbers of ``<collection handle>.get(...)`` calls in ``source``."""
    return sorted(
        node.lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and _is_collection_handle(node.func.value)
    )


def _helper_calls(source: str) -> int:
    return sum(
        1
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "get_document"
    )


def _sweep() -> tuple[list[str], int]:
    direct: list[str] = []
    helped = 0
    for path in sorted(DATA_ACCESS.rglob("*.py")):
        rel = path.relative_to(DATA_ACCESS).as_posix()
        if rel in _EXEMPT:
            continue
        source = path.read_text(encoding="utf-8")
        direct.extend(f"{rel}:{line}" for line in _direct_reads(source))
        helped += _helper_calls(source)
    return direct, helped


def test_no_repository_reads_a_document_past_the_helper() -> None:
    direct, helped = _sweep()

    assert direct == [], f"read by key through get_document (#2709), not collection.get: {direct}"
    # Not vacuous: the sweep sees the repositories that do read by key.
    assert helped >= 20, f"the sweep saw only {helped} get_document calls"


def test_the_detector_sees_both_spellings() -> None:
    planted = (
        "def a(self, key):\n"
        "    return self._db.collection('x').get(key)\n"
        "def b(self, key):\n"
        "    return self.collection.get(key)\n"
        "def c(self, row):\n"
        "    return row.get('collection')\n"
    )

    assert _direct_reads(planted) == [2, 4]
