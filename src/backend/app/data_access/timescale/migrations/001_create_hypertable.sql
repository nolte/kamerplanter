-- 001: Create sensor_readings hypertable
CREATE TABLE IF NOT EXISTS sensor_readings (
    time          TIMESTAMPTZ      NOT NULL,
    tenant_key    VARCHAR(64)      NOT NULL,
    sensor_key    VARCHAR(64)      NOT NULL,
    sensor_type   VARCHAR(50)      NOT NULL,
    value         DOUBLE PRECISION NOT NULL,
    unit          VARCHAR(20),
    source        VARCHAR(50)      DEFAULT 'manual',
    quality_score DOUBLE PRECISION,
    raw_value     DOUBLE PRECISION,
    metadata      JSONB
);

SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_time
    ON sensor_readings (sensor_key, time DESC);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_tenant_type_time
    ON sensor_readings (tenant_key, sensor_type, time DESC);
