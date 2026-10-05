"""MT-015 (#2112): the Home Assistant entity allowlist against a **real** ArangoDB.

* The repository: grants are unique per ``(tenant, entity)`` (the DB index, not only
  the code), a re-grant creates nothing, ``all_granted`` groups by tenant, revoke
  removes one row of one tenant.
* Migration v0084 seeds a grant for every reference that existed before the
  allowlist — sensors under a tank, a site and a location (whose tenant is its
  site's), actuators, weather sources, enabled HA notification destinations
  (granted to each tenant the user is a member of) — and nothing else: a malformed
  id, a disabled channel, an orphaned sensor. A second run changes nothing.
* After the seed, the real gate admits exactly the seeded references: the
  upgrade stops nothing that worked before it.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.data_access.arango.ha_entity_grant_repository import ArangoHaEntityGrantRepository
from app.domain.models.ha_entity_grant import HaEntityGrantSource
from app.domain.services.ha_entity_grant_service import HaEntityGrantService
from app.migrations.versions.v0084_tenant_ha_entity_grants import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("ha_entity_grants")

pytestmark = pytest.mark.usefixtures("arango_db")

_TOUCHED = (
    col.TENANT_HA_ENTITY_GRANTS,
    col.SENSORS,
    col.TANKS,
    col.SITES,
    col.LOCATIONS,
    col.ACTUATORS,
    col.WEATHER_SOURCE_CONFIGS,
    col.NOTIFICATION_PREFERENCES,
    col.MEMBERSHIPS,
)


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
    for name in _TOUCHED:
        database.collection(name).truncate()
    return database


class TestRepository:
    def test_the_database_holds_one_row_per_tenant_and_entity(self, db) -> None:
        db.collection(col.TENANT_HA_ENTITY_GRANTS).insert({"tenant_key": "t1", "entity_id": "sensor.tent"})

        with pytest.raises(DocumentInsertError):
            db.collection(col.TENANT_HA_ENTITY_GRANTS).insert({"tenant_key": "t1", "entity_id": "sensor.tent"})

    def test_grant_is_idempotent_and_scoped(self, db) -> None:
        repo = ArangoHaEntityGrantRepository(db)

        assert repo.grant("t1", ["sensor.tent", "switch.fan"], source=HaEntityGrantSource.ADMIN) == 2
        assert repo.grant("t1", ["sensor.tent"], source=HaEntityGrantSource.ADMIN) == 0
        assert repo.grant("t2", ["sensor.tent"], source=HaEntityGrantSource.ADMIN) == 1

        assert repo.granted_entity_ids(tenant_key="t1") == frozenset({"sensor.tent", "switch.fan"})
        assert [g.entity_id for g in repo.list_for_tenant(tenant_key="t1")] == ["sensor.tent", "switch.fan"]
        assert repo.all_granted() == {
            "t1": frozenset({"sensor.tent", "switch.fan"}),
            "t2": frozenset({"sensor.tent"}),
        }

    def test_revoke_removes_one_grant_of_one_tenant(self, db) -> None:
        repo = ArangoHaEntityGrantRepository(db)
        repo.grant("t1", ["sensor.tent"], source=HaEntityGrantSource.ADMIN)
        repo.grant("t2", ["sensor.tent"], source=HaEntityGrantSource.ADMIN)

        assert repo.revoke("t1", "sensor.tent") is True
        assert repo.revoke("t1", "sensor.tent") is False
        assert repo.all_granted() == {"t2": frozenset({"sensor.tent"})}


def _seed_references(db) -> None:
    db.collection(col.SITES).insert_many(
        [{"_key": "site-a", "tenant_key": "t-a", "name": "A"}, {"_key": "site-b", "tenant_key": "t-b", "name": "B"}]
    )
    db.collection(col.LOCATIONS).insert({"_key": "loc-a", "site_key": "site-a", "name": "Tent"})
    db.collection(col.TANKS).insert({"_key": "tank-b", "tenant_key": "t-b", "name": "Res"})
    db.collection(col.SENSORS).insert_many(
        [
            {"_key": "s-loc", "location_key": "loc-a", "ha_entity_id": "sensor.tent_temp", "is_active": True},
            {"_key": "s-site", "site_key": "site-a", "ha_entity_id": "sensor.garden_soil", "is_active": True},
            {"_key": "s-tank", "tank_key": "tank-b", "ha_entity_id": "sensor.res_ec", "is_active": True},
            {"_key": "s-bad", "site_key": "site-a", "ha_entity_id": "Sensor With Spaces", "is_active": True},
            {"_key": "s-orphan", "ha_entity_id": "sensor.nobodys", "is_active": True},
            {"_key": "s-manual", "site_key": "site-a", "ha_entity_id": None, "is_active": True},
        ]
    )
    db.collection(col.ACTUATORS).insert({"_key": "a-1", "tenant_key": "t-b", "ha_entity_id": "switch.res_pump"})
    db.collection(col.WEATHER_SOURCE_CONFIGS).insert(
        {
            "tenant_key": "t-a",
            "site_key": "site-a",
            "sources": [
                {"source_name": "open-meteo", "kind": "public", "config": None},
                {
                    "source_name": "ha_weather",
                    "kind": "home_assistant",
                    "config": {
                        "mode": "sensor_mapping",
                        "weather_entity_id": "weather.home",
                        "sensor_mapping": {"temp_min_entity": "sensor.out_min", "humidity_entity": None},
                    },
                },
            ],
        }
    )
    db.collection(col.MEMBERSHIPS).insert_many(
        [
            {"user_key": "u-multi", "tenant_key": "t-a", "is_active": True},
            {"user_key": "u-multi", "tenant_key": "t-b", "is_active": True},
            {"user_key": "u-multi", "tenant_key": "t-old", "is_active": False},
            {"user_key": "u-off", "tenant_key": "t-a", "is_active": True},
        ]
    )
    db.collection(col.NOTIFICATION_PREFERENCES).insert_many(
        [
            {
                "user_key": "u-multi",
                "channels": {
                    "home_assistant": {
                        "enabled": True,
                        "config": {"tts_enabled": True, "tts_entity_id": "media_player.kitchen"},
                    }
                },
            },
            {
                "user_key": "u-off",
                "channels": {"home_assistant": {"enabled": False, "config": {"notify_service": "mobile_app_x"}}},
            },
        ]
    )


EXPECTED = {
    "t-a": frozenset(
        {
            "sensor.tent_temp",  # location -> its site's tenant
            "sensor.garden_soil",
            "weather.home",
            "sensor.out_min",
            "notify.notify",  # the send default of an enabled channel with mobile push on
            "media_player.kitchen",
        }
    ),
    "t-b": frozenset({"sensor.res_ec", "switch.res_pump", "notify.notify", "media_player.kitchen"}),
}


class TestMigrationSeedsExistingReferences:
    def test_every_working_reference_is_granted_to_its_tenant_and_nothing_else(self, db) -> None:
        _seed_references(db)

        report = migration.up(db)

        assert ArangoHaEntityGrantRepository(db).all_granted() == EXPECTED
        assert report.details["malformed_not_granted"] == 1
        assert report.details["grants_seeded"] == sum(len(v) for v in EXPECTED.values())
        sources = {doc["source"] for doc in db.collection(col.TENANT_HA_ENTITY_GRANTS).all()}
        assert sources == {"migration"}

    def test_a_second_run_changes_nothing(self, db) -> None:
        _seed_references(db)
        migration.up(db)

        again = migration.up(db)

        assert again.changed == 0
        assert ArangoHaEntityGrantRepository(db).all_granted() == EXPECTED

    def test_a_dry_run_writes_nothing(self, db) -> None:
        _seed_references(db)

        report = migration.up(db, dry_run=True)

        assert report.changed == 0
        assert report.details["grants_to_seed"] == sum(len(v) for v in EXPECTED.values())
        assert db.collection(col.TENANT_HA_ENTITY_GRANTS).count() == 0

    def test_an_admin_grant_is_kept_and_not_counted_again(self, db) -> None:
        _seed_references(db)
        ArangoHaEntityGrantRepository(db).grant("t-a", ["sensor.tent_temp"], source=HaEntityGrantSource.ADMIN)

        report = migration.up(db)

        assert report.details["grants_seeded"] == sum(len(v) for v in EXPECTED.values()) - 1
        row = next(iter(db.collection(col.TENANT_HA_ENTITY_GRANTS).find({"entity_id": "sensor.tent_temp"})))
        assert row["source"] == "admin"

    def test_after_the_seed_the_gate_admits_exactly_what_worked_before(self, db) -> None:
        _seed_references(db)
        migration.up(db)
        gate = HaEntityGrantService(ArangoHaEntityGrantRepository(db))

        assert gate.is_granted("t-a", "sensor.tent_temp")
        assert gate.is_granted("t-b", "switch.res_pump")
        assert not gate.is_granted("t-a", "switch.res_pump")  # another tenant's actuator
        assert not gate.is_granted("t-old", "media_player.kitchen")  # an ended membership
        assert not gate.is_granted("t-a", "notify.mobile_app_x")  # a disabled channel
