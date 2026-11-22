"""WP 8.3 (#2646, GP-FR-106) — a care confirmation and its care event in ONE transaction, on a real ArangoDB.

The production writer (``create_confirmation_logged``) and the production reader of the bed log
(``ArangoCareEventRepository.list_events``) are exercised on the stored shapes; the M4 migration and the
consistency job must find the live event as already logged (the shared ``source_ref`` marker), and must backfill the
confirmations that have none, which carry no ``tenant_key`` at all.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from app.common.enums import ConfirmAction, ReminderType
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_gap_repository import ArangoCareEventGapReader
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository
from app.data_access.arango.collections import ensure_collections
from app.domain.engines.care_event_backfill_mapper import BedAnchor, map_document
from app.domain.interfaces.care_event_repository import CareEventFilter
from app.domain.models.care_reminder import CareConfirmation
from app.domain.services.care_event_consistency_service import CareEventConsistencyService
from app.migrations.versions.v0104_care_events_backfill import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the confirmation and its event are one stream transaction over a real server"),
]

_DB_NAME = run_database_name("care_confirmation_event")
NOW = datetime.now(UTC)
RECENT = (NOW - timedelta(days=2)).isoformat()
ANCHOR = BedAnchor(tenant_key="t1", site_key="S1", location_key="L1", plant_keys=("p1",))


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    database.collection(col.SITES).insert({"_key": "S1", "tenant_key": "t1"})
    database.collection(col.LOCATIONS).insert({"_key": "L1", "site_key": "S1"})
    database.collection(col.PLANT_INSTANCES).insert(
        {"_key": "p1", "instance_id": "P1", "tenant_key": "t1", "location_key": "L1", "site_key": "S1"}
    )
    database.collection(col.PLANT_INSTANCES).insert({"_key": "house", "instance_id": "H1", "tenant_key": "t1"})
    database.collection(col.CARE_PROFILES).insert({"_key": "cp1", "plant_key": "p1"})
    yield database
    system.delete_database(_DB_NAME)


def _confirmation(plant_key: str = "p1") -> CareConfirmation:
    return CareConfirmation(
        plant_key=plant_key,
        care_profile_key="cp1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=NOW,
    )


def _event_for(performed_at: datetime = NOW):  # type: ignore[no-untyped-def]
    return lambda key: map_document(
        "care_confirmations",
        {"_key": key, "reminder_type": "watering"},
        ANCHOR,
        performed_at,
        trigger="reminder",
        performed_by_user_key="u1",
    )


def test_one_confirmation_writes_exactly_one_event_with_the_confirmations_key(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoCareReminderRepository(db)

    stored = repo.create_confirmation_logged(_confirmation(), profile_key="cp1", plant_key="p1", event_for=_event_for())

    events = list(db.collection(col.CARE_EVENTS).all())
    assert len(events) == 1 and db.collection(col.CARE_CONFIRMATIONS).count() == 1
    assert events[0]["source_ref"] == {"collection": "care_confirmations", "key": stored.key}
    assert (events[0]["trigger"], events[0]["category"], events[0]["performed_by_user_key"]) == (
        "reminder",
        "watering",
        "u1",
    )
    # the edges of the confirmation and of the event
    assert db.collection(col.CONFIRMS_CARE).count() == 1
    assert db.collection(col.CARE_EVENT_AT).count() == 1
    # read back through the production read path of the bed log
    rows = ArangoCareEventRepository(db).list_events(
        CareEventFilter(location_key="L1"), tenant_key="t1", offset=0, limit=10
    )
    assert [row.event.trigger for row in rows] == ["reminder"]


def test_a_plant_without_a_bed_stores_the_confirmation_and_no_event(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoCareReminderRepository(db)

    repo.create_confirmation_logged(
        _confirmation("house"), profile_key="cp1", plant_key="house", event_for=lambda _k: None
    )

    assert db.collection(col.CARE_CONFIRMATIONS).count() == 1
    assert db.collection(col.CARE_EVENTS).count() == 0


def test_an_aborted_transaction_writes_neither(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoCareReminderRepository(db)

    def refuses(_key: str):  # type: ignore[no-untyped-def]
        raise RuntimeError("the event could not be built")

    with pytest.raises(RuntimeError):
        repo.create_confirmation_logged(_confirmation(), profile_key="cp1", plant_key="p1", event_for=refuses)

    assert db.collection(col.CARE_CONFIRMATIONS).count() == 0
    assert db.collection(col.CARE_EVENTS).count() == 0
    assert db.collection(col.CONFIRMS_CARE).count() == 0
    # counter-case: the same call that does not refuse writes both, so the zero above is the abort
    repo.create_confirmation_logged(_confirmation(), profile_key="cp1", plant_key="p1", event_for=_event_for())
    assert (db.collection(col.CARE_CONFIRMATIONS).count(), db.collection(col.CARE_EVENTS).count()) == (1, 1)


def test_the_job_and_the_migration_find_the_live_event_already_logged(db) -> None:  # type: ignore[no-untyped-def]
    ArangoCareReminderRepository(db).create_confirmation_logged(
        _confirmation(), profile_key="cp1", plant_key="p1", event_for=_event_for()
    )
    service = CareEventConsistencyService(ArangoCareEventGapReader(db), ArangoCareEventRepository(db), lambda _t: True)

    job = service.run(now=NOW, window_days=7)
    dry = migration.up(db, dry_run=True)

    assert job.hits == 0 and job.already_present == 1
    confirmations = dry.details["sources"]["care_confirmations"]
    assert (confirmations["read"], confirmations["already_present"], confirmations["will_write"]) == (1, 1, 0)


def test_confirmations_without_an_event_are_backfilled_and_only_the_performed_ones(db) -> None:  # type: ignore[no-untyped-def]
    confirmations = db.collection(col.CARE_CONFIRMATIONS)
    base = {"care_profile_key": "cp1", "reminder_type": "watering", "confirmed_at": RECENT}
    confirmations.insert_many(
        [
            {"_key": "c_done", "plant_key": "p1", "action": "confirmed", **base},
            {"_key": "c_skipped", "plant_key": "p1", "action": "skipped", **base},
            {"_key": "c_snoozed", "plant_key": "p1", "action": "snoozed", **base},
            {"_key": "c_house", "plant_key": "house", "action": "confirmed", **base},
            {"_key": "c_type", "plant_key": "p1", "action": "confirmed", **(base | {"reminder_type": "new_type"})},
        ]
    )

    report = migration.up(db)

    entry = report.details["sources"]["care_confirmations"]
    assert entry["read"] == 3  # skipped and snoozed are not a performed care and are not read
    assert entry["will_write"] == 1
    assert entry["without_bed_reasons"]["unresolved"]["listed"] == ["c_house"]
    assert entry["without_bed_reasons"]["unmapped_category"]["listed"] == ["c_type"]
    stored = [e for e in db.collection(col.CARE_EVENTS).all() if e["source_ref"]["collection"] == "care_confirmations"]
    assert [(e["source_ref"]["key"], e["trigger"], e["tenant_key"], e["plant_keys"]) for e in stored] == [
        ("c_done", "backfill", "t1", ["p1"])
    ]
    assert "performed_by_user_key" not in stored[0]
    # a second run writes nothing: the unstamped confirmation is found present through its plant's tenant
    assert migration.up(db).details["sources"]["care_confirmations"]["already_present"] == 1
