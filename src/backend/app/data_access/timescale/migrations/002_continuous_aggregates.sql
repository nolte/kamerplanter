-- 002: Continuous aggregates for hourly and daily rollups
CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    tenant_key,
    sensor_key,
    sensor_type,
    AVG(value)   AS avg_value,
    MIN(value)   AS min_value,
    MAX(value)   AS max_value,
    COUNT(*)     AS sample_count
FROM sensor_readings
GROUP BY bucket, tenant_key, sensor_key, sensor_type;

SELECT add_continuous_aggregate_policy('sensor_hourly',
    start_offset    => INTERVAL '3 hours',
    end_offset      => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists   => TRUE
);

CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', bucket) AS bucket,
    tenant_key,
    sensor_key,
    sensor_type,
    AVG(avg_value)       AS avg_value,
    MIN(min_value)       AS min_value,
    MAX(max_value)       AS max_value,
    SUM(sample_count)    AS sample_count
FROM sensor_hourly
GROUP BY time_bucket('1 day', bucket), tenant_key, sensor_key, sensor_type;

SELECT add_continuous_aggregate_policy('sensor_daily',
    start_offset    => INTERVAL '3 days',
    end_offset      => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists   => TRUE
);
