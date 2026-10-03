"""#2001 — two replicas booting at once write each create-if-absent seed row once.

The seed registry runs on every replica without a lock. The harvest-indicator seed
(by ``(species, indicator_type, measurement_unit)``) and the IPM treatment edges (by
vertex pair) look before they write, which holds only sequentially: two writers both
read "absent" and both insert. The unique identity indexes make the storage layer
refuse the loser, and the loaders read the refusal as "exists".

The writers are released together by a barrier, so the look-then-write windows
overlap on purpose rather than by luck.
"""

from __future__ import annotations

import threading
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.ipm_repository import ArangoIpmRepository
from app.migrations.seed_harvest_indicators import run_seed_harvest_indicators
from app.migrations.seeds.registry import run_seeds
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("concurrent writers are measured against a real server"),
]

_DB_NAME = run_database_name("seed_identity_concurrency")
_WRITERS = 6
_PAIRS = 25
#: The collections whose rows the create-if-absent seed writes produce (#2001).
_GUARDED = ("harvest_indicators", "has_harvest_indicator", "targets_pest", "targets_disease", "contraindicated_with")


@pytest.fixture(scope="module")
def booted(request):
    """A database the registry booted once; ``{collection: rows}`` of that boot."""
    monkeypatch = pytest.MonkeyPatch()
    system, db = create_database(_DB_NAME)
    bind_database(monkeypatch, db)
    try:
        run_seeds(db)
        yield db, {name: db.collection(name).count() for name in _GUARDED}
    finally:
        monkeypatch.undo()
        system.delete_database(_DB_NAME)


def _together(n: int, work: Callable[[], Any]) -> list[Any]:
    """Run ``work`` on ``n`` threads released at the same instant; re-raise the first failure."""
    barrier = threading.Barrier(n)

    def run() -> Any:
        barrier.wait()
        return work()

    with ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(run) for _ in range(n)]
        return [f.result() for f in futures]


def _wipe(db) -> None:
    for name in _GUARDED:
        db.collection(name).truncate()


def test_concurrent_edge_writers_leave_one_edge_per_pair(booted) -> None:
    db, _ = booted
    repo = ArangoIpmRepository(db)
    pairs = [(f"t-{i}", f"p-{i}") for i in range(_PAIRS)]

    def write_all() -> int:
        return sum(1 for t, p in pairs if repo.create_edge_if_absent(col.TARGETS_PEST, f"treatments/{t}", f"pests/{p}"))

    created = _together(_WRITERS, write_all)

    rows = db.collection(col.TARGETS_PEST).all()
    edges = Counter((e["_from"], e["_to"]) for e in rows if e["_from"].startswith("treatments/t-"))
    assert [pair for pair, n in edges.items() if n > 1] == []
    assert sum(created) == _PAIRS, "every pair is reported created exactly once"


def test_concurrent_harvest_indicator_seeds_write_each_identity_once(booted) -> None:
    db, counts = booted
    db.collection(col.HARVEST_INDICATORS).truncate()
    db.collection(col.HAS_HARVEST_INDICATOR).truncate()

    _together(_WRITERS, run_seed_harvest_indicators)

    rows = db.collection(col.HARVEST_INDICATORS).all()
    identities = Counter((d["species_key"], d["indicator_type"], d["measurement_unit"]) for d in rows)
    assert [identity for identity, n in identities.items() if n > 1] == []
    assert db.collection(col.HARVEST_INDICATORS).count() == counts["harvest_indicators"]
    assert db.collection(col.HAS_HARVEST_INDICATOR).count() == counts["has_harvest_indicator"]


def test_two_concurrent_boots_leave_the_guarded_counts_of_one_boot(booted) -> None:
    db, counts = booted
    _wipe(db)

    _together(2, lambda: run_seeds(db))

    assert {name: db.collection(name).count() for name in _GUARDED} == counts
