"""#2002 — v0071 removes the profiles a deleted phase left behind, and nothing else.

A profile goes only when no phase edge reaches it **and** its ``phase_key`` names no
growth phase. One reached by an edge, or whose phase still exists, stays.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.versions.v0071_remove_orphaned_phase_profiles import migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration is AQL over a real server"),
]

_DB_NAME = run_database_name("v0071_orphaned_phase_profiles")
_PAIRS = ((col.REQUIREMENT_PROFILES, col.REQUIRES_PROFILE), (col.NUTRIENT_PROFILES, col.USES_NUTRIENTS))


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    yield database
    system.delete_database(_DB_NAME)


def _volume(db) -> dict[str, Any]:
    """Per profile collection: one orphan of each orphan shape and one keeper of each keeper shape."""
    phase = db.collection(col.GROWTH_PHASES).insert({"name": "vegetative"})["_key"]
    edgeless_phase = db.collection(col.GROWTH_PHASES).insert({"name": "flowering"})["_key"]
    facts: dict[str, Any] = {"orphans": [], "kept": []}
    for profiles, edges in _PAIRS:
        rows = db.collection(profiles)
        # Orphans: the phase was deleted, its edge with it (the delete_phase leak) — or no phase at all.
        facts["orphans"].append((profiles, rows.insert({"phase_key": "deleted-phase"})["_key"]))
        facts["orphans"].append((profiles, rows.insert({"phase_key": ""})["_key"]))
        # Kept: reached by its phase's edge.
        linked = rows.insert({"phase_key": phase})["_key"]
        db.collection(edges).insert({"_from": f"{col.GROWTH_PHASES}/{phase}", "_to": f"{profiles}/{linked}"})
        facts["kept"].append((profiles, linked))
        # Kept: an edge points at it although its phase_key is stale.
        stale = rows.insert({"phase_key": "deleted-phase"})["_key"]
        db.collection(edges).insert({"_from": f"{col.GROWTH_PHASES}/{phase}", "_to": f"{profiles}/{stale}"})
        facts["kept"].append((profiles, stale))
        # Kept: no edge, but the phase it names exists.
        facts["kept"].append((profiles, rows.insert({"phase_key": edgeless_phase})["_key"]))
    return facts


def _present(db, rows: list[tuple[str, str]]) -> list[bool]:
    return [db.collection(collection).has(key) for collection, key in rows]


def test_only_profiles_no_edge_reaches_and_no_phase_owns_are_removed(db) -> None:
    facts = _volume(db)

    report = migration.up(db)

    assert _present(db, facts["orphans"]) == [False] * len(facts["orphans"])
    assert _present(db, facts["kept"]) == [True] * len(facts["kept"])
    assert report.changed == len(facts["orphans"])


def test_a_dry_run_counts_and_writes_nothing(db) -> None:
    facts = _volume(db)

    report = migration.up(db, dry_run=True)

    assert report.changed == 0
    assert report.details["to_remove"] == len(facts["orphans"])
    assert _present(db, facts["orphans"]) == [True] * len(facts["orphans"])


def test_a_second_run_changes_nothing(db) -> None:
    _volume(db)
    migration.up(db)

    assert migration.up(db).changed == 0
