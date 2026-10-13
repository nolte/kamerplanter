"""#2077 — the operator-run cleanup of pre-#2076 Home Assistant readings, against a real TimescaleDB and ArangoDB.

Before #2076 the Home Assistant poll stored readings under ``tenant_key = ''``;
``delete_by_tenant`` / ``delete_by_sensor`` never matched them. The cleanup
classifies those rows by the sensor document (ArangoDB) and deletes the rows of a
**deleted** sensor from the raw hypertable and from both continuous aggregates —
only with the count a dry run printed, and never a row of a sensor that exists.

The seeding is plain SQL (the repository's insert path cannot produce the shape any
more — that is #2076's point); the aggregates are materialised with an explicit
refresh, as the policy jobs (disabled here) would.

Locally it needs both servers (own throwaway containers; the tier reads its address
from ``ARANGODB_*`` / ``TIMESCALEDB_*``)::

    docker run -d --rm -p 127.0.0.1:28577:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    docker run -d --rm -p 127.0.0.1:25477:5432 -e POSTGRES_PASSWORD=changeme timescale/timescaledb:2.30.2-pg16
    ARANGODB_PORT=28577 TIMESCALEDB_PORT=25477 pytest tests/integration/test_legacy_ha_readings_cleanup.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.sensor_repository import ArangoSensorRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.data_access.arango.tank_repository import ArangoTankRepository
from app.data_access.timescale.legacy_reading_store import TimescaleLegacyReadingStore
from app.data_access.timescale.observation_repository import TimescaleObservationRepository
from app.data_access.timescale.schema import ensure_timescale_schema
from app.domain.interfaces.legacy_reading_store import LegacySeriesCounts
from app.domain.models.sensor import Sensor
from app.domain.services.legacy_reading_cleanup import CleanupStatus, LegacyReadingCleanup
from app.domain.services.observation_service import ObservationService
from app.migrations import purge_orphan_ha_readings as cmd
from tests.support import timescale_integration as ts
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db", "timescale_server")

ARANGO_DATABASE = run_database_name("legacy_ha_readings")
#: Readings per series, spread over 20 days so the raw delete needs three windows.
READINGS = 40
DEAD = "dead-sensor-2077"


@pytest.fixture(scope="module")
def arango():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(ARANGO_DATABASE):
        system.delete_database(ARANGO_DATABASE)
    system.create_database(ARANGO_DATABASE)
    database = client.db(ARANGO_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(database)
    yield database
    system.delete_database(ARANGO_DATABASE)


@pytest.fixture
def timescale():
    """A fresh database per test: the assertions count rows, and a shared one would count the neighbours'."""
    name = ts.provision_database("legacyha")
    pool = ts.open_pool(name)
    ensure_timescale_schema(pool)
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        conn.execute(
            "SELECT alter_job(job_id, scheduled => false) FROM timescaledb_information.jobs WHERE job_id >= 1000"
        )
    yield name, pool
    pool.close()


@pytest.fixture(autouse=True)
def _leave_logging_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.config.logging.setup_logging", lambda *a, **k: None)


class Directory:
    """The production sensor directory shape, over the real repositories."""

    def __init__(self, arango) -> None:
        self.sensor_repo = ArangoSensorRepository(arango)
        self.service = ObservationService(
            None,  # type: ignore[arg-type]
            self.sensor_repo,
            tank_repo=ArangoTankRepository(arango),
            site_anchors=ArangoSiteRepository(arango),
        )

    def exists(self, sensor_key: str) -> bool:
        return self.sensor_repo.get(sensor_key) is not None

    def owner_is_derivable(self, sensor_key: str) -> bool:
        return self.service.owning_tenant_key(sensor_key) is not None

    def sensor_count(self) -> int:
        return int(self.sensor_repo.collection.count())


