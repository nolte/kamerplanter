"""#1956 — v0068 removes the copies the seed loaders appended per boot, and nothing else.

The legacy volume is built the way it came to be: the rows one boot of the old loader
wrote (``harvest_indicators`` + a ``has_harvest_indicator`` edge each; the IPM edges),
repeated three times — by inserting the old loader's output, since the loader is fixed.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.versions.v0068_dedupe_seed_rows_multiplied_per_boot import migration
from app.migrations.yaml_loader import load_yaml
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration is AQL over a real server"),
]

_DB_NAME = run_database_name("v0068_dedupe_seed_rows")
_BOOTS = 3


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    yield database
    system.delete_database(_DB_NAME)


def _seed_entries() -> list[dict[str, Any]]:
    return load_yaml("harvest_indicators.yaml")["harvest_indicators"]


def _doc(entry: dict[str, Any], species_key: str | None, stamp: str) -> dict[str, Any]:
    return {
        "indicator_type": entry["indicator_type"],
        "measurement_unit": entry["measurement_unit"],
        "measurement_method": entry["measurement_method"],
        "observation_frequency": entry["observation_frequency"],
        "reliability_score": entry["reliability_score"],
        "species_key": species_key,
        "description": None,
        "created_at": stamp,
        "updated_at": stamp,
    }


def _boot(db, entry: dict[str, Any], species_key: str | None, stamp: str) -> str:
    """What one boot of the old loader wrote for one entry; returns the row's key."""
    key = db.collection(col.HARVEST_INDICATORS).insert(_doc(entry, species_key, stamp))["_key"]
    if species_key:
        db.collection(col.HAS_HARVEST_INDICATOR).insert(
            {"_from": f"{col.SPECIES}/{species_key}", "_to": f"{col.HARVEST_INDICATORS}/{key}", "created_at": stamp}
        )
    return key


def _rows(db, collection: str) -> list[dict[str, Any]]:
    return sorted(db.collection(collection).all(), key=lambda d: int(d["_key"]) if d["_key"].isdigit() else 0)


def _legacy_volume(db) -> dict[str, Any]:
    entries = _seed_entries()
    resolved = entries[0]
    anonymous = entries[1]
    species = db.collection(col.SPECIES).insert({"scientific_name": resolved["species_name"]})["_key"]
    facts: dict[str, Any] = {"species": species, "resolved": resolved, "anonymous": anonymous}

    resolved_keys = [_boot(db, resolved, species, f"2026-0{b + 1}-01T00:00:00+00:00") for b in range(_BOOTS)]
    anon_keys = [_boot(db, anonymous, None, f"2026-0{b + 1}-01T00:00:00+00:00") for b in range(_BOOTS)]
    facts.update(resolved_keys=resolved_keys, anon_keys=anon_keys)

    # A second entry of the same species, referenced by an observation from its youngest copy.
    other = next(e for e in entries if e["species_name"] == resolved["species_name"] and e is not resolved)
    other_keys = [_boot(db, other, species, f"2026-0{b + 1}-02T00:00:00+00:00") for b in range(_BOOTS)]
    obs = db.collection(col.HARVEST_OBSERVATIONS).insert({"plant_key": "p1", "indicator_key": other_keys[-1]})["_key"]
    facts.update(other_keys=other_keys, observation=obs)

    # Rows that are not exact copies of a seed row — all must stay byte-identical.
    third = entries[2]
    facts["tuned"] = db.collection(col.HARVEST_INDICATORS).insert(
        {**_doc(third, species, "2026-01-03T00:00:00+00:00"), "reliability_score": 0.01}
    )["_key"]
    facts["tuned_twin"] = db.collection(col.HARVEST_INDICATORS).insert(
        {**_doc(third, species, "2026-02-03T00:00:00+00:00"), "reliability_score": 0.01}
    )["_key"]
    facts["described"] = [
        db.collection(col.HARVEST_INDICATORS).insert(
            {**_doc(resolved, species, f"2026-0{i}-04T00:00:00+00:00"), "description": "admin note"}
        )["_key"]
        for i in (1, 2)
    ]
    facts["admin_made"] = [
        db.collection(col.HARVEST_INDICATORS).insert(
            {
                "indicator_type": "color",
                "measurement_unit": "custom_unit",
                "measurement_method": "visual",
                "observation_frequency": "daily",
                "reliability_score": 0.5,
                "species_key": species,
            }
        )["_key"]
        for _ in range(2)
    ]

    # IPM edges: three plain copies, and a pair that carries data of its own.
    t, p = f"{col.TREATMENTS}/t1", f"{col.PESTS}/p1"
    facts["plain_edges"] = [
        db.collection(col.TARGETS_PEST).insert(
            {"_from": t, "_to": p, "created_at": f"2026-0{b + 1}-01T00:00:00+00:00"}
        )["_key"]
        for b in range(_BOOTS)
    ]
    facts["data_edges"] = [
        db.collection(col.TARGETS_DISEASE).insert(
            {"_from": t, "_to": f"{col.DISEASES}/d1", "created_at": "2026-01-01", "efficacy": e}
        )["_key"]
        for e in (0.2, 0.9)
    ]
    facts["contra"] = [
        db.collection(col.CONTRAINDICATED_WITH).insert(
            {"_from": t, "_to": f"{col.TREATMENTS}/t2", "created_at": f"2026-0{b + 1}-01"}
        )["_key"]
        for b in range(2)
    ]
    return facts


