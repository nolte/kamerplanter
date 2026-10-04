"""#2028 — two replicas booting at once leave the counts of one boot, and neither aborts.

Measured on the unlocked registry (ArangoDB 3.12, fresh database, migrations applied,
two ``run_seeds`` released by a barrier): 40 phase sequences instead of 21, 66
nutrient plans instead of 38, 56 substrates instead of 28, and — without a prior
``location_types`` run — the losing replica died with ``ERR 1210 ... conflicting
key: home``. The registry now runs under the migration lock; the replica that waits
finds the other one's completed run and does not seed again.

The reference is one sequential boot of a separate fresh database. A second
sequential boot is *not* the reference: it is measured to add 11 cultivars and 6
companion edges on a fresh volume (cultivars and companions that name a species
seeded later in the registry converge on the second boot), so "counts of two boots"
would hide a skipped run and "counts of one boot" is what a concurrent first boot
must equal.

Run with: pytest tests/integration/test_seed_registry_lock.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.migrations.framework import tracking
from app.migrations.framework.runner import run_pending_migrations
from app.migrations.seeds.registry import run_seeds
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("two concurrent seed runs are measured against a real server"),
]

#: The collections #2028 measured duplicated (plus the fatal job's and two guarded ones).
_COUNTED = (
    "lifecycle_configs",
    "has_lifecycle",
    "growth_phases",
    "consists_of",
    "requirement_profiles",
    "nutrient_profiles",
    "cultivars",
    "has_cultivar",
    "nutrient_plans",
    "nutrient_plan_phase_entries",
    "phase_sequences",
    "phase_sequence_entries",
    "has_phase_sequence",
    "compatible_with",
    "phase_transition_rules",
    "next_phase",
    "governed_by",
    "substrates",
    "location_types",
    "species",
    "harvest_indicators",
)


def _boot(name: str, replicas: int) -> tuple[dict[str, int], list[str]]:
    """Fresh database, migrations applied, ``replicas`` concurrent ``run_seeds``; counts + outcomes."""
    monkeypatch = pytest.MonkeyPatch()
    system, db = create_database(name)
    bind_database(monkeypatch, db)
    try:
        run_pending_migrations(db)
        barrier = threading.Barrier(replicas)

        def replica() -> str:
            barrier.wait()
            run_seeds(db)
            return "started"

        with ThreadPoolExecutor(max_workers=replicas) as pool:
            futures = [pool.submit(replica) for _ in range(replicas)]
            outcomes = []
            for future in futures:
                try:
                    outcomes.append(future.result())
                except Exception as exc:  # the defect: a replica aborts its startup
                    outcomes.append(f"aborted: {exc!r}")
        counts = {collection: db.collection(collection).count() for collection in _COUNTED}
        assert db.collection("schema_migrations").get(tracking.LOCK_KEY) is None, "the lock was released"
        return counts, outcomes
    finally:
        monkeypatch.undo()
        system.delete_database(name)


@pytest.fixture(scope="module")
def one_sequential_boot() -> dict[str, int]:
    counts, outcomes = _boot(run_database_name("seed_lock_sequential"), replicas=1)
    assert outcomes == ["started"]
    return counts


def test_two_concurrent_first_boots_leave_the_counts_of_one_boot(one_sequential_boot) -> None:
    counts, outcomes = _boot(run_database_name("seed_lock_concurrent"), replicas=2)

    assert outcomes == ["started", "started"], "no replica aborts (ERR 1210 on location_types before #2028)"
    assert counts == one_sequential_boot
    assert counts["phase_sequences"] > 0 and counts["location_types"] > 0, "the boot seeded (non-vacuous)"


def test_refresh_lock_is_fenced_by_owner_and_revision_on_the_real_driver() -> None:
    """The in-memory double models ``_rev`` fencing; this measures the driver does the same."""
    from arango.exceptions import DocumentRevisionError

    name = run_database_name("seed_lock_refresh")
    system, db = create_database(name)
    try:
        col = db.collection("schema_migrations")
        owner = tracking.acquire_lock(db)
        col.update({"_key": tracking.LOCK_KEY, "acquired_at": "2000-01-01T00:00:00+00:00"})

        assert tracking.refresh_lock(db, owner) is True
        assert col.get(tracking.LOCK_KEY)["acquired_at"] > "2026"

        stale = col.get(tracking.LOCK_KEY)
        col.update({"_key": tracking.LOCK_KEY, "owner": owner})  # bumps _rev under the reader
        with pytest.raises(DocumentRevisionError):
            col.replace({**stale, "acquired_at": "x"})  # what refresh_lock's replace meets after a race

        col.update({"_key": tracking.LOCK_KEY, "owner": "taken-over"})
        assert tracking.refresh_lock(db, owner) is False
        assert col.get(tracking.LOCK_KEY)["owner"] == "taken-over"
    finally:
        system.delete_database(name)