class World:
    def __init__(self, arango, timescale) -> None:
        self.name, self.pool = timescale
        site = "site-2077"
        arango.collection(col.SITES).insert({"_key": site, "tenant_key": "tenant-live", "name": "Site"}, overwrite=True)
        self.directory = Directory(arango)
        self.live = (
            self.directory.sensor_repo.create(
                Sensor(name="Air", metric_type="temperature_celsius", site_key=site, ha_entity_id="sensor.air")
            ).key
            or ""
        )
        # A live sensor without a parent: exists, but its owner cannot be derived.
        self.live_parentless = (
            self.directory.sensor_repo.create(Sensor(name="Loose", metric_type="temperature_celsius")).key or ""
        )
        self.store = TimescaleLegacyReadingStore(self.pool)
        self.now = datetime.now(tz=UTC).replace(minute=30, second=0, microsecond=0)

    def seed(self, sensor_key: str, tenant_key: str = "", *, count: int = READINGS) -> None:
        with psycopg.connect(ts.conninfo(self.name), autocommit=True) as conn:
            for i in range(count):
                conn.execute(
                    "INSERT INTO sensor_readings (time, tenant_key, sensor_key, sensor_type, value, source) "
                    "VALUES (%s, %s, %s, 'temperature_celsius', %s, 'ha_auto')",
                    (self.now - timedelta(hours=12 * i), tenant_key, sensor_key, 20.0 + i % 5),
                )

    def refresh(self) -> None:
        with psycopg.connect(ts.conninfo(self.name), autocommit=True) as conn:
            for view in ("sensor_hourly", "sensor_daily"):
                conn.execute(f"CALL refresh_continuous_aggregate('{view}', NULL, NULL)")

    def counts(self, sensor_key: str, tenant_key: str = "") -> LegacySeriesCounts:
        """Rows of one (sensor, tenant) per table, read through the aggregate views."""
        with psycopg.connect(ts.conninfo(self.name), autocommit=True) as conn:
            values = [
                conn.execute(
                    f"SELECT count(*) FROM {table} WHERE sensor_key = %s AND tenant_key = %s", (sensor_key, tenant_key)
                ).fetchone()[0]
                for table in ("sensor_readings", "sensor_hourly", "sensor_daily")
            ]
        return LegacySeriesCounts(*values)

    def cleanup(self) -> LegacyReadingCleanup:
        return LegacyReadingCleanup(self.store, self.directory)


@pytest.fixture
def world(arango, timescale):
    world = World(arango, timescale)
    # A deleted sensor leaves rows and no document; a live one has both; a third series is unattributable.
    for key in (DEAD, world.live, world.live_parentless):
        world.seed(key)
    world.seed("not a key/at all", count=3)
    # Rows that are *not* legacy: the same keys under real tenants. Never part of any class.
    world.seed(DEAD, "tenant-erased", count=5)
    world.seed(world.live, "tenant-live", count=5)
    world.refresh()
    yield world
    for sensor in (world.live, world.live_parentless):
        arango.collection(col.SENSORS).delete(sensor, ignore_missing=True)


def test_the_dry_run_measures_every_table_and_changes_nothing(world: World) -> None:
    before = {k: world.counts(k) for k in (DEAD, world.live, world.live_parentless)}
    assert before[DEAD].raw == READINGS and before[DEAD].hourly > 0 and before[DEAD].daily > 0

    result = world.cleanup().run(confirm_delete_orphans=None)

    assert result.status is CleanupStatus.DRY_RUN
    report = result.before
    assert report is not None
    assert report.orphan.series == 1 and report.orphan.counts == before[DEAD]
    assert report.live.series == 2
    assert report.live.counts == before[world.live] + before[world.live_parentless]
    assert report.live_series_with_derivable_owner == 1
    assert report.unattributable.series == 1 and report.unattributable.counts.raw == 3
    assert {k: world.counts(k) for k in before} == before


def test_a_wrong_count_deletes_nothing_and_the_right_one_removes_only_the_dead_series(world: World) -> None:
    before_dead = world.counts(DEAD)
    live_before = (world.counts(world.live), world.counts(world.live_parentless))

    refused = world.cleanup().run(confirm_delete_orphans=before_dead.total - 1)

    assert refused.status is CleanupStatus.REFUSED
    assert world.counts(DEAD) == before_dead

    done = world.cleanup().run(confirm_delete_orphans=before_dead.total)

    assert done.status is CleanupStatus.DELETED
    assert done.deleted == before_dead
    assert world.counts(DEAD) == LegacySeriesCounts()
    assert (world.counts(world.live), world.counts(world.live_parentless)) == live_before
    assert world.counts("not a key/at all").raw == 3
    # Rows of the same dead sensor under a real tenant are the tenant erasure's business, not this command's.
    assert world.counts(DEAD, "tenant-erased").raw == 5
    assert world.counts(world.live, "tenant-live").raw == 5
    assert done.after is not None and done.after.orphan_rows == 0


