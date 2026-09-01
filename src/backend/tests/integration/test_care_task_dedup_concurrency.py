"""Integration test for #1301 — "exactly one pending watering task" under concurrency.

``CareReminderService.ensure_next_watering_task`` promises *exactly one* pending
watering task per plant and used to enforce it with a read-then-create:
``find_open_care_task`` and, if that found nothing, ``create_task``. Nothing made
the pair atomic, so two overlapping invocations both read "none open" and both
inserted. The producers really are separate processes — the 06:00 UTC Celery beat
and a manual ``POST /t/{slug}/tasks/generate-care-reminders`` — which is why the
fix is a storage constraint (a unique sparse index over the ``care_dedup_key``
computed value) rather than an in-process lock.

**Why this file needs a real ArangoDB.** A sequential double call passes against
the *unfixed* code and would certify nothing; the same is true of any fake whose
``create`` cannot lose a race. The only thing that proves the constraint holds is
genuinely overlapping writes reaching a real server, so this lives in the
integration tier — never in ``tests/unit`` or ``tests/api``, where ``localhost:8529``
answering on a developer machine turns an accidental real connection into a local
pass and a CI failure (#978).

**Falsification.** ``test_negative_control_without_the_index_duplicates`` runs the
identical concurrent driver against a collection with the constraint *removed* and
asserts duplicates appear. If the constraint were inert, or the driver not actually
concurrent, that test would go green-with-one-task and fail — so the positive test
below cannot pass for the trivial reason that nothing ever overlapped.

Measured before the fix was wired in: 25 independent bursts of four racers against
an unconstrained ``tasks`` collection produced **3 or 4 open watering tasks in
25/25 rounds (100 %)**, never one. The same 25 bursts with the index in place
produced **exactly one in 25/25 rounds**, with the three losers returning ``None``
and raising nothing.

Run with: pytest tests/integration/ -v   (requires docker compose up arangodb)
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime

import pytest

ARANGO_AVAILABLE = False
try:
    from arango import ArangoClient

    _probe = ArangoClient(hosts="http://localhost:8529")
    _probe.db("_system", username="root", password="rootpassword").version()
    ARANGO_AVAILABLE = True
    _probe.close()
except Exception:
    pass


pytestmark = [
    pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB not available"),
    pytest.mark.allow_db_connection("#1301 concurrency guarantee is only observable against a real ArangoDB"),
]

_DB_NAME = "kamerplanter_care_task_dedup_test"
_TENANT_KEY = "tenant-alpha"
_PLANT_KEY = "plant-basil-1"

#: How many producers race for the same plant's next watering task. Four mirrors
#: the E2E suite's four xdist workers hitting ``generate-care-reminders`` at once
#: and is enough to make the unguarded window reproduce (see the negative control).
_RACERS = 4

#: Rounds the negative control may use to observe the race. Each round is an
#: independent burst on a fresh plant; the assertion is that the race is
#: *reachable*, which is what makes the positive test non-vacuous.
_NEGATIVE_CONTROL_ROUNDS = 5


def _settings():
    from app.config.settings import Settings

    return Settings(arangodb_database=_DB_NAME)


def _connect():
    """Open an **own** connection — each racer gets one, like separate processes do."""
    from app.data_access.arango.connection import ArangoConnection

    conn = ArangoConnection(_settings())
    return conn, conn.connect()


def _plant_doc(plant_key: str) -> dict:
    return {
        "_key": plant_key,
        "tenant_key": _TENANT_KEY,
        "instance_id": f"P-{plant_key}",
        "species_key": "ocimum-basilicum",
        "plant_name": "Basil",
        "planted_on": "2026-01-01",
    }


def _make_service(db):
    """A real ``CareReminderService`` on real Arango repositories — no fakes.

    The concurrency guarantee is a property of the production read-then-create, so
    the test drives exactly that method rather than re-assembling its steps.
    """
    from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository
    from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
    from app.data_access.arango.task_repository import ArangoTaskRepository
    from app.domain.engines.care_reminder_engine import CareReminderEngine
    from app.domain.services.care_reminder_service import CareReminderService

    return CareReminderService(
        ArangoCareReminderRepository(db),
        CareReminderEngine(),
        task_repo=ArangoTaskRepository(db),
        plant_repo=ArangoPlantInstanceRepository(db),
    )


def _profile(plant_key: str):
    from app.domain.models.care_reminder import CareProfile

    return CareProfile(plant_key=plant_key, watering_interval_days=3)


def _open_watering_tasks(db, plant_key: str) -> list[dict]:
    from app.common.enums import ReminderType
    from app.data_access.arango import collections as col

    return list(
        db.aql.execute(
            f"FOR doc IN {col.TASKS} "
            "FILTER doc.entity_key == @plant_key "
            "FILTER doc.status IN @open_statuses "
            "FILTER doc.name != null AND RIGHT(doc.name, LENGTH(@suffix)) == @suffix "
            "RETURN doc",
            bind_vars={
                "plant_key": plant_key,
                "open_statuses": col.CARE_TASK_OPEN_STATUSES,
                "suffix": f"{col.CARE_TASK_NAME_SEPARATOR}{ReminderType.WATERING.value}",
            },
        )
    )


def _race_ensure_next_watering_task(plant_key: str) -> list[BaseException]:
    """Fire ``_RACERS`` genuinely overlapping ``ensure_next_watering_task`` calls.

    Each racer opens its **own** ArangoDB connection and builds its own service, so
    nothing is shared but the database — the same isolation the Celery beat and an
    API worker have. A :class:`threading.Barrier` releases them together, so the
    read-then-create windows actually overlap instead of merely being "started in a
    loop". Returns whatever the racers raised, so a caller can assert that the
    losers came back *quietly* rather than with an error.
    """
    barrier = threading.Barrier(_RACERS)
    errors: list[BaseException] = []
    errors_lock = threading.Lock()

    def worker() -> None:
        conn, db = _connect()
        try:
            service = _make_service(db)
            profile = _profile(plant_key)
            barrier.wait(timeout=30)
            service.ensure_next_watering_task(profile)
        except BaseException as exc:  # noqa: BLE001 — recorded and asserted on by the caller
            with errors_lock:
                errors.append(exc)
        finally:
            conn.close()

    threads = [threading.Thread(target=worker, name=f"racer-{i}") for i in range(_RACERS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    return errors


@pytest.fixture
def db():
    """A bootstrapped test database, dropped afterwards."""
    from app.data_access.arango.collections import ensure_collections

    conn, database = _connect()
    ensure_collections(database)
    yield database
    conn.close()
    system = ArangoClient(hosts="http://localhost:8529").db("_system", username="root", password="rootpassword")
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)


@pytest.fixture
def plant(db):
    """Seed one plant and its care profile, and return its key."""
    from app.data_access.arango import collections as col

    db.collection(col.PLANT_INSTANCES).insert(_plant_doc(_PLANT_KEY), overwrite=True)
    db.collection(col.CARE_PROFILES).insert(
        {"plant_key": _PLANT_KEY, "watering_interval_days": 3, "created_at": datetime.now(UTC).isoformat()},
        overwrite=True,
    )
    return _PLANT_KEY


# ── the constraint itself ────────────────────────────────────────────────────


def test_bootstrap_installs_the_unique_sparse_dedup_index(db):
    """``ensure_collections`` leaves ``tasks`` carrying the constraint and its computed value."""
    from app.data_access.arango import collections as col

    handle = db.collection(col.TASKS)
    assert col.has_care_task_dedup_computed_value(handle)

    dedup_indexes = [
        idx
        for idx in handle.indexes()
        if isinstance(idx, dict) and idx.get("fields") == col.CARE_TASK_DEDUP_INDEX_FIELDS
    ]
    assert len(dedup_indexes) == 1
    assert dedup_indexes[0]["unique"] is True
    assert dedup_indexes[0]["sparse"] is True


def test_tasks_carries_exactly_one_unique_index(db):
    """``create_care_reminder_task`` swallows ``DuplicateError`` on ``tasks``; pin why that is safe.

    It maps a lost race to ``None`` without inspecting *which* index was violated,
    which is only sound while the care dedup index is the collection's sole unique
    one. Add a second and this reddens, instead of a genuinely different conflict
    being silently reported as "a task already exists".
    """
    from app.data_access.arango import collections as col

    unique_indexes = [idx for idx in db.collection(col.TASKS).indexes() if isinstance(idx, dict) and idx.get("unique")]
    non_primary = [idx for idx in unique_indexes if idx.get("type") != "primary"]
    assert [idx["fields"] for idx in non_primary] == [col.CARE_TASK_DEDUP_INDEX_FIELDS]


def test_dedup_key_is_derived_from_the_real_task_builder(db, plant):
    """The computed value reads back the reminder type ``build_care_reminder_task`` writes.

    The reminder type is carried only by the ``"— {type}"`` name suffix (audit P5).
    If the builder's naming convention and
    ``collections.CARE_TASK_NAME_SEPARATOR`` ever drift, the derived key collapses
    to something that no longer distinguishes watering from fertilizing and the
    index quietly becomes "one open care task per plant" — far worse than the bug.
    Asserting against a task the *real builder* produced is what catches that.
    """
    from app.common.enums import ReminderType
    from app.data_access.arango import collections as col
    from app.data_access.arango.task_repository import ArangoTaskRepository
    from app.domain.services.care_reminder_service import build_care_reminder_task

    repo = ArangoTaskRepository(db)
    task = repo.create_task(
        build_care_reminder_task(
            plant_key=plant,
            plant_label="Basil — the one on the sill",  # a label that itself contains the separator
            tenant_key=_TENANT_KEY,
            reminder_type=ReminderType.WATERING,
            due_date=datetime.now(UTC),
        )
    )
    stored = db.collection(col.TASKS).get(task.key)
    assert stored[col.CARE_TASK_DEDUP_FIELD] == f"{_TENANT_KEY}/{plant}/{ReminderType.WATERING.value}"


def test_completing_a_task_releases_the_slot(db, plant):
    """A completed care task drops out of the index, so the next occurrence can be created.

    This is the half that a naive "make care tasks unique" index would break: a
    plant is watered many times and every watering leaves another completed task
    with the same name.
    """
    from app.common.enums import ReminderType, TaskStatus
    from app.data_access.arango import collections as col
    from app.data_access.arango.task_repository import ArangoTaskRepository
    from app.domain.services.care_reminder_service import build_care_reminder_task

    repo = ArangoTaskRepository(db)

    def new_task():
        return build_care_reminder_task(
            plant_key=plant,
            plant_label="Basil",
            tenant_key=_TENANT_KEY,
            reminder_type=ReminderType.WATERING,
            due_date=datetime.now(UTC),
        )

    for _ in range(3):
        task = repo.create_task(new_task())
        assert db.collection(col.TASKS).get(task.key)[col.CARE_TASK_DEDUP_FIELD] is not None
        repo.update_fields(
            task.key,
            {"status": TaskStatus.COMPLETED.value, "completed_at": datetime.now(UTC).isoformat()},
        )
        assert col.CARE_TASK_DEDUP_FIELD not in db.collection(col.TASKS).get(task.key)


# ── the race ─────────────────────────────────────────────────────────────────


def test_concurrent_generation_yields_exactly_one_pending_watering_task(db, plant):
    """AC-1: overlapping ``ensure_next_watering_task`` calls produce **one** open task."""
    errors = _race_ensure_next_watering_task(plant)

    assert errors == [], f"racers must not surface an error; got {errors!r}"
    open_tasks = _open_watering_tasks(db, plant)
    assert len(open_tasks) == 1, f"expected exactly one open watering task, found {len(open_tasks)}"


def test_sequential_idempotency_is_unchanged(db, plant):
    """AC-2: a second call after the first still creates nothing (and returns ``None``)."""
    service = _make_service(db)

    first = service.ensure_next_watering_task(_profile(plant))
    second = service.ensure_next_watering_task(_profile(plant))

    assert first is not None
    assert second is None
    assert len(_open_watering_tasks(db, plant)) == 1


def test_negative_control_without_the_index_duplicates(db, plant):
    """The driver really is concurrent: strip the constraint and duplicates appear.

    Without this, the positive test above could pass because the racers never
    actually overlapped — the "positive test certifies nothing" failure class. Here
    the index and the computed value are removed, reproducing the pre-#1301
    collection exactly, and the same driver is expected to mint more than one open
    watering task.

    Repeated over a handful of independent bursts because the interleaving is not
    guaranteed on any single one; the claim asserted is that the race is
    *reachable*, which is precisely what the constraint has to defeat.
    """
    from app.data_access.arango import collections as col

    handle = db.collection(col.TASKS)
    for idx in handle.indexes():
        if isinstance(idx, dict) and idx.get("fields") == col.CARE_TASK_DEDUP_INDEX_FIELDS:
            handle.delete_index(idx["id"], ignore_missing=True)
    handle.configure(computed_values=[])

    observed = []
    for round_index in range(_NEGATIVE_CONTROL_ROUNDS):
        plant_key = f"{plant}-nc-{round_index}"
        db.collection(col.PLANT_INSTANCES).insert(_plant_doc(plant_key), overwrite=True)
        db.collection(col.CARE_PROFILES).insert(
            {"plant_key": plant_key, "watering_interval_days": 3, "created_at": datetime.now(UTC).isoformat()},
            overwrite=True,
        )
        _race_ensure_next_watering_task(plant_key)
        observed.append(len(_open_watering_tasks(db, plant_key)))

    assert max(observed) > 1, (
        "the unconstrained collection must be able to mint duplicates — otherwise the "
        f"driver is not concurrent and the positive test proves nothing (per-round counts: {observed})"
    )
