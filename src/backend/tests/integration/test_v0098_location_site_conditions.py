"""#2399 (REQ-053 issue 75, WP 3.9) — v0098 measured on a real ArangoDB, prod point P-2.

``frost_exposed`` becomes ``site_conditions.microclimate.frost_risk``. The fixtures are written by the
production writer (``ArangoSiteRepository.create_location``), so the stored shape is the one the app
wrote, and the result is read back through the production ``Location`` model — a migration that put
``frost_risk`` one level too high, or dropped the neighbours of the nested object, fails here.

* ``true`` → ``high``, ``false`` → ``low``; ``null`` overrides stay untouched;
* a sun window already entered through the new UI survives the merge;
* a ``frost_risk`` that is already set is never overwritten — a disagreeing one is listed as a conflict;
* a second run changes no document (``_rev`` stays), a dry run writes nothing;
* the legacy ``frost_exposed`` is still there afterwards (additive).

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0098_location_site_conditions.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.common.enums import FrostRisk, SunWindow
from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.site import Location, Microclimate, SiteConditions, SunProfile
from app.migrations.versions.v0098_location_site_conditions import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration's scan and batched UPDATE are AQL over a real server"),
]

_DB_NAME = run_database_name("v0098_location_site_conditions")


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


def _revs(db) -> dict[str, str]:  # type: ignore[no-untyped-def]
    return {doc["_key"]: doc["_rev"] for doc in db.collection(col.LOCATIONS).all()}


def _location(db, name: str, **fields) -> str:  # type: ignore[no-untyped-def]
    created = ArangoSiteRepository(db).create_location(Location(name=name, site_key="", area_m2=2.0, **fields))
    assert created.key is not None
    return created.key


def _fixture(db) -> dict[str, str]:  # type: ignore[no-untyped-def]
    """The forms a real installation holds: a legacy override, a protected corner, an untouched bed, a
    bed that already carries a sun window, one already moved over by the app, one that disagrees."""
    keys = {
        "corner": _location(db, "Frost corner", frost_exposed=True),
        "niche": _location(db, "Warm niche", frost_exposed=False),
        "plain": _location(db, "Plain bed"),
    }
    keys["sunny"] = _location(
        db,
        "Sunny bed",
        frost_exposed=True,
        site_conditions=SiteConditions(sun_profile=SunProfile(sun_window=SunWindow.AFTERNOON)),
    )
    keys["mirrored"] = _location(
        db,
        "Already in step",
        frost_exposed=True,
        site_conditions=SiteConditions(microclimate=Microclimate(frost_risk=FrostRisk.HIGH)),
    )
    keys["disagree"] = _location(
        db,
        "Disagreeing bed",
        frost_exposed=True,
        site_conditions=SiteConditions(microclimate=Microclimate(frost_risk=FrostRisk.NORMAL)),
    )
    return keys


def _read(db, key: str) -> Location:  # type: ignore[no-untyped-def]
    return Location.model_validate(db.collection(col.LOCATIONS).get(key))


def test_the_legacy_override_is_copied_through_the_production_model(db) -> None:  # type: ignore[no-untyped-def]
    keys = _fixture(db)

    report = migration.up(db)

    assert _read(db, keys["corner"]).site_conditions.microclimate.frost_risk is FrostRisk.HIGH  # type: ignore[union-attr]
    assert _read(db, keys["niche"]).site_conditions.microclimate.frost_risk is FrostRisk.LOW  # type: ignore[union-attr]
    assert _read(db, keys["plain"]).site_conditions is None
    assert report.changed == 3  # corner, niche, sunny
    assert report.details["by_target"] == {"high": 2, "low": 1}
    assert report.details["untouched_inherit"] == 1


def test_the_neighbours_of_the_nested_object_survive(db) -> None:  # type: ignore[no-untyped-def]
    keys = _fixture(db)

    migration.up(db)

    sunny = _read(db, keys["sunny"]).site_conditions
    assert sunny is not None
    assert (sunny.sun_profile.sun_window, sunny.microclimate.frost_risk) == (SunWindow.AFTERNOON, FrostRisk.HIGH)


def test_a_set_risk_is_never_overwritten_and_a_disagreement_is_listed(db) -> None:  # type: ignore[no-untyped-def]
    keys = _fixture(db)

    report = migration.up(db)

    assert _read(db, keys["disagree"]).site_conditions.microclimate.frost_risk is FrostRisk.NORMAL  # type: ignore[union-attr]
    assert report.details["conflicts"] == {"count": 1, "listed": [keys["disagree"]]}
    assert report.details["already_in_step"] == 1


def test_the_legacy_field_stays(db) -> None:  # type: ignore[no-untyped-def]
    keys = _fixture(db)

    migration.up(db)

    assert db.collection(col.LOCATIONS).get(keys["corner"])["frost_exposed"] is True
    assert db.collection(col.LOCATIONS).get(keys["niche"])["frost_exposed"] is False


def test_a_second_run_changes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    _fixture(db)
    migration.up(db)
    before = _revs(db)

    report = migration.up(db)

    assert report.changed == 0 and _revs(db) == before


def test_the_dry_run_reports_and_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    keys = _fixture(db)
    before = _revs(db)

    report = migration.up(db, dry_run=True)

    assert report.dry_run is True and report.changed == 0
    assert report.details["will_update"] == 3
    assert sorted(report.details["listed_keys"]) == sorted([keys["corner"], keys["niche"], keys["sunny"]])
    assert _revs(db) == before
    assert _read(db, keys["corner"]).site_conditions is None
