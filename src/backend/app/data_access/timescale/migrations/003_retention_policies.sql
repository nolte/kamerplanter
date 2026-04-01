-- 003: Retention policies per NFR-011
-- Raw data: 90 days
SELECT add_retention_policy('sensor_readings', INTERVAL '90 days', if_not_exists => TRUE);

-- Hourly aggregates: 2 years
SELECT add_retention_policy('sensor_hourly', INTERVAL '2 years', if_not_exists => TRUE);

-- Daily aggregates: 5 years
SELECT add_retention_policy('sensor_daily', INTERVAL '5 years', if_not_exists => TRUE);
