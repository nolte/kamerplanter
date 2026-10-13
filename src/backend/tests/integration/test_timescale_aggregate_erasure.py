"""#1793 part 3 — erasing a tenant or a sensor reaches the continuous aggregates.

``sensor_hourly`` / ``sensor_daily`` are materialised from ``sensor_readings``
(migration 002). Deleting the raw rows removes the raw series only: the
materialised buckets keep the aggregated values of the deleted tenant or sensor
until a policy refresh happens to cover their range — and the policies refresh
the last 3 hours / 3 days. Buckets older than that are never recomputed, and
those older than the raw retention (90 days) cannot be: the raw rows they were
built from are gone. A deleted tenant's hourly and daily series therefore stayed
readable for up to 2 and 5 years (NFR-011 §3).

Only a real TimescaleDB can say whether the buckets are gone, so this reads them
back from the aggregate views. The drivers are the production steps — the
tenant-erasure step ``TenantService._purge_tenant_readings`` and
``SensorService.delete_sensor`` — over the real repository and the real
migrations, not a call to the repository method alone.

The seed deliberately includes **history older than the raw retention**: the raw
chunks are dropped (as migration 003's policy would) after the aggregates were
materialised. A fix that only refreshed the aggregates over the deleted rows'
window would leave exactly those buckets behind, and would — worse — wipe the
other tenants' valid history if it refreshed a wider window, because the refresh
recomputes from raw rows that no longer exist.

Locally it needs a server::

    docker compose --profile timescaledb up -d timescaledb
    pytest tests/integration/test_timescale_aggregate_erasure.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock

import psycopg
import pytest

from app.data_access.timescale.observation_repository import TimescaleObservationRepository
from app.data_access.timescale.schema import ensure_timescale_schema
from app.domain.models.sensor import Sensor
from app.domain.services.sensor_service import SensorService
from app.domain.services.tenant_service import TenantService
from tests.support import timescale_integration as ts

pytestmark = pytest.mark.usefixtures("timescale_server")

#: (tenant, sensor) series seeded. ``other`` shares a sensor key with ``gone``'s
#: sensor on purpose: the sensor delete must be tenant-scoped.
GONE, KEPT = "tenant-gone", "tenant-kept"
SENSOR_A, SENSOR_B = "sensor-a", "sensor-b"

#: Ages in days of the seeded raw rows. 1 and 5 are inside the raw retention; 120
#: and 400 are older than it, so their raw rows are dropped before the test runs.
AGES = (1, 5, 120, 400)


@pytest.fixture(scope="module")
def database():
    name = ts.provision_database("tsaggregate")
    pool = ts.open_pool(name)
    ensure_timescale_schema(pool)
    # The policy jobs (refresh / retention) would run in the background of this
    # test database and move buckets under the assertions. The seed applies the
    # raw retention by hand and the tests call no refresh in the window they
    # measure, so nothing but the code under test changes the aggregates.
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        conn.execute(
            "SELECT alter_job(job_id, scheduled => false) FROM timescaledb_information.jobs WHERE job_id >= 1000"
        )
    yield name, pool
    pool.close()


@pytest.fixture
def seeded(database):
    """Raw rows -> materialised aggregates -> raw retention applied, for four series."""
    name, pool = database
    series = [(GONE, SENSOR_A), (GONE, SENSOR_B), (KEPT, SENSOR_A), (KEPT, SENSOR_B)]
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        conn.execute("DELETE FROM sensor_readings")
        # Aggregates left over from the previous test (the retained history this
        # fixture re-creates) must not leak between tests.
        for view in ("sensor_hourly", "sensor_daily"):
            conn.execute(f"CALL refresh_continuous_aggregate('{view}', NULL, NULL)")
        for tenant, sensor in series:
            for age in AGES:
                conn.execute(
                    "INSERT INTO sensor_readings (time, tenant_key, sensor_key, sensor_type, value) "
                    "VALUES (now() - make_interval(days => %s), %s, %s, 'temperature', 21.5)",
                    (age, tenant, sensor),
                )
        conn.execute("CALL refresh_continuous_aggregate('sensor_hourly', NULL, NULL)")
        conn.execute("CALL refresh_continuous_aggregate('sensor_daily', NULL, NULL)")
        # What migration 003's raw retention does: the raw rows older than 90 days
        # go, the aggregates built from them stay (2 y hourly / 5 y daily).
        conn.execute("SELECT drop_chunks('sensor_readings', older_than => INTERVAL '90 days')")
    yield TimescaleObservationRepository(pool), name
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        conn.execute("DELETE FROM sensor_readings")


def _buckets(name: str, view: str, tenant: str, sensor: str | None = None) -> int:
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        if sensor is None:
            query, params = f"SELECT count(*) FROM {view} WHERE tenant_key = %s", (tenant,)
        else:
            query, params = f"SELECT count(*) FROM {view} WHERE tenant_key = %s AND sensor_key = %s", (tenant, sensor)
        return conn.execute(query, params).fetchone()[0]


def _raw(name: str, tenant: str) -> int:
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        return conn.execute("SELECT count(*) FROM sensor_readings WHERE tenant_key = %s", (tenant,)).fetchone()[0]


def _tenant_service(repo: TimescaleObservationRepository) -> TenantService:
    return TenantService(
        tenant_repo=MagicMock(),
        membership_repo=MagicMock(),
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=MagicMock(),
        membership_engine=MagicMock(),
        invitation_engine=MagicMock(),
        observation_repo=repo,
    )


def test_the_seed_materialises_what_the_defect_is_about(seeded):
    """Guards the other tests: without old buckets there would be nothing to be stale."""
    _repo, name = seeded
    for view in ("sensor_hourly", "sensor_daily"):
        assert _buckets(name, view, GONE) == 2 * len(AGES)
        assert _buckets(name, view, KEPT) == 2 * len(AGES)
    assert _raw(name, GONE) == 2 * 2  # only the two inside the raw retention survive


def test_tenant_erasure_step_removes_every_aggregate_bucket_of_the_tenant(seeded):
    repo, name = seeded

    result = _tenant_service(repo)._purge_tenant_readings(GONE)

    assert result == {"timeseries_rows_removed": 4}
    assert _raw(name, GONE) == 0
    assert _buckets(name, "sensor_hourly", GONE) == 0
    assert _buckets(name, "sensor_daily", GONE) == 0


def test_tenant_erasure_leaves_another_tenants_history_untouched(seeded):
    repo, name = seeded

    _tenant_service(repo)._purge_tenant_readings(GONE)

    # Including the buckets whose raw rows are long gone: they are the history the
    # retention design keeps, and a refresh over the whole range would drop them.
    assert _raw(name, KEPT) == 4
    assert _buckets(name, "sensor_hourly", KEPT) == 2 * len(AGES)
    assert _buckets(name, "sensor_daily", KEPT) == 2 * len(AGES)


def test_tenant_erasure_removes_aggregates_whose_raw_rows_are_already_gone(seeded):
    """A tenant whose raw rows all aged out still has aggregates, and still erases them."""
    repo, name = seeded
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        conn.execute("DELETE FROM sensor_readings WHERE tenant_key = %s", (GONE,))

    result = _tenant_service(repo)._purge_tenant_readings(GONE)

    assert result == {"timeseries_rows_removed": 0}
    assert _buckets(name, "sensor_hourly", GONE) == 0
    assert _buckets(name, "sensor_daily", GONE) == 0


class _SensorDocuments:
    """The sensor document store, which is not what is under test: it accepts the delete."""

    def __init__(self) -> None:
        self._sensor = Sensor(_key=SENSOR_A, name="Air", metric_type="temperature_celsius", site_key="s1")

    def get(self, key: str) -> Sensor | None:
        return self._sensor if key == SENSOR_A else None

    def update(self, key: str, sensor: Sensor) -> Sensor:
        """The mark ``delete_sensor`` writes before it purges (#1944)."""
        self._sensor = sensor
        return sensor

    def delete(self, key: str) -> bool:
        return key == SENSOR_A


def test_sensor_delete_removes_that_sensors_aggregates_only(seeded):
    repo, name = seeded
    service = SensorService(_SensorDocuments(), None, observation_repo=repo)

    assert service.delete_sensor(SENSOR_A, parent_field="site_key", parent_key="s1", tenant_key=GONE)

    for view in ("sensor_hourly", "sensor_daily"):
        assert _buckets(name, view, GONE, SENSOR_A) == 0
        # The tenant's other sensor, and another tenant's sensor with the SAME key.
        assert _buckets(name, view, GONE, SENSOR_B) == len(AGES)
        assert _buckets(name, view, KEPT, SENSOR_A) == len(AGES)
        assert _buckets(name, view, KEPT, SENSOR_B) == len(AGES)


def test_an_empty_tenant_key_still_deletes_nothing(seeded):
    repo, name = seeded

    with pytest.raises(ValueError):
        repo.delete_by_tenant("")

    assert _buckets(name, "sensor_hourly", GONE) == 2 * len(AGES)


def test_a_later_refresh_does_not_disturb_the_other_tenants_daily_buckets(seeded):
    """The purge deletes inside the hierarchy (hourly feeds daily); a refresh afterwards must not corrupt the rest."""
    repo, name = seeded
    before = _daily_values(name, KEPT)

    _tenant_service(repo)._purge_tenant_readings(GONE)
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        conn.execute("CALL refresh_continuous_aggregate('sensor_daily', NULL, NULL)")

    assert _daily_values(name, KEPT) == before


def test_a_sensor_delete_needs_both_keys(seeded):
    repo, name = seeded

    for sensor_key, tenant_key in (("", GONE), (SENSOR_A, ""), (None, GONE)):
        with pytest.raises(ValueError):
            repo.delete_by_sensor(sensor_key, tenant_key)

    assert _buckets(name, "sensor_daily", GONE) == 2 * len(AGES)


def _daily_values(name: str, tenant: str) -> list[tuple]:
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        return conn.execute(
            "SELECT bucket, sensor_key, avg_value, sample_count FROM sensor_daily "
            "WHERE tenant_key = %s ORDER BY bucket, sensor_key",
            (tenant,),
        ).fetchall()
