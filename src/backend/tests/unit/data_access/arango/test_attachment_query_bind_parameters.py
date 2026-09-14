"""#1393 — every bind parameter the attachment queries name is supplied, and vice versa.

**What this covers and what it does not.** ``tests/integration/`` is deliberately
absent from CI (see the "API tests" step in ``.github/workflows/backend.yml``): it
needs a real ArangoDB and without one it self-skips, reporting green having tested
almost nothing. So the two queries below — the orphan sweep and the predicate behind
the interactive photo delete, both of which decide what gets **deleted** — are
executed by no gate. A syntax or semantics regression in them ships green and is
found by the nightly job destroying the wrong row.

Running the integration tier in CI is the real fix and is tracked in #1432; it needs a
service container and a guard that the tier did not self-skip to green, which is a
decision about the whole tier rather than about this file.

What is checkable offline is the failure class that actually occurred while writing
these queries: a bind parameter and the query drifting apart. Both directions are
silent in different ways —

* a parameter the query names and the caller does not supply raises at execution, in
  the nightly Celery task, seen by nobody until someone reads the log;
* a parameter supplied and not named is inert, and inert is how the tenant narrowing
  would look if it were dropped from the prelude while ``ref_tenant_key`` kept being
  passed: the delete route would go back to scanning every tenant and nothing would
  say so.

Asserted against the query text the methods actually build, extracted by monkeypatching
``execute`` — not against a copy of it. A test holding its own transcription of the
AQL certifies the transcription (this PR's round-4 finding, in a different file).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import pytest

from app.data_access.arango.attachment_repository import ArangoAttachmentRepository

#: ``@@name`` (a collection) or ``@name`` (a value). The longer alternative first,
#: so ``@@ref_col_0`` is not read as the value parameter ``@ref_col_0``.
_BIND = re.compile(r"@@?[A-Za-z_][A-Za-z0-9_]*")


class _CapturingAQL:
    def __init__(self):
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.calls.append((query, dict(bind_vars or {})))
        return iter(())


class _CapturingDB:
    def __init__(self):
        self.aql = _CapturingAQL()


def _repo() -> tuple[ArangoAttachmentRepository, _CapturingDB]:
    repo = ArangoAttachmentRepository.__new__(ArangoAttachmentRepository)
    db = _CapturingDB()
    repo._db = db
    repo._collection_name = "attachments"
    return repo, db


def _named(query: str) -> set[str]:
    """Bind parameters the query names, in ``bind_vars`` spelling.

    ``@@x`` is supplied as ``"@x"`` and ``@x`` as ``"x"``, so both are normalised to
    the key the caller must use.
    """
    return {token[1:] for token in _BIND.findall(query)}


def _run_all() -> list[tuple[str, str, dict[str, Any]]]:
    """Every attachment query that carries the reference prelude, with its binds."""
    captured: list[tuple[str, str, dict[str, Any]]] = []

    repo, db = _repo()
    repo.find_orphaned_task_photos(older_than=datetime(2026, 1, 1, tzinfo=UTC), limit=10)
    captured += [("find_orphaned_task_photos", q, b) for q, b in db.aql.calls]

    repo, db = _repo()
    repo.unreferenced_among(["att-1"], "tenant-a")
    captured += [("unreferenced_among", q, b) for q, b in db.aql.calls]

    repo, db = _repo()
    repo.unreferenced_among(["att-1"], "tenant-a", ignoring_task_key="task-1")
    captured += [("unreferenced_among(ignoring)", q, b) for q, b in db.aql.calls]

    return captured


def test_the_queries_were_actually_captured():
    """The control. Without it every assertion below passes over an empty list.

    That is not hypothetical: these methods return early for empty input, and an
    early return would leave ``calls`` empty and each parametrized case vacuous.
    """
    captured = _run_all()
    assert len(captured) == 3, [name for name, _q, _b in captured]
    for name, query, _binds in captured:
        assert "FOR" in query and "@@collection" in query, name


@pytest.mark.parametrize("case", _run_all(), ids=lambda case: case[0])
def test_every_named_bind_parameter_is_supplied(case: tuple[str, str, dict[str, Any]]):
    name, query, binds = case
    missing = _named(query) - set(binds)
    assert not missing, (
        f"{name} names bind parameters it does not supply: {sorted(missing)}. "
        f"ArangoDB rejects the query at execution — in the nightly Celery task, where "
        f"nobody is watching (#1393)."
    )


@pytest.mark.parametrize("case", _run_all(), ids=lambda case: case[0])
def test_every_supplied_bind_parameter_is_named(case: tuple[str, str, dict[str, Any]]):
    name, query, binds = case
    unused = set(binds) - _named(query)
    assert not unused, (
        f"{name} supplies bind parameters the query never names: {sorted(unused)}. "
        f"ArangoDB rejects this too, and before it does it means a filter went missing "
        f"while its value kept being passed — which is what a dropped tenant narrowing "
        f"looks like from the outside: nothing (#1393)."
    )


def test_the_tenant_narrowing_reaches_the_interactive_query_only():
    """Where ``ref_tenant_key`` may and may not appear, asserted on the real queries.

    The sweep is installation-wide and has no tenant; narrowing it would make it
    check one tenant's references against every tenant's photos, and delete other
    tenants' data. The delete route is the opposite case and must carry it.
    """
    by_name = {name: (query, binds) for name, query, binds in _run_all()}

    sweep_query, sweep_binds = by_name["find_orphaned_task_photos"]
    assert "@ref_tenant_key" not in sweep_query
    assert "ref_tenant_key" not in sweep_binds

    for name in ("unreferenced_among", "unreferenced_among(ignoring)"):
        query, binds = by_name[name]
        assert "@ref_tenant_key" in query, name
        assert binds.get("ref_tenant_key") == "tenant-a", name
