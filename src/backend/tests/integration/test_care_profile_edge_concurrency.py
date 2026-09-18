"""Integration test for #1292 — a lost care-profile race is not a 500.

``CareReminderService.get_or_create_profile(..., may_create=True)`` reads the
plant's profile and, finding none, writes a ``CareProfile`` plus a
``has_care_profile`` edge. The edge collection carries a **unique** persistent
index over ``_from`` (``collections.py``) — the storage-level statement of "one
care profile per plant" — so when two requests for the same plant overlap, the
loser is rejected.

The two defects below were both the *pair not being atomic*: the document was
committed and readable before its edge existed. Since round two they are a single
stream transaction (``ArangoCareReminderRepository.create_linked_profile``), which
is what the last test in this file measures. The history is kept because it is
what each test is for, not because it still describes the code.

Measured, in the ``e2e-nightly`` of 2026-09-14 (run 34814941664, profile
``mobile``), on ``GET /api/v1/care-reminders/plants/522789/profile``::

    arango.exceptions.DocumentInsertError: [HTTP 409][ERR 1200] write-write
    conflict - in index idx_1876288907249713152 of type persistent over '_from';
    document key: 526429; indexed values: ["plant_instances/522789"]

``1200`` is ``arango.errno.CONFLICT``. ``create_edge`` wrote through the driver
directly, so it never inherited the ``1200 → WriteConflictError`` mapping
``_insert_doc`` grew for #1436, and the loser surfaced a raw driver exception —
a 500 for a condition that is, at worst, retryable.

**Why this file needs a real ArangoDB.** Whether the server answers ``1200`` (a
serialization failure) or ``1210`` (unique constraint violated) on this index is
the server's decision under real contention; no double can be trusted to make it.
A sequential double call passes against the *unfixed* code and certifies nothing.
Hence the integration tier — never ``tests/unit``/``tests/api``, where a
developer machine's ``localhost:8529`` turns an accidental connection into a local
pass and a CI failure (#978).

**The second defect, measured 2026-09-16 (#1292 round two).** The four-way race
above went red in the required ``Integration tests (ArangoDB)`` lane of PR #1498
with ``racers answered with different profiles: ['11770', '11772', '11772',
'11772']`` while the surviving edge *and* the surviving document were both
``11772``. Storage was consistent; one caller's ANSWER was not. The cause is the
window between the profile insert and the edge insert: a loser's document was
committed and readable through the non-unique ``plant_key`` field before its edge
was refused, so a fourth caller's ``get_profile_by_plant_key`` returned the orphan
and answered with it — moments before the loser deleted it again.
``test_a_second_connection_never_sees_a_profile_before_its_edge`` below pins that
window deterministically instead of waiting for the four-way race to hit it, and
it carries a positive control: the same reader, run again after the writer has
committed, must find the profile — otherwise its earlier ``None`` only says the
reader was blind.

**Falsification.** ``test_negative_control_without_the_index_duplicates`` runs the
identical concurrent driver against the edge collection with the unique index
*removed*, and asserts that two edges then appear. If the racers did not actually
overlap, that control would see one edge and fail — so the positive test below
cannot pass for the trivial reason that nothing ever raced.

The branch behaviour (winner found → answer with it; nothing linked → keep
raising) is pinned solitarily in
``tests/unit/domain/services/test_care_profile_edge_write_conflict.py``, which,
unlike this file, runs in a CI gate (#1432).

Run with: pytest tests/integration/ -v   (requires docker compose up arangodb)
"""

from __future__ import annotations

import threading

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#1292 is a race whose resolution only exists against a real ArangoDB"),
]

_DB_NAME = "kamerplanter_care_profile_edge_test"
_TENANT_KEY = "tenant-alpha"
_PLANT_KEY = "plant-basil-1"
_SPECIES_KEY = "ocimum-basilicum"
#: A family ``_key`` in the numeric shape ArangoDB assigns — never the name.
_FAMILY_KEY = "7242"
_FAMILY_NAME = "Lamiaceae"

#: How many requests race for the same plant's profile. Four mirrors the E2E
#: suite's four xdist workers driving one tenant at once.
_RACERS = 4

#: Independent bursts the negative control may use to observe the race.
_NEGATIVE_CONTROL_ROUNDS = 5


def _settings():
    from app.config.settings import Settings

    return Settings(arangodb_database=_DB_NAME)


