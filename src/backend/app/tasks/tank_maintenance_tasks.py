import structlog

from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.tank_maintenance_tasks.generate_tank_maintenance_tasks")
def generate_tank_maintenance_tasks() -> dict:
    """Generate Task objects for due tank maintenance schedules.

    Daily. Idempotent: checks if a pending/in_progress task already exists
    for this tank + maintenance_type before creating.
    """
    from datetime import UTC, datetime, timedelta

    from app.common.dependencies import get_tank_repo, get_task_repo
    from app.common.enums import TaskCategory, TaskPriority, TaskStatus
    from app.domain.models.task import Task

    maintenance_to_task_priority = {
        "low": TaskPriority.LOW,
        "medium": TaskPriority.MEDIUM,
        "high": TaskPriority.HIGH,
        "critical": TaskPriority.HIGH,
    }

    tank_repo = get_tank_repo()
    task_repo = get_task_repo()

    schedules = tank_repo.get_active_auto_create_schedules()
    created_count = 0
    skipped_count = 0
    now = datetime.now(UTC)

    for schedule in schedules:
        tank_key = schedule.tank_key
        if not tank_key:
            continue

        # Check if maintenance is due
        last_log = tank_repo.get_last_maintenance_by_type(tank_key, schedule.maintenance_type)
        if last_log and last_log.performed_at:
            next_due = last_log.performed_at + timedelta(days=schedule.interval_days)
            reminder_offset = timedelta(days=schedule.reminder_days_before or 0)
            if now < (next_due - reminder_offset):
                continue
        # No last log means never performed — create task

        # Idempotency: check if pending/in_progress task already exists
        task_name = f"maintenance:{schedule.maintenance_type}:{tank_key}"
        existing, _ = task_repo.get_all_tasks(
            0,
            200,
            {
                "category": TaskCategory.MAINTENANCE.value,
            },
        )
        already_exists = any(
            t.name == task_name and t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS) for t in existing
        )
        if already_exists:
            skipped_count += 1
            continue

        # Resolve tank name for instruction
        tank = tank_repo.get_by_key(tank_key)
        tank_label = tank.name if tank else tank_key

        due_date = now
        if last_log and last_log.performed_at:
            due_date = last_log.performed_at + timedelta(days=schedule.interval_days)

        priority_str = schedule.priority.value if schedule.priority else "medium"
        task_priority = maintenance_to_task_priority.get(priority_str, TaskPriority.MEDIUM)

        task = Task(
            name=task_name,
            instruction=(
                schedule.instructions or f"Scheduled maintenance ({schedule.maintenance_type}) for tank '{tank_label}'"
            ),
            category=TaskCategory.MAINTENANCE,
            due_date=due_date,
            status=TaskStatus.PENDING,
            priority=task_priority,
        )
        task_repo.create_task(task)
        created_count += 1

    logger.info(
        "tank_maintenance_tasks_generated",
        created=created_count,
        skipped=skipped_count,
        schedules_checked=len(schedules),
    )
    return {"created": created_count, "skipped": skipped_count}


@celery_app.task(name="app.tasks.tank_maintenance_tasks.sync_tank_states_from_ha")
def sync_tank_states_from_ha() -> dict:
    """Poll HA sensors for all tanks and persist TankState in ArangoDB.

    Runs every 5 minutes. For each tank that has linked sensors with
    ha_entity_id, queries HA for current values and creates a TankState
    record. This keeps the alert engine and state history up-to-date.
    """
    from datetime import UTC, datetime

    from app.common.dependencies import get_ha_client, get_sensor_repo, get_tank_repo
    from app.domain.models.tank import TankState

    ha_client = get_ha_client()
    if ha_client is None:
        return {"status": "skipped", "reason": "ha_not_configured"}

    sensor_repo = get_sensor_repo()
    tank_repo = get_tank_repo()

    tanks, _total = tank_repo.get_all(offset=0, limit=1000)
    updated = 0
    skipped = 0
    errors: list[dict] = []

    for tank in tanks:
        if not tank.key:
            continue

        sensors = sensor_repo.find_by_tank(tank.key)
        if not sensors:
            skipped += 1
            continue

        # Only process sensors with HA entity IDs
        ha_sensors = [s for s in sensors if s.ha_entity_id]
        if not ha_sensors:
            skipped += 1
            continue

        now = datetime.now(tz=UTC)
        values: dict[str, float] = {}

        for sensor in ha_sensors:
            try:
                result = ha_client.get_state(sensor.ha_entity_id)  # type: ignore[arg-type]
                if result and result["value"] is not None:
                    values[sensor.metric_type] = result["value"]
            except Exception as exc:
                errors.append({"tank_key": tank.key, "entity_id": sensor.ha_entity_id, "error": str(exc)})

        if not values:
            continue

        state = TankState(
            tank_key=tank.key,
            recorded_at=now,
            ph=values.get("ph"),
            ec_ms=values.get("ec_ms"),
            water_temp_celsius=values.get("water_temp_celsius"),
            tds_ppm=values.get("tds_ppm"),
            dissolved_oxygen_mgl=values.get("dissolved_oxygen_mgl"),
            orp_mv=int(values["orp_mv"]) if "orp_mv" in values else None,
            fill_level_liters=values.get("fill_level_liters"),
            fill_level_percent=values.get("fill_level_percent"),
            source="ha_auto",
        )
        tank_repo.create_state(state)
        updated += 1
        logger.debug("tank_state_synced", tank_key=tank.key, values=list(values.keys()))

    logger.info(
        "tank_state_sync_completed",
        tanks_updated=updated,
        tanks_skipped=skipped,
        errors=len(errors),
    )
    return {"updated": updated, "skipped": skipped, "errors": len(errors)}


