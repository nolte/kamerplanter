"""#2001 — v0070 resets the v0004 stamp on seed harvest indicators, re-dedupes, and guards the identity.

The legacy volume is built the way it came to be: one boot of the pre-#1956 loader
before ``v0004`` (the original, later stamped with the default tenant), more boots
after it (unstamped copies), and then ``v0068`` — which skipped the stamped row,
because ``tenant_key`` is an attribute the loader never writes. What is left is the
stamped original beside one copy of every identity, and no unique index can be
created over that.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.collections import (
    EDGE_PAIR_FIELDS,
    HARVEST_INDICATOR_IDENTITY_FIELDS,
    UNIQUE_PAIR_EDGE_COLLECTIONS,
    has_unique_index,
)
from app.migrations.versions.v0068_dedupe_seed_rows_multiplied_per_boot import migration as v0068
from app.migrations.versions.v0070_reset_harvest_indicator_stamps_and_guard_seed_identity import migration
from app.migrations.yaml_loader import load_yaml
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database, drop_seed_identity_indexes

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration is AQL and index DDL over a real server"),
]

_DB_NAME = run_database_name("v0070_harvest_indicator_stamps")
_STAMP = "t-default"
#: Seed entries the volume is built from — enough species and units to make groups real.
_ENTRIES = 12


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    drop_seed_identity_indexes(database)
    yield database
    system.delete_database(_DB_NAME)


def _entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = load_yaml("harvest_indicators.yaml")["harvest_indicators"][:_ENTRIES]
    return entries


def _insert(db, entry: dict[str, Any], species_key: str, stamp_time: str, **extra: Any) -> str:
    doc = {
        "indicator_type": entry["indicator_type"],
        "measurement_unit": entry["measurement_unit"],
        "measurement_method": entry["measurement_method"],
        "observation_frequency": entry["observation_frequency"],
        "reliability_score": entry["reliability_score"],
        "species_key": species_key,
        "description": None,
        "created_at": stamp_time,
        "updated_at": stamp_time,
        **extra,
    }
    key: str = db.collection(col.HARVEST_INDICATORS).insert(doc)["_key"]
    db.collection(col.HAS_HARVEST_INDICATOR).insert(
        {"_from": f"{col.SPECIES}/{species_key}", "_to": f"{col.HARVEST_INDICATORS}/{key}"}
    )
    return key


def _legacy_volume(db) -> dict[str, Any]:
    species: dict[str, str] = {}
    for entry in _entries():
        name = entry["species_name"]
        if name not in species:
            species[name] = db.collection(col.SPECIES).insert(
                {"scientific_name": name, "scientific_name_normalized": name.lower(), "tenant_key": ""}
            )["_key"]
    originals: list[str] = []
    for entry in _entries():
        sp = species[entry["species_name"]]
        originals.append(_insert(db, entry, sp, "2025-01-01T00:00:00+00:00", tenant_key=_STAMP))
        for boot in (2, 3):
            _insert(db, entry, sp, f"2026-0{boot}-01T00:00:00+00:00")
    # An indicator an operator created (not named by the seed) carrying the same stamp: left alone.
    first_species = next(iter(species.values()))
    admin_made = db.collection(col.HARVEST_INDICATORS).insert(
        {
            "indicator_type": "color",
            "measurement_unit": "operator_unit",
            "measurement_method": "visual",
            "observation_frequency": "daily",
            "reliability_score": 0.5,
            "species_key": first_species,
            "tenant_key": _STAMP,
        }
    )["_key"]
    # Duplicate IPM edges the pre-#1956 loader wrote per boot.
    for name in UNIQUE_PAIR_EDGE_COLLECTIONS:
        for _ in range(3):
            db.collection(name).insert({"_from": f"{col.TREATMENTS}/t1", "_to": f"{col.PESTS}/p1"})
    v0068.up(db)  # what every deployed volume already ran
    return {"species": species, "originals": originals, "admin_made": admin_made}


def _identities(db) -> Counter[tuple[Any, ...]]:
    return Counter(
        (d.get("species_key"), d["indicator_type"], d["measurement_unit"])
        for d in db.collection(col.HARVEST_INDICATORS).all()
    )


def test_after_v0068_the_stamped_original_still_has_a_twin(db) -> None:
    """The defect the migration exists for, measured on the state v0068 left."""
    _legacy_volume(db)

    assert all(n == 2 for identity, n in _identities(db).items() if identity[2] != "operator_unit")


def test_the_stamp_is_removed_and_each_seed_identity_is_one_row(db) -> None:
    facts = _legacy_volume(db)

    report = migration.up(db)

    rows = {d["_key"]: d for d in db.collection(col.HARVEST_INDICATORS).all()}
    assert [n for n in _identities(db).values() if n > 1] == []
    for key in facts["originals"]:
        assert key in rows, "the oldest row of a group is the one kept"
        assert "tenant_key" not in rows[key]
    assert rows[facts["admin_made"]]["tenant_key"] == _STAMP, "a row the seed does not name is left alone"
    assert report.details["stamps_reset"] == len(facts["originals"])
    edges = db.collection(col.HAS_HARVEST_INDICATOR).all()
    assert {e["_to"].split("/")[1] for e in edges} == set(rows) - {facts["admin_made"]}, "each kept row keeps its edge"


def test_the_identity_indexes_exist_afterwards(db) -> None:
    _legacy_volume(db)

    migration.up(db)

    assert has_unique_index(db.collection(col.HARVEST_INDICATORS), HARVEST_INDICATOR_IDENTITY_FIELDS, sparse=True)
    for name in UNIQUE_PAIR_EDGE_COLLECTIONS:
        assert has_unique_index(db.collection(name), EDGE_PAIR_FIELDS), name
        assert db.collection(name).count() == 1


def test_a_duplicate_an_observation_refers_to_blocks_the_index_without_failing(db) -> None:
    _legacy_volume(db)
    entry = _entries()[0]
    species_key = db.collection(col.SPECIES).find({"scientific_name": entry["species_name"]}).next()["_key"]
    referenced = _insert(db, entry, species_key, "2026-05-01T00:00:00+00:00")
    db.collection(col.HARVEST_OBSERVATIONS).insert({"plant_key": "p1", "indicator_key": referenced})

    report = migration.up(db)

    assert db.collection(col.HARVEST_INDICATORS).has(referenced)
    assert report.details["indexes_blocked"] == [col.HARVEST_INDICATORS]
    assert not has_unique_index(db.collection(col.HARVEST_INDICATORS), HARVEST_INDICATOR_IDENTITY_FIELDS, sparse=True)


def test_a_dry_run_writes_nothing_and_a_second_run_changes_nothing(db) -> None:
    _legacy_volume(db)
    before = sorted(db.collection(col.HARVEST_INDICATORS).all(), key=lambda d: d["_key"])

    dry = migration.up(db, dry_run=True)
    assert dry.changed == 0
    assert dry.details["stamps_reset"] == len(_entries())
    assert sorted(db.collection(col.HARVEST_INDICATORS).all(), key=lambda d: d["_key"]) == before

    migration.up(db)
    again = migration.up(db)
    assert again.changed == 0
