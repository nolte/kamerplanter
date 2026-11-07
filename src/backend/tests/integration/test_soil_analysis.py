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
from app.data_access.arango.task_completion_repository import ArangoTaskCompletionRepository
from app.domain.models.care_event import CareEvent
from app.domain.models.task_completion import CompletionWrite, UndoWrite
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


class TestTheProfileFollowsVoidAndCorrection:
    """#2706 (operator default from #2643): a void or a correction derives the profile again from the open analyses."""

    def test_voiding_the_newest_analysis_brings_back_the_one_before(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        repo.insert(_analysis(NOW - timedelta(days=2), [_measure("ph", 6.1, "pH", ph_method="cacl2")]), tenant_key="t1")
        gone = repo.insert(
            _analysis(NOW - timedelta(days=1), [_measure("ph", 9.9, "pH", ph_method="h2o")]), tenant_key="t1"
        )
        assert _profile(db)["ph"] == 9.9  # positive control: the newest one did land

        repo.void(gone.key or "", tenant_key="t1", voided_by="u1", reason="typo", at=NOW)

        profile = _profile(db)
        assert (profile["ph"], profile["ph_method"]) == (6.1, "cacl2")
        assert datetime.fromisoformat(profile["last_analysis_at"]) == NOW - timedelta(days=2)
        assert profile["drainage"] == "good"

    def test_the_undo_of_the_only_analysis_clears_the_measured_values_and_keeps_the_hand_fields(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        only = repo.insert(
            _analysis(
                NOW, [_measure("ph", 6.4, "pH", ph_method="cacl2"), _measure("ec", 1.1, "mS/cm", ec_method="sensor")]
            ),
            tenant_key="t1",
        )

        repo.void(only.key or "", tenant_key="t1", voided_by="u1", reason="undo", at=NOW)

        assert _profile(db) == {"drainage": "good", "hand_values": {}}

    def test_a_correction_that_drops_a_parameter_takes_its_value_out(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        repo.insert(_analysis(NOW - timedelta(days=2), [_measure("humus", 3.0, "%")]), tenant_key="t1")
        wrong = repo.insert(
            _analysis(
                NOW - timedelta(days=1),
                [_measure("ph", 6.5, "pH", ph_method="cacl2"), _measure("ec", 1.0, "mS/cm", ec_method="sensor")],
            ),
            tenant_key="t1",
        )
        assert _profile(db)["ec_ms_cm"] == 1.0

        repo.supersede(
            wrong.key or "",
            _analysis(
                NOW - timedelta(days=1), [_measure("ph", 6.6, "pH", ph_method="cacl2")], supersedes_key=wrong.key
            ),
            tenant_key="t1",
        )

        profile = _profile(db)
        assert "ec_ms_cm" not in profile and "ec_method" not in profile
        assert (profile["ph"], profile["humus_percent"]) == (6.6, 3.0)

    def test_a_correction_to_an_earlier_date_moves_last_analysis_at_back(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        repo.insert(_analysis(NOW - timedelta(days=10), [_measure("ph", 6.0, "pH")]), tenant_key="t1")
        late = repo.insert(_analysis(NOW - timedelta(days=1), [_measure("ph", 6.8, "pH")]), tenant_key="t1")

        repo.supersede(
            late.key or "",
            _analysis(NOW - timedelta(days=20), [_measure("ph", 6.7, "pH")], supersedes_key=late.key),
            tenant_key="t1",
        )

        profile = _profile(db)
        assert profile["ph"] == 6.0
        assert datetime.fromisoformat(profile["last_analysis_at"]) == NOW - timedelta(days=10)
        # an analysis between the two dates is newer than the profile now and is no longer refused
        repo.insert(_analysis(NOW - timedelta(days=5), [_measure("ph", 6.3, "pH")]), tenant_key="t1")
        assert _profile(db)["ph"] == 6.3

    def test_correcting_the_newest_analysis_at_the_same_instant_refreshes_the_profile(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        repo.insert(_analysis(NOW - timedelta(days=3), [_measure("ph", 5.9, "pH")]), tenant_key="t1")
        newest = repo.insert(_analysis(NOW, [_measure("ph", 6.4, "pH", ph_method="cacl2")]), tenant_key="t1")

        repo.supersede(
            newest.key or "",
            _analysis(NOW, [_measure("ph", 6.5, "pH", ph_method="h2o")], supersedes_key=newest.key),
            tenant_key="t1",
        )

        profile = _profile(db)
        assert (profile["ph"], profile["ph_method"]) == (6.5, "h2o")
        assert datetime.fromisoformat(profile["last_analysis_at"]) == NOW
        assert db.collection(col.CARE_EVENTS).get(newest.key)["superseded_by_key"]

    def test_a_batch_insert_writes_the_profile_like_a_single_insert(self, db) -> None:  # type: ignore[no-untyped-def]
        ArangoCareEventRepository(db).insert_many([_analysis(NOW, [_measure("ph", 6.2, "pH")])], tenant_key="t1")

        assert _profile(db)["ph"] == 6.2

    def test_an_unreadable_stored_instant_does_not_lock_the_profile(self, db) -> None:  # type: ignore[no-untyped-def]
        db.collection(col.LOCATIONS).update({"_key": "L1", "soil_profile": {"last_analysis_at": "garbage"}})

        ArangoCareEventRepository(db).insert(_analysis(NOW, [_measure("ph", 6.2, "pH")]), tenant_key="t1")

        assert _profile(db)["ph"] == 6.2


class TestTaskCompletionWithASoilAnalysis:
    """#2706 item 4: the completion of a soil-analysis task declares ``locations`` and writes the profile."""

    @staticmethod
    def _task(db) -> None:  # type: ignore[no-untyped-def]
        db.collection(col.TASKS).insert(
            {"_key": "T1", "tenant_key": "t1", "name": "Soil test", "status": "pending", "category": "soil_analysis"}
        )

    @staticmethod
    def _completion(measurements: list[dict], **extra) -> CompletionWrite:  # type: ignore[no-untyped-def]
        return CompletionWrite(
            task_key="T1",
            task_patch={"status": "completed", "completed_at": NOW.isoformat()},
            event=_analysis(NOW, measurements, task_key="T1", trigger="task"),
            **extra,
        )

    def test_the_completion_writes_the_profile_and_the_undo_takes_it_back(self, db) -> None:  # type: ignore[no-untyped-def]
        self._task(db)
        repo = ArangoTaskCompletionRepository(db)

        (done,) = repo.complete([self._completion([_measure("ph", 6.4, "pH", ph_method="cacl2")])], tenant_key="t1")

        assert (_profile(db)["ph"], db.collection(col.TASKS).get("T1")["status"]) == (6.4, "completed")
        repo.reopen(
            UndoWrite(
                task_key="T1",
                task_patch={"status": "pending", "completed_at": None},
                event_key=done.event_key,
                voided_by="u1",
                voided_at=NOW,
            ),
            tenant_key="t1",
        )
        assert _profile(db) == {"drainage": "good", "hand_values": {}}

    def test_a_re_completion_that_drops_a_parameter_derives_the_profile_again(self, db) -> None:  # type: ignore[no-untyped-def]
        self._task(db)
        repo = ArangoTaskCompletionRepository(db)
        (first,) = repo.complete(
            [self._completion([_measure("ph", 6.4, "pH"), _measure("humus", 4.0, "%")])], tenant_key="t1"
        )
        db.collection(col.TASKS).update({"_key": "T1", "status": "pending"})  # a plain reopen: the line stays

        repo.complete(
            [self._completion([_measure("ph", 6.9, "pH")], replaces_event_key=first.event_key)], tenant_key="t1"
        )

        profile = _profile(db)
        assert profile["ph"] == 6.9 and "humus_percent" not in profile
        assert db.collection(col.CARE_EVENTS).get(first.event_key)["void_reason"] == "reopened"


class TestOneWriteModelWithProvenance:
    """#2706 review: one write path (store = re-derive) and provenance, so a void never takes a hand value."""

    def test_a_late_older_analysis_fills_a_gap_alike_on_insert_and_on_rederive(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        repo.insert(_analysis(NOW, [_measure("ph", 6.4, "pH", ph_method="cacl2")]), tenant_key="t1")

        repo.insert(
            _analysis(NOW - timedelta(days=30), [_measure("ph", 5.0, "pH"), _measure("humus", 3.5, "%")]),
            tenant_key="t1",
        )
        on_insert = _profile(db)
        other = repo.insert(_analysis(NOW - timedelta(days=60), [_measure("caco3", 1.0, "%")]), tenant_key="t1")
        repo.void(other.key or "", tenant_key="t1", voided_by="u1", reason="typo", at=NOW)

        assert (on_insert["ph"], on_insert["humus_percent"]) == (6.4, 3.5)  # the gap filled, the newer pH kept
        assert datetime.fromisoformat(on_insert["last_analysis_at"]) == NOW
        assert _profile(db) == on_insert  # the re-derivation after a void reaches the very same profile

    def test_a_hand_ph_survives_voiding_an_unrelated_humus_analysis(self, db) -> None:  # type: ignore[no-untyped-def]
        entry = {"value": 6.0, "method": "h2o", "at": (NOW - timedelta(days=10)).isoformat()}
        db.collection(col.LOCATIONS).update(
            {
                "_key": "L1",
                "soil_profile": {"drainage": "good", "ph": 6.0, "ph_method": "h2o", "hand_values": {"ph": entry}},
            }
        )
        repo = ArangoCareEventRepository(db)
        humus = repo.insert(_analysis(NOW, [_measure("humus", 3.0, "%")]), tenant_key="t1")
        assert _profile(db)["humus_percent"] == 3.0  # positive control: the analysis landed

        repo.void(humus.key or "", tenant_key="t1", voided_by="u1", reason="typo", at=NOW)

        assert _profile(db) == {"drainage": "good", "ph": 6.0, "ph_method": "h2o", "hand_values": {"ph": entry}}

    def test_a_hand_ph_on_a_row_from_before_the_entries_survives_too(self, db) -> None:  # type: ignore[no-untyped-def]
        db.collection(col.LOCATIONS).update({"_key": "L1", "soil_profile": {"ph": 6.0}})  # merged: drainage stays
        repo = ArangoCareEventRepository(db)
        humus = repo.insert(_analysis(NOW, [_measure("humus", 3.0, "%")]), tenant_key="t1")

        repo.void(humus.key or "", tenant_key="t1", voided_by="u1", reason="typo", at=NOW)

        profile = _profile(db)
        assert (profile["ph"], "humus_percent" in profile) == (6.0, False)
        assert profile["hand_values"]["ph"]["at"].startswith("0001-01-01")  # classified once, at the oldest instant

    def test_a_legacy_value_an_analysis_measured_goes_with_that_analysis(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        old = repo.insert(_analysis(NOW, [_measure("ph", 9.9, "pH")]), tenant_key="t1")
        db.collection(col.LOCATIONS).update(  # what a pre-#2706 forward write left: the value, no entries
            {"_key": "L1", "soil_profile": {"ph": 9.9, "humus_percent": 4.0}}, merge=False
        )

        repo.void(old.key or "", tenant_key="t1", voided_by="u1", reason="typo", at=NOW)

        profile = _profile(db)
        assert "ph" not in profile and profile["humus_percent"] == 4.0

    def test_the_ph_of_a_voided_analysis_is_still_removed(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        only = repo.insert(_analysis(NOW, [_measure("ph", 9.9, "pH", ph_method="cacl2")]), tenant_key="t1")
        assert _profile(db)["ph"] == 9.9

        repo.void(only.key or "", tenant_key="t1", voided_by="u1", reason="typo", at=NOW)

        profile = _profile(db)
        assert "ph" not in profile and "ph_method" not in profile and "last_analysis_at" not in profile

    def test_every_derivation_writes_the_bed_so_concurrent_ones_conflict(self, db) -> None:  # type: ignore[no-untyped-def]
        """M1: an unchanged profile still moves ``soil_profile_rev``, so two derivations collide on the bed."""
        repo = ArangoCareEventRepository(db)
        repo.insert(_analysis(NOW, [_measure("ph", 6.4, "pH")]), tenant_key="t1")
        before = db.collection(col.LOCATIONS).get("L1")
        repo.insert(
            _analysis(NOW - timedelta(days=90), [_measure("ph", 5.0, "pH")]), tenant_key="t1"
        )  # changes nothing

        after = db.collection(col.LOCATIONS).get("L1")
        assert after["soil_profile"] == before["soil_profile"]
        assert after["soil_profile_rev"] == before["soil_profile_rev"] + 1

    def test_two_concurrent_derivations_of_one_bed_conflict(self, db) -> None:  # type: ignore[no-untyped-def]
        from app.common.exceptions import WriteConflictError
        from app.data_access.arango.care_event_repository import rederive_soil_profile
        from app.data_access.arango.transactions import stream_transaction

        ArangoCareEventRepository(db).insert(_analysis(NOW, [_measure("ph", 6.4, "pH")]), tenant_key="t1")
        write, read = (col.LOCATIONS,), (col.SITES, col.CARE_EVENTS)  # both derive the same, unchanged profile
        with stream_transaction(db, write=write, read=read, entity="care_event") as first:
            rederive_soil_profile(first, "L1", tenant_key="t1")
            with (
                pytest.raises(WriteConflictError),
                stream_transaction(db, write=write, read=read, entity="care_event") as second,
            ):
                rederive_soil_profile(second, "L1", tenant_key="t1")

    def test_a_bed_of_another_tenants_site_is_not_written(self, db) -> None:  # type: ignore[no-untyped-def]
        # L2 sits on t2's site; an event stamped t1 that names it must not reach its profile (defence in depth)
        ArangoCareEventRepository(db).insert(
            _analysis(NOW, [_measure("ph", 6.4, "pH")]).model_copy(update={"location_key": "L2"}), tenant_key="t1"
        )

        assert db.collection(col.LOCATIONS).get("L2").get("soil_profile") is None
        assert db.collection(col.CARE_EVENTS).count() == 1  # the event is still the record

    def test_unit_spellings_land_in_one_series(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        for days, unit in ((3, "mS/cm"), (2, " ms/cm"), (1, "dS/m")):
            repo.insert(
                _analysis(NOW - timedelta(days=days), [_measure("ec", 1.0 + days, unit, ec_method="sensor")]),
                tenant_key="t1",
            )

        result = _service(db).series("L1", tenant_key="t1", parameter="ec")

        assert [(s.method, s.unit, len(s.points)) for s in result.series] == [("sensor", "mS/cm", 3)]


class TestHandEntriesThroughThePatch:
    """#2706 re-review: per field the newest observation wins - hand edits through ``PATCH /locations`` vs. analyses."""

    @staticmethod
    def _patch(db, soil: dict | None) -> None:  # type: ignore[no-untyped-def]
        from app.common.enums import TenantRole
        from app.data_access.arango.garden_object_repository import ArangoGardenObjectRepository
        from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
        from app.domain.models.garden_plan import LocationPatch
        from app.domain.services.garden_plan_service import GardenPlanService
        from app.domain.services.garden_resource_service import GardenResourceService

        sites, plans = ArangoSiteRepository(db), ArangoGardenPlanRepository(db)
        service = GardenResourceService(sites, plans, ArangoGardenObjectRepository(db), GardenPlanService(sites, plans))
        service.patch_location(
            "L1",
            tenant_key="t1",
            user_key="u1",
            role=TenantRole.GROWER,
            patch=LocationPatch.model_validate({"soil_profile": soil}),
        )

    @staticmethod
    def _echo(db, **changes) -> dict:  # type: ignore[no-untyped-def]
        """What a client sends back: the stored profile without the server-owned entries, with ``changes``."""
        stored = {k: v for k, v in _profile(db).items() if k != "hand_values"}
        return {**stored, **changes}

    def test_voiding_a_newer_analysis_returns_to_the_hand_value(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        repo.insert(
            _analysis(NOW - timedelta(days=30), [_measure("ph", 6.0, "pH", ph_method="cacl2")]), tenant_key="t1"
        )
        self._patch(db, self._echo(db, ph=6.5, ph_method="h2o"))  # H, now
        newer = repo.insert(
            _analysis(NOW + timedelta(days=1), [_measure("ph", 6.9, "pH", ph_method="cacl2")]), tenant_key="t1"
        )
        assert _profile(db)["ph"] == 6.9  # positive control: the newer analysis wins over the hand value

        repo.void(newer.key or "", tenant_key="t1", voided_by="u1", reason="typo", at=NOW)

        assert (_profile(db)["ph"], _profile(db)["ph_method"]) == (6.5, "h2o")  # H, not the older analysis A

    def test_a_ph_cleared_by_hand_survives_an_unrelated_analysis(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        repo.insert(_analysis(NOW - timedelta(days=30), [_measure("ph", 6.0, "pH")]), tenant_key="t1")
        self._patch(db, self._echo(db, ph=None, ph_method=None))

        repo.insert(_analysis(NOW - timedelta(days=1), [_measure("humus", 3.0, "%")]), tenant_key="t1")

        profile = _profile(db)
        assert profile.get("ph") is None and profile["humus_percent"] == 3.0

    def test_the_hand_times_are_per_field(self, db) -> None:  # type: ignore[no-untyped-def]
        repo = ArangoCareEventRepository(db)
        self._patch(db, self._echo(db, ph=6.5))
        db.collection(col.LOCATIONS).update(  # the pH was entered a month ago
            {"_key": "L1", "soil_profile": {"hand_values": {"ph": {"at": (NOW - timedelta(days=30)).isoformat()}}}}
        )
        self._patch(db, self._echo(db, humus_percent=4.0))  # a humus edit now

        repo.insert(
            _analysis(NOW - timedelta(days=10), [_measure("ph", 6.9, "pH"), _measure("humus", 3.0, "%")]),
            tenant_key="t1",
        )

        profile = _profile(db)
        assert (profile["ph"], profile["humus_percent"]) == (6.9, 4.0)  # the humus edit did not protect the pH

    def test_a_stale_last_analysis_at_is_a_409_and_a_matching_or_absent_one_is_not(self, db) -> None:  # type: ignore[no-untyped-def]
        from app.common.exceptions import PlanError

        repo = ArangoCareEventRepository(db)
        repo.insert(_analysis(NOW - timedelta(days=30), [_measure("ph", 6.0, "pH")]), tenant_key="t1")
        read_before = self._echo(db)  # an open form
        repo.insert(_analysis(NOW - timedelta(days=1), [_measure("ph", 6.6, "pH")]), tenant_key="t1")

        with pytest.raises(PlanError) as stale:
            self._patch(db, {**read_before, "drainage": "poor"})
        assert stale.value.status_code == 409 and stale.value.error_code == "soil_profile.stale"
        assert _profile(db)["ph"] == 6.6 and "ph" not in _profile(db)["hand_values"]  # nothing was written

        self._patch(db, self._echo(db, drainage="poor"))  # matching
        without = {k: v for k, v in self._echo(db, drainage="moderate").items() if k != "last_analysis_at"}
        self._patch(db, without)  # absent: no check

        profile = _profile(db)
        assert (profile["drainage"], profile["ph"]) == ("moderate", 6.6)
        assert datetime.fromisoformat(profile["last_analysis_at"]) == NOW - timedelta(days=1)


class TestThePatchGoesThroughTheDerivation:
    """#2706 third review: PATCH records hand entries and runs the one derivation in its own transaction."""

    @staticmethod
    def _plan_repo(db):  # type: ignore[no-untyped-def]
        from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository

        return ArangoGardenPlanRepository(db)

    def test_a_patch_and_a_concurrent_analysis_insert_conflict_instead_of_overwriting(self, db) -> None:  # type: ignore[no-untyped-def]
        from app.common.exceptions import WriteConflictError
        from app.data_access.arango.care_event_repository import (
            SOIL_ANALYSIS_WRITE_COLLECTIONS,
            SOIL_PROFILE_READ_COLLECTIONS,
            rederive_soil_profile,
            write_care_event,
        )
        from app.data_access.arango.transactions import stream_transaction
        from app.domain.interfaces.garden_plan_repository import SoilProfileEdit

        ArangoCareEventRepository(db).insert(_analysis(NOW, [_measure("ph", 6.9, "pH")]), tenant_key="t1")
        before = _profile(db)
        edit = SoilProfileEdit(tenant_key="t1", profile={"drainage": "good", "ph": 6.0, "ph_method": "h2o"})
        with stream_transaction(
            db, write=SOIL_ANALYSIS_WRITE_COLLECTIONS, read=SOIL_PROFILE_READ_COLLECTIONS, entity="care_event"
        ) as insert:
            # an older analysis: its derivation changes nothing, and it must still take the bed (M1)
            write_care_event(insert, _analysis(NOW - timedelta(days=9), [_measure("ph", 5.0, "pH")]), NOW.isoformat())
            rederive_soil_profile(insert, "L1", tenant_key="t1")
            with pytest.raises(WriteConflictError):
                self._plan_repo(db).update_location_fields("L1", {}, soil=edit)

        assert _profile(db) == before  # the insert committed, the PATCH wrote nothing and was told so

    def test_a_drainage_patch_on_a_legacy_row_creates_no_hand_entry_and_a_void_clears_the_analysis_value(
        self, db
    ) -> None:  # type: ignore[no-untyped-def]
        from app.domain.interfaces.garden_plan_repository import SoilProfileEdit

        repo = ArangoCareEventRepository(db)
        only = repo.insert(_analysis(NOW, [_measure("ph", 6.4, "pH")]), tenant_key="t1")
        db.collection(col.LOCATIONS).update(  # a pre-#2706 row: the forward write's value, no entries
            {"_key": "L1", "soil_profile": {"ph": 6.4, "drainage": "good"}}, merge=False
        )

        self._plan_repo(db).update_location_fields(
            "L1", {}, soil=SoilProfileEdit(tenant_key="t1", profile={"ph": 6.4, "drainage": "poor"})
        )
        patched = _profile(db)
        repo.void(only.key or "", tenant_key="t1", voided_by="u1", reason="typo", at=NOW)

        assert (patched["drainage"], patched["ph"], patched["hand_values"]) == ("poor", 6.4, {})
        assert "ph" not in _profile(db) and _profile(db)["drainage"] == "poor"

    def test_an_echoed_legacy_hand_value_the_derivation_replaces_is_not_a_hand_edit(self, db) -> None:  # type: ignore[no-untyped-def]
        """Review of 7773667d8: the legacy row's pH 6.0 was a hand value; an open analysis measured 7.0 (newer than the
        legacy instant), so the derivation shows 7.0. A PATCH that changes only the drainage and echoes the 6.0 it
        read must not turn the 6.0 into a hand entry at now and displace the analysis."""
        from app.domain.interfaces.garden_plan_repository import SoilProfileEdit

        repo = ArangoCareEventRepository(db)
        repo.insert(_analysis(NOW - timedelta(days=3), [_measure("ph", 7.0, "pH")]), tenant_key="t1")
        db.collection(col.LOCATIONS).update(  # a pre-#2706 row: a hand pH no analysis measured, no entries
            {"_key": "L1", "soil_profile": {"ph": 6.0, "drainage": "good"}}, merge=False
        )

        self._plan_repo(db).update_location_fields(
            "L1", {}, soil=SoilProfileEdit(tenant_key="t1", profile={"ph": 6.0, "drainage": "poor"})
        )

        profile = _profile(db)
        assert (profile["drainage"], profile["ph"]) == ("poor", 7.0)
        assert (
            "ph" not in profile["hand_values"]
            or profile["hand_values"]["ph"]["value"] != 6.0
            or (datetime.fromisoformat(profile["hand_values"]["ph"]["at"]) < NOW - timedelta(days=3))
        )

    def test_a_hand_override_moves_last_analysis_at_to_the_newest_analysis_that_still_wins(self, db) -> None:  # type: ignore[no-untyped-def]
        from app.domain.interfaces.garden_plan_repository import SoilProfileEdit

        repo = ArangoCareEventRepository(db)
        repo.insert(_analysis(NOW - timedelta(days=40), [_measure("humus", 3.0, "%")]), tenant_key="t1")
        repo.insert(_analysis(NOW - timedelta(days=30), [_measure("ph", 6.0, "pH")]), tenant_key="t1")
        assert datetime.fromisoformat(_profile(db)["last_analysis_at"]) == NOW - timedelta(days=30)

        sent = {k: v for k, v in _profile(db).items() if k not in ("hand_values", "last_analysis_at")}
        self._plan_repo(db).update_location_fields(
            "L1", {}, soil=SoilProfileEdit(tenant_key="t1", profile={**sent, "ph": 6.6})
        )

        profile = _profile(db)
        assert (profile["ph"], profile["humus_percent"]) == (6.6, 3.0)
        assert datetime.fromisoformat(profile["last_analysis_at"]) == NOW - timedelta(days=40)

    def test_a_derived_profile_the_model_refuses_aborts_the_void(self, db) -> None:  # type: ignore[no-untyped-def]
        from app.common.exceptions import PlanError

        repo = ArangoCareEventRepository(db)
        analysis = repo.insert(_analysis(NOW - timedelta(days=5), [_measure("humus", 3.0, "%")]), tenant_key="t1")
        broken = {"value": 1.2, "method": None, "at": NOW.isoformat()}  # a conductivity without its method
        db.collection(col.LOCATIONS).update({"_key": "L1", "soil_profile": {"hand_values": {"ec_ms_cm": broken}}})

        with pytest.raises(PlanError) as refused:
            repo.void(analysis.key or "", tenant_key="t1", voided_by="u1", reason="typo", at=NOW)

        assert refused.value.status_code == 422 and refused.value.error_code == "soil_profile.derivation_invalid"
        assert "1.2" not in str(refused.value.details)  # names the field, never a value
        assert db.collection(col.CARE_EVENTS).get(analysis.key).get("voided_at") is None  # the void was rolled back
