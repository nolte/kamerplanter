"""#2165 — the personal garden's sensor readings reach the Art. 15 bundle, on a real TimescaleDB.

``TimescalePersonalTimeSeriesRepository`` is SQL over the raw table and the two continuous
aggregates, so only a real server says which rows it reaches. The seed is the shape the
data has in production:

* the subject's garden (``own``) with two sensors — one with readings stamped with the
  tenant key, one whose older readings carry the **empty** tenant key the Home Assistant
  poll wrote before #2076;
* an organisation the subject is a member of, and somebody else's personal garden, each
  with readings of their own — and, in the foreign garden, a pre-#2076 row of a sensor
  that is *not* the subject's (it must stay out);
* raw history older than the raw retention, dropped after the aggregates were built, so
  the hourly and daily sections carry buckets no raw row backs any more.

Locally it needs a server::

    docker compose --profile timescaledb up -d timescaledb
    pytest tests/integration/test_privacy_export_garden_readings_timescale.py -v
"""

from __future__ import annotations

import psycopg
import pytest

from app.data_access.timescale.personal_time_series_repository import TimescalePersonalTimeSeriesRepository
from app.data_access.timescale.schema import ensure_timescale_schema
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.models.privacy import DataSourceDefinition
from tests.support import timescale_integration as ts

pytestmark = pytest.mark.usefixtures("timescale_server")

OWN, ORG, FOREIGN = "t-own", "t-org", "t-foreign"
OWN_SENSORS = ["s-own-ec", "s-own-legacy"]
#: Days ago of each seeded reading; 120 and 400 are older than the raw retention.
AGES = (1, 2, 5, 120, 400)


@pytest.fixture(scope="module")
def database():
    name = ts.provision_database("tsexport")
    pool = ts.open_pool(name)
    ensure_timescale_schema(pool)
    with psycopg.connect(ts.conninfo(name), autocommit=True) as conn:
        conn.execute(
            "SELECT alter_job(job_id, scheduled => false) FROM timescaledb_information.jobs WHERE job_id >= 1000"
        )
        series = [
            (OWN, "s-own-ec"),
            ("", "s-own-legacy"),  # the pre-#2076 poll: no tenant key, a sensor of the garden
            (ORG, "s-org"),
            (FOREIGN, "s-foreign"),
            ("", "s-foreign-legacy"),  # pre-#2076, a sensor of somebody else's garden
        ]
        for tenant, sensor in series:
            for age in AGES:
                conn.execute(
                    "INSERT INTO sensor_readings (time, tenant_key, sensor_key, sensor_type, value, unit, metadata) "
                    "VALUES (now() - make_interval(days => %s), %s, %s, 'ec_ms', %s, 'mS/cm', '{\"probe\": 1}')",
                    (age, tenant, sensor, float(age)),
                )
        conn.execute("CALL refresh_continuous_aggregate('sensor_hourly', NULL, NULL)")
        conn.execute("CALL refresh_continuous_aggregate('sensor_daily', NULL, NULL)")
        conn.execute("SELECT drop_chunks('sensor_readings', older_than => INTERVAL '90 days')")
    yield TimescalePersonalTimeSeriesRepository(pool)
    pool.close()


def _source(collection: str) -> DataSourceDefinition:
    (source,) = [s for s in DataExportEngine().build_export_manifest("u") if s.collection == collection]
    return source


@pytest.mark.parametrize(
    ("collection", "per_series"),
    [("sensor_readings", 3), ("sensor_hourly", len(AGES)), ("sensor_daily", len(AGES))],
)
def test_only_the_own_gardens_series_are_reached(database, collection: str, per_series: int) -> None:
    found = database.collect_personal_tenant_series(_source(collection), [OWN], OWN_SENSORS, max_rows=1000)

    assert {row["sensor_key"] for row in found.records} == set(OWN_SENSORS)
    assert found.total == len(found.records) == 2 * per_series


def test_the_rows_carry_the_declared_columns_newest_first(database) -> None:
    source = _source("sensor_readings")

    found = database.collect_personal_tenant_series(source, [OWN], OWN_SENSORS, max_rows=1000)

    assert all(list(row) == source.fields for row in found.records)
    times = [row["time"] for row in found.records]
    assert times == sorted(times, reverse=True)
    assert found.records[0]["metadata"] == {"probe": 1}


def test_a_bounded_section_returns_the_newest_rows_and_the_full_total(database) -> None:
    found = database.collect_personal_tenant_series(_source("sensor_daily"), [OWN], OWN_SENSORS, max_rows=3)

    assert len(found.records) == 3
    assert found.total == 2 * len(AGES)
    newest = sorted(
        (
            r["bucket"]
            for r in database.collect_personal_tenant_series(
                _source("sensor_daily"), [OWN], OWN_SENSORS, max_rows=1000
            ).records
        ),
        reverse=True,
    )[:3]
    assert [r["bucket"] for r in found.records] == newest


def test_a_legacy_row_is_matched_by_the_gardens_sensor_only(database) -> None:
    """Without the garden's sensor keys, the empty-tenant rows are nobody's."""
    found = database.collect_personal_tenant_series(_source("sensor_readings"), [OWN], [], max_rows=1000)

    assert {row["sensor_key"] for row in found.records} == {"s-own-ec"}


def test_no_personal_tenant_means_no_rows_even_with_sensor_keys(database) -> None:
    """The legacy match never runs unbounded by a tenant: ``[]`` tenants, ``[]`` rows."""
    for collection in ("sensor_readings", "sensor_hourly", "sensor_daily"):
        found = database.collect_personal_tenant_series(
            _source(collection), [], ["s-own-legacy", "s-foreign-legacy"], max_rows=1000
        )
        assert found.records == [] and found.total == 0, collection


def test_a_source_that_is_not_a_declared_table_is_refused(database) -> None:
    sites = next(s for s in DataExportEngine().build_export_manifest("u") if s.collection == "sites")
    with pytest.raises(ValueError, match="not a time-series source"):
        database.collect_personal_tenant_series(sites, [OWN], [], max_rows=10)
    forged = _source("sensor_readings").model_copy(update={"collection": "users"})
    with pytest.raises(ValueError, match="no known time-series table"):
        database.collect_personal_tenant_series(forged, [OWN], [], max_rows=10)
