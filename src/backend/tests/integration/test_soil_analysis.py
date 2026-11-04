"""WP 8.7 (#2650, GP-FR-122) — a soil analysis writes the bed's profile in its own transaction; the series read back.

The production writer (``ArangoCareEventRepository.insert`` -> ``write_care_event`` -> the profile update) and the
production reader (``SoilAnalysisService`` over ``list_events``) run on a real ArangoDB: the stored location document
is what changes, and what the series are built from is what was stored.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from app.common.exceptions import DuplicateError, NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.care_event import CareEvent
from app.domain.services.soil_analysis_service import SoilAnalysisService
from app.migrations.versions.v0105_soil_profile_ec_method_unknown import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the profile update is a stream transaction over a real server"),
]

_DB_NAME = run_database_name("soil_analysis")
NOW = datetime.now(UTC).replace(microsecond=0)


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    database.collection(col.SITES).insert({"_key": "S1", "tenant_key": "t1", "name": "Garden", "type": "outdoor"})
    database.collection(col.SITES).insert({"_key": "S2", "tenant_key": "t2", "name": "Other", "type": "outdoor"})
    database.collection(col.LOCATIONS).insert(
        {
            "_key": "L1",
            "site_key": "S1",
            "name": "Bed",
            "area_m2": 1.0,
            "location_type_key": "bed",
            "soil_profile": {"drainage": "good"},
        }
    )
    database.collection(col.LOCATIONS).insert(
        {"_key": "L2", "site_key": "S2", "name": "Foreign", "area_m2": 1.0, "location_type_key": "bed"}
    )
    yield database
    system.delete_database(_DB_NAME)


def _measure(parameter: str, value: float, unit: str, **extra) -> dict:  # type: ignore[no-untyped-def]
    return {"parameter": parameter, "value": value, "unit": unit, "source": "lab", **extra}


def _analysis(at: datetime, measurements: list[dict], **extra) -> CareEvent:  # type: ignore[no-untyped-def]
    return CareEvent(
        tenant_key="t1",
        site_key="S1",
        location_key="L1",
        category="soil_analysis",
        summary="Soil analysis",
        performed_at=at,
        measurements=measurements,
        **extra,
    )


def _profile(db) -> dict:  # type: ignore[no-untyped-def]
    return db.collection(col.LOCATIONS).get("L1")["soil_profile"]


def test_the_latest_values_land_in_the_profile_in_the_events_transaction(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoCareEventRepository(db)

    repo.insert(
        _analysis(
            NOW,
            [
                _measure("ph", 6.4, "pH", ph_method="cacl2"),
                _measure("ec", 1.1, "mS/cm", ec_method="ratio_1_5"),
                _measure("humus", 3.2, "%"),
                _measure("p", 12, "mg_per_100g", extraction_method="cal", content_class="C"),
            ],
        ),
        tenant_key="t1",
    )

    profile = _profile(db)
    assert (
        profile["ph"],
        profile["ph_method"],
        profile["ec_ms_cm"],
        profile["ec_method"],
        profile["humus_percent"],
    ) == (
        6.4,
        "cacl2",
        1.1,
        "ratio_1_5",
        3.2,
    )
    assert datetime.fromisoformat(profile["last_analysis_at"]) == NOW
    assert profile["drainage"] == "good"  # what the analysis does not carry is untouched
    assert db.collection(col.CARE_EVENTS).count() == 1


def test_an_older_analysis_does_not_overwrite_a_newer_state(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoCareEventRepository(db)
    repo.insert(_analysis(NOW, [_measure("ph", 6.4, "pH", ph_method="cacl2")]), tenant_key="t1")

    repo.insert(_analysis(NOW - timedelta(days=200), [_measure("ph", 5.1, "pH", ph_method="h2o")]), tenant_key="t1")

    profile = _profile(db)
    assert (profile["ph"], profile["ph_method"]) == (6.4, "cacl2")
    assert db.collection(col.CARE_EVENTS).count() == 2  # the old analysis is still on record
    # counter-case: a NEWER one does replace it, so the guard above is the age rule
    repo.insert(_analysis(NOW + timedelta(days=1), [_measure("ph", 6.9, "pH", ph_method="h2o")]), tenant_key="t1")
    assert (_profile(db)["ph"], _profile(db)["ph_method"]) == (6.9, "h2o")


def test_the_profile_and_the_event_stand_or_fall_together(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoCareEventRepository(db)
    marker = {"collection": "watering_events", "key": "taken"}
    repo.insert(
        CareEvent(
            tenant_key="t1",
            site_key="S1",
            location_key="L1",
            category="watering",
            summary="x",
            performed_at=NOW,
            source_ref=marker,
        ),
        tenant_key="t1",
    )

    with pytest.raises(DuplicateError):
        repo.insert(_analysis(NOW, [_measure("ph", 6.4, "pH")], source_ref=marker), tenant_key="t1")

    assert "ph" not in _profile(db)
    assert db.collection(col.CARE_EVENTS).count() == 1


def test_a_bed_that_is_gone_still_gets_its_event(db) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.LOCATIONS).delete("L1")

    ArangoCareEventRepository(db).insert(_analysis(NOW, [_measure("ph", 6.4, "pH")]), tenant_key="t1")

    assert db.collection(col.CARE_EVENTS).count() == 1


def _service(db) -> SoilAnalysisService:  # type: ignore[no-untyped-def]
    return SoilAnalysisService(ArangoSiteRepository(db), ArangoCareEventRepository(db))


def test_two_methods_are_two_series_with_the_change_marked_and_no_conversion(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoCareEventRepository(db)
    repo.insert(
        _analysis(NOW - timedelta(days=120), [_measure("ec", 0.8, "mS/cm", ec_method="ratio_1_5")]), tenant_key="t1"
    )
    repo.insert(
        _analysis(NOW - timedelta(days=60), [_measure("ec", 2.4, "mS/cm", ec_method="saturated_paste")]),
        tenant_key="t1",
    )

    result = _service(db).series("L1", tenant_key="t1", parameter="ec")

    assert [(s.method, [p.value for p in s.points]) for s in result.series] == [
        ("ratio_1_5", [0.8]),
        ("saturated_paste", [2.4]),
    ]
    assert [(c.from_method, c.to_method) for c in result.method_changes] == [("ratio_1_5", "saturated_paste")]
    assert result.truncated is False


def test_a_voided_analysis_is_not_in_the_series(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoCareEventRepository(db)
    kept = repo.insert(_analysis(NOW - timedelta(days=2), [_measure("ph", 6.1, "pH")]), tenant_key="t1")
    gone = repo.insert(_analysis(NOW - timedelta(days=1), [_measure("ph", 9.9, "pH")]), tenant_key="t1")
    repo.void(gone.key or "", tenant_key="t1", voided_by="u1", reason="typo", at=NOW)

    result = _service(db).series("L1", tenant_key="t1")

    assert [p.event_key for s in result.series for p in s.points] == [kept.key]
    # a taken-back analysis neither takes a place of the bounded read nor makes it look cut
    bounded = _service(db).series("L1", tenant_key="t1", limit=1)
    assert [p.event_key for s in bounded.series for p in s.points] == [kept.key] and bounded.truncated is False


def test_the_read_is_bounded_and_says_when_it_was_cut(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoCareEventRepository(db)
    for day in range(8):
        repo.insert(_analysis(NOW - timedelta(days=day + 1), [_measure("humus", 3.0 + day, "%")]), tenant_key="t1")

    result = _service(db).series("L1", tenant_key="t1", limit=5)

    assert result.analyses == 5 and result.truncated is True
    assert len(result.series[0].points) == 5
    assert [p.value for p in result.series[0].points][-1] == 3.0  # the newest five, oldest first
    assert _service(db).series("L1", tenant_key="t1", limit=500).truncated is False


def test_a_foreign_tenants_bed_is_a_404(db) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(NotFoundError):
        _service(db).series("L2", tenant_key="t1")
    with pytest.raises(NotFoundError):
        _service(db).series("L1", tenant_key="t2")
    with pytest.raises(NotFoundError):
        _service(db).series("nope", tenant_key="t1")


class TestMigrationEcMethodUnknown:
    def test_a_stored_conductivity_without_a_method_is_stamped_unknown_and_nothing_else_changes(self, db) -> None:  # type: ignore[no-untyped-def]
        locations = db.collection(col.LOCATIONS)
        locations.insert({"_key": "legacy", "site_key": "S1", "soil_profile": {"ec_ms_cm": 1.4, "drainage": "poor"}})
        locations.insert({"_key": "ready", "site_key": "S1", "soil_profile": {"ec_ms_cm": 1.4, "ec_method": "sensor"}})
        locations.insert({"_key": "noec", "site_key": "S1", "soil_profile": {"ph": 6.5}})
        locations.insert({"_key": "noprofile", "site_key": "S1"})

        dry = migration.up(db, dry_run=True)
        assert dry.details["will_stamp"] == 1 and locations.get("legacy")["soil_profile"].get("ec_method") is None
        first = migration.up(db)
        second = migration.up(db)

        assert first.changed == 1 and second.changed == 0
        assert locations.get("legacy")["soil_profile"] == {"ec_ms_cm": 1.4, "drainage": "poor", "ec_method": "unknown"}
        assert locations.get("ready")["soil_profile"]["ec_method"] == "sensor"
        assert "ec_method" not in locations.get("noec")["soil_profile"]


def test_only_the_soil_analysis_transaction_declares_the_locations_collection() -> None:
    """A care event that is no soil analysis writes no bed, so its transaction must not need the collection."""
    from arango.exceptions import TransactionInitError

    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    name = run_database_name("soil_analysis_no_locations")
    if system.has_database(name):
        system.delete_database(name)
    system.create_database(name)
    try:
        bare = client.db(name, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
        for collection in (col.CARE_EVENTS, col.USERS, col.PLANT_INSTANCES):
            bare.create_collection(collection)
        for edge in (col.CARE_EVENT_AT, col.CARE_EVENT_FOR, col.TASK_LOGGED_AS):
            bare.create_collection(edge, edge=True)
        repo = ArangoCareEventRepository(bare)

        plain = repo.insert(
            CareEvent(
                tenant_key="t1", site_key="S1", location_key="L1", category="watering", summary="x", performed_at=NOW
            ),
            tenant_key="t1",
        )
        many = repo.insert_many(
            [
                CareEvent(
                    tenant_key="t1", site_key="S1", location_key="L1", category="note", summary="y", performed_at=NOW
                )
            ],
            tenant_key="t1",
        )

        assert plain.key and len(many) == 1
        # counter-case: a soil analysis does declare it (the bed profile is written there)
        with pytest.raises(TransactionInitError):
            repo.insert(_analysis(NOW, [_measure("ph", 6.4, "pH")]), tenant_key="t1")
    finally:
        system.delete_database(name)
