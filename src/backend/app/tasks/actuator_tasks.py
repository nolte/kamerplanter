"""REQ-018 §5 environment-control Celery tasks.

Three periodic tasks close the sensor -> actuator loop and keep control state
fresh:

* ``evaluate_control_rules`` (30 s) — for every actuator, resolve the latest
  sensor readings for its location and let the :class:`ControlEngine` decide the
  winning command (priority + hysteresis), then dispatch it. HA outages degrade
  to fallback tasks inside the service (never a crash).
* ``expire_manual_overrides`` (hourly) — deactivate overrides past ``expires_at``.
* ``sync_actuator_states`` (5 min) — refresh online/offline status from HA.

All tasks are guarded by the ``actuator_control_loop_enabled`` kill-switch. The
two that walk actuators select the rows of the tenants they may touch in AQL and
read them one page at a time (MT-032, #2128). Each actuator is
processed defensively so one bad document never aborts the run.
"""

from __future__ import annotations

import structlog

from app.common.enums import TenantStatus
from app.common.exceptions import NotFoundError
from app.common.log_privacy import loggable_error
from app.config.settings import settings
from app.domain.services.ha_entity_grant_service import HaEntityGate
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


def _resolve_location_readings(
    sensor_repo, ha_client, location_key: str, *, tenant_key: str, grants: HaEntityGate
) -> dict[str, float]:
    """Best-effort map of ``metric_type -> latest value`` for a location's sensors.

    Only entities granted to ``tenant_key`` — the actuator's, which is its
    location's — are read (MT-015, #2112).
    """
    readings: dict[str, float] = {}
    if not location_key:
        return readings
    try:
        sensors = sensor_repo.find_by_location(location_key)
    except Exception as exc:  # noqa: BLE001 — a lookup failure must not abort the loop
        logger.warning("actuator_sensor_lookup_failed", location=location_key, error=loggable_error(exc))
        return readings
    if ha_client is None:
        return readings
    for sensor in sensors:
        if not sensor.is_active or not sensor.ha_entity_id:
            continue
        if not grants.is_granted(tenant_key, sensor.ha_entity_id):
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

    from app.common.dependencies import (
        get_actuator_repo,
        get_actuator_service,
        get_ha_client,
        get_ha_entity_grant_service,
        get_sensor_repo,
        get_tenant_repo,
    )
    from app.tasks.tenant_gate import CLOSED_WITH_HARDWARE

    repo = get_actuator_repo()
    service = get_actuator_service()
    sensor_repo = get_sensor_repo()
    ha_client = get_ha_client()
    # MT-015 (#2112): one read of every tenant's grants for the whole run.
    grants = get_ha_entity_grant_service().snapshot()
    # REQ-056 §5.2 — the control loop of a tenant that is not ``active`` runs no schedule, no override
    # and no sensor rule. SEC-003: its hardware is not left latched either — a suspended, pending-deletion
    # or orphaned tenant's devices are driven to a safe state (safety rules, then off) instead. A
    # ``deleted`` or vanished tenant is not walked at all: its erasure removes the devices.
    # MT-032 (#2128): the walk selects those tenants' actuators in AQL, one page at a time, every 30 s.
    tenant_states = get_tenant_repo().keys_in_status({TenantStatus.ACTIVE, *CLOSED_WITH_HARDWARE})

    evaluated = 0
    dispatched = 0
    errors = 0
    closed_tenant = 0
    safe_state = 0
    readings_cache: dict[tuple[str, str], dict[str, float]] = {}
    for actuator in repo.iter_for_tenants(tenant_states):
        closed = tenant_states.get(actuator.tenant_key) != TenantStatus.ACTIVE
        try:
            cache_key = (actuator.tenant_key, actuator.location_key)
            if cache_key not in readings_cache:
                readings_cache[cache_key] = _resolve_location_readings(
                    sensor_repo, ha_client, actuator.location_key, tenant_key=actuator.tenant_key, grants=grants
                )
            if closed:
                closed_tenant += 1
                if service.drive_to_safe_state(actuator, readings_cache[cache_key]) is not None:
                    safe_state += 1
                continue
            event = service.evaluate_actuator(actuator, readings_cache[cache_key])
            evaluated += 1
            if event is not None:
                dispatched += 1
        except Exception as exc:  # noqa: BLE001 — isolate a single bad actuator
            errors += 1
            logger.warning("actuator_evaluation_failed", actuator=actuator.key, error=loggable_error(exc))

    logger.info(
        "actuator_control_rules_evaluated",
        evaluated=evaluated,
        dispatched=dispatched,
        errors=errors,
        closed_tenant=closed_tenant,
        safe_state_commands=safe_state,
    )
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

    from app.common.dependencies import get_actuator_repo, get_ha_client, get_ha_entity_grant_service, get_tenant_repo

    repo = get_actuator_repo()
    ha_client = get_ha_client()
    if ha_client is None:
        return {"status": "skipped", "reason": "ha_not_configured"}
    # MT-015 (#2112): an ungranted entity is not polled on the tenant's behalf.
    grants = get_ha_entity_grant_service().snapshot()
    # REQ-056 §5.2 — nor is one of a tenant that is not ``active``. MT-032 (#2128): the active tenants'
    # actuators with an entity are selected in AQL and read one page at a time.
    active_tenants = get_tenant_repo().keys_in_status({TenantStatus.ACTIVE})

    synced = 0
    offline = 0
    not_granted = 0
    for actuator in repo.iter_for_tenants(active_tenants, filters=[("ha_entity_id", "!=", None)]):
        if actuator.ha_entity_id is None:
            continue
        if not grants.is_granted(actuator.tenant_key, actuator.ha_entity_id):
            not_granted += 1
            continue
        try:
            state = ha_client.get_state(actuator.ha_entity_id)
            is_online = state is not None
        except Exception:  # noqa: BLE001 — an unreachable entity is treated as offline
            is_online = False
        if is_online != actuator.is_online:
            # Field-level write (#1970 class): the HA round trip above can take long enough for
            # an edit of the actuator to land, and a whole-document write would revert it.
            try:
                repo.update_fields(
                    actuator.key or "",
                    {"is_online": is_online, "last_seen": datetime.now(UTC).isoformat()},
                )
            except NotFoundError:
                continue  # deleted while Home Assistant was polled; the rest of the run proceeds
            synced += 1
        if not is_online:
            offline += 1
    logger.info("actuator_states_synced", synced=synced, offline=offline, not_granted=not_granted)
    return {"status": "ok", "synced": synced, "offline": offline, "not_granted": not_granted}