def _connect():
    """Open an **own** connection — each racer gets one, like separate workers do."""
    from app.data_access.arango.connection import ArangoConnection

    conn = ArangoConnection(_settings())
    return conn, conn.connect()


def _plant_doc(plant_key: str) -> dict:
    return {
        "_key": plant_key,
        "tenant_key": _TENANT_KEY,
        "instance_id": f"P-{plant_key}",
        "species_key": _SPECIES_KEY,
        "plant_name": "Basil",
        "planted_on": "2026-01-01",
    }


def _species_doc() -> dict:
    """The species the racing plant names, pointing at a family by its ``_key``.

    Seeded because the write path *resolves* it since #1489: the service reads the
    plant, its species and the family document to derive the presets. A race run
    against a service that could not perform those reads would no longer be the
    production path — it would be a shorter one, and the read-then-create window
    this file exists to overlap is exactly what got longer.
    """
    return {"_key": _SPECIES_KEY, "scientific_name": "Ocimum basilicum", "family_key": _FAMILY_KEY}


def _family_doc() -> dict:
    """``Lamiaceae`` — and its ``_key`` is numeric, as ArangoDB assigns them.

    That is the #1489 shape: the species stores the key, ``FAMILY_CARE_MAP`` is
    keyed by the name, and handing the key over produced the TROPICAL fallback.
    Here it makes the resolution observable — the answered profile's care style is
    the family's, which it cannot be unless the resolver ran inside the race.
    """
    return {"_key": _FAMILY_KEY, "name": _FAMILY_NAME}


def _make_service(db):
    """A real service on real Arango repositories — the production write path, unfaked.

    Wired as ``dependencies.get_care_reminder_service`` wires it, and that is not
    decoration: since #1489 ``get_or_create_profile`` resolves the plant's species,
    cultivar and family name itself, so a service built without those collaborators
    would take a different (shorter, read-free) path to the same insert and the race
    would no longer be the one production runs.
    """
    from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
    from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository
    from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
    from app.data_access.arango.species_repository import ArangoSpeciesRepository
    from app.domain.engines.care_reminder_engine import CareReminderEngine
    from app.domain.services.care_reminder_service import CareReminderService

    family_repo = ArangoBotanicalFamilyRepository(db)

    def _resolve_family_name(family_key: str) -> str | None:
        family = family_repo.get_by_key(family_key)
        return getattr(family, "name", None) if family else None

    return CareReminderService(
        ArangoCareReminderRepository(db),
        CareReminderEngine(),
        plant_repo=ArangoPlantInstanceRepository(db),
        species_repo=ArangoSpeciesRepository(db),
        family_name_resolver=_resolve_family_name,
    )


def _profile_edges(db, plant_key: str) -> list[dict]:
    from app.data_access.arango import collections as col

    return list(
        db.aql.execute(
            f"FOR e IN {col.HAS_CARE_PROFILE} FILTER e._from == @from RETURN e",
            bind_vars={"from": f"{col.PLANT_INSTANCES}/{plant_key}"},
        )
    )


def _profile_docs(db, plant_key: str) -> list[dict]:
    from app.data_access.arango import collections as col

    return list(
        db.aql.execute(
            f"FOR doc IN {col.CARE_PROFILES} FILTER doc.plant_key == @plant_key RETURN doc",
            bind_vars={"plant_key": plant_key},
        )
    )


