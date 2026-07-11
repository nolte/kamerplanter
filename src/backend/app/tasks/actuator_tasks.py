"""REQ-018 §5 environment-control Celery tasks.

Three periodic tasks close the sensor -> actuator loop and keep control state
fresh:

* ``evaluate_control_rules`` (30 s) — for every actuator, resolve the latest
  sensor readings for its location and let the :class:`ControlEngine` decide the
  winning command (priority + hysteresis), then dispatch it. HA outages degrade
  to fallback tasks inside the service (never a crash).
* ``expire_manual_overrides`` (hourly) — deactivate overrides past ``expires_at``.
* ``sync_actuator_states`` (5 min) — refresh online/offline status from HA.

All tasks are guarded by the ``actuator_control_loop_enabled`` kill-switch and
iterate across tenants in the data-access layer (NFR-001). Each actuator is
processed defensively so one bad document never aborts the run.
"""

from __future__ import annotations

import structlog

from app.config.settings import settings
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


def _resolve_location_readings(sensor_repo, ha_client, location_key: str) -> dict[str, float]:
    """Best-effort map of ``metric_type -> latest value`` for a location's sensors."""
    readings: dict[str, float] = {}
    if not location_key:
        return readings
    try:
        sensors = sensor_repo.find_by_location(location_key)
    except Exception as exc:  # noqa: BLE001 — a lookup failure must not abort the loop
        logger.warning("actuator_sensor_lookup_failed", location=location_key, error=str(exc))
        return readings
    if ha_client is None:
        return readings
    for sensor in sensors:
        if not sensor.is_active or not sensor.ha_entity_id:
            continue
        try:
            state = ha_client.get_state(sensor.ha_entity_id)
        except Exception:  # noqa: BLE001 — skip a single unreadable sensor
            continue
        if state and state.get("value") is not None:
            readings[sensor.metric_type] = float(state["value"])
    return readings


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def evaluate_control_rules(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Evaluate every actuator against its rules/schedules/override (30 s beat)."""
    if not settings.actuator_control_loop_enabled:
        return {"status": "skipped", "reason": "actuator_control_loop_disabled"}

    from app.common.dependencies import get_actuator_repo, get_actuator_service, get_ha_client, get_sensor_repo

    repo = get_actuator_repo()
    service = get_actuator_service()
    sensor_repo = get_sensor_repo()
    ha_client = get_ha_client()

    actuators, _ = repo.get_all(offset=0, limit=5000, all_tenants=True)
    evaluated = 0
    dispatched = 0
    errors = 0
    readings_cache: dict[str, dict[str, float]] = {}
    for actuator in actuators:
        try:
            if actuator.location_key not in readings_cache:
                readings_cache[actuator.location_key] = _resolve_location_readings(
                    sensor_repo, ha_client, actuator.location_key
                )
            event = service.evaluate_actuator(actuator, readings_cache[actuator.location_key])
            evaluated += 1
            if event is not None:
                dispatched += 1
        except Exception as exc:  # noqa: BLE001 — isolate a single bad actuator
            errors += 1
            logger.warning("actuator_evaluation_failed", actuator=actuator.key, error=str(exc))

    logger.info("actuator_control_rules_evaluated", evaluated=evaluated, dispatched=dispatched, errors=errors)
    return {"status": "ok", "evaluated": evaluated, "dispatched": dispatched, "errors": errors}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def expire_manual_overrides(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Deactivate every manual override whose expiry has passed (hourly beat)."""
    if not settings.actuator_control_loop_enabled:
        return {"status": "skipped", "reason": "actuator_control_loop_disabled"}

    from datetime import UTC, datetime

    from app.common.dependencies import get_actuator_repo

    repo = get_actuator_repo()
    expired = repo.expire_overrides(datetime.now(UTC).isoformat())
    logger.info("actuator_overrides_expired", expired=expired)
    return {"status": "ok", "expired": expired}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_actuator_states(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Refresh actuator online/offline status from Home Assistant (5 min beat)."""
    if not settings.actuator_control_loop_enabled:
        return {"status": "skipped", "reason": "actuator_control_loop_disabled"}

    from datetime import UTC, datetime

    from app.common.dependencies import get_actuator_repo, get_ha_client

    repo = get_actuator_repo()
    ha_client = get_ha_client()
    if ha_client is None:
        return {"status": "skipped", "reason": "ha_not_configured"}

    actuators, _ = repo.get_all(offset=0, limit=5000, all_tenants=True)
    synced = 0
    offline = 0
    for actuator in actuators:
        if actuator.ha_entity_id is None:
            continue
        try:
            state = ha_client.get_state(actuator.ha_entity_id)
            is_online = state is not None
        except Exception:  # noqa: BLE001 — an unreachable entity is treated as offline
            is_online = False
        if is_online != actuator.is_online:
            updated = actuator.model_copy(update={"is_online": is_online, "last_seen": datetime.now(UTC)})
            repo.update_actuator(actuator.key or "", updated)
            synced += 1
        if not is_online:
            offline += 1
    logger.info("actuator_states_synced", synced=synced, offline=offline)
    return {"status": "ok", "synced": synced, "offline": offline}
