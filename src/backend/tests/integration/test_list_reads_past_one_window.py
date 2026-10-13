"""#2025 — list reads that are not ``get_all`` see the whole collection, on a real ArangoDB.

The unit tests drive the services against doubles that page like the repositories.
What only the server can answer is whether the repository side holds: the AQL
aggregates count every row (and treat a missing ``previous_state`` like Python did),
the ``find_by_field`` reads carry no ``LIMIT``, the phase-sequence listing is a total
order a pager can walk, and — on the real seed registry — a seed dedup read past its
old window does not create a second copy of a catalogue row.

Run with: pytest tests/integration/test_list_reads_past_one_window.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

from collections import Counter

import pytest
import structlog.testing

from app.data_access.arango import collections as col
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#2025 measures the real repository reads past their old windows"),
]

_DB_NAME = run_database_name("list_reads_past_one_window")
_TENANT = "tenant-a"


@pytest.fixture(scope="module")
def db():
    monkeypatch = pytest.MonkeyPatch()
    system, database = create_database(_DB_NAME)
    bind_database(monkeypatch, database)
    try:
        yield database
    finally:
        monkeypatch.undo()
        system.delete_database(_DB_NAME)


def test_actuator_event_counts_cover_the_whole_history(db) -> None:
    """600 events (old window: 500); 200 without a previous state, 200 failed."""
    from app.data_access.arango.actuator_repository import ArangoActuatorRepository

    rows = []
    for i in range(600):
        row = {"tenant_key": _TENANT, "actuator_key": "act-1", "command": "turn_on", "new_state": "on"}
        row["success"] = i % 3 != 0
        if i % 3 != 1:
            row["previous_state"] = "on" if i % 2 else "off"  # 'on'->'on' is no switch
        rows.append(row)
    rows.append({**rows[0], "tenant_key": "tenant-b"})  # another tenant's event is not counted
    db.collection(col.CONTROL_EVENTS).insert_many(rows)
    expected_cycles = sum(1 for r in rows[:600] if r.get("previous_state") != r["new_state"])
    expected_failures = sum(1 for r in rows[:600] if not r["success"])

    counts = ArangoActuatorRepository(db).count_events("act-1", tenant_key=_TENANT)

    assert counts == {"total": 600, "switch_cycles": expected_cycles, "failures": expected_failures}
    assert ArangoActuatorRepository(db).count_events("act-none", tenant_key=_TENANT) == {
        "total": 0,
        "switch_cycles": 0,
        "failures": 0,
    }


def test_fish_feeding_sum_covers_every_feeding(db) -> None:
    from app.data_access.arango.aquaponik_repository import ArangoAquaponikRepository

    rows = [{"tenant_key": _TENANT, "system_key": "sys-1", "amount_g": 2.5, "water_temp_c": 25} for _ in range(600)]
    rows.append({**rows[0], "tenant_key": "tenant-b"})
    db.collection(col.FISH_FEEDING_EVENTS).insert_many(rows)

    repo = ArangoAquaponikRepository(db)

    assert repo.sum_feedings("sys-1", tenant_key=_TENANT) == (600, 1500.0)
    assert repo.sum_feedings("sys-none", tenant_key=_TENANT) == (0, 0.0)


def test_propagation_batch_events_and_phenotypes_are_not_cut_at_500(db) -> None:
    from app.data_access.repositories.propagation_repository import PropagationRepository

    db.collection(col.PROPAGATION_EVENTS).insert_many(
        [
            {
                "tenant_key": _TENANT,
                "method": "cutting",
                "batch_key": "b-1",
                "created_at": f"2026-01-01T00:{i // 60:02d}:{i % 60:02d}Z",
            }
            for i in range(600)
        ]
        + [{"tenant_key": "tenant-b", "method": "cutting", "batch_key": "b-1"}]
    )
    db.collection(col.PHENOTYPE_NOTES).insert_many(
        [{"tenant_key": _TENANT, "plant_key": "pl-1", "note": f"n{i}"} for i in range(600)]
        + [{"tenant_key": "tenant-b", "plant_key": "pl-1", "note": "foreign"}]
    )
    repo = PropagationRepository(db)

    events = repo.list_events_for_batch("b-1", _TENANT)
    notes = repo.list_phenotypes_for_plant("pl-1", _TENANT)

    assert len(events) == 600 and {e.tenant_key for e in events} == {_TENANT}
    assert [e.created_at for e in events] == sorted(e.created_at for e in events), "oldest first"
    assert len(notes) == 600 and {n.tenant_key for n in notes} == {_TENANT}


def test_post_harvest_batches_of_a_harvest_batch_are_not_cut_at_the_default_50(db) -> None:
    from app.data_access.arango.post_harvest_repository import ArangoPostHarvestRepository

    db.collection(col.POST_HARVEST_BATCHES).insert_many(
        [{"tenant_key": _TENANT, "harvest_batch_key": "hb-1"} for _ in range(60)]
        + [{"tenant_key": "tenant-b", "harvest_batch_key": "hb-1"}]
    )

    batches = ArangoPostHarvestRepository(db).list_for_harvest_batch("hb-1", _TENANT)

    assert len(batches) == 60 and {b.tenant_key for b in batches} == {_TENANT}


def test_phase_sequences_page_as_a_total_order_with_duplicate_names(db) -> None:
    """Names are not unique; a pager over ``SORT doc.name`` alone could drop a tie."""
    from app.data_access.arango.base_repository import read_all_pages
    from app.data_access.arango.phase_sequence_repository import ArangoPhaseSequenceRepository

    db.collection(col.PHASE_SEQUENCES).insert_many([{"_key": f"dup{i:02d}", "name": "same_name"} for i in range(7)])

    rows = read_all_pages(ArangoPhaseSequenceRepository(db).get_all_sequences, page_size=2)

    assert sorted(r.key for r in rows if r.name == "same_name") == [f"dup{i:02d}" for i in range(7)]


def test_seed_dedup_reads_see_rows_past_their_old_window(db) -> None:
    """A re-boot with more pests/diseases/treatments/sequences than the old windows is clean.

    The fillers sort before every seeded row (``_key`` ``0…`` for the ``_key``-ordered IPM
    reads, name ``aaa…`` for the name-ordered sequence read), so the seeded rows sit past
    the old windows of 200/500, where the old loaders did not look. Each filler is a
    valid model row (the repositories validate what they read). Measured on the old
    code: the phase sequences were created a second time, and the pest create hit the
    ``scientific_name`` unique index, so ``core_data``, ``adventskalender`` and
    ``plant_info`` each failed (``seed_failed``) and skipped everything after their IPM
    block. Both halves are asserted.
    """
    from app.migrations.seeds.registry import run_seeds

    run_seeds(db)
    seeded_names = {
        "pests": {d["scientific_name"] for d in db.collection(col.PESTS).all()},
        "diseases": {d["scientific_name"] for d in db.collection(col.DISEASES).all()},
        "treatments": {d["name"] for d in db.collection(col.TREATMENTS).all()},
        "phase_sequences": {d["name"] for d in db.collection(col.PHASE_SEQUENCES).all()} - {"same_name"},
    }
    db.collection(col.PESTS).insert_many(
        [
            {"_key": f"0filler{i:04d}", "scientific_name": f"Filler pest {i}", "common_name": f"fp{i}"}
            for i in range(600)
        ]
    )
    db.collection(col.DISEASES).insert_many(
        [
            {
                "_key": f"0filler{i:04d}",
                "scientific_name": f"Filler disease {i}",
                "common_name": f"fd{i}",
                "pathogen_type": "fungal",
            }
            for i in range(600)
        ]
    )
    db.collection(col.TREATMENTS).insert_many(
        [{"_key": f"0filler{i:04d}", "name": f"Filler treatment {i}", "treatment_type": "cultural"} for i in range(600)]
    )
    db.collection(col.PHASE_SEQUENCES).insert_many(
        [{"_key": f"0filler{i:04d}", "name": f"aaa_filler_{i:04d}"} for i in range(600)]
    )

    with structlog.testing.capture_logs() as logs:
        run_seeds(db)

    assert [e["seed"] for e in logs if e["event"] in ("seed_failed", "seed_failed_fatal")] == []
    copies = {
        "pests": Counter(d["scientific_name"] for d in db.collection(col.PESTS).all()),
        "diseases": Counter(d["scientific_name"] for d in db.collection(col.DISEASES).all()),
        "treatments": Counter(d["name"] for d in db.collection(col.TREATMENTS).all()),
        "phase_sequences": Counter(d["name"] for d in db.collection(col.PHASE_SEQUENCES).all()),
    }
    duplicated = {name: sorted(n for n in seeded_names[name] if copies[name][n] > 1) for name in seeded_names}
    assert duplicated == {name: [] for name in seeded_names}
    assert all(seeded_names.values()), "the first boot seeded every catalogue (non-vacuous)"


def test_a_first_boot_beside_many_other_sequences_binds_every_species() -> None:
    """The sequence name maps of the linker and the outdoor seed read every sequence.

    A database that already holds 600 sequences sorting before the seeded ones (a
    tenant's own, or an earlier duplicate run) put the seeded sequences past the old
    windows of 500 (linker, binder) and 200 (outdoor lifecycles): those reads found no
    sequence to bind to. One ``has_phase_sequence`` edge per species is the outcome a
    clean boot measures (207 of 207).
    """
    from app.migrations.seeds.registry import run_seeds

    name = run_database_name("list_reads_sequences_first_boot")
    monkeypatch = pytest.MonkeyPatch()
    system, database = create_database(name)
    bind_database(monkeypatch, database)
    try:
        database.collection(col.PHASE_SEQUENCES).insert_many(
            [{"_key": f"0filler{i:04d}", "name": f"aaa_filler_{i:04d}"} for i in range(600)]
        )

        run_seeds(database)

        species = database.collection(col.SPECIES).count()
        bound = int(
            next(
                database.aql.execute(
                    "RETURN LENGTH(FOR s IN species FILTER LENGTH(FOR e IN has_phase_sequence "
                    "FILTER e._from == s._id LIMIT 1 RETURN 1) > 0 RETURN 1)"
                )
            )
        )
        assert species > 0
        assert bound == species
    finally:
        monkeypatch.undo()
        system.delete_database(name)
