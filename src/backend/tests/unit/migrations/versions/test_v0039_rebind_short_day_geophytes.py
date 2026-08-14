"""v0039 moves short-day geophytes onto the sequence their year actually has (#1149).

The resolver fix only changes what a **fresh** install binds. An existing install
carries the `photoperiodic_ornamental` edge `v0027` wrote, and a shipped migration
is a record of what it did — not a live statement of what is correct. Without
this rebind the two diverge permanently, which is precisely what
`test_photoperiodic_ornamental_seed_convergence` caught.

Three properties matter beyond "it rewrites the edge", and each has a test:

* **the scope guard** — only an edge currently on `photoperiodic_ornamental`
  moves. A species an operator has since bound by hand is not this migration's
  business, and a rebind that ignored that would silently overwrite a human
  decision with a classifier's;
* **idempotence (M-3)** — the second run reports zero, so a re-run after a partial
  failure is safe;
* **the no-op paths** — an unseeded database, a missing target sequence, an
  unaffected species. A migration that raised on any of those would break boot on
  a fresh install rather than doing nothing.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.versions.v0039_rebind_short_day_geophytes import (
    RebindShortDayGeophytesMigration,
)

_DAHLIA = "Dahlia pinnata"
_UNAFFECTED = "Euphorbia pulcherrima"


class _Aql:
    def __init__(self, db: _Db) -> None:
        self._db = db
        self.updates: list[dict[str, Any]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if query.strip().startswith("UPDATE"):
            assert bind_vars is not None
            self.updates.append(bind_vars)
            for edge in self._db.collections[col.HAS_PHASE_SEQUENCE]:
                if edge["_key"] == bind_vars["key"]:
                    edge["_to"] = bind_vars["to_id"]
            return []
        # `FOR d IN <collection> RETURN d`
        name = query.split(" IN ", 1)[1].split(" ", 1)[0].strip()
        return list(self._db.collections.get(name, []))


class _Db:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self.collections = collections
        self.aql = _Aql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.collections


def _db(
    *,
    species: list[str] | None = None,
    sequences: tuple[str, ...] = ("photoperiodic_ornamental", "geophyte_fine"),
    bound_to: str = "photoperiodic_ornamental",
) -> _Db:
    species_names = [_DAHLIA] if species is None else species
    species_docs = [{"_key": f"sp{i}", "scientific_name": n} for i, n in enumerate(species_names)]
    seq_docs = [{"_key": f"seq{i}", "name": n} for i, n in enumerate(sequences)]
    seq_key = {d["name"]: d["_key"] for d in seq_docs}
    edges = [
        {
            "_key": f"e{i}",
            "_from": f"{col.SPECIES}/{d['_key']}",
            "_to": f"{col.PHASE_SEQUENCES}/{seq_key[bound_to]}",
        }
        for i, d in enumerate(species_docs)
        if bound_to in seq_key
    ]
    return _Db(
        {
            col.SPECIES: species_docs,
            col.PHASE_SEQUENCES: seq_docs,
            col.HAS_PHASE_SEQUENCE: edges,
        }
    )


def _target_of(db: _Db) -> str:
    seq_name = {f"{col.PHASE_SEQUENCES}/{s['_key']}": s["name"] for s in db.collections[col.PHASE_SEQUENCES]}
    return seq_name[db.collections[col.HAS_PHASE_SEQUENCE][0]["_to"]]


@pytest.fixture
def migration() -> RebindShortDayGeophytesMigration:
    return RebindShortDayGeophytesMigration()


def test_a_dahlia_on_the_ornamental_cycle_is_rebound(migration) -> None:
    db = _db()

    report = migration.up(db)

    assert report.changed == 1
    assert _target_of(db) == "geophyte_fine"


def test_a_dry_run_writes_nothing_but_reports_the_plan(migration) -> None:
    db = _db()

    report = migration.up(db, dry_run=True)

    assert report.scanned == 1
    assert report.changed == 0
    assert _target_of(db) == "photoperiodic_ornamental"


def test_a_second_run_is_a_no_op(migration) -> None:
    """M-3. A re-run after a partial failure must not thrash the edge."""
    db = _db()
    migration.up(db)

    second = migration.up(db)

    assert second.changed == 0


def test_a_hand_bound_species_is_left_alone(migration) -> None:
    """The scope guard, and the reason it is not "rebind everything affected".

    An edge on some third sequence is an operator's decision. Overwriting it would
    let a classifier correction silently undo human curation — a worse failure than
    the one being fixed, because nothing reports it.
    """
    db = _db(
        sequences=("photoperiodic_ornamental", "geophyte_fine", "evergreen_foliage_perennial"),
        bound_to="evergreen_foliage_perennial",
    )

    report = migration.up(db)

    assert report.changed == 0
    assert _target_of(db) == "evergreen_foliage_perennial"


def test_a_species_outside_the_map_is_untouched(migration) -> None:
    """Poinsettia is short-day and genuinely belongs on the ornamental cycle."""
    db = _db(species=[_UNAFFECTED])

    report = migration.up(db)

    assert report.changed == 0
    assert _target_of(db) == "photoperiodic_ornamental"


def test_an_empty_database_is_a_clean_no_op(migration) -> None:
    report = migration.up(_Db({}))

    assert report.changed == 0


def test_a_missing_target_sequence_is_a_clean_no_op(migration) -> None:
    """A partially seeded install must not raise during boot."""
    db = _db(sequences=("photoperiodic_ornamental",))

    report = migration.up(db)

    assert report.changed == 0
