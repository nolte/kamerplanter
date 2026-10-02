"""#1885 — v0065 strips the typed-in e-mail recipient from stored preferences, against a real ArangoDB.

The rows carry the shapes that exist on a volume written before #1885; the
migration must remove only ``channels.email.config.email`` / ``address`` and
leave the digest flag, other channels and unrelated rows untouched.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.migrations.versions.v0065_drop_free_text_email_recipients import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("v0065_drop_email_recipients")

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    prefs = db.create_collection(col.NOTIFICATION_PREFERENCES)
    prefs.insert(
        {
            "_key": "typed",
            "user_key": "u1",
            "channels": {
                "email": {"enabled": True, "priority": 1, "config": {"email": "x@stranger.example", "digest": True}},
                "pwa": {"enabled": True, "priority": 0, "config": {"subscriptions": [{"endpoint": "e"}]}},
            },
            "quiet_hours": {"enabled": True},
        }
    )
    prefs.insert(
        {
            "_key": "legacy_address",
            "user_key": "u2",
            "channels": {"email": {"enabled": True, "config": {"address": "y@stranger.example"}}},
        }
    )
    prefs.insert(
        {"_key": "clean", "user_key": "u3", "channels": {"email": {"enabled": True, "config": {"digest": False}}}}
    )
    prefs.insert({"_key": "no_email_channel", "user_key": "u4", "channels": {"pwa": {"enabled": True, "config": {}}}})
    prefs.insert({"_key": "no_config", "user_key": "u5", "channels": {"email": {"enabled": False}}})
    yield db
    system.delete_database(TEST_DATABASE)


def test_v0065_drops_only_the_recipient_and_is_idempotent(database) -> None:
    prefs = database.collection(col.NOTIFICATION_PREFERENCES)
    before_clean = prefs.get("clean")

    dry = migration.up(database, dry_run=True)
    assert (dry.scanned, dry.changed) == (2, 0)
    assert prefs.get("typed")["channels"]["email"]["config"]["email"] == "x@stranger.example"

    first = migration.up(database)
    second = migration.up(database)

    typed = prefs.get("typed")
    assert typed["channels"]["email"]["config"] == {"digest": True}
    assert typed["channels"]["email"]["enabled"] is True and typed["channels"]["email"]["priority"] == 1
    assert typed["channels"]["pwa"]["config"] == {"subscriptions": [{"endpoint": "e"}]}
    assert typed["quiet_hours"] == {"enabled": True}
    assert prefs.get("legacy_address")["channels"]["email"] == {"enabled": True, "config": {}}
    assert prefs.get("clean") == before_clean
    assert prefs.get("no_config")["channels"]["email"] == {"enabled": False}
    assert (first.scanned, first.changed) == (2, 2)
    assert (second.scanned, second.changed) == (0, 0)