def test_a_rerun_after_the_delete_has_nothing_to_do(world: World) -> None:
    total = world.counts(DEAD).total
    world.cleanup().run(confirm_delete_orphans=total)

    again = world.cleanup().run(confirm_delete_orphans=total)

    assert again.status is CleanupStatus.NOTHING_TO_DO


def test_the_command_defaults_to_a_dry_run_and_deletes_with_the_confirmation(
    world: World, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cmd, "_build", lambda: (world.store, world.directory))
    total = world.counts(DEAD).total

    assert cmd.main([]) == 0
    out = capsys.readouterr().out
    assert f"--confirm-delete-orphans {total}" in out
    assert DEAD not in out
    assert world.counts(DEAD).total == total

    assert cmd.main(["--confirm-delete-orphans", str(total + 1)]) == cmd.EXIT_REFUSED
    assert world.counts(DEAD).total == total

    assert cmd.main(["--confirm-delete-orphans", str(total)]) == 0
    assert world.counts(DEAD) == LegacySeriesCounts()


def _point_settings_at(monkeypatch: pytest.MonkeyPatch, database: str) -> None:
    from app.config.settings import settings

    monkeypatch.setattr(settings, "arangodb_host", ts_arango_host())
    monkeypatch.setattr(settings, "arangodb_port", ts_arango_port())
    monkeypatch.setattr(settings, "arangodb_username", ARANGO_USERNAME)
    monkeypatch.setattr(settings, "arangodb_password", ARANGO_PASSWORD)
    monkeypatch.setattr(settings, "arangodb_database", database)


def ts_arango_host() -> str:
    from tests.support.arango_integration import ARANGO_HOST

    return ARANGO_HOST


def ts_arango_port() -> int:
    from tests.support.arango_integration import ARANGO_PORT

    return int(ARANGO_PORT)


def test_the_production_directory_classifies_against_the_real_collections(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    _point_settings_at(monkeypatch, ARANGO_DATABASE)

    directory = cmd._ArangoSensorDirectory()  # noqa: SLF001 — the command's own wiring is what is measured

    assert directory.exists(world.live) and not directory.exists(DEAD)
    assert directory.owner_is_derivable(world.live) and not directory.owner_is_derivable(world.live_parentless)
    assert directory.sensor_count() >= 2
    result = LegacyReadingCleanup(world.store, directory).run(confirm_delete_orphans=None)
    assert result.before is not None and result.before.orphan.series == 1 and result.before.live.series == 2


def test_the_production_directory_refuses_a_database_that_was_never_initialised(
    arango, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A mistyped ARANGODB_DATABASE must not make every series look orphaned (nor create a database)."""
    system = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    missing = run_database_name("legacy_ha_missing")
    _point_settings_at(monkeypatch, missing)

    with pytest.raises(Exception):  # noqa: B017, PT011 — the server answers "database not found" for the absent one
        cmd._ArangoSensorDirectory()  # noqa: SLF001

    assert not system.has_database(missing)

    empty = run_database_name("legacy_ha_empty")
    system.create_database(empty)
    try:
        _point_settings_at(monkeypatch, empty)
        with pytest.raises(cmd.SensorDirectoryError, match="never initialised"):
            cmd._ArangoSensorDirectory()  # noqa: SLF001
    finally:
        system.delete_database(empty)


def test_an_unreachable_store_is_reported_and_nothing_is_touched(world: World) -> None:
    broken = TimescaleLegacyReadingStore(ts.open_pool(world.name))
    broken._pool.close()  # noqa: SLF001 — a closed pool is the outage

    result = LegacyReadingCleanup(broken, world.directory).run(confirm_delete_orphans=1)

    assert result.status is CleanupStatus.UNAVAILABLE
    assert world.counts(DEAD).raw == READINGS


def test_the_repository_erasures_still_do_not_reach_an_empty_tenant_key(world: World) -> None:
    """The reason the command exists: ``delete_by_sensor`` needs a tenant key and ``''`` is not one."""
    repo = TimescaleObservationRepository(world.pool)

    with pytest.raises(ValueError, match="tenant key"):
        repo.delete_by_sensor(DEAD, "")
    with pytest.raises(ValueError, match="tenant key"):
        repo.delete_by_tenant("")

    assert world.counts(DEAD).raw == READINGS
