"""#2171: a calendar feed's iCal token is not readable off the stored feed.

Measured before the change: ``CalendarService.create_feed`` / ``regenerate_token``
wrote the raw token into ``calendar_feeds.token`` and ``generate_ical_for_feed``
matched it by value (``get_by_token``), so anyone with read access to the database
or a backup held a working subscription URL for every feed of every tenant.

Driven through the real ``CalendarService`` over the real
``ArangoCalendarFeedRepository``: the raw token is taken from what the service
hands back for the create / rotate response (the only place it may go) and searched
for in the stored document as the server returns it. The legacy half writes feeds
the pre-#2171 way - plaintext ``token`` under the old unique ``token`` index - runs
the migration and proves the URL distributed before the upgrade still resolves.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

import hashlib
import json

import pytest
from arango import ArangoClient

from app.common.exceptions import ValidationError
from app.data_access.arango import collections as col
from app.data_access.arango.calendar_feed_repository import ArangoCalendarFeedRepository
from app.data_access.arango.calendar_source_repository import ArangoCalendarSourceRepository
from app.domain.engines.calendar_aggregation_engine import CalendarAggregationEngine
from app.domain.models.calendar import CalendarFeed
from app.domain.services.calendar_service import CalendarService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("calendar_feed_token_at_rest")
TENANT = "tenant-feed"

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    database.collection(col.CALENDAR_FEEDS).truncate()
    return database


def _service(db) -> CalendarService:
    return CalendarService(
        ArangoCalendarFeedRepository(db),
        CalendarAggregationEngine(),
        ArangoCalendarSourceRepository(db),
    )


def _stored(db) -> dict:
    (doc,) = list(db.collection(col.CALENDAR_FEEDS).all())
    return doc


def _sha256(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _new_feed() -> CalendarFeed:
    return CalendarFeed(name="Garten", tenant_key=TENANT, user_key="owner")


def test_a_created_feed_is_stored_with_the_hash_of_its_token_only(db) -> None:
    service = _service(db)

    issued = service.create_feed(_new_feed())
    raw = issued.token
    stored = _stored(db)

    assert raw  # the create response carries the token, once
    assert raw not in json.dumps(stored)
    assert "token" not in stored
    assert stored["token_hash"] == _sha256(raw)

    ics = service.generate_ical_for_feed(stored["_key"], raw)
    assert ics.startswith("BEGIN:VCALENDAR")


def test_the_stored_hash_is_not_itself_a_working_feed_token(db) -> None:
    service = _service(db)
    service.create_feed(_new_feed())
    stored = _stored(db)

    with pytest.raises(ValidationError, match="Invalid feed token"):
        service.generate_ical_for_feed(stored["_key"], stored["token_hash"])


def test_a_rotation_stores_only_the_new_hash_and_retires_the_old_url(db) -> None:
    service = _service(db)
    old = service.create_feed(_new_feed())
    key = _stored(db)["_key"]

    rotated = service.regenerate_token(key, tenant_key=TENANT)
    stored = _stored(db)

    assert rotated.token and rotated.token != old.token
    assert rotated.token not in json.dumps(stored) and old.token not in json.dumps(stored)
    assert stored["token_hash"] == _sha256(rotated.token)
    with pytest.raises(ValidationError, match="Invalid feed token"):
        service.generate_ical_for_feed(key, old.token)
    assert service.generate_ical_for_feed(key, rotated.token).startswith("BEGIN:VCALENDAR")


def test_an_update_keeps_the_hash_and_never_reintroduces_a_token(db) -> None:
    service = _service(db)
    issued = service.create_feed(_new_feed())
    key = _stored(db)["_key"]

    service.update_feed(key, CalendarFeed(name="Umbenannt", is_active=True), tenant_key=TENANT)
    stored = _stored(db)

    assert stored["name"] == "Umbenannt"
    assert stored["token_hash"] == _sha256(issued.token)
    assert "token" not in stored
    assert service.generate_ical_for_feed(key, issued.token).startswith("BEGIN:VCALENDAR")


def test_two_feeds_can_be_created_one_after_the_other(db) -> None:
    """The unique index is on ``token_hash`` now; no attribute both feeds lack is indexed uniquely."""
    service = _service(db)

    first = service.create_feed(_new_feed())
    second = service.create_feed(CalendarFeed(name="Balkon", tenant_key=TENANT, user_key="owner"))

    assert first.token != second.token
    assert db.collection(col.CALENDAR_FEEDS).count() == 2


def test_the_migration_hashes_the_urls_distributed_before_the_upgrade(db) -> None:
    """Feeds written the pre-#2171 way: plaintext ``token`` under the old unique ``token`` index."""
    from app.migrations.versions.v0090_hash_calendar_feed_tokens import HashCalendarFeedTokensMigration

    feeds = db.collection(col.CALENDAR_FEEDS)
    # The legacy constraint ensure_collections created before #2171.
    feeds.add_persistent_index(fields=["token"], unique=True)
    legacy_tokens = {"legacy-a": "legacy-token-" + "a" * 30, "legacy-b": "legacy-token-" + "b" * 30}
    for key, raw in legacy_tokens.items():
        feeds.insert(
            {
                "_key": key,
                "tenant_key": TENANT,
                "name": key,
                "user_key": "owner",
                "token": raw,
                "filters": {"categories": [], "site_key": None},
                "is_active": True,
            }
        )
    migration = HashCalendarFeedTokensMigration()

    dry = migration.up(db, dry_run=True)
    assert dry.changed == 0
    assert dry.details["feeds_with_clear_token"] == 2
    assert dry.details["legacy_indexes"] == 1
    assert feeds.get("legacy-a")["token"] == legacy_tokens["legacy-a"]

    report = migration.up(db)

    assert not report.precondition_unmet
    assert report.details["feeds_hashed"] == 2
    assert report.details["legacy_indexes_dropped"] == 1
    assert report.changed == 3
    for key, raw in legacy_tokens.items():
        doc = feeds.get(key)
        assert raw not in json.dumps(doc)
        assert "token" not in doc
        assert doc["token_hash"] == _sha256(raw)
    assert not [idx for idx in feeds.indexes() if list(idx.get("fields") or []) == ["token"]]

    second = migration.up(db)
    assert (second.scanned, second.changed) == (0, 0)  # idempotent

    service = _service(db)
    for key, raw in legacy_tokens.items():
        assert service.generate_ical_for_feed(key, raw).startswith("BEGIN:VCALENDAR")
    # A new feed after the migration does not collide with the migrated ones.
    service.create_feed(_new_feed())
    assert feeds.count() == 3


