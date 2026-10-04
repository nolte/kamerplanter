"""#2113 — integration secrets are Fernet-encrypted at rest, measured on the stored document.

Against a real ArangoDB, through the same providers the API uses
(``app.common.dependencies``): the Home Assistant long-lived token, the Pl@ntNet
key and the Apprise URLs must never appear in the stored document in clear, the
internal readers must still get the plaintext, a value stored before #2113 is
re-encrypted the first time it is read (lazy, race-safe, idempotent), and a
delete must actually remove the stored secret — before #2113 the system-settings
upsert *merged* nested objects, so ``delete_ha_settings`` and
``delete_global_openweathermap_key`` returned success and left the secret in
the document (measured 2026-10-05).

Every credential-shaped value is assembled at runtime (BACKEND.md §16.3).
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from arango import ArangoClient
from arango.database import StandardDatabase
from cryptography.fernet import Fernet

from app.common import dependencies
from app.data_access.arango import collections as col
from app.data_access.arango.notification_preference_repository import NOTIFICATION_PREFERENCES
from app.data_access.arango.system_settings_repository import SINGLETON_KEY
from app.domain.models.notification import ChannelPreference, NotificationPreferences
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("secrets_at_rest")

pytestmark = pytest.mark.usefixtures("arango_db")

# Assembled at run time: a secret scanner must not see a token shape (BACKEND.md §16.3).
HA_TOKEN = "eyJ" + "hbGciOiJIUzI1NiJ9" + "-ha-2113-" + "Zq8vW3"
PLANTNET_KEY = "2b10" + "Plantnet2113" + "xYz"
OWM_KEY = "owm" + "2113" + "global" + "Key"
APPRISE_URL = "tgram://" + "123456789:" + "AAbot2113" + "Token/987654"
GOTIFY_URL = "gotifys://" + "gotify.example.org/" + "Atoken2113"


@pytest.fixture(scope="module")
def database() -> Iterator[StandardDatabase]:
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection(col.SYSTEM_SETTINGS)
    db.create_collection(NOTIFICATION_PREFERENCES)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database: StandardDatabase, monkeypatch: pytest.MonkeyPatch) -> StandardDatabase:
    database.collection(col.SYSTEM_SETTINGS).truncate()
    database.collection(NOTIFICATION_PREFERENCES).truncate()
    monkeypatch.setattr(dependencies, "get_db", lambda: database)
    monkeypatch.setattr(dependencies.settings, "fernet_key", Fernet.generate_key().decode())
    return database


def _raw(db: StandardDatabase, collection: str, key: str) -> str:
    doc = db.collection(collection).get(key)
    assert doc is not None
    return json.dumps(doc)


# ── stored document carries no plaintext ────────────────────────────────


def test_the_ha_token_is_not_stored_in_clear_and_the_reader_still_gets_it(db: StandardDatabase) -> None:
    service = dependencies.get_system_settings_service()

    service.update_ha_settings(ha_url="http://ha.example:8123", ha_access_token=HA_TOKEN, ha_timeout=10)

    assert HA_TOKEN not in _raw(db, col.SYSTEM_SETTINGS, SINGLETON_KEY)
    assert service.get_effective_ha_settings()["ha_access_token"] == HA_TOKEN


def test_the_plantnet_key_is_not_stored_in_clear_and_the_reader_still_gets_it(db: StandardDatabase) -> None:
    service = dependencies.get_system_settings_service()

    service.update_plant_identification_settings(plantnet_api_key=PLANTNET_KEY)

    assert PLANTNET_KEY not in _raw(db, col.SYSTEM_SETTINGS, SINGLETON_KEY)
    assert service.get_effective_plantnet_api_key() == PLANTNET_KEY


def test_apprise_urls_are_not_stored_in_clear_and_the_reader_still_gets_them(db: StandardDatabase) -> None:
    repo = dependencies.get_notification_preference_repo()
    prefs = NotificationPreferences(
        user_key="u2113",
        channels={"apprise": ChannelPreference(enabled=True, config={"urls": [APPRISE_URL, GOTIFY_URL]})},
    )

    repo.upsert(prefs)

    raw = _raw(db, NOTIFICATION_PREFERENCES, "notifpref_u2113")
    assert APPRISE_URL not in raw
    assert GOTIFY_URL not in raw
    stored = repo.get_by_user("u2113")
    assert stored is not None
    assert stored.channels["apprise"].config["urls"] == [APPRISE_URL, GOTIFY_URL]


def test_a_second_save_of_apprise_urls_leaves_no_plaintext_key_behind(db: StandardDatabase) -> None:
    repo = dependencies.get_notification_preference_repo()
    repo.upsert(
        NotificationPreferences(
            user_key="u2113", channels={"apprise": ChannelPreference(enabled=True, config={"urls": [APPRISE_URL]})}
        )
    )
    repo.upsert(
        NotificationPreferences(
            user_key="u2113", channels={"apprise": ChannelPreference(enabled=True, config={"urls": [GOTIFY_URL]})}
        )
    )

    raw = _raw(db, NOTIFICATION_PREFERENCES, "notifpref_u2113")
    assert APPRISE_URL not in raw
    assert GOTIFY_URL not in raw
    stored = repo.get_by_user("u2113")
    assert stored is not None
    assert stored.channels["apprise"].config["urls"] == [GOTIFY_URL]


# ── a delete removes the secret ──────────────────────────────────────────


def test_deleting_the_ha_settings_removes_the_stored_token(db: StandardDatabase) -> None:
    service = dependencies.get_system_settings_service()
    service.update_ha_settings(ha_url="http://ha.example:8123", ha_access_token=HA_TOKEN, ha_timeout=10)

    service.delete_ha_settings()

    stored = db.collection(col.SYSTEM_SETTINGS).get(SINGLETON_KEY)
    assert stored is not None
    assert stored.get("home_assistant", {}) == {}


def test_deleting_the_plantnet_key_removes_it(db: StandardDatabase) -> None:
    service = dependencies.get_system_settings_service()
    service.update_plant_identification_settings(plantnet_api_key=PLANTNET_KEY)

    service.delete_plant_identification_settings()

    stored = db.collection(col.SYSTEM_SETTINGS).get(SINGLETON_KEY)
    assert stored is not None
    assert not any(stored.get("plant_identification", {}).values())


def test_deleting_the_global_owm_key_removes_it(db: StandardDatabase) -> None:
    from app.domain.services.weather_settings_service import WeatherSettingsService

    service = WeatherSettingsService(dependencies.get_system_settings_repo(), dependencies.get_encryption_engine())
    service.update_weather_settings(openweathermap_global_api_key=OWM_KEY)

    assert service.delete_global_openweathermap_key() is True

    stored = db.collection(col.SYSTEM_SETTINGS).get(SINGLETON_KEY)
    assert stored is not None
    assert "openweathermap_global_api_key_encrypted" not in stored.get("weather_providers", {})
    assert service.has_global_openweathermap_key() is False


def test_deleting_the_storage_settings_removes_the_override(db: StandardDatabase) -> None:
    """Same merge defect, non-secret block: the reset to env left the stored override in place."""
    service = dependencies.get_system_settings_service()
    service.update_storage_settings(backend="s3", s3_bucket="bucket-2113")

    assert service.delete_storage_settings() is True

    stored = db.collection(col.SYSTEM_SETTINGS).get(SINGLETON_KEY)
    assert stored is not None
    assert stored.get("storage", {}) == {}


# ── values stored before #2113: lazily re-encrypted on read ───────────────


def _seed_legacy_settings(db: StandardDatabase) -> None:
    db.collection(col.SYSTEM_SETTINGS).insert(
        {
            "_key": SINGLETON_KEY,
            "home_assistant": {"ha_url": "http://ha.example:8123", "ha_access_token": HA_TOKEN, "ha_timeout": 10},
            "plant_identification": {"plantnet_api_key": PLANTNET_KEY},
            "weather_providers": {"dwd_enabled": True},
        }
    )


def test_a_legacy_plaintext_ha_token_and_plantnet_key_are_encrypted_on_first_read(db: StandardDatabase) -> None:
    _seed_legacy_settings(db)
    service = dependencies.get_system_settings_service()

    assert service.get_effective_ha_settings()["ha_access_token"] == HA_TOKEN
    assert service.get_effective_plantnet_api_key() == PLANTNET_KEY

    raw = _raw(db, col.SYSTEM_SETTINGS, SINGLETON_KEY)
    assert HA_TOKEN not in raw
    assert PLANTNET_KEY not in raw
    stored = db.collection(col.SYSTEM_SETTINGS).get(SINGLETON_KEY)
    assert "ha_access_token" not in stored["home_assistant"]
    assert "plantnet_api_key" not in stored["plant_identification"]
    # Nothing beside the two secrets was touched.
    assert stored["weather_providers"] == {"dwd_enabled": True}
    assert stored["home_assistant"]["ha_url"] == "http://ha.example:8123"


def test_the_lazy_re_encryption_is_idempotent(db: StandardDatabase) -> None:
    _seed_legacy_settings(db)
    service = dependencies.get_system_settings_service()
    service.get_effective_ha_settings()
    first = db.collection(col.SYSTEM_SETTINGS).get(SINGLETON_KEY)

    service.get_effective_ha_settings()
    service.get_ha_settings_with_source()
    service.get_plantnet_settings_with_source()

    second = db.collection(col.SYSTEM_SETTINGS).get(SINGLETON_KEY)
    assert second["_rev"] == first["_rev"]
    assert service.get_effective_ha_settings()["ha_access_token"] == HA_TOKEN


def test_legacy_plaintext_apprise_urls_are_encrypted_on_first_read(db: StandardDatabase) -> None:
    db.collection(NOTIFICATION_PREFERENCES).insert(
        {
            "_key": "notifpref_u2113",
            "user_key": "u2113",
            "channels": {
                "apprise": {"enabled": True, "priority": 0, "config": {"urls": [APPRISE_URL]}},
                "email": {"enabled": True, "priority": 0, "config": {"digest": True}},
            },
        }
    )
    repo = dependencies.get_notification_preference_repo()

    stored = repo.get_by_user("u2113")

    assert stored is not None
    assert stored.channels["apprise"].config["urls"] == [APPRISE_URL]
    raw_doc = db.collection(NOTIFICATION_PREFERENCES).get("notifpref_u2113")
    assert APPRISE_URL not in json.dumps(raw_doc)
    assert raw_doc["channels"]["email"] == {"enabled": True, "priority": 0, "config": {"digest": True}}
    rev = raw_doc["_rev"]
    assert repo.get_by_user("u2113") is not None
    assert db.collection(NOTIFICATION_PREFERENCES).get("notifpref_u2113")["_rev"] == rev


# ── the one-shot migration ────────────────────────────────────────────────


def test_the_migration_encrypts_every_legacy_secret_and_a_second_run_changes_nothing(db: StandardDatabase) -> None:
    from app.migrations.versions.v0083_encrypt_integration_secrets import migration

    _seed_legacy_settings(db)
    for user in ("a", "b"):
        db.collection(NOTIFICATION_PREFERENCES).insert(
            {
                "_key": f"notifpref_{user}",
                "user_key": user,
                "channels": {"apprise": {"enabled": True, "config": {"urls": [APPRISE_URL, GOTIFY_URL]}}},
            }
        )
    db.collection(NOTIFICATION_PREFERENCES).insert(
        {"_key": "notifpref_c", "user_key": "c", "channels": {"email": {"enabled": True, "config": {"digest": True}}}}
    )

    dry = migration.up(db, dry_run=True)
    assert dry.changed == 0
    assert HA_TOKEN in _raw(db, col.SYSTEM_SETTINGS, SINGLETON_KEY)

    report = migration.up(db)

    assert report.changed == 4  # HA token, Pl@ntNet key, two preference documents
    everything = json.dumps(list(db.collection(col.SYSTEM_SETTINGS).all())) + json.dumps(
        list(db.collection(NOTIFICATION_PREFERENCES).all())
    )
    for secret in (HA_TOKEN, PLANTNET_KEY, APPRISE_URL, GOTIFY_URL):
        assert secret not in everything
    assert dependencies.get_system_settings_service().get_effective_ha_settings()["ha_access_token"] == HA_TOKEN
    prefs = dependencies.get_notification_preference_repo().get_by_user("a")
    assert prefs is not None
    assert prefs.channels["apprise"].config["urls"] == [APPRISE_URL, GOTIFY_URL]

    assert migration.up(db).changed == 0


def test_the_migration_without_a_key_writes_nothing(db: StandardDatabase, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.migrations.versions.v0083_encrypt_integration_secrets import migration

    monkeypatch.setattr(dependencies.settings, "fernet_key", "")
    _seed_legacy_settings(db)
    before = db.collection(col.SYSTEM_SETTINGS).get(SINGLETON_KEY)["_rev"]

    report = migration.up(db)

    assert report.changed == 0
    assert report.details.get("skipped") == "no_fernet_key"
    assert db.collection(col.SYSTEM_SETTINGS).get(SINGLETON_KEY)["_rev"] == before
