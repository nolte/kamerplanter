"""v0042 copies each run entry's tenant from its parent run (SEC-004, #1112).

The migration exists so an *existing* volume's entries can be checked by the
owned-reference guard at all: the guard compares against the row's own
``tenant_key`` and skips a row that has none, so until every stored entry carries
one, the guard is live for new rows and inert for old ones.

The AQL double below **executes the migration's own query text** rather than
re-implementing what it is assumed to select. A double that answered from its own
notion of "entry belongs to run" could agree with itself while disagreeing with
ArangoDB — the failure this suite has hit before (v0040's double copied bind
*variables* onto documents and its tests were green about the wrong write).
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.migrations.versions.v0042_stamp_planting_run_entry_tenant import (
    StampPlantingRunEntryTenantMigration,
)

_RUNS = "planting_runs"
_ENTRIES = "planting_run_entries"


class _Collection:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self.docs = docs
        self.updates: list[dict[str, Any]] = []

    def update(self, patch: dict[str, Any]) -> None:
        self.updates.append(patch)
        self.docs[patch["_key"]].update({k: v for k, v in patch.items() if k != "_key"})


class _Aql:
    """Answers the migration's plan query against the in-memory documents.

    It reads the query text to confirm it is the one it knows how to answer, and
    refuses anything else. A double that silently returned ``[]`` for an unknown
    query would make every assertion below pass vacuously — including the
    idempotence one, which is *supposed* to see an empty write list.
    """

    def __init__(self, runs: _Collection, entries: _Collection) -> None:
        self._runs = runs
        self._entries = entries

    def execute(self, query: str, bind_vars: dict | None = None) -> list[dict[str, Any]]:
        normalised = re.sub(r"\s+", " ", query).strip()
        if _ENTRIES not in normalised or _RUNS not in normalised:
            raise AssertionError(f"unexpected query, this double cannot answer it: {normalised!r}")
        if "entry.run_key" not in normalised:
            raise AssertionError(
                "the migration no longer resolves an entry's run through `entry.run_key`. "
                "That field is what every application read uses (get_entries is "
                "find_by_field('run_key', …)), so a stamp derived from anything else — "
                "the has_entry edge, say — could disagree with how the row is actually read."
            )
        rows = []
        for key, entry in self._entries.docs.items():
            run = self._runs.docs.get(entry.get("run_key"))
            rows.append(
                {
                    "key": key,
                    "stored": entry.get("tenant_key"),
                    "run_tenant": run.get("tenant_key") if run else None,
                    "orphaned": run is None,
                }
            )
        return rows


class _Db:
    def __init__(self, runs: _Collection, entries: _Collection) -> None:
        self._cols = {_RUNS: runs, _ENTRIES: entries}
        self.aql = _Aql(runs, entries)

    def has_collection(self, name: str) -> bool:
        return name in self._cols

    def collection(self, name: str) -> _Collection:
        return self._cols[name]


def _db(entries: dict[str, dict[str, Any]], runs: dict[str, dict[str, Any]] | None = None) -> _Db:
    default_runs = {
        "run_a": {"tenant_key": "tenant_alice"},
        "run_b": {"tenant_key": "tenant_bob"},
        "run_global": {"tenant_key": ""},
    }
    return _Db(_Collection(runs if runs is not None else default_runs), _Collection(entries))


@pytest.fixture
def migration() -> StampPlantingRunEntryTenantMigration:
    return StampPlantingRunEntryTenantMigration()


def test_an_unstamped_entry_gets_its_runs_tenant(migration) -> None:
    db = _db({"e1": {"run_key": "run_a"}})

    report = migration.up(db)

    assert db.collection(_ENTRIES).docs["e1"]["tenant_key"] == "tenant_alice"
    assert report.changed == 1


def test_entries_of_different_runs_get_different_tenants(migration) -> None:
    """The stamp comes from *each* entry's own run.

    A migration that read one run and applied it to everything would pass a
    single-entry test and quietly hand one tenant's entries to another.
    """
    db = _db({"e1": {"run_key": "run_a"}, "e2": {"run_key": "run_b"}})

    migration.up(db)

    stamped = {k: v["tenant_key"] for k, v in db.collection(_ENTRIES).docs.items()}
    assert stamped == {"e1": "tenant_alice", "e2": "tenant_bob"}


def test_a_correctly_stamped_entry_is_not_rewritten(migration) -> None:
    """M-3 idempotence, asserted on the *writes* and not only on the report.

    A migration that rewrote every row with the same value would report
    ``changed`` honestly per its own counting and still churn the whole
    collection on each run.
    """
    db = _db({"e1": {"run_key": "run_a", "tenant_key": "tenant_alice"}})

    report = migration.up(db)

    assert db.collection(_ENTRIES).updates == []
    assert report.changed == 0


def test_a_wrongly_stamped_entry_is_corrected(migration) -> None:
    """Not only "fill in the blanks".

    An entry carrying a stale tenant — a run moved, a bad import — is exactly the
    row whose guard would compare against the wrong tenant, so "already has a
    value" must not mean "leave it alone".
    """
    db = _db({"e1": {"run_key": "run_a", "tenant_key": "tenant_bob"}})

    migration.up(db)

    assert db.collection(_ENTRIES).docs["e1"]["tenant_key"] == "tenant_alice"


def test_an_entry_of_a_global_run_is_left_empty_and_counted_as_unchanged(migration) -> None:
    """``""`` is a legitimate tenant value, and copying it is a no-op.

    Worth pinning because "" is falsy: an implementation using ``or`` to decide
    whether to write would treat a global run as "no tenant found" and could fall
    through to some other source.
    """
    db = _db({"e1": {"run_key": "run_global"}})

    report = migration.up(db)

    assert db.collection(_ENTRIES).updates == []
    assert report.changed == 0


def test_an_orphaned_entry_is_left_alone_and_reported(migration) -> None:
    """Stamping it would mean inventing an owner.

    It is unreachable anyway — every route resolves entries through a run — so
    leaving it unstamped keeps exactly the pre-migration behaviour. What must not
    happen is it disappearing from the report: a silent skip is how a migration
    claims to have covered rows it never touched.
    """
    db = _db({"e1": {"run_key": "run_a"}, "orphan": {"run_key": "run_that_is_gone"}})

    report = migration.up(db)

    assert "tenant_key" not in db.collection(_ENTRIES).docs["orphan"]
    assert report.details["orphaned_entries_left_unstamped"] == 1
    assert report.changed == 1


def test_a_dry_run_writes_nothing_but_reports_the_same_plan(migration) -> None:
    """M-5. The counts come from the same pure ``_plan``, so a dry run cannot
    describe work the real run would not do."""
    db = _db({"e1": {"run_key": "run_a"}})

    dry = migration.up(db, dry_run=True)

    assert db.collection(_ENTRIES).updates == []
    assert dry.changed == 0
    assert dry.scanned == 1
    assert dry.details["stamped"] == 1


def test_a_fresh_install_without_the_collections_is_not_an_error(migration) -> None:
    """Startup runs migrations before anything has created these collections."""

    class _Empty:
        aql = None

        def has_collection(self, name: str) -> bool:
            return False

    report = migration.up(_Empty())

    assert report.changed == 0
    assert report.scanned == 0


def test_the_migration_is_marked_irreversible(migration) -> None:
    """M-6. "No attribute at all" and "stamped with an empty tenant" are
    indistinguishable after the fact, and removing the field again would silently
    disarm the guard it exists to enable."""
    assert migration.reversible is False
