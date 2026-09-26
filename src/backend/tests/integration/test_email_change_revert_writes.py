"""#1848 / /code-review of #1893 — the conditional writes the e-mail change and revert rely on.

The in-memory doubles of the route tests mirror these, so the real AQL is held
here against a real ArangoDB:

* ``claim_status`` is a compare-and-set, and claiming ``confirmed`` stamps
  ``confirmed_at`` in the same write — a revert's supersede must see a
  confirmation that is still in flight;
* ``record_confirmation`` writes nothing onto a request a revert superseded;
* ``find_revert_reservation`` holds an address only within the open window;
* ``ArangoUserRepository.move_email`` writes only while the address is the
  expected one, clears ``None`` fields, and answers a taken address with
  ``DuplicateError`` from the unique index.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient
from arango.database import StandardDatabase

from app.common.exceptions import DuplicateError
from app.data_access.arango import collections as col
from app.data_access.arango.email_change_repository import ArangoEmailChangeRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("email_change_revert")
NOW = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection(col.USERS).add_persistent_index(fields=["email"], unique=True)
    db.create_collection(col.EMAIL_CHANGE_REQUESTS)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database: StandardDatabase) -> StandardDatabase:
    for name in (col.USERS, col.EMAIL_CHANGE_REQUESTS):
        database.collection(name).truncate()
    return database


def _change(db: StandardDatabase, **fields: object) -> str:
    doc = {
        "user_key": "u1",
        "new_email": "new@example.org",
        "verification_token_hash": f"h-{len(fields)}-{fields.get('status', 'pending')}",
        "status": "pending",
        "expires_at": (NOW + timedelta(hours=24)).isoformat(),
        **fields,
    }
    return db.collection(col.EMAIL_CHANGE_REQUESTS).insert(doc)["_key"]


def test_claiming_confirmed_stamps_confirmed_at_and_is_a_compare_and_set(db: StandardDatabase) -> None:
    repo = ArangoEmailChangeRepository(db)
    key = _change(db)

    first = repo.claim_status(key, "pending", "confirmed", NOW.isoformat())
    second = repo.claim_status(key, "pending", "confirmed", NOW.isoformat())

    stored = db.collection(col.EMAIL_CHANGE_REQUESTS).get(key)
    assert (first, second) == (True, False)
    assert stored["status"] == "confirmed"
    assert stored["confirmed_at"] == NOW.isoformat()


def test_a_superseded_request_gets_no_revert_record(db: StandardDatabase) -> None:
    repo = ArangoEmailChangeRepository(db)
    key = _change(db, status="superseded")

    recorded = repo.record_confirmation(
        key,
        previous_email="old@example.org",
        revert_token_hash="rh",
        revert_expires_at_iso=(NOW + timedelta(days=7)).isoformat(),
        now_iso=NOW.isoformat(),
    )

    stored = db.collection(col.EMAIL_CHANGE_REQUESTS).get(key)
    assert recorded is False
    assert stored["status"] == "superseded"
    assert "revert_token_hash" not in stored


def test_an_address_is_held_only_within_its_revert_window(db: StandardDatabase) -> None:
    repo = ArangoEmailChangeRepository(db)
    _change(
        db,
        status="confirmed",
        previous_email="Old@Example.org",
        revert_expires_at=(NOW + timedelta(days=1)).isoformat(),
    )

    held = repo.find_revert_reservation("old@example.org", NOW.isoformat())
    after = repo.find_revert_reservation("old@example.org", (NOW + timedelta(days=2)).isoformat())

    assert held is not None
    assert after is None


def test_move_email_writes_only_from_the_expected_address(db: StandardDatabase) -> None:
    repo = ArangoUserRepository(db)
    db.collection(col.USERS).insert(
        {"_key": "u1", "email": "b@example.org", "display_name": "U", "password_reset_token": "t"}
    )

    stale = repo.move_email("u1", "c@example.org", {"email": "a@example.org"})
    moved = repo.move_email("u1", "B@example.org", {"email": "a@example.org", "password_reset_token": None})

    stored = db.collection(col.USERS).get("u1")
    assert stale is None
    assert moved is not None and moved.email == "a@example.org"
    assert stored["email"] == "a@example.org"
    assert stored.get("password_reset_token") is None


def test_move_email_onto_a_taken_address_is_a_duplicate(db: StandardDatabase) -> None:
    repo = ArangoUserRepository(db)
    db.collection(col.USERS).insert({"_key": "u1", "email": "b@example.org", "display_name": "U"})
    db.collection(col.USERS).insert({"_key": "u2", "email": "a@example.org", "display_name": "V"})

    with pytest.raises(DuplicateError):
        repo.move_email("u1", "b@example.org", {"email": "a@example.org"})

    assert db.collection(col.USERS).get("u1")["email"] == "b@example.org"
