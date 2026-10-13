"""Finding A — the IPM rows of plant_info.yaml and adventskalender.yaml reach the database.

Both loaders read ``pests`` / ``diseases`` / ``treatments`` while the files say
``new_pests`` / ``new_diseases`` / ``new_treatments``. Measured on ArangoDB 3.12.8 after
a full seed run: ``Bemisia tabaci``, ``Septoria apiicola`` and ``Ferramol`` absent.

The real loaders run through the real registry (under the migration lock), against
the shared catalogue the core seed writes first — the order of the boot.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.runner import run_pending_migrations
from app.migrations.seed_adventskalender import run_seed_adventskalender
from app.migrations.seed_data import run_seed
from app.migrations.seed_plant_info import run_seed_plant_info
from app.migrations.seeds.registry import SeedJob, run_seeds
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the seed loaders write IPM rows to a real server"),
]

_IPM = (col.PESTS, col.DISEASES, col.TREATMENTS, col.TARGETS_PEST, col.TARGETS_DISEASE)


def _jobs() -> list[SeedJob]:
    """The three jobs of the boot that write IPM rows, in the registry's order."""
    return [
        SeedJob("core_data", lambda db: run_seed()),
        SeedJob("adventskalender", lambda db: run_seed_adventskalender()),
        SeedJob("plant_info", lambda db: run_seed_plant_info()),
    ]


def _counts(db) -> dict[str, int]:
    return {name: db.collection(name).count() for name in _IPM}


def _has_edge(db, edge: str, treatment: str, target_collection: str, field: str, value: str) -> bool:
    query = """
        FOR t IN treatments FILTER t.name == @treatment
            FOR x IN @@targets FILTER x[@field] == @value
                FOR e IN @@edges FILTER e._from == t._id AND e._to == x._id RETURN 1
    """
    rows = db.aql.execute(
        query,
        bind_vars={
            "treatment": treatment,
            "@targets": target_collection,
            "field": field,
            "value": value,
            "@edges": edge,
        },
    )
    return bool(list(rows))


def _boot(name: str, replicas: int, runs: int = 1) -> tuple[dict[str, int], object, object, pytest.MonkeyPatch]:
    monkeypatch = pytest.MonkeyPatch()
    system, db = create_database(name)
    bind_database(monkeypatch, db)
    run_pending_migrations(db)

    def replica(barrier: threading.Barrier) -> None:
        barrier.wait()
        run_seeds(db, jobs=_jobs())

    for _ in range(runs):
        barrier = threading.Barrier(replicas)
        with ThreadPoolExecutor(max_workers=replicas) as pool:
            for future in [pool.submit(replica, barrier) for _ in range(replicas)]:
                future.result()
    return _counts(db), system, db, monkeypatch


@pytest.fixture
def booted():
    name = run_database_name("seed_ipm_rows_reach")
    counts, system, db, monkeypatch = _boot(name, replicas=1)
    yield counts, db
    monkeypatch.undo()
    system.delete_database(name)


def test_the_files_rows_and_edges_are_seeded(booted) -> None:
    _counts_after, db = booted

    assert db.collection(col.PESTS).find({"scientific_name": "Bemisia tabaci"}).count() == 1
    assert db.collection(col.DISEASES).find({"scientific_name": "Septoria apiicola"}).count() == 1
    assert db.collection(col.TREATMENTS).find({"name": "Ferramol"}).count() == 1
    # adventskalender names this disease by ``name``, the model by ``common_name``
    assert db.collection(col.DISEASES).find({"scientific_name": "Puccinia porri"}).next()["common_name"] == "Leek Rust"
    # plant_info links a treatment adventskalender created to a pest of ipm.yaml
    assert _has_edge(db, col.TARGETS_PEST, "Ferramol", col.PESTS, "scientific_name", "Arion vulgaris")
    # …and its own name of a pest stored under another common name ("Gray Mold" for Botrytis)
    assert _has_edge(db, col.TARGETS_DISEASE, "Straw Mulch", col.DISEASES, "scientific_name", "Botrytis cinerea")
    # a row the model refuses is skipped, not invented: a chemical treatment without a safety interval
    assert db.collection(col.TREATMENTS).find({"name": "Alcohol Spray"}).count() == 0


def test_a_second_run_writes_nothing(booted) -> None:
    first, db = booted

    run_seeds(db, jobs=_jobs())

    assert _counts(db) == first


def test_a_concurrent_pair_equals_one_run() -> None:
    sequential_name = run_database_name("seed_ipm_rows_sequential")
    concurrent_name = run_database_name("seed_ipm_rows_concurrent")
    sequential, system, _db, patch_a = _boot(sequential_name, replicas=1)
    patch_a.undo()
    system.delete_database(sequential_name)
    concurrent, system, _db, patch_b = _boot(concurrent_name, replicas=2)
    patch_b.undo()
    system.delete_database(concurrent_name)

    assert concurrent == sequential
