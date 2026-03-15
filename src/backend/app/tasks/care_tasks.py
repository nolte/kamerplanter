import structlog

from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.care_tasks.generate_due_care_reminders")
def generate_due_care_reminders() -> dict:
    """Generate Task objects for due care reminders.

    Daily at 06:00 UTC. Idempotent: checks if a task already exists
    for plant + reminder_type + date before creating.

    For profiles with auto_create_watering_task=True, ensures exactly
    one pending watering task exists (even if the due date is in the future).
    """
    from datetime import UTC, date, datetime

    from app.common.dependencies import (
        get_care_reminder_service,
        get_nutrient_plan_repo,
        get_plant_repo,
        get_planting_run_repo,
        get_task_repo,
    )
    from app.common.enums import ReminderType, TaskCategory, TaskPriority, TaskStatus
    from app.domain.models.task import Task

    care_service = get_care_reminder_service()
    task_repo = get_task_repo()
    run_repo = get_planting_run_repo()
    plant_repo = get_plant_repo()
    nutrient_plan_repo = get_nutrient_plan_repo()

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
        has_nutrient_plan = nutrient_plan_repo.get_plant_plan(plant_key) is not None

        # Always ensure next watering task exists (unless plant has active run schedule)
        if not has_plan:
            task = care_service.ensure_next_watering_task(profile)
            if task is not None:
                created_count += 1
                logger.info("auto_watering_task_created", plant_key=plant_key, due_date=str(task.due_date))

        for rt in ReminderType:
            # Watering always handled above via ensure_next_watering_task
            if rt == ReminderType.WATERING:
                continue

            if not care_service._engine.should_generate_reminder(
                profile, rt, has_active_watering_plan=has_plan,
                has_nutrient_plan=has_nutrient_plan,
            ):
                continue

            last = care_service._repo.get_last_confirmation(plant_key, rt)
            due_date = care_service._engine.calculate_due_date(profile, rt, last)
            urgency = care_service._engine.calculate_urgency(due_date)

            if urgency not in ("overdue", "due_today"):
                continue

            # Check if task already exists for this plant/type
            name_suffix = f"\u2014 {rt.value}"
            existing = task_repo.find_by_field("plant_key", plant_key)
            already_exists = any(
                t.get("category") == TaskCategory.CARE_REMINDER.value
                and t.get("name", "").endswith(name_suffix)
                and t.get("status") in (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value)
                for t in existing
            )
            if already_exists:
                skipped_count += 1
                continue

            # Resolve plant name for user-friendly display
            plant_label = plant_key
            plant = plant_repo.get_by_key(plant_key)
            if plant is not None:
                plant_label = plant.plant_name or plant.instance_id or plant_key

            rt_instructions = {
                ReminderType.FERTILIZING: f"Fertilize {plant_label} according to care profile.",
                ReminderType.REPOTTING: f"Check if {plant_label} needs repotting.",
                ReminderType.PEST_CHECK: f"Inspect {plant_label} for pests and diseases.",
                ReminderType.LOCATION_CHECK: f"Check if {plant_label} needs a location change.",
                ReminderType.HUMIDITY_CHECK: f"Check humidity around {plant_label}.",
            }

            task = Task(
                name=f"{plant_label} \u2014 {rt.value}",
                instruction=rt_instructions.get(rt, f"Care reminder: {rt.value} for {plant_label}."),
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
