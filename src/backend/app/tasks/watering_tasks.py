import structlog

from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.watering_tasks.generate_watering_tasks")
def generate_watering_tasks() -> dict:
    """Generate Task objects for scheduled watering.

    Daily at 05:00 UTC. Idempotent: uses task name pattern watering:{run_key}:{date}
    to prevent duplicates.
    """
    from datetime import UTC, date, datetime

    from app.common.dependencies import get_planting_run_repo, get_task_repo
    from app.common.enums import TaskCategory, TaskPriority, TaskStatus
    from app.domain.engines.watering_schedule_engine import WateringScheduleEngine
    from app.domain.models.nutrient_plan import WateringSchedule
    from app.domain.models.task import Task

    run_repo = get_planting_run_repo()
    task_repo = get_task_repo()
    engine = WateringScheduleEngine()

    today = date.today()
    created_count = 0
    skipped_count = 0

    active_runs = run_repo.get_active_runs_with_schedule()

    for run_data in active_runs:
        run_key = run_data["run_key"]
        schedule_data = run_data["watering_schedule"]

        try:
            schedule = WateringSchedule(**schedule_data)
        except Exception:
            logger.warning("invalid_watering_schedule", run_key=run_key)
            continue

        # Check if watering is due today
        # Get last watering date (check recent tasks)
        last_watering_date = None
        recent_tasks = task_repo.find_by_field("planting_run_key", run_key)
        for t in sorted(recent_tasks, key=lambda x: x.get("completed_at", ""), reverse=True):
            if (
                t.get("category") == TaskCategory.FEEDING.value
                and t.get("name", "").startswith("watering:")
                and t.get("status") == TaskStatus.COMPLETED.value
                and t.get("completed_at")
            ):
                try:
                    completed = datetime.fromisoformat(t["completed_at"])
                    last_watering_date = completed.date()
                except (ValueError, TypeError):
                    pass
                break

        if not engine.is_watering_due(schedule, today, last_watering_date):
            continue

        # Check idempotency
        task_name = f"watering:{run_key}:{today.isoformat()}"
        existing = task_repo.find_by_field("name", task_name)
        if existing:
            skipped_count += 1
            continue

        preferred_time = schedule.preferred_time or "08:00"
        hour, minute = int(preferred_time[:2]), int(preferred_time[3:])

        task = Task(
            name=task_name,
            instruction=f"Scheduled watering for run {run_data.get('run_name', run_key)}",
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
