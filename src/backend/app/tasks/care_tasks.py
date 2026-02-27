import structlog

from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.care_tasks.generate_due_care_reminders")
def generate_due_care_reminders() -> dict:
    """Generate Task objects for due care reminders.

    Daily at 06:00 UTC. Idempotent: checks if a task already exists
    for plant + reminder_type + date before creating.
    """
    from datetime import UTC, date, datetime

    from app.common.dependencies import get_care_reminder_service, get_planting_run_repo, get_task_repo
    from app.common.enums import ReminderType, TaskCategory, TaskPriority, TaskStatus
    from app.domain.models.task import Task

    care_service = get_care_reminder_service()
    task_repo = get_task_repo()
    run_repo = get_planting_run_repo()

    today = date.today()
    created_count = 0
    skipped_count = 0

    # Get plant keys with active watering schedules (Gießplan-Guard)
    plants_with_schedule = run_repo.get_plant_keys_with_active_schedule()

    # Get all care profiles
    profiles = care_service._repo.get_all_profiles()

    for profile in profiles:
        plant_key = profile.plant_key
        if not plant_key:
            continue

        has_plan = plant_key in plants_with_schedule

        for rt in ReminderType:
            if not care_service._engine.should_generate_reminder(
                profile, rt, has_active_watering_plan=has_plan,
            ):
                continue

            last = care_service._repo.get_last_confirmation(plant_key, rt)
            due_date = care_service._engine.calculate_due_date(profile, rt, last)
            urgency = care_service._engine.calculate_urgency(due_date)

            if urgency not in ("overdue", "due_today"):
                continue

            # Check if task already exists for this plant/type/date
            existing = task_repo.find_by_field("plant_key", plant_key)
            already_exists = any(
                t.get("category") == TaskCategory.CARE_REMINDER.value
                and t.get("name", "").startswith(f"care:{rt.value}")
                and t.get("status") in (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value)
                for t in existing
            )
            if already_exists:
                skipped_count += 1
                continue

            task = Task(
                name=f"care:{rt.value}:{plant_key}",
                instruction=f"Care reminder: {rt.value} for plant {plant_key}",
                category=TaskCategory.CARE_REMINDER,
                plant_key=plant_key,
                due_date=datetime(today.year, today.month, today.day, tzinfo=UTC),
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM if urgency == "due_today" else TaskPriority.HIGH,
            )
            task_repo.create(task)
            created_count += 1

    logger.info(
        "care_reminders_generated",
        created=created_count,
        skipped=skipped_count,
    )
    return {"created": created_count, "skipped": skipped_count}
