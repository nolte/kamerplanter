"""#1827 — pruning expired Web-Push subscriptions is one atomic update that never creates a document.

``ArangoNotificationPreferenceRepository.remove_subscriptions`` against a real
ArangoDB: it removes exactly the named endpoints of one channel, leaves every
other part of the document as stored, returns the count — and for a user whose
preferences are gone (an erasure removed them) it creates nothing. A
read-then-``upsert`` would have recreated the document with its remaining
subscriptions and the rest of the channel configuration (#1892 security review).

No personal data: every value is synthetic.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient
from arango.database import StandardDatabase

from app.data_access.arango.notification_preference_repository import (
    NOTIFICATION_PREFERENCES,
    ArangoNotificationPreferenceRepository,
)
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("push_prune")
LIVE = "https://fcm.googleapis.com/fcm/send/live-1827"
GONE = "https://fcm.googleapis.com/fcm/send/gone-1827"
ALSO_GONE = "https://updates.push.services.mozilla.com/wpush/v2/gone-1827"

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection(NOTIFICATION_PREFERENCES)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database: StandardDatabase) -> StandardDatabase:
    database.collection(NOTIFICATION_PREFERENCES).truncate()
    return database


def _seed(db: StandardDatabase, user_key: str = "u1") -> None:
    db.collection(NOTIFICATION_PREFERENCES).insert(
        {
            "_key": f"notifpref_{user_key}",
            "user_key": user_key,
            "channels": {
                "pwa": {
                    "enabled": True,
                    "priority": 5,
                    "config": {
                        "subscriptions": [
                            {"endpoint": GONE, "p256dh": "k1", "auth": "a1"},
                            {"endpoint": LIVE, "p256dh": "k2", "auth": "a2", "user_agent": "probe"},
                            {"endpoint": ALSO_GONE, "p256dh": "k3", "auth": "a3"},
                        ],
                        "other": "kept",
                    },
                },
                "email": {"enabled": True, "config": {"digest": True}},
            },
            "quiet_hours": {"enabled": False},
        }
    )


def test_only_the_named_endpoints_are_removed_and_the_rest_of_the_document_is_kept(db: StandardDatabase) -> None:
    _seed(db)

    removed = ArangoNotificationPreferenceRepository(db).remove_subscriptions("u1", "pwa", [GONE, ALSO_GONE])

    doc = db.collection(NOTIFICATION_PREFERENCES).get("notifpref_u1")
    assert removed == 2
    assert doc["channels"]["pwa"]["config"]["subscriptions"] == [
        {"endpoint": LIVE, "p256dh": "k2", "auth": "a2", "user_agent": "probe"}
    ]
    assert doc["channels"]["pwa"]["config"]["other"] == "kept"
    assert doc["channels"]["pwa"]["enabled"] is True and doc["channels"]["pwa"]["priority"] == 5
    assert doc["channels"]["email"] == {"enabled": True, "config": {"digest": True}}
    assert doc["quiet_hours"] == {"enabled": False}


def test_nothing_is_written_when_no_endpoint_matches(db: StandardDatabase) -> None:
    _seed(db)
    before = db.collection(NOTIFICATION_PREFERENCES).get("notifpref_u1")

    removed = ArangoNotificationPreferenceRepository(db).remove_subscriptions("u1", "pwa", ["https://push/unknown"])

    assert removed == 0
    assert db.collection(NOTIFICATION_PREFERENCES).get("notifpref_u1")["_rev"] == before["_rev"]


def test_a_user_without_preferences_gets_none_created(db: StandardDatabase) -> None:
    removed = ArangoNotificationPreferenceRepository(db).remove_subscriptions("erased-user", "pwa", [GONE])

    assert removed == 0
    assert db.collection(NOTIFICATION_PREFERENCES).count() == 0


def test_another_users_document_is_untouched(db: StandardDatabase) -> None:
    _seed(db, "u1")
    _seed(db, "u2")

    ArangoNotificationPreferenceRepository(db).remove_subscriptions("u1", "pwa", [GONE])

    subscriptions = db.collection(NOTIFICATION_PREFERENCES).get("notifpref_u2")["channels"]["pwa"]["config"][
        "subscriptions"
    ]
    assert GONE in [s["endpoint"] for s in subscriptions]
