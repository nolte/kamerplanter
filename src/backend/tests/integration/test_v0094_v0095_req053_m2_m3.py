"""#2325 (REQ-053 M2 + M3) — v0094 and v0095 measured on a real ArangoDB.

* v0094 stamps ``is_bed`` / ``supports_layout`` on the stored location types that lack
  them — the bed and layout keys ``true``, every other key and a user type ``false`` — and
  keeps a flag a row already carries; the seed job that runs right after it inserts the
  four new bed seeds with both flags and never touches the stamped rows;
* v0095 stamps ``suggested = false`` on every stored task without it, so the AQL filter
  the queue will use (``suggested == false``) sees the legacy rows;
* a second run of either changes no document (``_rev`` stays), a dry run writes nothing.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0094_v0095_req053_m2_m3.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.migrations.seed_location_types import seed_location_types
from app.migrations.versions.v0094_location_type_bed_flags import migration as m2
from app.migrations.versions.v0095_task_suggested_flag import migration as m3
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migrations' scans and UPDATE statements are AQL over a real server"),
]

_DB_NAME = run_database_name("v0094_v0095_req053_m2_m3")

#: The 12 seeds as the loader wrote them before the flags existed.
_PRE_M2_SEEDS = (
    "zone",
    "home",
    "garden",
    "greenhouse",
    "building",
    "room",
    "balcony",
    "terrace",
    "tent",
    "bed",
    "shelf",
    "container",
)


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    yield database
    system.delete_database(_DB_NAME)


def _pre_m2_types(db) -> None:  # type: ignore[no-untyped-def]
    types = db.collection(col.LOCATION_TYPES)
    for key in _PRE_M2_SEEDS:
        types.insert({"_key": key, "name": key, "name_en": key, "is_indoor": False, "is_system": True})
    types.insert({"_key": "huegelbeet", "name": "Hügelbeet", "is_indoor": False, "is_system": False})
    types.insert({"_key": "terrassenbeet", "name": "Terrassenbeet", "is_system": False, "is_bed": True})


def _flags(db) -> dict[str, tuple[object, object]]:  # type: ignore[no-untyped-def]
    return {
        doc["_key"]: (doc.get("is_bed", "absent"), doc.get("supports_layout", "absent"))
        for doc in db.collection(col.LOCATION_TYPES).all()
    }


def _revs(db, collection: str) -> dict[str, str]:  # type: ignore[no-untyped-def]
    return {doc["_key"]: doc["_rev"] for doc in db.collection(collection).all()}


class TestM2LocationTypeBedFlags:
    def test_stored_types_get_the_flags_and_the_seed_adds_the_new_beds(self, db) -> None:  # type: ignore[no-untyped-def]
        _pre_m2_types(db)

        report = m2.up(db)
        seed_location_types(db)  # the boot order: migrations, then the seed jobs

        assert (report.scanned, report.changed) == (14, 14)
        assert report.details["bed_type_keys"] == ["bed"]
        assert report.details["layout_type_keys"] == ["bed", "shelf", "tent", "terrassenbeet"]
        flags = _flags(db)
        assert len(flags) == 18, "12 pre-M2 seeds + 2 user types + the 4 new bed seeds"
        assert {k for k, (bed, _) in flags.items() if bed is True} == {
            "bed",
            "raised_bed",
            "planter",
            "greenhouse_bed",
            "cold_frame",
            "terrassenbeet",
        }
        assert {k for k, (_, layout) in flags.items() if layout is True} == {
            "bed",
            "raised_bed",
            "planter",
            "greenhouse_bed",
            "cold_frame",
            "tent",
            "shelf",
            "terrassenbeet",
        }
        assert flags["huegelbeet"] == (False, False)
        assert flags["terrassenbeet"] == (True, True), "the stored true is kept and implies the layout (§9.2a)"
        assert "absent" not in {v for pair in flags.values() for v in pair}

    def test_a_second_run_changes_nothing(self, db) -> None:  # type: ignore[no-untyped-def]
        _pre_m2_types(db)
        m2.up(db)
        seed_location_types(db)
        before = _revs(db, col.LOCATION_TYPES)

        report = m2.up(db)
        seed_location_types(db)

        assert report.changed == 0 and report.scanned == 0
        assert _revs(db, col.LOCATION_TYPES) == before

    def test_the_dry_run_writes_nothing(self, db) -> None:  # type: ignore[no-untyped-def]
        _pre_m2_types(db)
        before = _revs(db, col.LOCATION_TYPES)

        report = m2.up(db, dry_run=True)

        assert (report.scanned, report.changed, report.details["will_update"]) == (14, 0, 14)
        assert report.details["layout_type_keys"] == ["bed", "shelf", "tent", "terrassenbeet"]
        assert _revs(db, col.LOCATION_TYPES) == before
        assert "is_bed" not in db.collection(col.LOCATION_TYPES).get("bed")

    def test_the_bed_filter_the_api_will_use_sees_the_stamped_rows(self, db) -> None:  # type: ignore[no-untyped-def]
        _pre_m2_types(db)
        m2.up(db)
        seed_location_types(db)

        cursor = db.aql.execute(
            "FOR t IN @@c FILTER t.is_bed == true SORT t._key RETURN t._key", bind_vars={"@c": col.LOCATION_TYPES}
        )

        assert list(cursor) == ["bed", "cold_frame", "greenhouse_bed", "planter", "raised_bed", "terrassenbeet"]


class TestM3TaskSuggestedFlag:
    def _tasks(self, db) -> None:  # type: ignore[no-untyped-def]
        tasks = db.collection(col.TASKS)
        tasks.insert({"_key": "legacy", "tenant_key": "t", "name": "Mulchen", "status": "pending"})
        tasks.insert({"_key": "explicit_null", "tenant_key": "t", "name": "Gießen", "suggested": None})
        tasks.insert({"_key": "proposed", "tenant_key": "t", "name": "Fruchtfolge", "suggested": True})
        tasks.insert({"_key": "accepted", "tenant_key": "t", "name": "Ernte", "suggested": False})
        # Two open care-reminder tasks: the UPDATE re-derives the ``care_dedup_key`` computed
        # value (v0045, unique sparse index) on every stamped row — measured here, not assumed.
        for key, entity in (("care_a", "plant_a"), ("care_b", "plant_b")):
            tasks.insert(
                {
                    "_key": key,
                    "tenant_key": "t",
                    "name": f"Gießen {col.CARE_TASK_NAME_SEPARATOR}Pflanze",
                    "category": "care_reminder",
                    "status": "pending",
                    "entity_key": entity,
                }
            )

    def test_legacy_rows_get_false_and_an_equality_filter_sees_them(self, db) -> None:  # type: ignore[no-untyped-def]
        self._tasks(db)
        # Measured, not assumed: in AQL ``null == false`` is false, so before the stamp the
        # legacy rows are invisible to an equality filter — and ``!= true`` sees them all.
        equality = "FOR t IN @@c FILTER t.suggested == false SORT t._key RETURN t._key"
        null_safe = "FOR t IN @@c FILTER t.suggested != true SORT t._key RETURN t._key"
        everyone_but_proposed = ["accepted", "care_a", "care_b", "explicit_null", "legacy"]
        assert list(db.aql.execute(equality, bind_vars={"@c": col.TASKS})) == ["accepted"]
        assert list(db.aql.execute(null_safe, bind_vars={"@c": col.TASKS})) == everyone_but_proposed

        report = m3.up(db)

        assert (report.scanned, report.changed, report.details) == (4, 4, {"tasks_without_flag": 4})
        assert list(db.aql.execute(equality, bind_vars={"@c": col.TASKS})) == everyone_but_proposed
        assert db.collection(col.TASKS).get("proposed")["suggested"] is True
        assert "suggestion_reason" not in db.collection(col.TASKS).get("legacy")

    def test_the_stamp_re_derives_the_care_dedup_key_without_a_conflict(self, db) -> None:  # type: ignore[no-untyped-def]
        self._tasks(db)

        m3.up(db)

        tasks = db.collection(col.TASKS)
        keys = {k: tasks.get(k).get(col.CARE_TASK_DEDUP_FIELD) for k in ("care_a", "care_b", "legacy")}
        assert keys["care_a"] == "t/plant_a/Pflanze" and keys["care_b"] == "t/plant_b/Pflanze"
        assert keys["legacy"] is None, "a non-care task derives null and stays out of the sparse index"

    def test_a_second_run_changes_nothing(self, db) -> None:  # type: ignore[no-untyped-def]
        self._tasks(db)
        m3.up(db)
        before = _revs(db, col.TASKS)

        report = m3.up(db)

        assert report.changed == 0
        assert _revs(db, col.TASKS) == before

    def test_the_dry_run_writes_nothing(self, db) -> None:  # type: ignore[no-untyped-def]
        self._tasks(db)
        before = _revs(db, col.TASKS)

        report = m3.up(db, dry_run=True)

        assert (report.scanned, report.changed, report.details["tasks_without_flag"]) == (4, 0, 4)
        assert _revs(db, col.TASKS) == before