def _untouched(db, facts: dict[str, Any]) -> list[tuple[str, list[dict]]]:
    spec = (
        (col.HARVEST_INDICATORS, [facts["tuned"], facts["tuned_twin"], *facts["described"], *facts["admin_made"]]),
        (col.HARVEST_OBSERVATIONS, [facts["observation"]]),
        (col.TARGETS_DISEASE, facts["data_edges"]),
    )
    return [(c, [db.collection(c).get(k) for k in keys]) for c, keys in spec]


def test_exact_copies_are_removed_and_one_per_group_is_kept(db) -> None:
    facts = _legacy_volume(db)

    report = migration.up(db)

    survivors = {d["_key"] for d in db.collection(col.HARVEST_INDICATORS).all()}
    assert facts["resolved_keys"][0] in survivors
    assert survivors.isdisjoint(facts["resolved_keys"][1:])
    assert facts["anon_keys"][0] in survivors
    assert survivors.isdisjoint(facts["anon_keys"][1:])
    # the removed copies took their edge along; the kept rows keep theirs
    edge_targets = {e["_to"] for e in db.collection(col.HAS_HARVEST_INDICATOR).all()}
    assert f"{col.HARVEST_INDICATORS}/{facts['resolved_keys'][0]}" in edge_targets
    assert not {f"{col.HARVEST_INDICATORS}/{k}" for k in facts["resolved_keys"][1:]} & edge_targets
    # the IPM edge groups keep their oldest
    assert [e["_key"] for e in db.collection(col.TARGETS_PEST).all()] == [facts["plain_edges"][0]]
    assert [e["_key"] for e in db.collection(col.CONTRAINDICATED_WITH).all()] == [facts["contra"][0]]
    assert (
        report.details[col.HARVEST_INDICATORS] == 2 + 2 + 1
    )  # resolved + anonymous + the one unreferenced copy of the referenced group
    assert report.details[col.TARGETS_PEST] == 2


def test_a_referenced_copy_is_kept_so_no_observation_dangles(db) -> None:
    facts = _legacy_volume(db)

    report = migration.up(db)

    survivors = {d["_key"] for d in db.collection(col.HARVEST_INDICATORS).all()}
    assert facts["other_keys"][-1] in survivors  # the youngest copy, referenced
    assert facts["other_keys"][0] in survivors  # the oldest, kept as the group's one
    assert facts["other_keys"][1] not in survivors
    assert report.details["duplicate_indicators_kept_because_referenced"] == 1


def test_rows_that_differ_or_carry_data_stay_byte_identical(db) -> None:
    facts = _legacy_volume(db)
    before = _untouched(db, facts)

    migration.up(db)

    assert _untouched(db, facts) == before


def test_dry_run_writes_nothing_and_a_second_run_is_a_no_op(db) -> None:
    _legacy_volume(db)
    snapshot = {c: _rows(db, c) for c in (col.HARVEST_INDICATORS, col.HAS_HARVEST_INDICATOR, col.TARGETS_PEST)}

    dry = migration.up(db, dry_run=True)
    assert dry.changed == 0
    assert dry.details["to_remove"] > 0
    assert {c: _rows(db, c) for c in snapshot} == snapshot

    first = migration.up(db)
    second = migration.up(db)
    assert first.changed == dry.details["to_remove"]
    assert second.changed == 0


def test_a_volume_without_duplicates_is_untouched(db) -> None:
    entry = _seed_entries()[0]
    species = db.collection(col.SPECIES).insert({"scientific_name": entry["species_name"]})["_key"]
    _boot(db, entry, species, "2026-01-01T00:00:00+00:00")
    before = _rows(db, col.HARVEST_INDICATORS)

    report = migration.up(db)

    assert report.changed == 0
    assert _rows(db, col.HARVEST_INDICATORS) == before
