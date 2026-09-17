"""Tests for v0048_backfill_missing_care_profiles (#1444 part 2).

**What makes the fake honest.** The population is selected by the AQL the
repository exports, and a fake that re-implemented "non-removed plant with no
profile naming it" would certify its own copy — the failure class this migration
exists to avoid in the first place (audit, nightly warning and backfill must
select ONE population). So ``_FakeAql`` does not know the predicate: it reads the
two FILTER fields **out of the query text** it is handed and applies exactly
those. Renaming the link field in the repository, or dropping the ``removed_on``
arm, therefore turns these tests red instead of leaving them green against a
private copy. ``TestThePredicateIsNotCopied`` adds the other half: the *identity*
of the imported builders, which is what a hand-rolled copy in the migration
module would break.

The fake cannot certify ArangoDB's own ``_key`` assignment, the unique ``_from``
index on ``has_care_profile`` or that the audit script agrees afterwards;
``tests/integration/test_v0048_backfill_missing_care_profiles.py`` runs the same
migration against a real server for those.
"""

from __future__ import annotations

import copy
import re
from typing import Any

import pytest
from arango.exceptions import DocumentInsertError

from app.common.enums import CareStyleType
from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0048_backfill_missing_care_profiles import (
    REQUIRED_COLLECTIONS,
    migration,
)

TENANT = "mein-garten"
PLANT = "plant-1"
SPECIES_KEY = "5551"
#: A botanical family ``_key`` as ArangoDB assigns it — short and numeric, and
#: emphatically not the family name ``FAMILY_CARE_MAP`` is keyed by.
FAMILY_KEY = "7242"
FAMILY_NAME = "Cactaceae"


# ── the fake ──────────────────────────────────────────────────────────────────

#: Reads the population predicate out of the query instead of knowing it.
_REMOVED_RE = re.compile(r"FILTER plant\.(\w+) == null")
_LINK_RE = re.compile(r"FILTER profile\.(\w+) == plant\.(\w+)")


