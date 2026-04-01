from datetime import UTC, datetime

import structlog

from app.config.settings import settings
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.tasks.sensor_ingestion_tasks.ingest_ha_readings")
def ingest_ha_readings() -> dict:
    """Poll Home Assistant for all active sensors and batch-insert into TimescaleDB."""
    if not settings.timescaledb_enabled:
        return {"status": "skipped", "reason": "timescaledb_disabled"}

    from app.common.dependencies import get_ha_client, get_observation_repo, get_sensor_repo
    from app.domain.models.observation import SensorReading

    ha_client = get_ha_client()
    if ha_client is None:
        return {"status": "skipped", "reason": "ha_not_configured"}

    sensor_repo = get_sensor_repo()
    obs_repo = get_observation_repo()

    if not obs_repo.is_available():
        logger.warning("sensor_ingest_timescaledb_unavailable")
        return {"status": "error", "reason": "timescaledb_unavailable"}

    # Get all sensors across all tenants that have HA entity IDs
    from app.data_access.arango.collections import SENSORS

    db = sensor_repo._db  # noqa: SLF001 — direct access for AQL query
    cursor = db.aql.execute(
        "FOR s IN @@col FILTER s.is_active == true AND s.ha_entity_id != null AND s.ha_entity_id != '' RETURN s",
        bind_vars={"@col": SENSORS},
    )

    readings: list[SensorReading] = []
    errors: list[dict] = []
    now = datetime.now(tz=UTC)

    for doc in cursor:
        try:
            result = ha_client.get_state(doc["ha_entity_id"])
            if result and result["value"] is not None:
                readings.append(
                    SensorReading(
                        time=now,
                        tenant_key=doc.get("tenant_key", ""),
                        sensor_key=doc["_key"],
                        sensor_type=doc.get("metric_type", "unknown"),
                        value=float(result["value"]),
                        unit=result.get("unit"),
                        source="ha_auto",
                        quality_score=1.0,
                    )
                )
        except Exception as exc:
            logger.warning("sensor_ingest_ha_error", entity_id=doc.get("ha_entity_id"), error=str(exc))
            errors.append({"entity_id": doc.get("ha_entity_id"), "error": str(exc)})

    inserted = 0
    if readings:
        inserted = obs_repo.insert_batch(readings)

    logger.info("sensor_ingest_complete", inserted=inserted, errors=len(errors))
    return {"status": "ok", "inserted": inserted, "errors": len(errors)}