def test_the_migration_creates_the_hash_index_itself_before_it_drops_the_old_one(db) -> None:
    """A volume whose boot did not create the ``token_hash`` index yet: never a window without a constraint."""
    from app.migrations.versions.v0090_hash_calendar_feed_tokens import (
        REPLACEMENT_INDEX,
        HashCalendarFeedTokensMigration,
    )

    feeds = db.collection(col.CALENDAR_FEEDS)
    for idx in feeds.indexes():
        if REPLACEMENT_INDEX.matches(idx):
            feeds.delete_index(idx["id"])
    feeds.add_persistent_index(fields=["token"], unique=True)
    feeds.insert({"_key": "legacy", "tenant_key": TENANT, "name": "legacy", "user_key": "owner", "token": "t" * 43})

    try:
        report = HashCalendarFeedTokensMigration().up(db)

        assert report.details["replacement_created"] is True
        assert report.details["legacy_indexes_dropped"] == 1
        assert report.changed == 3
        assert any(REPLACEMENT_INDEX.matches(idx) for idx in feeds.indexes())
        assert feeds.get("legacy")["token_hash"] == _sha256("t" * 43)
    finally:
        # Leave the module's database as ensure_collections builds it.
        if not any(REPLACEMENT_INDEX.matches(idx) for idx in feeds.indexes()):
            feeds.add_persistent_index(fields=list(REPLACEMENT_INDEX.fields), unique=True, sparse=True)