def _population(query: str, plants: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply the FILTERs the query actually spells, to the fake's documents."""
    removed = _REMOVED_RE.search(query)
    link = _LINK_RE.search(query)
    if removed is None or link is None:
        raise AssertionError(
            f"the migration no longer selects through the repository's unprofiled-plant predicate; query was: {query!r}"
        )
    removed_field = removed.group(1)
    profile_field, plant_field = link.groups()
    return [
        plant
        for plant in plants
        if plant.get(removed_field) is None
        and not any(profile.get(profile_field) == plant.get(plant_field) for profile in profiles)
    ]


class _CollectionState:
    """Per-collection state the plain handle and a transaction handle must share.

    A transaction writes through its own handle, but it writes into the *same*
    collection: the unique-index rejection a test arms and the key sequence
    ArangoDB hands out both belong to the collection, not to the handle. Keeping
    them here is what stops ``db.collection(X).refuse_insert = ...`` from silently
    arming a handle the code under test never touches.
    """

    def __init__(self) -> None:
        #: Raised by the next ``insert`` — models the unique ``_from`` index.
        self.refuse_insert: Exception | None = None
        self.next_key = 1000


class _FakeCollection:
    def __init__(
        self,
        name: str,
        documents: list[dict[str, Any]],
        writes: list[tuple[str, str, Any]],
        state: _CollectionState,
    ) -> None:
        self._name = name
        self._documents = documents
        self._writes = writes
        self._state = state

    @property
    def refuse_insert(self) -> Exception | None:
        return self._state.refuse_insert

    @refuse_insert.setter
    def refuse_insert(self, error: Exception | None) -> None:
        self._state.refuse_insert = error

    def insert(self, data: dict[str, Any], return_new: bool = False):
        if self._state.refuse_insert is not None:
            raise self._state.refuse_insert
        document = dict(data)
        # ArangoDB assigns the key; the repository never sends one (``_to_doc``
        # pops ``_key``), so neither does the fake honour one.
        document.pop("_key", None)
        document["_key"] = str(self._state.next_key)
        self._state.next_key += 1
        document["_id"] = f"{self._name}/{document['_key']}"
        self._documents.append(document)
        self._writes.append(("insert", self._name, document))
        return {"new": dict(document)} if return_new else {"_key": document["_key"]}

    def delete(self, key: str) -> bool:
        for index, document in enumerate(self._documents):
            if document.get("_key") == key:
                del self._documents[index]
                self._writes.append(("delete", self._name, key))
                return True
        raise AssertionError(f"no document {key!r} in {self._name}")


class _FakeAql:
    """Interprets exactly the five queries the migration issues."""

    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections
        self.queries: list[str] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        stripped = query.strip()
        self.queries.append(stripped)

        plants = self._collections.get(col.PLANT_INSTANCES, [])
        profiles = self._collections.get(col.CARE_PROFILES, [])

        if stripped.startswith("FOR p IN"):
            keys = set(bind_vars["keys"])
            return iter([{"key": p["_key"], "species": p.get("species_key")} for p in plants if p["_key"] in keys])
        if stripped.startswith("FOR s IN"):
            keys = set(bind_vars["keys"])
            return iter(
                [
                    {"key": s["_key"], "name": s.get("scientific_name"), "family": s.get("family_key")}
                    for s in self._collections.get(col.SPECIES, [])
                    if s["_key"] in keys
                ]
            )
        if stripped.startswith("FOR f IN"):
            keys = set(bind_vars["keys"])
            return iter(
                [
                    {"key": f["_key"], "name": f.get("name")}
                    for f in self._collections.get(col.BOTANICAL_FAMILIES, [])
                    if f["_key"] in keys
                ]
            )

        assert bind_vars.get("@plants") == col.PLANT_INSTANCES, "the population must bind the plant collection"
        assert bind_vars.get("@profiles") == col.CARE_PROFILES, "the population must bind the profile collection"
        selected = _population(stripped, plants, profiles)
        if "COLLECT WITH COUNT INTO" in stripped:
            return iter([len(selected)])
        limit = bind_vars["limit"]
        return iter(
            [
                {
                    "key": plant["_key"],
                    "tenant_key": plant.get("tenant_key"),
                    "instance_id": plant.get("instance_id"),
                    "plant_name": plant.get("plant_name"),
                    "planted_on": plant.get("planted_on"),
                    "created_at": plant.get("created_at"),
                }
                for plant in sorted(selected, key=lambda p: (p.get("tenant_key") or "", p["_key"]))
            ][:limit]
        )


class _FakeTransaction:
    """A stream transaction that really buffers: nothing lands until the commit.

    The migration stores a care profile through
    ``ArangoCareReminderRepository.create_linked_profile``, whose whole point is
    that the profile document is invisible until its ``has_care_profile`` edge is
    in too (#1292). A handle that wrote straight through to the collections would
    let this file certify that guarantee while the code under test had lost it —
    the #1155 shape, a double accepting a state the real thing forbids. So a staged
    document is absent from ``db.collections`` and from ``db.writes`` until
    :meth:`commit_transaction`, and :meth:`abort_transaction` drops it.
    """

    def __init__(self, db: _FakeDb, write: list[str]) -> None:
        self._db = db
        self._write = list(write)
        self._staged: dict[str, list[dict[str, Any]]] = {}
        self._handles: dict[str, _FakeCollection] = {}
        self.committed = False
        self.aborted = False

    def collection(self, name: str) -> _FakeCollection:
        assert name in self._write, (
            f"{name!r} is written inside the transaction but was not declared in "
            f"begin_transaction(write={self._write!r}); ArangoDB refuses that"
        )
        if name not in self._handles:
            self._handles[name] = _FakeCollection(
                name,
                self._staged.setdefault(name, []),
                [],
                self._db.state(name),
            )
        return self._handles[name]

    def commit_transaction(self) -> None:
        self.committed = True
        for name, documents in self._staged.items():
            self._db.collections.setdefault(name, []).extend(documents)
            for document in documents:
                self._db.writes.append(("insert", name, document))
        self._staged.clear()

    def abort_transaction(self) -> None:
        self.aborted = True
        self._staged.clear()


class _FakeDb:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self.collections = collections
        self.aql = _FakeAql(collections)
        self.writes: list[tuple[str, str, Any]] = []
        self._handles: dict[str, _FakeCollection] = {}
        self._states: dict[str, _CollectionState] = {}
        self.transactions: list[_FakeTransaction] = []

    def has_collection(self, name: str) -> bool:
        return name in self.collections

    def state(self, name: str) -> _CollectionState:
        return self._states.setdefault(name, _CollectionState())

    def collection(self, name: str) -> _FakeCollection:
        if name not in self._handles:
            self._handles[name] = _FakeCollection(
                name,
                self.collections.setdefault(name, []),
                self.writes,
                self.state(name),
            )
        return self._handles[name]

    def begin_transaction(self, write: list[str] | None = None, **_: Any) -> _FakeTransaction:
        transaction = _FakeTransaction(self, write or [])
        self.transactions.append(transaction)
        return transaction


def _plant(key: str = PLANT, **overrides: Any) -> dict[str, Any]:
    document = {
        "_key": key,
        "tenant_key": TENANT,
        "instance_id": f"P-{key}",
        "plant_name": "Feigenkaktus",
        "species_key": SPECIES_KEY,
        "removed_on": None,
    }
    document.update(overrides)
    return document


def _seeded(
    *,
    plants: list[dict[str, Any]] | None = None,
    profiles: list[dict[str, Any]] | None = None,
    species: list[dict[str, Any]] | None = None,
    families: list[dict[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    return {
        col.PLANT_INSTANCES: plants if plants is not None else [_plant()],
        col.CARE_PROFILES: profiles if profiles is not None else [],
        col.HAS_CARE_PROFILE: [],
        col.SPECIES: (
            species
            if species is not None
            else [{"_key": SPECIES_KEY, "scientific_name": "Opuntia ficus-indica", "family_key": FAMILY_KEY}]
        ),
        col.BOTANICAL_FAMILIES: (families if families is not None else [{"_key": FAMILY_KEY, "name": FAMILY_NAME}]),
    }


@pytest.fixture
def db() -> _FakeDb:
    return _FakeDb(_seeded())


# ── the predicate is imported, never re-spelled ───────────────────────────────


class TestThePredicateIsNotCopied:
    """The audit, the nightly warning and this migration answer with one FILTER.

    The fake above proves the migration keeps *issuing* that predicate. This
    proves it keeps *importing* it: a copy pasted into the migration module would
    still issue an identical string on the day it was pasted, and would then drift
    silently — which is the only way audit and backfill can come to describe two
    different populations.
    """

    def test_the_builders_are_the_repository_objects_themselves(self) -> None:
        from app.data_access.arango import care_reminder_repository as repository
        from app.migrations.versions import v0048_backfill_missing_care_profiles as version

        assert version.unprofiled_plant_count_aql is repository.unprofiled_plant_count_aql
        assert version.unprofiled_plant_keys_aql is repository.unprofiled_plant_keys_aql

    def test_the_audit_script_and_the_migration_read_one_listing(self) -> None:
        """The positive control depends on it: the audit re-reads what this wrote."""
        import scripts.audit_care_profiles  # noqa: F401 — imported for the shared module path
        from app.data_access.arango.care_reminder_repository import (
            unprofiled_plant_count_aql,
            unprofiled_plant_keys_aql,
        )

        listing = unprofiled_plant_keys_aql()
        counting = unprofiled_plant_count_aql(scoped=False)
        shared = "FILTER profile.plant_key == plant._key"

        assert shared in listing
        assert shared in counting

    def test_the_migration_module_holds_no_second_filter(self) -> None:
        import inspect

        from app.migrations.versions import v0048_backfill_missing_care_profiles as version

        source = inspect.getsource(version)

        assert "FOR profile IN" not in source
        assert "removed_on == null" not in source


# ── the backfill ──────────────────────────────────────────────────────────────


class TestUp:
    def test_an_unprofiled_plant_gets_one_profile_and_one_edge(self, db: _FakeDb) -> None:
        report = migration.up(db)

        profiles = db.collections[col.CARE_PROFILES]
        edges = db.collections[col.HAS_CARE_PROFILE]
        assert len(profiles) == 1
        assert len(edges) == 1
        assert profiles[0]["plant_key"] == PLANT
        assert edges[0]["_from"] == f"{col.PLANT_INSTANCES}/{PLANT}"
        assert edges[0]["_to"] == f"{col.CARE_PROFILES}/{profiles[0]['_key']}"
        assert report.scanned == 1
        assert report.changed == 1
        assert report.details["created_total"] == 1
        # One transaction, committed: the document and the edge are one write (#1292).
        assert [(t.committed, t.aborted) for t in db.transactions] == [(True, False)]

    def test_the_family_decides_the_preset_not_the_tropical_fallback(self, db: _FakeDb) -> None:
        """#1440 round 1: without the family every plant is profiled TROPICAL.

        The species stores the family's document ``_key``; ``FAMILY_CARE_MAP`` is
        keyed by the family NAME. Passing the stored key through unresolved is the
        same defect wearing a different hat, so the assertion is on the resolved
        care style of a Cactaceae — and on a preset value the tropical one does not
        share, so a coincidence of enum names cannot satisfy it.
        """
        report = migration.up(db)

        profile = db.collections[col.CARE_PROFILES][0]
        assert profile["care_style"] == CareStyleType.CACTUS.value
        assert profile["care_style"] != CareStyleType.TROPICAL.value
        assert profile["watering_interval_days"] > 7
        assert report.details["created"][0]["botanical_family"] == FAMILY_NAME
        assert report.details["by_care_style"] == {CareStyleType.CACTUS.value: 1}

    def test_the_profile_carries_no_tenant_key(self, db: _FakeDb) -> None:
        """A CareProfile is tenant-anchored through its plant; the model has no field."""
        migration.up(db)

        assert "tenant_key" not in db.collections[col.CARE_PROFILES][0]

    def test_a_plant_without_a_species_gets_the_fallback_and_is_reported(self) -> None:
        db = _FakeDb(_seeded(plants=[_plant(species_key=None)]))

        report = migration.up(db)

        profile = db.collections[col.CARE_PROFILES][0]
        assert profile["care_style"] == CareStyleType.TROPICAL.value
        assert report.changed == 1
        assert report.details["species_missing"] == [
            {"plant_key": PLANT, "tenant_key": TENANT, "species_key": None, "reason": "no_species_key"}
        ]

    def test_a_species_key_that_names_nothing_is_reported_too(self) -> None:
        db = _FakeDb(_seeded(species=[]))

        report = migration.up(db)

        assert report.details["species_missing_total"] == 1
        assert report.details["species_missing"][0]["reason"] == "species_document_missing"

    def test_a_family_key_that_names_no_family_is_tried_verbatim_and_reported(self) -> None:
        """An installation storing the NAME in ``family_key`` is still served."""
        db = _FakeDb(
            _seeded(
                species=[{"_key": SPECIES_KEY, "scientific_name": "Opuntia ficus-indica", "family_key": FAMILY_NAME}],
                families=[],
            )
        )

        report = migration.up(db)

        assert db.collections[col.CARE_PROFILES][0]["care_style"] == CareStyleType.CACTUS.value
        assert report.details["family_unresolved"] == [
            {"plant_key": PLANT, "species_key": SPECIES_KEY, "family_key": FAMILY_NAME}
        ]

    def test_a_profiled_plant_is_byte_identical_afterwards(self) -> None:
        stored = {
            "_key": "profile-1",
            "plant_key": PLANT,
            "care_style": CareStyleType.ORCHID.value,
            "watering_interval_days": 9,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        db = _FakeDb(_seeded(profiles=[stored]))
        before = copy.deepcopy(db.collections)

        report = migration.up(db)

        assert db.collections == before
        assert db.writes == []
        assert report.scanned == 0
        assert report.changed == 0

    def test_a_removed_plant_is_not_touched(self) -> None:
        db = _FakeDb(_seeded(plants=[_plant(removed_on="2025-11-02")]))

        report = migration.up(db)

        assert db.collections[col.CARE_PROFILES] == []
        assert db.writes == []
        assert report.scanned == 0
        assert report.changed == 0

    def test_a_second_run_writes_nothing(self, db: _FakeDb) -> None:
        first = migration.up(db)
        writes_after_first = len(db.writes)

        second = migration.up(db)

        assert first.changed == 1
        assert second.scanned == 0
        assert second.changed == 0
        assert len(db.writes) == writes_after_first

    def test_dry_run_writes_nothing_and_reports_the_same_rows(self, db: _FakeDb) -> None:
        planned = migration.up(db, dry_run=True)

        assert db.writes == []
        assert db.collections[col.CARE_PROFILES] == []
        assert planned.dry_run is True
        assert planned.scanned == 1
        assert planned.changed == 1

        applied = migration.up(db)

        assert planned.details["created"] == [
            {key: value for key, value in applied.details["created"][0].items() if key != "profile_key"}
        ]

    def test_a_taken_edge_rolls_the_profile_back_and_reports_the_plant(self, db: _FakeDb) -> None:
        """The #1486 race, and the state that reaches it without any concurrency.

        A plant can already own a ``has_care_profile`` edge pointing at a profile
        whose ``plant_key`` names somebody else — inside the predicate, with its
        unique ``_from`` slot taken. The run must not abort a whole installation
        over it, and must not leave a second profile behind either.
        """
        db.collection(col.HAS_CARE_PROFILE).refuse_insert = DocumentInsertError(
            _ArangoResponse(1210, "unique constraint violated - in index 42 over '[\"_from\"]'"),
            _ArangoRequest(),
        )

        report = migration.up(db)

        assert db.collections[col.CARE_PROFILES] == []
        assert db.collections[col.HAS_CARE_PROFILE] == []
        # "Rolls back" is now literal. The profile used to be committed and then
        # deleted again, which is the window #1292 round two measured; the refused
        # edge aborts the transaction it was staged in and nothing is ever visible.
        assert [(t.committed, t.aborted) for t in db.transactions] == [(False, True)]
        assert db.writes == []
        assert report.changed == 0
        assert report.details["created_total"] == 0
        assert report.details["already_profiled"] == [
            {"plant_key": PLANT, "tenant_key": TENANT, "reason": "profile_edge_already_present"}
        ]
        assert report.details["by_care_style"] == {}

    @pytest.mark.parametrize("absent", REQUIRED_COLLECTIONS)
    def test_a_missing_collection_stops_the_run_unmet(self, absent: str) -> None:
        collections = _seeded()
        del collections[absent]
        db = _FakeDb(collections)

        report = migration.up(db)

        assert report.precondition_unmet is True
        assert report.changed == 0
        assert db.writes == []
        assert report.details["missing_collections"] == [absent]

    def test_an_empty_installation_is_a_recorded_no_op(self) -> None:
        db = _FakeDb(_seeded(plants=[]))

        report = migration.up(db)

        assert report.precondition_unmet is False
        assert report.scanned == 0
        assert report.changed == 0
        assert report.details["created"] == []

    def test_it_refuses_to_pretend_an_inverse(self, db: _FakeDb) -> None:
        with pytest.raises(IrreversibleMigrationError):
            migration.down(db)


class _ArangoResponse:
    """The two attributes ``DocumentInsertError`` reads off a driver response."""

    def __init__(self, error_code: int, error_message: str) -> None:
        self.error_code = error_code
        self.error_message = error_message
        self.status_code = 409
        self.status_text = "Conflict"
        self.method = "post"
        self.url = "http://localhost:8529"
        self.headers: dict[str, str] = {}
        self.body = None


class _ArangoRequest:
    method = "post"
    endpoint = "/_api/document"
