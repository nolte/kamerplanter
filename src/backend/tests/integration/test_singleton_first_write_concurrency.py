"""Integration test for #1458 — a lost per-user-singleton race is not a 500.

``UserPreferenceService`` and ``OnboardingService`` each own a **per-user
singleton**: exactly one ``user_preferences`` / ``onboarding_states`` document
per user, enforced by the unique+sparse ``user_key`` index
(``collections.ensure_user_singleton_index``). Nothing makes "look, then insert"
atomic, so two callers materialising the same user's singleton at the same time
both find nothing and both insert; the index refuses one of them.

Both services caught :class:`DuplicateError` (ArangoDB ``1210``) and re-read the
winner. They did **not** catch :class:`WriteConflictError` (``1200``) — which the
repository did not even raise from ``_update_doc``/``_update_doc_fields`` before
#1458. Which of the two codes the loser gets is the *server's* decision about how
far the winner's transaction had got:

* ``1210`` — the winner's index entry is committed and visible;
* ``1200`` — the winner's transaction still holds the entry.

So a caller that handled only one of them was still a 500 under exactly the load
the re-read exists for. This is the same pairing ``care_reminder_service`` was
given for the profile+edge race (#1292), applied to the sibling path.

**Why this file needs a real ArangoDB.** Which code the server answers under real
contention is not something a double can be trusted to decide; a sequential
double call passes against the *unfixed* code and certifies nothing. Hence the
integration tier — never ``tests/unit``/``tests/api``, where a developer
machine's ``localhost:8529`` turns an accidental connection into a local pass and
a CI failure (#978).

**Falsification.** ``test_negative_control_without_the_index_duplicates`` runs the
identical concurrent driver against the collection with the unique index
*removed* and asserts that several documents then appear. If the racers did not
actually overlap, that control would see one document and fail — so the positive
tests below cannot pass for the trivial reason that nothing ever raced.

Run with: pytest tests/integration/ -v   (requires docker compose up arangodb)
"""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from typing import Any

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#1458 is a race whose resolution only exists against a real ArangoDB"),
]

_DB_NAME = "kamerplanter_singleton_first_write_test"

#: How many callers materialise the same user's singleton at once. Four mirrors
#: the E2E suite's four xdist workers driving one account.
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


def _docs_for_user(db, collection: str, user_key: str) -> list[dict]:
    return list(
        db.aql.execute(
            f"FOR doc IN {collection} FILTER doc.user_key == @user_key RETURN doc",
            bind_vars={"user_key": user_key},
        )
    )


def _race(materialise: Callable[[Any, str], str | None], user_key: str) -> tuple[list[BaseException], list[str | None]]:
    """Fire ``_RACERS`` genuinely overlapping first writes of one user's singleton.

    Each racer opens its **own** connection and builds its own service, so nothing
    is shared but the database. A :class:`threading.Barrier` releases them
    together, so the look-then-insert windows actually overlap instead of merely
    being started in a loop. Returns what the racers raised and which document key
    each one answered with.
    """
    barrier = threading.Barrier(_RACERS)
    errors: list[BaseException] = []
    keys: list[str | None] = []
    lock = threading.Lock()

    def worker() -> None:
        conn, db = _connect()
        try:
            barrier.wait(timeout=30)
            key = materialise(db, user_key)
            with lock:
                keys.append(key)
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


# ── the constraints the resolutions lean on ──────────────────────────────────


@pytest.mark.parametrize("collection_attr", ["USER_PREFERENCES", "ONBOARDING_STATES"])
def test_bootstrap_installs_the_unique_user_key_index(db, collection_attr: str):
    """The invariant both re-reads lean on is really in the database.

    Both services treat "the insert was refused" as "somebody else won, re-read",
    which is only sound while ``user_key`` is unique here. Without the constraint
    they would resolve a race that storage no longer prevents, and the re-read
    would pick one of several duplicates.
    """
    from app.data_access.arango import collections as col

    unique = [
        idx
        for idx in db.collection(getattr(col, collection_attr)).indexes()
        if isinstance(idx, dict) and idx.get("unique") and idx.get("type") != "primary"
    ]
    assert [idx["fields"] for idx in unique] == [["user_key"]]


# ── the race ─────────────────────────────────────────────────────────────────


def _materialise_preferences(db, user_key: str) -> str | None:
    from app.domain.services.user_preference_service import UserPreferenceService

    return UserPreferenceService(db).update_preferences(user_key, {"experience_level": "expert"}).key


def _materialise_onboarding_state(db, user_key: str) -> str | None:
    from app.domain.services.onboarding_service import OnboardingService
    from app.domain.services.starter_kit_service import StarterKitService

    return OnboardingService(db, StarterKitService(db)).save_progress(user_key, 2).key


def test_concurrent_first_preferences_write_yields_one_document_and_no_error(db):
    """Four overlapping first writes: one document, four quiet answers.

    Before #1458 a loser that got ``1200`` instead of ``1210`` raised out of
    ``get_preferences`` as a bare driver exception — a 500 for a condition the
    re-read right underneath already knew how to resolve.
    """
    from app.data_access.arango import collections as col

    user_key = f"user-{uuid.uuid4().hex[:8]}"
    errors, keys = _race(_materialise_preferences, user_key)

    assert errors == [], f"racers raised: {[repr(e) for e in errors]}"
    documents = _docs_for_user(db, col.USER_PREFERENCES, user_key)
    assert len(documents) == 1, "a loser minted a second singleton"
    assert all(key for key in keys), "a racer answered without a document"
    assert set(keys) == {documents[0]["_key"]}, f"racers answered with different documents: {keys}"


def test_concurrent_first_onboarding_write_yields_one_document_and_no_error(db):
    """The sibling path, raced the same way — the two services share the shape."""
    from app.data_access.arango import collections as col

    user_key = f"user-{uuid.uuid4().hex[:8]}"
    errors, keys = _race(_materialise_onboarding_state, user_key)

    assert errors == [], f"racers raised: {[repr(e) for e in errors]}"
    documents = _docs_for_user(db, col.ONBOARDING_STATES, user_key)
    assert len(documents) == 1, "a loser minted a second singleton"
    assert all(key for key in keys), "a racer answered without a document"
    assert set(keys) == {documents[0]["_key"]}, f"racers answered with different documents: {keys}"


def test_negative_control_without_the_index_duplicates(db):
    """Without the unique ``user_key`` index the same racers really do double-write.

    This is what makes the two tests above non-vacuous: it shows the callers
    overlap, and that the constraint — not the code's ordering, and not luck — is
    what collapses them to one document.
    """
    from app.data_access.arango import collections as col

    collection = db.collection(col.USER_PREFERENCES)
    dropped = [
        idx
        for idx in collection.indexes()
        if isinstance(idx, dict) and idx.get("unique") and idx.get("type") != "primary"
    ]
    assert dropped, "nothing to drop — the control would be vacuous"
    for idx in dropped:
        collection.delete_index(idx["id"])

    # The index is deliberately NOT restored: the ``db`` fixture drops the whole
    # database after this test, and the duplicates this control creates on purpose
    # would make a re-creation fail with the very 1210 it was asked to produce.
    for _ in range(_NEGATIVE_CONTROL_ROUNDS):
        user_key = f"user-{uuid.uuid4().hex[:8]}"
        _race(_materialise_preferences, user_key)
        if len(_docs_for_user(db, col.USER_PREFERENCES, user_key)) > 1:
            return

    pytest.fail(
        f"{_NEGATIVE_CONTROL_ROUNDS} unconstrained bursts never produced a duplicate. The racers are not "
        "overlapping, so the positive tests above prove nothing about a race."
    )
