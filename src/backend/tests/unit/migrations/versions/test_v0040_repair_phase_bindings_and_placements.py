"""v0040 repairs both phase defects with one placement rule (#1146, #1150).

Two defects that end in the same place — a plant sitting in a phase its species
cannot reach — so one migration, and one rule for where the plant lands.

The cases that matter most are not the happy paths:

* **the two halves interact.** A plant must be placed into the sequence its
  species will be bound to *after* the rebind, not the one it is bound to now.
  Planning them separately would place half the plants into a sequence this same
  migration is about to move them off — `test_a_plant_lands_in_the_sequence_the_rebind_creates`
  is the one that catches that.
* **a `manual` edge is never corrected.** No such edge can exist yet (#1099),
  which is exactly why the exclusion is asserted before it can be exercised: the
  first time an override becomes writable, a repair pass without this would revert
  it silently.
* **`entered_at` is backdated.** Setting it to "now" would restart a phase the
  plant is most of the way through and delay every downstream schedule.
* **nothing is guessed.** A plant the placement rule declines is reported and left,
  as v0021 refuses to guess a dangling key.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.versions.v0040_repair_phase_bindings_and_placements import (
    BOUND_BY,
    RepairPhaseBindingsAndPlacementsMigration,
)

_EVERGREEN = "seq_evergreen"
_INDOOR = "seq_indoor"


class _Aql:
    def __init__(self, db: _Db) -> None:
        self._db = db
        self.updates: list[dict[str, Any]] = []

    #: `UPDATE {attribute: @bind_var, ...} IN collection` — the attribute names come
    #: from the *expression*, not from the bind-variable names. A first version of
    #: this double copied bind vars onto the document and special-cased the ones
    #: whose names differed (`@at` -> `bound_at`, `@entered` -> `entered_at`). That
    #: made the double disagree with ArangoDB about what the migration writes,
    #: which is the one thing a database double must not do.
    _ASSIGNMENT = re.compile(r"(\w+)\s*:\s*@(\w+)")

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if query.strip().startswith("UPDATE"):
            assert bind_vars is not None
            self.updates.append({"query": query, **bind_vars})
            collection = query.split(" IN ", 1)[1].strip()
            assignments = {attr: bind_vars[var] for attr, var in self._ASSIGNMENT.findall(query) if var in bind_vars}
            for doc in self._db.collections.get(collection, []):
                if doc["_key"] == assignments.get("_key"):
                    doc.update({k: v for k, v in assignments.items() if k != "_key"})
            return []
        name = query.split(" IN ", 1)[1].split(" ", 1)[0].strip()
        return list(self._db.collections.get(name, []))


class _Db:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self.collections = collections
        self.aql = _Aql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.collections


#: Planting dates are expressed **relative to today**, because the migration takes
#: its own `today` from the clock. A fixed date made the plant's age drift with the
#: calendar: the first version planted it on 2026-06-16, which on the day this was
#: written landed it exactly on the 60-day boundary between `establishment` and
#: `active_growth` — so the backdated `entered_at` equalled today and the assertion
#: failed for a reason that had nothing to do with the code. 30 days keeps it in the
#: middle of the first phase on every day of the year.
_AGE_DAYS = 30


def _days_ago(days: int) -> str:
    return (datetime.now(UTC).date() - timedelta(days=days)).isoformat()


def _db(
    *,
    bound_to: str = _INDOOR,
    bound_by: str | None = "seed",
    current_phase: str = "ind_1",
    planted_on: str | None = None,
    open_phase_name: str = "seedling",
) -> _Db:
    """A perennial polycarpic tree bound to the annual blanket — the Yucca shape."""
    edge: dict[str, Any] = {
        "_key": "e1",
        "_from": f"{col.SPECIES}/sp1",
        "_to": f"{col.PHASE_SEQUENCES}/{bound_to}",
    }
    if bound_by is not None:
        edge["bound_by"] = bound_by
    return _Db(
        {
            col.SPECIES: [
                {"_key": "sp1", "scientific_name": "Yucca gigantea", "growth_habit": "tree"},
            ],
            col.LIFECYCLE_CONFIGS: [
                {
                    "species_key": "sp1",
                    "cycle_type": "perennial",
                    "cultivation_cycle_type": None,
                    "grown_as_annual": False,
                    "flowering_strategy": "polycarpic",
                    "photoperiod_type": "day_neutral",
                }
            ],
            col.PHASE_SEQUENCES: [
                {"_key": _EVERGREEN, "name": "evergreen_foliage_perennial"},
                {"_key": _INDOOR, "name": "indoor_default"},
            ],
            col.PHASE_DEFINITIONS: [
                {"_key": "d_est", "name": "establishment", "typical_duration_days": 60},
                {"_key": "d_act", "name": "active_growth", "typical_duration_days": 120},
                {"_key": "d_seed", "name": "seedling", "typical_duration_days": 20},
            ],
            col.PHASE_SEQUENCE_ENTRIES: [
                {
                    "_key": "ev_1",
                    "phase_sequence_key": _EVERGREEN,
                    "phase_definition_key": "d_est",
                    "sequence_order": 0,
                },
                {
                    "_key": "ev_2",
                    "phase_sequence_key": _EVERGREEN,
                    "phase_definition_key": "d_act",
                    "sequence_order": 1,
                },
                {"_key": "ind_1", "phase_sequence_key": _INDOOR, "phase_definition_key": "d_seed", "sequence_order": 0},
            ],
            col.HAS_PHASE_SEQUENCE: [edge],
            col.PLANT_INSTANCES: [
                {
                    "_key": "p1",
                    "species_key": "sp1",
                    "current_phase_key": current_phase,
                    "planted_on": _days_ago(_AGE_DAYS) if planted_on is None else planted_on,
                }
            ],
            col.PHASE_HISTORIES: [
                {
                    "_key": "h1",
                    "plant_instance_key": "p1",
                    "phase_key": current_phase,
                    "phase_name": open_phase_name,
                    "exited_at": None,
                    "entered_at": f"{_days_ago(_AGE_DAYS)}T00:00:00+00:00",
                }
            ],
        }
    )


@pytest.fixture
def migration() -> RepairPhaseBindingsAndPlacementsMigration:
    return RepairPhaseBindingsAndPlacementsMigration()


def _edge(db: _Db) -> dict[str, Any]:
    return db.collections[col.HAS_PHASE_SEQUENCE][0]


def _plant(db: _Db) -> dict[str, Any]:
    return db.collections[col.PLANT_INSTANCES][0]


def _history(db: _Db) -> dict[str, Any]:
    return db.collections[col.PHASE_HISTORIES][0]


# ── half 1: the binding ──────────────────────────────────────────────────────


def test_a_diverged_binding_is_repointed(migration) -> None:
    """The Yucca case: perennial polycarpic tree on the annual blanket."""
    db = _db()

    report = migration.up(db)

    assert report.details["rebound"] == 1
    assert _edge(db)["_to"] == f"{col.PHASE_SEQUENCES}/{_EVERGREEN}"


def test_the_repointed_edge_records_who_did_it(migration) -> None:
    """Provenance, so the next reconciler can tell this from a human override."""
    db = _db()

    migration.up(db)

    assert _edge(db)["bound_by"] == BOUND_BY
    assert _edge(db)["bound_at"]


def test_a_manual_binding_is_never_corrected(migration) -> None:
    """An override is a decision, not drift — asserted before it can be exercised.

    #1099 measured both candidate write paths silently dropping the field, so no
    `manual` edge exists yet. That is the reason to write this now: the first time
    an override becomes writable, a repair pass without this exclusion reverts it
    and nothing reports that it did.
    """
    db = _db(bound_by="manual")

    report = migration.up(db)

    assert report.details["rebound"] == 0
    assert _edge(db)["_to"] == f"{col.PHASE_SEQUENCES}/{_INDOOR}"


def test_a_binding_that_already_agrees_is_left_alone(migration) -> None:
    """The half that keeps this from rewriting every edge on every run."""
    db = _db(bound_to=_EVERGREEN, current_phase="ev_1", open_phase_name="establishment")

    report = migration.up(db)

    assert report.changed == 0


# ── half 2: the plant, and its interaction with half 1 ───────────────────────


def test_a_plant_lands_in_the_sequence_the_rebind_creates(migration) -> None:
    """The interaction, and the reason both halves are planned in one pass.

    The plant is placed into `evergreen_foliage_perennial` — the sequence its
    species will be bound to *after* this migration — not into `indoor_default`,
    which it is bound to at the moment planning starts. Planning the halves
    separately would place the plant into a sequence this same run is about to
    move it off.
    """
    db = _db()

    migration.up(db)

    assert _plant(db)["current_phase_key"] in {"ev_1", "ev_2"}


def test_entered_at_is_backdated_not_set_to_now(migration) -> None:
    """The whole point of repairing in a migration rather than through the API.

    `transition_plant_phase` sets `entered_at = now`, which would restart a
    60-day `establishment` for a plant potted long before — delaying every
    downstream schedule by the plant's whole age.
    """
    db = _db()

    migration.up(db)

    entered = datetime.fromisoformat(_history(db)["entered_at"])
    assert entered.date() < datetime.now(UTC).date()


def test_the_open_history_record_follows_the_plant(migration) -> None:
    """Key *and* name. Leaving the name behind would report the old phase for a
    plant that is now in a different one — the exact symptom #1150 describes."""
    db = _db()

    migration.up(db)

    assert _history(db)["phase_key"] == _plant(db)["current_phase_key"]
    assert _history(db)["phase_name"] in {"establishment", "active_growth"}


