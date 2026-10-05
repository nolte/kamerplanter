from datetime import UTC, datetime

import structlog

from app.common.log_privacy import loggable_error
from app.config.settings import settings
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.tasks.sensor_ingestion_tasks.ingest_ha_readings")
def ingest_ha_readings() -> dict:
    """Poll Home Assistant for all active sensors and batch-insert into TimescaleDB.

    Only entities granted to the sensor's tenant are read (MT-015, #2112): the one
    Home Assistant instance is the operator's, and a sensor stored before the
    allowlist — or whose grant was withdrawn — is skipped and counted
    (``not_granted``), never read. The log carries the count, never an entity id
    or a value.
    """
    if not settings.timescaledb_enabled:
        return {"status": "skipped", "reason": "timescaledb_disabled"}

    from app.common.dependencies import (
        get_ha_client,
        get_ha_entity_grant_service,
        get_observation_repo,
        get_observation_service,
        get_sensor_repo,
    )
    from app.common.exceptions import NotFoundError
    from app.domain.models.observation import SensorReading

    ha_client = get_ha_client()
    if ha_client is None:
        return {"status": "skipped", "reason": "ha_not_configured"}

    sensor_repo = get_sensor_repo()
    obs_repo = get_observation_repo()
    # The one path readings are stored through: it resolves whose a sensor is, refuses
    # one that is gone or on its way out, and takes a reading back that raced an
    # erasure (#1944). A sensor document has no tenant_key of its own.
    observation_service = get_observation_service()
    # One read of every tenant's grants for the whole run.
    grants = get_ha_entity_grant_service().snapshot()

    if not obs_repo.is_available():
        logger.warning("sensor_ingest_timescaledb_unavailable")
        return {"status": "error", "reason": "timescaledb_unavailable"}

    # Get all sensors across all tenants that have HA entity IDs
    from app.data_access.arango.collections import SENSORS

    db = sensor_repo._db  # noqa: SLF001 — direct access for AQL query
    cursor = db.aql.execute(
        "FOR s IN @@col FILTER s.is_active == true AND s.deletion_pending != true "
        "AND s.ha_entity_id != null AND s.ha_entity_id != '' RETURN s",
        bind_vars={"@col": SENSORS},
    )

    errors: list[dict] = []
    skipped = 0
    not_granted = 0
    inserted = 0
    now = datetime.now(tz=UTC)

    for doc in cursor:
        try:
            tenant_key = observation_service.owning_tenant_key(doc["_key"])
            if tenant_key is None:
                skipped += 1  # no parent, or its delete began: nobody to store a reading for
                continue
            if not grants.is_granted(tenant_key, doc["ha_entity_id"]):
                not_granted += 1  # MT-015: the tenant may not read this entity of the operator's instance
                continue
            result = ha_client.get_state(doc["ha_entity_id"])
            if result and result["value"] is not None:
                reading = SensorReading(
                    time=now,
                    tenant_key=tenant_key,
                    sensor_key=doc["_key"],
                    sensor_type=doc.get("metric_type", "unknown"),
                    value=float(result["value"]),
                    unit=result.get("unit"),
                    source="ha_auto",
                    quality_score=1.0,
                )
                inserted += observation_service.record_readings_batch(doc["_key"], [reading], tenant_key=tenant_key)
        except NotFoundError:
            skipped += 1  # erased while Home Assistant was being asked; nothing was kept
        except Exception as exc:
            logger.warning("sensor_ingest_ha_error", entity_id=doc.get("ha_entity_id"), error=loggable_error(exc))
            errors.append({"entity_id": doc.get("ha_entity_id"), "error": str(exc)})

    logger.info(
        "sensor_ingest_complete", inserted=inserted, errors=len(errors), skipped=skipped, not_granted=not_granted
    )
    return {
        "status": "ok",
        "inserted": inserted,
        "errors": len(errors),
        "skipped": skipped,
        "not_granted": not_granted,
    }
