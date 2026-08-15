"""v0043 derives a batch's owner from the plants that use it (#1195).

The migration exists so the new strict batch filter has something to filter *by*.
Its interesting cases are all in the residue: the batches it deliberately does
**not** attribute, and whether it reports them loudly enough that an operator can
act — because an unattributed batch is invisible to every tenant afterwards.

The AQL double answers the migration's *own* query text and refuses one it does
not recognise. A double that silently returned `[]` for an unknown query would
make every assertion here pass vacuously, including the idempotence one, which is
supposed to see an empty write list.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.migrations.versions.v0043_attribute_substrate_batches import (
    AttributeSubstrateBatchesMigration,
)

_BATCHES = "substrate_batches"
_PLANTS = "plant_instances"


class _Collection:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self.docs = docs
        self.updates: list[dict[str, Any]] = []

    def update(self, patch: dict[str, Any]) -> None:
        self.updates.append(patch)
        self.docs[patch["_key"]].update({k: v for k, v in patch.items() if k != "_key"})


class _Aql:
    def __init__(self, batches: _Collection, plants: _Collection) -> None:
        self._batches = batches
        self._plants = plants

    def execute(self, query: str, bind_vars: dict | None = None) -> list[dict[str, Any]]:
        normalised = re.sub(r"\s+", " ", query).strip()
        if _BATCHES not in normalised or _PLANTS not in normalised:
            raise AssertionError(f"unexpected query, this double cannot answer it: {normalised!r}")
        if "p.substrate_batch_key == batch._key" not in normalised:
            raise AssertionError(
                "the migration no longer derives ownership from plant_instance.substrate_batch_key. "
                "That reference is the only evidence of who mixed a batch; anything else would be a guess."
            )
        rows = []
        for key, batch in self._batches.docs.items():
            tenants = sorted(
                {p.get("tenant_key") for p in self._plants.docs.values() if p.get("substrate_batch_key") == key}
            )
            rows.append({"key": key, "stored": batch.get("tenant_key"), "tenants": tenants})
        return rows


class _Db:
    def __init__(self, batches: _Collection, plants: _Collection) -> None:
        self._cols = {_BATCHES: batches, _PLANTS: plants}
        self.aql = _Aql(batches, plants)

    def has_collection(self, name: str) -> bool:
        return name in self._cols

    def collection(self, name: str) -> _Collection:
        return self._cols[name]


def _db(batches: dict[str, dict], plants: dict[str, dict]) -> _Db:
    return _Db(_Collection(batches), _Collection(plants))


@pytest.fixture
def migration() -> AttributeSubstrateBatchesMigration:
    return AttributeSubstrateBatchesMigration()


def test_a_batch_used_by_one_tenants_plants_gets_that_tenant(migration) -> None:
    db = _db({"b1": {}}, {"p1": {"substrate_batch_key": "b1", "tenant_key": "t_alice"}})

    report = migration.up(db)

    assert db.collection(_BATCHES).docs["b1"]["tenant_key"] == "t_alice"
    assert report.changed == 1


def test_several_plants_of_the_same_tenant_are_still_unambiguous(migration) -> None:
    db = _db(
        {"b1": {}},
        {
            "p1": {"substrate_batch_key": "b1", "tenant_key": "t_alice"},
            "p2": {"substrate_batch_key": "b1", "tenant_key": "t_alice"},
        },
    )

    migration.up(db)

    assert db.collection(_BATCHES).docs["b1"]["tenant_key"] == "t_alice"


def test_a_batch_used_by_two_tenants_is_left_unstamped_and_named(migration) -> None:
    """The decided rule: no invented owner.

    Picking the majority hands somebody else's batch to a stranger; stamping it
    globally makes it readable by everyone, which is the state this migration
    ends. The *keys* are reported, not just a count — an operator cannot attribute
    a batch they cannot name, and these rows are invisible in the UI until they do.
    """
    db = _db(
        {"b1": {}},
        {
            "p1": {"substrate_batch_key": "b1", "tenant_key": "t_alice"},
            "p2": {"substrate_batch_key": "b1", "tenant_key": "t_bob"},
        },
    )

    report = migration.up(db)

    assert "tenant_key" not in db.collection(_BATCHES).docs["b1"]
    assert report.details["ambiguous_left_unstamped"] == ["b1"]
    assert report.changed == 0


def test_a_batch_no_plant_references_is_counted_separately(migration) -> None:
    """Not the same case as ambiguous. A freshly mixed, not-yet-used batch is
    normal; two owners is evidence of a data problem. Folding them into one
    number would hide the difference an operator needs to act on."""
    db = _db({"b1": {}}, {})

    report = migration.up(db)

    assert report.details["orphaned_left_unstamped"] == 1
    assert report.details["ambiguous_left_unstamped"] == []


def test_an_unstamped_referencing_plant_does_not_make_a_batch_ambiguous(migration) -> None:
    """A plant that itself carries no tenant is no evidence of ownership.

    Counting its empty key as a distinct owner would make every batch touched by
    one un-migrated plant look ambiguous — and ambiguity here means the batch
    disappears from its real owner's UI. So the empty key is dropped, not counted.
    """
    db = _db(
        {"b1": {}},
        {
            "p1": {"substrate_batch_key": "b1", "tenant_key": "t_alice"},
            "p2": {"substrate_batch_key": "b1", "tenant_key": ""},
        },
    )

    migration.up(db)

    assert db.collection(_BATCHES).docs["b1"]["tenant_key"] == "t_alice"


def test_an_already_correct_batch_is_not_rewritten(migration) -> None:
    """M-3, asserted on the writes and not only on the report: a migration that
    rewrote every row with the same value would count honestly and still churn
    the whole collection on each run."""
    db = _db({"b1": {"tenant_key": "t_alice"}}, {"p1": {"substrate_batch_key": "b1", "tenant_key": "t_alice"}})

    report = migration.up(db)

    assert db.collection(_BATCHES).updates == []
    assert report.changed == 0


def test_a_wrongly_stamped_batch_is_corrected(migration) -> None:
    db = _db({"b1": {"tenant_key": "t_bob"}}, {"p1": {"substrate_batch_key": "b1", "tenant_key": "t_alice"}})

    migration.up(db)

    assert db.collection(_BATCHES).docs["b1"]["tenant_key"] == "t_alice"


def test_a_dry_run_writes_nothing_but_reports_the_same_plan(migration) -> None:
    db = _db({"b1": {}}, {"p1": {"substrate_batch_key": "b1", "tenant_key": "t_alice"}})

    dry = migration.up(db, dry_run=True)

    assert db.collection(_BATCHES).updates == []
    assert dry.changed == 0
    assert dry.details["attributed"] == 1


def test_a_fresh_install_without_the_collections_is_not_an_error(migration) -> None:
    class _Empty:
        aql = None

        def has_collection(self, name: str) -> bool:
            return False

    report = migration.up(_Empty())

    assert report.changed == 0
    assert report.scanned == 0


def test_the_migration_is_marked_irreversible(migration) -> None:
    assert migration.reversible is False