def test_a_reachable_plant_is_not_moved(migration) -> None:
    db = _db(bound_to=_EVERGREEN, current_phase="ev_1", open_phase_name="establishment")

    migration.up(db)

    assert _plant(db)["current_phase_key"] == "ev_1"


def test_an_unplaceable_plant_is_reported_and_left(migration) -> None:
    """Nothing is guessed — v0021's rule, carried over.

    No planting date and a phase name the incoming sequence does not have leaves
    the rule no information to place on.
    """
    db = _db(planted_on="", open_phase_name="flushing")

    report = migration.up(db)

    assert report.details["placed"] == 0
    assert report.details["unplaceable"] == ["p1"]
    assert _plant(db)["current_phase_key"] == "ind_1"


def test_the_report_says_how_each_plant_was_placed(migration) -> None:
    """A dry-run reviewer needs to see which plants were *computed* into place
    rather than recognised — an estimate deserves more scrutiny than an anchor."""
    db = _db()

    report = migration.up(db, dry_run=True)

    assert report.details["by_name_anchor"] + report.details["by_elapsed_days"] == report.details["placed"]


# ── migration hygiene ────────────────────────────────────────────────────────


def test_a_dry_run_writes_nothing(migration) -> None:
    db = _db()

    report = migration.up(db, dry_run=True)

    assert report.changed == 0
    assert _edge(db)["_to"] == f"{col.PHASE_SEQUENCES}/{_INDOOR}"
    assert _plant(db)["current_phase_key"] == "ind_1"


def test_a_second_run_is_a_no_op(migration) -> None:
    """M-3. After the first run the binding agrees and the plant's phase name is
    in its own sequence, so the second run anchors on the name and changes nothing."""
    db = _db()
    migration.up(db)

    second = migration.up(db)

    assert second.changed == 0


def test_an_empty_database_is_a_clean_no_op(migration) -> None:
    assert migration.up(_Db({})).changed == 0


def test_a_species_whose_target_sequence_is_unseeded_is_skipped(migration) -> None:
    """A partially seeded install must not have its bindings rewritten to nothing."""
    db = _db()
    db.collections[col.PHASE_SEQUENCES] = [{"_key": _INDOOR, "name": "indoor_default"}]

    report = migration.up(db)

    assert report.details["rebound"] == 0