@celery_app.task(name="app.tasks.tank_maintenance_tasks.check_tank_alerts")
def check_tank_alerts() -> dict:
    """Hourly check of all tanks for alert conditions.

    Iterates all tanks, loads latest state + last fill event,
    runs the enhanced alert engine, and logs results.
    """
    from app.common.dependencies import get_tank_repo
    from app.domain.engines.tank_engine import TankEngine

    tank_repo = get_tank_repo()
    engine = TankEngine()

    tanks, _total = tank_repo.get_all(offset=0, limit=1000)
    tanks_checked = 0
    total_alerts = 0
    critical_count = 0

    for tank in tanks:
        if not tank.key:
            continue

        state = tank_repo.get_latest_state(tank.key)
        if state is None:
            continue

        last_fill = tank_repo.get_latest_full_change(tank.key)
        alerts = engine.check_alerts(tank, state, last_fill)

        tanks_checked += 1
        total_alerts += len(alerts)
        critical_count += sum(1 for a in alerts if a.get("severity") == "critical")

        if alerts:
            logger.info(
                "tank_alerts_detected",
                tank_key=tank.key,
                tank_name=tank.name,
                alert_count=len(alerts),
                alert_types=[a["type"] for a in alerts],
            )

    logger.info(
        "tank_alert_check_completed",
        tanks_checked=tanks_checked,
        total_alerts=total_alerts,
        critical_count=critical_count,
    )
    return {
        "tanks_checked": tanks_checked,
        "total_alerts": total_alerts,
        "critical_count": critical_count,
    }


@celery_app.task(name="app.tasks.tank_maintenance_tasks.check_runoff_trends")
def check_runoff_trends() -> dict:
    """Daily check for runoff EC trend anomalies.

    For each active plant (VEGETATIVE or FLOWERING), inspects the last 5
    FeedingEvents with runoff_ec. If 3+ events have runoff_ratio > 1.3,
    creates a flush task (idempotent).
    """
    from datetime import UTC, datetime

    from app.common.dependencies import get_feeding_repo, get_task_repo
    from app.common.enums import PhaseName, TaskCategory, TaskPriority, TaskStatus
    from app.domain.models.task import Task

    feeding_repo = get_feeding_repo()
    task_repo = get_task_repo()

    # Get all plant instances in vegetative or flowering phase
    query = """
    FOR doc IN plant_instances
      LET gp = DOCUMENT(CONCAT('growth_phases/', doc.current_phase_key))
      FILTER gp != null AND gp.name IN @phases
      RETURN doc._key
    """
    from app.common.dependencies import get_db

    db = get_db()
    cursor = db.aql.execute(
        query,
        bind_vars={
            "phases": [PhaseName.VEGETATIVE.value, PhaseName.FLOWERING.value],
        },
    )
    plant_keys = list(cursor)

    created = 0
    skipped = 0

    for plant_key in plant_keys:
        events = feeding_repo.get_recent_runoff_events(plant_key, limit=5)
        if len(events) < 3:
            continue

        # Calculate runoff ratios
        high_ratio_count = 0
        for ev in events:
            if ev.runoff_ec and ev.measured_ec_before and ev.measured_ec_before > 0:
                ratio = ev.runoff_ec / ev.measured_ec_before
                if ratio > 1.3:
                    high_ratio_count += 1

        if high_ratio_count < 3:
            continue

        # Idempotency: check if flush task already exists
        task_name = f"flush:runoff_trend:{plant_key}"
        existing, _ = task_repo.get_all_tasks(
            0,
            200,
            {
                "category": TaskCategory.MAINTENANCE.value,
            },
        )
        already_exists = any(
            t.name == task_name and t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS) for t in existing
        )
        if already_exists:
            skipped += 1
            continue

        task = Task(
            name=task_name,
            instruction=(
                f"Salt accumulation detected for plant {plant_key}: "
                f"{high_ratio_count}/5 recent runoff EC readings exceed 1.3× input EC. "
                "Perform a flush to reduce salt buildup."
            ),
            category=TaskCategory.MAINTENANCE,
            due_date=datetime.now(UTC),
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
        )
        task_repo.create_task(task)
        created += 1

    logger.info(
        "runoff_trend_check_completed",
        plants_checked=len(plant_keys),
        flush_tasks_created=created,
        skipped=skipped,
    )
    return {"plants_checked": len(plant_keys), "created": created, "skipped": skipped}
