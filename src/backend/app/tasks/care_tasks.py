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
        get_lifecycle_repo,
        get_nutrient_plan_repo,
        get_phase_sequence_repo,
        get_plant_repo,
        get_planting_run_repo,
        get_season_state_repo,
        get_task_repo,
    )
    from app.common.enums import ReminderType, TaskCategory, TaskPriority, TaskStatus
    from app.domain.services.care_reminder_service import build_care_reminder_task

    care_service = get_care_reminder_service()
    task_repo = get_task_repo()
    run_repo = get_planting_run_repo()
    plant_repo = get_plant_repo()
    nutrient_plan_repo = get_nutrient_plan_repo()
    lifecycle_repo = get_lifecycle_repo()
    phase_seq_repo = get_phase_sequence_repo()
    season_repo = get_season_state_repo()

    today = date.today()
    created_count = 0
    skipped_count = 0

    # Get plant keys with active watering schedules (Gießplan-Guard)
    plants_with_schedule = run_repo.get_plant_keys_with_active_schedule()

    # Get all care profiles
    profiles = care_service._repo.get_all_profiles()

    # Per-run caches for the winter-reminder context (REQ-022 §3.2, B1).
    species_cache: dict = {}
    cultivar_cache: dict = {}
    # Per-site SeasonState phase cache (REQ-047 §3.2, C2): a site with a SeasonState
    # drives its winter reminders by phase, so the month-based path here is only the
    # fallback for sites without one — no double firing.
    season_phase_cache: dict = {}

    def _season_phase_for(p) -> object | None:  # noqa: ANN001 — PlantInstance
        site_key = p.site_key
        if not site_key:
            return None
        if site_key not in season_phase_cache:
            state = season_repo.get_by_site(site_key, p.tenant_key)
            season_phase_cache[site_key] = state.phase if state is not None else None
        return season_phase_cache[site_key]

    for profile in profiles:
        plant_key = profile.plant_key
        if not plant_key:
            continue

        # Skip removed plants: their care profiles must not keep spawning tasks.
        plant = plant_repo.get_by_key(plant_key)
        if plant is None or plant.removed_on is not None:
            skipped_count += 1
            continue

        has_plan = plant_key in plants_with_schedule
        has_nutrient_plan = nutrient_plan_repo.get_plant_plan(plant_key) is not None

        # REQ-022 §3.2 winter-reminder gating context (B1): without the
        # overwintering profile + frost sensitivity the engine suppresses every
        # winter-protection reminder, so they would never spawn a task.
        overwintering_profile = care_service.resolve_overwintering_profile(plant_key)
        species = care_service._resolve_species(plant.species_key, species_cache)
        frost_sensitivity = species.frost_sensitivity if species else None
        cultivar_traits = care_service._resolve_cultivar_traits(plant.cultivar_key, cultivar_cache)
        season_phase = _season_phase_for(plant)

        # Always ensure next watering task exists (unless plant has active run schedule)
        if not has_plan:
            # Resolve phase-specific watering interval — prefer PhaseSequence, fallback to LifecycleConfig
            phase_interval = None
            if plant.current_phase_key:
                # Try PhaseSequence first
                resolved = False
                if phase_seq_repo:
                    entry = phase_seq_repo.get_entry_by_key(plant.current_phase_key)
                    if entry:
                        defn = phase_seq_repo.get_definition_by_key(entry.phase_definition_key)
                        if defn and defn.watering_interval_days:
                            phase_interval = defn.watering_interval_days
                            resolved = True
                # Fallback to LifecycleConfig
                if not resolved:
                    phase = lifecycle_repo.get_phase_by_key(plant.current_phase_key)
                    if phase and phase.watering_interval_days:
                        phase_interval = phase.watering_interval_days
            task = care_service.ensure_next_watering_task(
                profile,
                phase_watering_interval=phase_interval,
            )
            if task is not None:
                created_count += 1
                logger.info("auto_watering_task_created", plant_key=plant_key, due_date=str(task.due_date))

        for rt in ReminderType:
            # Watering always handled above via ensure_next_watering_task
            if rt == ReminderType.WATERING:
                continue

            if not care_service._engine.should_generate_reminder(
                profile,
                rt,
                has_active_watering_plan=has_plan,
                has_nutrient_plan=has_nutrient_plan,
                overwintering_profile=overwintering_profile,
                frost_sensitivity=frost_sensitivity,
                cultivar_traits=cultivar_traits,
                season_phase=season_phase,
            ):
                continue

            last = care_service._repo.get_last_confirmation(plant_key, rt)
            due_date = care_service._engine.calculate_due_date(
                profile,
                rt,
                last,
                overwintering_profile=overwintering_profile,
            )
            urgency = care_service._engine.calculate_urgency(due_date)

            if urgency not in ("overdue", "due_today"):
                continue

            # Check if task already exists for this plant/type
            # Skip if PENDING/IN_PROGRESS or COMPLETED today (avoid re-creation)
            name_suffix = f"\u2014 {rt.value}"
            existing = task_repo.find_by_field("entity_key", plant_key)
            today_str = today.isoformat()
            # The repository wraps documents into Pydantic ``Task`` models, so the
            # dedup filter must use attribute access, not ``dict.get`` (regression #456).
            already_exists = any(
                t.category == TaskCategory.CARE_REMINDER.value
                and (t.name or "").endswith(name_suffix)
                and (
                    t.status in (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value)
                    or (t.status == TaskStatus.COMPLETED.value and str(t.completed_at or "")[:10] >= today_str)
                )
                for t in existing
            )
            if already_exists:
                skipped_count += 1
                continue

            # Resolve plant name and tenant for user-friendly display
            plant_label = plant.plant_name or plant.instance_id or plant_key
            plant_tenant_key = plant.tenant_key

            # Shared factory + instruction source (P4): identical task shape and
            # wording as the service path, so the two can never drift.
            task = build_care_reminder_task(
                plant_key=plant_key,
                plant_label=plant_label,
                tenant_key=plant_tenant_key,
                reminder_type=rt,
                due_date=datetime(today.year, today.month, today.day, tzinfo=UTC),
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