def _race_get_or_create(plant_key: str) -> tuple[list[BaseException], list[str]]:
    """Fire ``_RACERS`` genuinely overlapping ``get_or_create_profile`` calls.

    Each racer opens its **own** connection and builds its own service, so nothing
    is shared but the database. A :class:`threading.Barrier` releases them
    together, so the read-then-create windows actually overlap instead of merely
    being started in a loop. Returns what the racers raised and which profile key
    each one answered with.
    """
    barrier = threading.Barrier(_RACERS)
    errors: list[BaseException] = []
    keys: list[str] = []
    lock = threading.Lock()

    def worker() -> None:
        conn, db = _connect()
        try:
            service = _make_service(db)
            barrier.wait(timeout=30)
            profile = service.get_or_create_profile(plant_key, may_create=True)
            with lock:
                keys.append(profile.key or "")
        except BaseException as exc:  # noqa: BLE001 — recorded and asserted on by the caller
            with lock:
                errors.append(exc)
        finally:
            conn.close()

    threads = [threading.Thread(target=worker, name=f"racer-{i}") for i in range(_RACERS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    return errors, keys


@pytest.fixture
def db():
    """A bootstrapped test database, dropped afterwards."""
    from app.data_access.arango.collections import ensure_collections

    conn, database = _connect()
    ensure_collections(database)
    yield database
    conn.close()
    system = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)


@pytest.fixture
def plant(db):
    """Seed one plant *without* a care profile — the state the race starts from.

    Its species and that species' family are seeded too, because the write path
    reads them (#1489). Without them the racers would still race, but over a
    service that resolves nothing.
    """
    from app.data_access.arango import collections as col

    db.collection(col.SPECIES).insert(_species_doc(), overwrite=True)
    db.collection(col.BOTANICAL_FAMILIES).insert(_family_doc(), overwrite=True)
    db.collection(col.PLANT_INSTANCES).insert(_plant_doc(_PLANT_KEY), overwrite=True)
    return _PLANT_KEY


# ── the constraint itself ────────────────────────────────────────────────────


def test_bootstrap_installs_the_unique_from_index_on_the_profile_edge(db):
    """The invariant the resolution leans on is really in the database.

    ``_resolve_lost_profile_race`` treats the edge as the authority on which of
    two documents won, which is only sound while ``_from`` is unique here. Drop
    the constraint and the service would resolve a race that storage no longer
    prevents.
    """
    from app.data_access.arango import collections as col

    unique = [
        idx
        for idx in db.collection(col.HAS_CARE_PROFILE).indexes()
        if isinstance(idx, dict) and idx.get("unique") and idx.get("type") != "primary"
    ]
    assert [idx["fields"] for idx in unique] == [["_from"]]


# ── the race ─────────────────────────────────────────────────────────────────


def test_concurrent_get_or_create_yields_one_profile_and_no_error(db, plant):
    """Four overlapping requests: one profile, one edge, four quiet answers.

    Before the fix, the losers raised ``DocumentInsertError`` here — the 500 the
    2026-09-14 nightly reported as ``could not create a care profile for '522789'
    (status=500)``.
    """
    errors, keys = _race_get_or_create(plant)

    assert errors == [], f"racers raised: {[repr(e) for e in errors]}"
    assert len(_profile_edges(db, plant)) == 1
    assert len(_profile_docs(db, plant)) == 1, "a loser left an unlinked duplicate profile behind"
    assert len(set(keys)) == 1, f"racers answered with different profiles: {keys}"
    assert keys[0] == _profile_edges(db, plant)[0]["_to"].split("/", 1)[-1]

    # The survivor is the *resolved* profile, not the fallback (#1489). Compared
    # against the engine's own answer rather than a literal care style, so a preset
    # change cannot make this assertion quietly wrong.
    from app.domain.engines.care_reminder_engine import CareReminderEngine

    expected = CareReminderEngine().auto_generate_profile(botanical_family=_FAMILY_NAME, plant_key=plant)
    stored = _profile_docs(db, plant)[0]
    assert stored["care_style"] == expected.care_style.value, (
        "the racers' service did not resolve the family inside the race — it answered with "
        f"{stored['care_style']!r} where the resolved family {_FAMILY_NAME!r} gives "
        f"{expected.care_style.value!r}"
    )
    assert stored["watering_interval_days"] == expected.watering_interval_days


def test_negative_control_without_the_index_duplicates(db):
    """Without the unique ``_from`` index the same driver really does double-write.

    This is what makes the test above non-vacuous: it shows the racers overlap and
    that the constraint — not the code's ordering, and not luck — is what collapses
    them to one.
    """
    from app.data_access.arango import collections as col

    handle = db.collection(col.HAS_CARE_PROFILE)
    for idx in handle.indexes():
        if isinstance(idx, dict) and idx.get("fields") == ["_from"] and idx.get("unique"):
            handle.delete_index(idx["id"], ignore_missing=True)

    observed_duplicate = False
    for round_no in range(_NEGATIVE_CONTROL_ROUNDS):
        plant_key = f"control-plant-{round_no}"
        db.collection(col.PLANT_INSTANCES).insert(_plant_doc(plant_key), overwrite=True)
        _race_get_or_create(plant_key)
        if len(_profile_edges(db, plant_key)) > 1:
            observed_duplicate = True
            break

    assert observed_duplicate, (
        f"{_NEGATIVE_CONTROL_ROUNDS} bursts of {_RACERS} racers never produced a second edge "
        "without the unique index — the racers are not actually overlapping, so the positive "
        "test proves nothing."
    )


# ── the window between the two writes ────────────────────────────────────────


def test_a_second_connection_never_sees_a_profile_before_its_edge(db, plant, monkeypatch):
    """No reader may observe a care profile that is not yet linked (#1292).

    **Deterministic, not timed.** The four-way race above reproduces this only when
    the interleaving happens to land right; it did on 2026-09-16 and had not for two
    days before. This test creates the interleaving instead of hoping for it: the
    writer is suspended *inside* the profile write, at the instant the profile
    document has been handed to the driver and the edge has not, and a **second
    connection** then asks the exact question production asks —
    ``get_profile_by_plant_key``, the non-unique ``plant_key`` field lookup that
    ``get_or_create_profile`` opens with.

    The suspension point is ``StandardCollection.insert`` on ``care_profiles``,
    restricted to the writer thread. That is deliberately below the repository API
    rather than a patch of one of its methods: ``TransactionDatabase.collection()``
    hands back a ``StandardCollection`` too (measured against python-arango on
    ArangoDB 3.12.8), so the same hook catches the write whether it goes through a
    transaction or not, and the test cannot pass merely because the method it used
    to patch was renamed.

    Against the pre-fix code — ``create_profile`` committing, then
    ``create_profile_edge`` — the reader sees the unlinked document and this is red.
    Against the transactional write it sees nothing, because nothing is committed.
    """
    from arango.collection import StandardCollection

    from app.data_access.arango import collections as col
    from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository

    original_insert = StandardCollection.insert
    writer_name = "profile-writer"
    profile_written = threading.Event()
    reader_finished = threading.Event()

    def insert(self, document, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202
        result = original_insert(self, document, *args, **kwargs)
        if self.name == col.CARE_PROFILES and threading.current_thread().name == writer_name:
            profile_written.set()
            # Bounded, so a future implementation that never reaches this point
            # fails the assertion below instead of hanging the suite.
            reader_finished.wait(timeout=30)
        return result

    monkeypatch.setattr(StandardCollection, "insert", insert)

    writer_result: list[object] = []
    observations: list[object] = []

    def write() -> None:
        conn, writer_db = _connect()
        try:
            writer_result.append(_make_service(writer_db).get_or_create_profile(plant, may_create=True))
        except BaseException as exc:  # noqa: BLE001 — asserted on by the caller
            writer_result.append(exc)
        finally:
            profile_written.set()  # never leave the reader waiting on a failed writer
            conn.close()

    def read_from_a_second_connection():  # noqa: ANN202
        conn, reader_db = _connect()
        try:
            return ArangoCareReminderRepository(reader_db).get_profile_by_plant_key(plant)
        finally:
            conn.close()

    def read() -> None:
        try:
            if not profile_written.wait(timeout=30):
                observations.append("the writer never inserted a care-profile document")
                return
            observations.append(read_from_a_second_connection())
        finally:
            reader_finished.set()

    writer = threading.Thread(target=write, name=writer_name)
    reader = threading.Thread(target=read, name="profile-reader")
    writer.start()
    reader.start()
    reader.join(timeout=60)
    writer.join(timeout=60)

    assert observations, "the reader never ran — the observation this test is built on did not happen"
    seen = observations[0]
    assert seen is None, (
        "a second connection read a care profile while it had no has_care_profile edge: "
        f"{seen!r}. That document is a loser's orphan the moment the edge insert is refused, "
        "and answering a request with it is #1292."
    )
    assert writer_result, "the writer thread produced neither a profile nor an exception"
    assert not isinstance(writer_result[0], BaseException), f"the writer failed: {writer_result[0]!r}"
    assert len(_profile_docs(db, plant)) == 1
    assert len(_profile_edges(db, plant)) == 1

    # The positive control (SCR-010). `seen is None` is satisfied by a reader that
    # is simply blind — a wrong database, a typo in the plant key, a connection
    # that never saw anything. Running the SAME function once the writer has
    # committed must find the profile; if it does not, the assertion above proved
    # nothing about timing and everything about the reader.
    after = read_from_a_second_connection()
    assert after is not None and after.plant_key == plant, (
        "the same reader cannot see the profile even after the writer committed — it was never "
        "able to see anything, so its earlier `None` is not evidence"
    )
    assert after.key == _profile_edges(db, plant)[0]["_to"].split("/", 1)[-1]
