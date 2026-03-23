import structlog

from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.watering_tasks.generate_watering_tasks")
def generate_watering_tasks() -> dict:
    """Generate Task objects for scheduled watering.

    Daily at 05:00 UTC. Idempotent: uses task name pattern watering:{run_key}:{date}
    (legacy) or watering:{run_key}:{channel_id}:{date} (multi-channel) to prevent
    duplicates.
    """
    from datetime import UTC, date, datetime

    from app.common.dependencies import get_nutrient_plan_repo, get_planting_run_repo, get_task_repo
    from app.common.enums import TaskCategory, TaskPriority, TaskStatus
    from app.domain.engines.watering_schedule_engine import WateringScheduleEngine
    from app.domain.models.nutrient_plan import WateringSchedule
    from app.domain.models.task import Task

    run_repo = get_planting_run_repo()
    task_repo = get_task_repo()
    nutrient_plan_repo = get_nutrient_plan_repo()
    engine = WateringScheduleEngine()

    today = date.today()
    created_count = 0
    skipped_count = 0

    active_runs = run_repo.get_active_runs_with_schedule()

    for run_data in active_runs:
        run_key = run_data["run_key"]
        schedule_data = run_data["watering_schedule"]
        run_name = run_data.get("run_name", run_key)

        try:
            schedule = WateringSchedule(**schedule_data)
        except Exception:
            logger.warning("invalid_watering_schedule", run_key=run_key)
            continue

        # Check for multi-channel entries
        plan_key = run_data.get("plan_key")
        has_channels = False
        if plan_key and nutrient_plan_repo:
            try:
                entries = nutrient_plan_repo.get_phase_entries(plan_key)
                for entry in entries:
                    if entry.delivery_channels:
                        has_channels = True
                        # Multi-channel mode: generate per-channel tasks
                        for ch in entry.delivery_channels:
                            if not ch.enabled or ch.schedule is None:
                                continue
                            # Get last channel date
                            ch_task_prefix = f"watering:{run_key}:{ch.channel_id}:"
                            last_ch_date = _find_last_completed_date(
                                task_repo,
                                run_key,
                                ch_task_prefix,
                            )
                            if not engine.is_watering_due(ch.schedule, today, last_ch_date):
                                continue
                            task_name = f"watering:{run_key}:{ch.channel_id}:{today.isoformat()}"
                            existing = task_repo.find_by_field("name", task_name)
                            if existing:
                                skipped_count += 1
                                continue
                            preferred_time = ch.schedule.preferred_time or schedule.preferred_time or "08:00"
                            hour, minute = int(preferred_time[:2]), int(preferred_time[3:])
                            method_label = (
                                ch.application_method.value
                                if hasattr(ch.application_method, "value")
                                else str(ch.application_method)
                            )
                            instruction = (
                                f"Scheduled {method_label} for run {run_name} — channel '{ch.label or ch.channel_id}'"
                            )
                            task = Task(
                                name=task_name,
                                instruction=instruction,
                                category=TaskCategory.FEEDING,
                                planting_run_key=run_key,
                                due_date=datetime(today.year, today.month, today.day, hour, minute, tzinfo=UTC),
                                status=TaskStatus.PENDING,
                                priority=TaskPriority.MEDIUM,
                            )
                            task_repo.create(task)
                            created_count += 1
            except Exception:
                logger.warning("multi_channel_schedule_error", run_key=run_key, exc_info=True)

        if has_channels:
            continue

        # Legacy mode: single plan-level schedule
        last_watering_date = _find_last_completed_date(
            task_repo,
            run_key,
            f"watering:{run_key}:",
        )
        if not engine.is_watering_due(schedule, today, last_watering_date):
            continue

        task_name = f"watering:{run_key}:{today.isoformat()}"
        existing = task_repo.find_by_field("name", task_name)
        if existing:
            skipped_count += 1
            continue

        preferred_time = schedule.preferred_time or "08:00"
        hour, minute = int(preferred_time[:2]), int(preferred_time[3:])

        task = Task(
            name=task_name,
            instruction=f"Scheduled watering for run {run_name}",
            category=TaskCategory.FEEDING,
            planting_run_key=run_key,
            due_date=datetime(today.year, today.month, today.day, hour, minute, tzinfo=UTC),
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
        )
        task_repo.create(task)
        created_count += 1

    logger.info(
        "watering_tasks_generated",
        created=created_count,
        skipped=skipped_count,
    )
    return {"created": created_count, "skipped": skipped_count}


def _find_last_completed_date(task_repo, run_key: str, task_prefix: str):
    """Find the most recent completed watering date for a run/channel prefix."""
    from datetime import datetime

    from app.common.enums import TaskCategory, TaskStatus

    recent_tasks = task_repo.find_by_field("planting_run_key", run_key)
    for t in sorted(recent_tasks, key=lambda x: x.get("completed_at", ""), reverse=True):
        if (
            t.get("category") == TaskCategory.FEEDING.value
            and t.get("name", "").startswith(task_prefix)
            and t.get("status") == TaskStatus.COMPLETED.value
            and t.get("completed_at")
        ):
            try:
                completed = datetime.fromisoformat(t["completed_at"])
                return completed.date()
            except (ValueError, TypeError):  # fmt: skip
                pass
            break
    return None
