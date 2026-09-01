from datetime import UTC, datetime

import structlog

from app.common.datetimes import today_utc
from app.common.enums import (
    ApplicationMethod,
    ConfirmAction,
    ReminderType,
    SeasonPhase,
    TaskCategory,
    TaskPriority,
    TaskStatus,
)
from app.common.exceptions import DuplicateError, NotFoundError
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.engines.recurrence_engine import RecurrenceEngine
from app.domain.interfaces.care_reminder_repository import ICareReminderRepository
from app.domain.interfaces.nutrient_plan_repository import INutrientPlanRepository
from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
from app.domain.interfaces.overwintering_profile_template_repository import (
    IOverwinteringProfileTemplateRepository,
)
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.interfaces.task_repository import ITaskRepository
from app.domain.interfaces.watering_log_repository import IWateringLogRepository
from app.domain.models.care_reminder import CareConfirmation, CareDashboardEntry, CareProfile
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.overwintering_profile_template import OverwinteringProfileTemplate
from app.domain.models.species import Species
from app.domain.models.task import Task
from app.domain.models.watering_log import WateringLog, WateringLogFertilizer
from app.domain.services.notification_propagation_service import NotificationPropagationService

logger = structlog.get_logger()

#: Which winter/spring reminder types a SeasonState transition into a given phase
#: owns (REQ-047 §3.2). Used to create them the moment the site enters the phase.
_SEASON_PHASE_REMINDERS: dict[SeasonPhase, tuple[ReminderType, ...]] = {
    SeasonPhase.PRE_WINTER: (ReminderType.WINTER_PROTECTION, ReminderType.TUBER_DIG),
    SeasonPhase.PRE_SPRING: (ReminderType.SPRING_UNCOVER,),
}

#: CareProfile interval field → the care-reminder type whose pending task must be
#: re-terminated when that field is edited (#622). Editing e.g.
#: ``watering_interval_days`` recomputes the pending watering task's due date and
#: refreshes its "every N days" instruction; the same wiring covers fertilizing,
#: pest-check, humidity-check and repotting.
_INTERVAL_FIELD_REMINDERS: dict[str, ReminderType] = {
    "watering_interval_days": ReminderType.WATERING,
    "fertilizing_interval_days": ReminderType.FERTILIZING,
    "pest_check_interval_days": ReminderType.PEST_CHECK,
    "humidity_check_interval_days": ReminderType.HUMIDITY_CHECK,
    "repotting_interval_months": ReminderType.REPOTTING,
}


def _is_due(due_date: datetime | None) -> bool:
    """Return whether a care task is due today or overdue (#768).

    A task without a ``due_date`` counts as due — it carries no schedule that
    could postpone it. Comparison is on the calendar day in UTC, matching the
    ``LEFT(completed_at, 10)`` day granularity the dedup helper uses.
    """
    if due_date is None:
        return True
    return due_date.date() <= datetime.now(UTC).date()


def reminder_type_from_task_name(name: str | None) -> ReminderType | None:
    """Resolve a care task's reminder type from its ``"— {type}"`` name suffix.

    The reminder type is not yet a first-class ``Task`` field (audit P5), so the
    suffix written by :func:`build_care_reminder_task` is its carrier — the same
    convention :meth:`ITaskRepository.find_open_care_task` matches on. Returns
    ``None`` for a task whose name carries no known reminder type.
    """
    if not name:
        return None
    for reminder_type in ReminderType:
        if name.endswith(f"— {reminder_type.value}"):
            return reminder_type
    return None


def care_reminder_instruction(reminder_type: ReminderType, plant_label: str) -> str:
    """Human-readable task instruction for a care-reminder type (shared, REQ-022).

    Single source of the per-reminder-type instruction text (P4). Consumed by both
    the service path (:meth:`CareReminderService._ensure_care_task`) and the daily
    Celery producer (``generate_due_care_reminders``) via
    :func:`build_care_reminder_task`, so the two paths can never drift on wording.
    """
    return {
        ReminderType.FERTILIZING: f"Fertilize {plant_label} according to care profile.",
        ReminderType.REPOTTING: f"Check if {plant_label} needs repotting.",
        ReminderType.PEST_CHECK: f"Inspect {plant_label} for pests and diseases.",
        ReminderType.LOCATION_CHECK: f"Check if {plant_label} needs a location change.",
        ReminderType.HUMIDITY_CHECK: f"Check humidity around {plant_label}.",
        ReminderType.WINTER_PROTECTION: f"Apply winter protection for {plant_label}.",
        ReminderType.SPRING_UNCOVER: f"Uncover / reactivate {plant_label} for spring.",
        ReminderType.TUBER_DIG: f"Dig up and store the tubers/bulbs of {plant_label}.",
        ReminderType.STORAGE_CHECK: f"Check the stored tubers/bulbs of {plant_label}.",
        ReminderType.DEADHEADING: f"Deadhead spent blooms on {plant_label}.",
    }.get(reminder_type, f"Care reminder: {reminder_type.value} for {plant_label}.")


def build_care_reminder_task(
    *,
    plant_key: str,
    plant_label: str,
    tenant_key: str,
    reminder_type: ReminderType,
    due_date: datetime,
    instruction: str | None = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
) -> Task:
    """Build the care-reminder ``Task`` shared by the service and Celery paths (P4).

    Single construction point so the dashboard-confirmation path, the seasonal
    winter path (:meth:`CareReminderService._ensure_care_task`), the auto-watering
    path (:meth:`CareReminderService.ensure_next_watering_task`) and the daily
    ``generate_due_care_reminders`` producer can never drift on task shape.

    ``instruction`` defaults to the shared per-type text from
    :func:`care_reminder_instruction`; the watering path passes its
    interval-specific instruction explicitly. ``priority`` defaults to
    ``MEDIUM``; the daily producer raises it to ``HIGH`` for overdue reminders.
    """
    return Task(
        name=f"{plant_label} — {reminder_type.value}",
        instruction=(instruction if instruction is not None else care_reminder_instruction(reminder_type, plant_label)),
        category=TaskCategory.CARE_REMINDER,
        entity_key=plant_key,
        entity_type="plant_instance",
        tenant_key=tenant_key,
        due_date=due_date,
        status=TaskStatus.PENDING,
        priority=priority,
    )


def create_care_reminder_task(task_repo: ITaskRepository, task: Task) -> Task | None:
    """Insert a care-reminder task, resolving a lost creation race to ``None`` (#1301).

    The single insertion point for every care-reminder producer — the seasonal
    path (:meth:`CareReminderService._ensure_care_task`), the watering follow-up
    (:meth:`CareReminderService.ensure_next_watering_task`), the quarter-climate
    service and the daily ``generate_due_care_reminders`` Celery producer. All
    four first ask :meth:`ITaskRepository.find_open_care_task` whether an
    equivalent task is already open; that read-then-create is not atomic, so two
    overlapping producers (the 06:00 beat and a manual
    ``POST /t/{slug}/tasks/generate-care-reminders``, or two E2E workers) both
    read "none open" and both insert.

    The ``tasks`` collection now carries a **unique sparse index over the open
    care-reminder dedup key** (``ensure_care_task_dedup_index``), so exactly one
    of the two inserts lands and the other is rejected with ArangoDB error code
    ``1210``, which the repository already surfaces as :class:`DuplicateError`.

    The loser wanted to know one thing — "does an equivalent open task already
    exist?" — and the rejection *is* that answer, so this returns ``None``: the
    same outcome as the ``existing is not None`` branch the racing read missed by
    microseconds. It is never an error, and never a 409 leaking out of a
    generation endpoint.

    Why the exception is not narrowed further: ``tasks`` carries exactly one
    unique index, this one, so on this collection code ``1210`` can only be it.
    That assumption is pinned by
    ``tests/integration/test_care_task_dedup_concurrency.py::test_tasks_carries_exactly_one_unique_index``
    — add a second unique index to ``tasks`` and it reddens rather than letting a
    genuinely different conflict be swallowed as "already exists".
    """
    try:
        return task_repo.create_task(task)
    except DuplicateError:
        logger.info(
            "care_reminder_task_dedup_race_lost",
            entity_key=task.entity_key,
            tenant_key=task.tenant_key,
            task_name=task.name,
        )
        return None


def _template_to_profile(
    template: OverwinteringProfileTemplate | None,
    plant_key: str,
) -> OverwinteringProfile | None:
    """Adapt a shared species template into a transient per-plant profile.

    Returns ``None`` when there is no template or the template carries no timed
    winter action (``winter_action_month`` is ``None`` — e.g. a house plant that
    simply stays indoors), so no phantom winter reminder is scheduled.
    """
    if template is None or template.winter_action_month is None:
        return None
    return OverwinteringProfile(
        plant_key=plant_key,
        hardiness_zone_min=template.hardiness_zone_min,
        hardiness_rating=template.hardiness_rating,
        winter_action=template.winter_action,
        winter_action_month=template.winter_action_month,
        spring_action=template.spring_action,
        spring_action_month=template.spring_action_month,
        auto_generated=True,
        **template.winter_quarter_fields(),
    )


class CareReminderService:
    def __init__(
        self,
        care_repo: ICareReminderRepository,
        engine: CareReminderEngine,
        task_repo: ITaskRepository | None = None,
        watering_log_repo: IWateringLogRepository | None = None,
        plant_repo: IPlantInstanceRepository | None = None,
        lifecycle_repo: IPhaseRepository | None = None,
        phase_seq_repo: IPhaseSequenceRepository | None = None,
        species_repo: ISpeciesRepository | None = None,
        nutrient_plan_repo: INutrientPlanRepository | None = None,
        overwintering_repo: IOverwinteringProfileRepository | None = None,
        overwintering_template_repo: IOverwinteringProfileTemplateRepository | None = None,
        recurrence: RecurrenceEngine | None = None,
        notification_propagation: NotificationPropagationService | None = None,
    ) -> None:
        self._repo = care_repo
        self._engine = engine
        self._recurrence = recurrence or RecurrenceEngine()
        self._task_repo = task_repo
        #: Optional REQ-030 §4.2 coupling (Issue #742): a rescheduled/confirmed care
        #: reminder synchronously updates/closes its in-app notification. Guarded at
        #: every call site so the core care flow is unaffected when it is absent.
        self._notifications = notification_propagation
        self._watering_log_repo = watering_log_repo
        self._plant_repo = plant_repo
        self._lifecycle_repo = lifecycle_repo
        self._phase_seq_repo = phase_seq_repo
        self._species_repo = species_repo
        self._nutrient_plan_repo = nutrient_plan_repo
        self._overwintering_repo = overwintering_repo
        self._overwintering_template_repo = overwintering_template_repo

    def get_or_create_profile(
        self,
        plant_key: str,
        species_name: str | None = None,
        botanical_family: str | None = None,
    ) -> CareProfile:
        """Get existing profile or auto-generate one."""
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is not None:
            return profile

        new_profile = self._engine.auto_generate_profile(
            species_name=species_name,
            botanical_family=botanical_family,
            plant_key=plant_key,
        )
        created = self._repo.create_profile(new_profile)
        if created.key:
            self._repo.create_profile_edge(plant_key, created.key)
        return created

    def _propagate(self, action) -> None:  # noqa: ANN001 — Callable[[NotificationPropagationService], None]
        """Run a notification-propagation ``action`` when the coupling is wired.

        Best-effort (NFR-007): a notification-centre failure is logged and swallowed
        so it can never abort the underlying care mutation.
        """
        if self._notifications is None:
            return
        try:
            action(self._notifications)
        except Exception:  # pragma: no cover - defensive; propagation is best-effort
            import structlog

            structlog.get_logger().warning("care_notification_propagation_failed")

    def update_profile(self, plant_key: str, updates: dict, *, user_key: str = "") -> CareProfile:
        """Persist care-profile edits and re-terminate the affected pending tasks.

        Beyond writing the fields, an edit to any task-interval field
        (``watering_interval_days`` and its fertilizing/pest/humidity/repotting
        siblings) reschedules the corresponding **pending** care task so its due
        date and "every N days" instruction reflect the new cadence immediately —
        instead of staying stale until the next confirmation regenerates the task
        (#622). Only pending tasks are touched; completed/skipped history is never
        revived and no duplicates are created (the tenant-aware dedup helper is the
        single predicate). An explicit interval edit also resets the matching
        adaptive-learned interval, so the edited base value — not a stale learned
        value — drives the new schedule.
        """
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            raise NotFoundError("CareProfile", plant_key)

        # Which task-interval fields actually change (a no-op write is not a change).
        changed_reminders = {
            reminder_type
            for field, reminder_type in _INTERVAL_FIELD_REMINDERS.items()
            if field in updates and updates[field] != getattr(profile, field)
        }

        data = profile.model_dump()
        data.update(updates)

        # An explicit interval edit takes precedence over the adaptive-learned
        # value: reset the learned interval (unless the caller set it in the same
        # request) so the freshly edited base interval drives scheduling (#622).
        if ReminderType.WATERING in changed_reminders and "watering_interval_learned" not in updates:
            data["watering_interval_learned"] = None
        if ReminderType.FERTILIZING in changed_reminders and "fertilizing_interval_learned" not in updates:
            data["fertilizing_interval_learned"] = None

        updated = CareProfile(**data)
        saved = self._repo.update_profile(profile.key or "", updated)

        for reminder_type in changed_reminders:
            self._reschedule_pending_care_task(saved, reminder_type, user_key=user_key)

        return saved

    def _reschedule_pending_care_task(
        self, profile: CareProfile, reminder_type: ReminderType, *, user_key: str = ""
    ) -> None:
        """Re-terminate the plant's pending care task after an interval edit (#622).

        Routes through the single tenant-aware dedup helper
        (:meth:`ITaskRepository.find_open_care_task`) with
        ``include_completed_today=False`` so only a still-open task is considered —
        completed/skipped history is never revived. Only a ``PENDING`` task is
        rescheduled in place (an ``IN_PROGRESS`` task is being worked on and is left
        untouched). When no pending task exists, the opted-in watering path
        materialises the next occurrence via :meth:`ensure_next_watering_task`
        (which respects ``auto_create_watering_task`` and its own dedup); every
        other reminder type is left as-is, so no duplicates are created.
        """
        if self._task_repo is None:
            return

        plant_key = profile.plant_key
        tenant_key = self._resolve_tenant_key(plant_key)
        task = self._task_repo.find_open_care_task(
            plant_key,
            reminder_type,
            tenant_key,
            include_completed_today=False,
        )

        if task is not None:
            if task.status != TaskStatus.PENDING:
                return
            due_dt, instruction = self._compute_care_reschedule(profile, reminder_type, plant_key)
            if due_dt is None:
                return
            task.due_date = due_dt
            if instruction is not None:
                task.instruction = instruction
            self._task_repo.update_task(task.key or "", task)
            # #742 — the in-app care notification follows the new cycle (single entry).
            # The occurrence itself is unchanged (only its date moved), so the note is
            # retimed in place and keeps whatever read state the user gave it (#769).
            self._propagate_care_reschedule(
                profile, reminder_type, tenant_key, user_key, due_dt, task.key, announces_new_task=False
            )
            return

        # No pending task to re-terminate. Only the opted-in watering path creates
        # the next occurrence here; ensure_next_watering_task's own dedup prevents
        # a duplicate when a task was already completed today.
        if reminder_type == ReminderType.WATERING and profile.auto_create_watering_task:
            phase_interval = self._get_phase_watering_interval(plant_key)
            created = self.ensure_next_watering_task(profile, phase_watering_interval=phase_interval)
            if created is not None:
                # A brand-new occurrence, not a retiming — it must reach the badge (#769).
                self._propagate_care_reschedule(
                    profile,
                    reminder_type,
                    tenant_key,
                    user_key,
                    created.due_date,
                    created.key,
                    announces_new_task=True,
                )

    def _propagate_care_reschedule(
        self,
        profile: CareProfile,
        reminder_type: ReminderType,
        tenant_key: str,
        user_key: str,
        due_date: datetime | None,
        task_key: str | None,
        *,
        announces_new_task: bool,
    ) -> None:
        """Upsert the plant's care notification to the new cycle (#742, single entry).

        Args:
            announces_new_task: Whether this update announces a **newly created**
                care task rather than retiming the one the user already has. Only
                then is the row's read state cleared (#769): the single-entry
                guarantee recycles the row a preceding confirmation stamped read, so
                a follow-up occurrence would otherwise never reach the unread badge.
                A pure retiming keeps the read state — resurfacing a note the user
                deliberately dealt with would be a defect in its own right, and the
                task path behaves the same way (moving a task's due date via
                ``sync_task_due_notification`` also leaves the read state alone).
        """
        plant_label = self._resolve_plant_label(profile.plant_key)
        self._propagate(
            lambda p: p.sync_care_notification(
                tenant_key=tenant_key,
                user_key=user_key,
                plant_key=profile.plant_key,
                plant_label=plant_label,
                reminder_type=reminder_type,
                due_date=due_date,
                task_key=task_key,
                reset_read=announces_new_task,
            )
        )

    def _compute_care_reschedule(
        self,
        profile: CareProfile,
        reminder_type: ReminderType,
        plant_key: str,
    ) -> tuple[datetime | None, str | None]:
        """Compute the ``(due_date, instruction)`` for a rescheduled care task (#622).

        Reuses the existing scheduling machinery so the interval edit never
        duplicates cadence math: the watering path routes through the same
        :meth:`_next_watering_due_date` (RecurrenceEngine) and interval authority
        (:meth:`CareReminderEngine._get_interval_days`) as
        :meth:`ensure_next_watering_task`; every other reminder type reuses the
        engine's :meth:`CareReminderEngine.calculate_due_date`. Both cases anchor on
        the last confirmation (or the profile bootstrap when none exists).
        """
        last = self._repo.get_last_confirmation(plant_key, reminder_type)
        plant_label = self._resolve_plant_label(plant_key)

        if reminder_type == ReminderType.WATERING:
            phase_interval = self._get_phase_watering_interval(plant_key)
            due_dt = self._next_watering_due_date(
                profile,
                last,
                hemisphere="north",
                phase_watering_interval=phase_interval,
            )
            interval = self._engine._get_interval_days(
                profile,
                ReminderType.WATERING,
                "north",
                phase_watering_interval=phase_interval,
            )
            instruction = f"Water {plant_label} (every {interval} days)." if interval is not None else None
            return due_dt, instruction

        # Non-watering reminders: the engine owns the cadence and the instruction is
        # the shared per-type text (no interval baked into the string).
        due_date = self._engine.calculate_due_date(profile, reminder_type, last)
        if due_date is None:
            return None, None
        due_dt = datetime(due_date.year, due_date.month, due_date.day, tzinfo=UTC)
        return due_dt, care_reminder_instruction(reminder_type, plant_label)

    def _resolve_plant_label(self, plant_key: str) -> str:
        """Resolve a plant's display label (name → instance id → key) for task text."""
        if self._plant_repo is None:
            return plant_key
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None:
            return plant_key
        return plant.plant_name or plant.instance_id or plant_key

    def confirm_reminder(
        self,
        plant_key: str,
        reminder_type: ReminderType,
        notes: str | None = None,
        *,
        volume_liters: float | None = None,
        fertilizers_used: list[dict] | None = None,
        measured_ec: float | None = None,
        measured_ph: float | None = None,
        tenant_key: str = "",
        user_key: str = "",
    ) -> CareConfirmation:
        # SEC-001 defense-in-depth (mirrors the #517 shared-guard pattern): when a
        # caller passes its ``tenant_key`` (the MCP path always does), re-verify
        # the plant belongs to that tenant before mutating any care state. A
        # foreign/missing key fails closed with NotFoundError (→ HTTP 404), never
        # a 403, so a plant's existence is never disclosed across the boundary.
        if tenant_key and self._plant_repo is not None:
            plant = self._plant_repo.get_or_raise(plant_key)
            verify_tenant_ownership(plant, tenant_key, "PlantInstance")

        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            profile = self.get_or_create_profile(plant_key)

        now = datetime.now(UTC)
        watering_log_key: str | None = None
        is_feeding_type = reminder_type in (ReminderType.WATERING, ReminderType.FERTILIZING)
        effective_volume = volume_liters or 1.0

        # Create a single WateringLog for watering/fertilizing confirmations
        if is_feeding_type and self._watering_log_repo is not None:
            slot_keys = self._resolve_slot_keys(plant_key)
            ferts = [
                WateringLogFertilizer(
                    fertilizer_key=f["fertilizer_key"],
                    ml_per_liter=f["ml_applied"],
                )
                for f in (fertilizers_used or [])
            ]
            watering_log = WateringLog(
                # Stamp the tenant so the confirmation's log is visible in the
                # global Gießprotokoll view, which filters strictly on tenant_key
                # (#580). Prefer the caller-supplied tenant (MCP path); otherwise
                # resolve it from the plant so the REST care path is also bound.
                tenant_key=tenant_key or self._resolve_tenant_key(plant_key),
                logged_at=now,
                application_method=ApplicationMethod.DRENCH,
                volume_liters=effective_volume,
                slot_keys=slot_keys or ["default"],
                plant_keys=[plant_key],
                ec_before=measured_ec,
                ph_before=measured_ph,
                fertilizers_used=ferts,
                notes=notes,
            )
            created_log = self._watering_log_repo.create(watering_log)
            watering_log_key = created_log.key

        confirmation = CareConfirmation(
            plant_key=plant_key,
            care_profile_key=profile.key or "",
            reminder_type=reminder_type,
            action=ConfirmAction.CONFIRMED,
            confirmed_at=now,
            watering_log_key=watering_log_key,
            notes=notes,
            interval_at_time=self._get_current_interval(profile, reminder_type),
        )
        created = self._repo.create_confirmation(confirmation)
        if created.key and profile.key:
            self._repo.create_confirmation_edges(created.key, profile.key, plant_key)

        # Apply adaptive learning
        if profile.adaptive_learning_enabled:
            history = self._repo.get_confirmations_by_plant(plant_key, reminder_type, limit=10)
            learned = self._engine.apply_adaptive_learning(profile, reminder_type, history)
            if learned is not None:
                if reminder_type == ReminderType.WATERING:
                    self._repo.update_profile(
                        profile.key or "",
                        CareProfile(
                            **{**profile.model_dump(), "watering_interval_learned": learned},
                        ),
                    )
                elif reminder_type == ReminderType.FERTILIZING:
                    self._repo.update_profile(
                        profile.key or "",
                        CareProfile(
                            **{**profile.model_dump(), "fertilizing_interval_learned": learned},
                        ),
                    )

        # Auto-complete matching pending task
        closed_task = self._complete_pending_care_task(plant_key, reminder_type)

        # #742 — mark the plant's in-app care notification done (badge drops).
        resolved_tenant = tenant_key or self._resolve_tenant_key(plant_key)
        self._propagate(
            lambda p: p.on_care_confirmed(
                tenant_key=resolved_tenant,
                plant_key=plant_key,
                reminder_type=reminder_type,
            )
        )

        # Auto-create next watering task if opted in
        if reminder_type == ReminderType.WATERING:
            next_task = self._schedule_next_watering_after_completion(
                profile,
                created,
                just_completed_task=closed_task,
            )
            # The confirmation closed the current note; if a next watering task was
            # scheduled, surface it as the fresh, correctly-terminated care note.
            # ``on_care_confirmed`` above stamped that very row read, so the follow-up
            # only reaches the unread badge when the read state is cleared (#769).
            if next_task is not None:
                self._propagate_care_reschedule(
                    profile,
                    reminder_type,
                    resolved_tenant,
                    user_key,
                    next_task.due_date,
                    next_task.key,
                    announces_new_task=True,
                )

        return created

    def _is_foreign_plant(self, plant_key: str, tenant_key: str) -> bool:
        """Return whether *plant_key* must not be touched on behalf of *tenant_key*.

        The single cross-tenant write guard of the care paths (SEC-001): a plant
        that is unknown or belongs to another tenant is *foreign*, and every write
        derived from it (confirmation + graph edges, watering log, follow-up care
        task) must be refused. Fails **closed** — an unresolvable plant counts as
        foreign — and stays silent (``True``, caller returns ``None``) instead of
        raising, so a foreign key's existence is never disclosed (no cross-tenant
        oracle, SEC-B4).

        An empty ``tenant_key`` is the system context (Celery producers, MCP): it
        carries no tenant to verify against, so the check is skipped exactly as it
        is for a service built without a ``plant_repo``.
        """
        if not tenant_key or self._plant_repo is None:
            return False
        plant = self._plant_repo.get_by_key(plant_key)
        return plant is None or plant.tenant_key != tenant_key

    def _resolve_care_task_context(
        self,
        task: Task,
        tenant_key: str,
    ) -> tuple[str, CareProfile, ReminderType] | None:
        """Resolve and tenant-verify the plant, profile and reminder type of a care task.

        The single gate both task-queue bridges (:meth:`record_care_task_completion`
        and :meth:`record_care_task_skip`) pass through, so neither can write into a
        foreign tenant's care state. Returns ``None`` — a silent no-op for the
        caller — when any of these does not hold:

        * the task is a ``care_reminder`` on a ``plant_instance`` and names a plant;
        * the task itself belongs to ``tenant_key`` (defence in depth: the router
          already verifies it, but the service must not depend on that);
        * the plant belongs to ``tenant_key`` (:meth:`_is_foreign_plant`) — the
          check the completion bridge was missing (SEC-001): ``entity_key`` is
          caller-supplied at task creation and is *not* validated against the
          creating tenant, so a task in tenant A can point at a plant in tenant B;
        * the plant has a care profile and the task name carries a known reminder
          type suffix.
        """
        if task.category != TaskCategory.CARE_REMINDER or task.entity_type != "plant_instance":
            return None
        plant_key = task.entity_key
        if not plant_key:
            return None
        if tenant_key and task.tenant_key != tenant_key:
            return None
        if self._is_foreign_plant(plant_key, tenant_key):
            return None

        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            return None

        reminder_type = reminder_type_from_task_name(task.name)
        if reminder_type is None:
            return None
        return plant_key, profile, reminder_type

    def advance_watering_task_after_log(
        self,
        plant_key: str,
        last_confirmation: CareConfirmation | None = None,
        *,
        tenant_key: str = "",
    ) -> Task | None:
        """Advance the watering care-reminder task after an out-of-band watering log.

        Mirrors both the dashboard-confirmation path (:meth:`confirm_reminder`) and
        the task-queue completion bridge so that logging watering via the
        Gießprotokoll tab has the *same* effect as completing the watering task in
        the queue (#548): it completes the plant's still-open watering
        care-reminder task and schedules the next occurrence.

        Tenant-scoped and idempotent: when ``tenant_key`` is supplied the plant is
        verified to belong to that tenant first and a foreign/unknown plant is left
        untouched (``None``). Both the completion and the next-occurrence check
        route through the single tenant-aware dedup helper
        (:meth:`ITaskRepository.find_open_care_task`), so logging watering twice can
        neither double-complete an already-closed task nor leave more than one
        pending watering task behind: the second log finds the freshly scheduled
        follow-up (not yet due, so not completed) still ``PENDING`` and stops.

        The task closed here is handed on as ``just_completed_task`` so the
        completed-today recency rule cannot veto the very follow-up this advance
        exists to create (#761/#768). Returns the newly scheduled watering task,
        or ``None`` when no profile exists, auto-scheduling is disabled, or
        another task already satisfies the reminder.
        """
        if self._is_foreign_plant(plant_key, tenant_key):
            return None

        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            return None

        # Close the still-open watering task for the plant's own tenant (idempotent:
        # a task already completed earlier is not reopened/re-completed).
        closed_task = self._complete_pending_care_task(plant_key, ReminderType.WATERING)

        # The notification world has to be told, exactly as on the confirmation
        # path (#813). Without this the care note kept its *old* due date after a
        # watering was logged: not stale-marked, not updated, not re-raised — the
        # user saw a note announcing a date that had already been served, while
        # the freshly scheduled follow-up was announced nowhere.
        #
        # Mirroring `confirm_reminder` rather than inventing a third behaviour is
        # what this method's contract already promises ("the *same* effect as
        # completing the watering task in the queue", #548). The concern that a
        # backdated log should perhaps not clear today's badge does not arise
        # here: `WateringLogCreate` carries no client-settable timestamp, the
        # service stamps `watered_at=log.logged_at` and the accompanying
        # `CareConfirmation` with `confirmed_at=now`. A log is always a
        # present-tense confirmation on this path.
        resolved_tenant = tenant_key or self._resolve_tenant_key(plant_key)
        self._propagate(
            lambda p: p.on_care_confirmed(
                tenant_key=resolved_tenant,
                plant_key=plant_key,
                reminder_type=ReminderType.WATERING,
            )
        )

        next_task = self._schedule_next_watering_after_completion(
            profile,
            last_confirmation,
            just_completed_task=closed_task,
        )

        # `on_care_confirmed` above stamped the plant's single care row read, so
        # the follow-up only reaches the unread badge when that read state is
        # cleared — the #769 rule, applied to this path too.
        if next_task is not None:
            self._propagate_care_reschedule(
                profile,
                ReminderType.WATERING,
                resolved_tenant,
                "",
                next_task.due_date,
                next_task.key,
                announces_new_task=True,
            )

        return next_task

    def _schedule_next_watering_after_completion(
        self,
        profile: CareProfile,
        last_confirmation: CareConfirmation | None,
        *,
        just_completed_task: Task | None,
    ) -> Task | None:
        """Schedule the follow-up watering task of a complete-then-schedule operation.

        The single place that encodes the #761/#768 rule shared by all three
        complete-then-schedule paths (dashboard/API confirmation, Gießprotokoll
        log, task-queue completion): a task **this operation just completed** must
        not satisfy the dedup lookup, or the follow-up is never scheduled and the
        plant's reminder chain ends. ``just_completed_task`` is that task (``None``
        when nothing was closed, e.g. a second watering on the same day).

        Respects the profile's ``auto_create_watering_task`` opt-in and returns the
        newly scheduled task, or ``None``.
        """
        if not profile.auto_create_watering_task:
            return None

        phase_interval = self._get_phase_watering_interval(profile.plant_key)
        return self.ensure_next_watering_task(
            profile,
            last_confirmation,
            phase_watering_interval=phase_interval,
            just_completed_task=just_completed_task,
        )

    def record_care_task_completion(
        self,
        task: Task,
        *,
        tenant_key: str = "",
    ) -> Task | None:
        """Mirror a completed care-reminder task into the plant's care state (REQ-022).

        The task-queue completion bridge: when a ``care_reminder`` task on a plant
        instance is completed from the task queue, the plant's care state must move
        exactly as it does on the dashboard-confirmation path — a ``CareConfirmation``
        (plus its graph edges) is written, a watering/fertilizing log is
        materialised, and for watering the next occurrence is scheduled through the
        shared :meth:`_schedule_next_watering_after_completion`.

        ``tenant_key`` (the completing request's tenant, #580) is stamped onto the
        generated log so it surfaces in the global Gießprotokoll view. It is also
        the tenant every write is verified against: a task or plant belonging to
        another tenant is refused (:meth:`_resolve_care_task_context`, SEC-001).

        Non-care tasks, non-plant entities, foreign tasks/plants and plants without
        a care profile are no-ops. Returns the newly scheduled follow-up watering
        task, or ``None``.
        """
        context = self._resolve_care_task_context(task, tenant_key)
        if context is None:
            return None
        plant_key, profile, reminder_type = context

        confirmation = CareConfirmation(
            plant_key=plant_key,
            care_profile_key=profile.key or "",
            reminder_type=reminder_type,
            action=ConfirmAction.CONFIRMED,
            confirmed_at=datetime.now(UTC),
            task_key=task.key,
            notes=task.completion_notes,
            interval_at_time=self._engine._get_interval_days(profile, reminder_type),
        )
        created = self._repo.create_confirmation(confirmation)
        if created.key and profile.key:
            self._repo.create_confirmation_edges(created.key, profile.key, plant_key)
        self.complete_care_task_with_log(task.key or "", plant_key, reminder_type, tenant_key=tenant_key)

        if reminder_type != ReminderType.WATERING:
            return None

        # ``TaskService.complete_task`` has already stamped ``completed_at=now`` on
        # this very task, so it must not satisfy the follow-up dedup lookup (#768).
        return self._schedule_next_watering_after_completion(profile, None, just_completed_task=task)

    def record_care_task_skip(
        self,
        task: Task,
        *,
        tenant_key: str = "",
    ) -> CareConfirmation | None:
        """Mirror a skipped care-reminder task into the plant's care state (REQ-022).

        The skip sibling of :meth:`record_care_task_completion`: skipping a
        ``care_reminder`` task from the task queue records a ``SKIPPED``
        :class:`CareConfirmation` (plus its graph edges) so the plant's care
        history shows the deliberate omission and the adaptive interval learner
        sees it. Unlike a completion it materialises no log and schedules no
        follow-up — a skip is not a care event.

        This composition used to live inline in the API layer, reaching around the
        service into its repository and engine (NFR-001 violation); that also made
        it bypass the tenant guard. It now shares the single gate
        (:meth:`_resolve_care_task_context`), so a task or plant belonging to
        another tenant is refused (SEC-001).

        Returns the persisted confirmation, or ``None`` when the task is not a
        tenant-owned care reminder on a profiled plant.
        """
        context = self._resolve_care_task_context(task, tenant_key)
        if context is None:
            return None
        plant_key, profile, reminder_type = context

        confirmation = CareConfirmation(
            plant_key=plant_key,
            care_profile_key=profile.key or "",
            reminder_type=reminder_type,
            action=ConfirmAction.SKIPPED,
            confirmed_at=datetime.now(UTC),
            task_key=task.key,
            interval_at_time=self._engine._get_interval_days(profile, reminder_type),
        )
        created = self._repo.create_confirmation(confirmation)
        if created.key and profile.key:
            self._repo.create_confirmation_edges(created.key, profile.key, plant_key)
        return created

    def _get_phase_watering_interval(self, plant_key: str) -> int | None:
        """Look up watering_interval_days from the plant's current growth phase.

        Tries PhaseSequence (via entry -> definition) first, falls back to LifecycleConfig.
        """
        if not self._plant_repo:
            return None
        plant = self._plant_repo.get_by_key(plant_key)
        if not plant or not plant.current_phase_key:
            return None

        # Try PhaseSequence first: current_phase_key may be a PhaseSequenceEntry key
        if self._phase_seq_repo:
            entry = self._phase_seq_repo.get_entry_by_key(plant.current_phase_key)
            if entry:
                defn = self._phase_seq_repo.get_definition_by_key(entry.phase_definition_key)
                if defn and defn.watering_interval_days:
                    return defn.watering_interval_days

        # Fallback to LifecycleConfig
        if self._lifecycle_repo:
            phase = self._lifecycle_repo.get_phase_by_key(plant.current_phase_key)
            if phase and phase.watering_interval_days:
                return phase.watering_interval_days

        return None

    def _resolve_slot_keys(self, plant_key: str) -> list[str]:
        """Look up the slot_key for a plant instance."""
        if self._plant_repo is None:
            return []
        plant = self._plant_repo.get_by_key(plant_key)
        if plant is not None and plant.slot_key:
            return [plant.slot_key]
        return []

    def _resolve_tenant_key(self, plant_key: str) -> str:
        """Resolve a plant's ``tenant_key`` so care-task lookups stay tenant-scoped.

        Returns ``""`` when the plant can't be resolved (no plant repo / unknown
        key); the tenant-aware dedup helper then scopes to the empty-tenant slice
        rather than scanning across tenants (#509).
        """
        if self._plant_repo is None:
            return ""
        plant = self._plant_repo.get_by_key(plant_key)
        return plant.tenant_key if plant is not None else ""

    def _complete_pending_care_task(
        self,
        plant_key: str,
        reminder_type: ReminderType,
    ) -> Task | None:
        """Auto-complete the matching *due* pending care task; return it (#761/#768).

        Routes through the single tenant-aware dedup helper
        (:meth:`ITaskRepository.find_open_care_task`) so it can only ever complete
        a still-open task belonging to the plant's own tenant (#509). A task that
        was already completed earlier today is intentionally excluded here
        (``include_completed_today=False``): only an open task is completed.

        Only a task that is **due** (``due_date <= today``) is completed. A task
        scheduled for a later day is the *follow-up* of an earlier confirmation on
        the same day; closing it would collapse the whole reminder cycle into a
        single day.

        Returns:
            The task this call closed, or ``None`` when nothing open was due.
            Callers that schedule the follow-up occurrence pass it on as
            ``just_completed_task`` so the recency rule cannot self-block: without
            it that lookup finds the task this call just completed and the
            follow-up is never scheduled (#761/#768).
        """
        if self._task_repo is None:
            return None
        tenant_key = self._resolve_tenant_key(plant_key)
        task = self._task_repo.find_open_care_task(
            plant_key,
            reminder_type,
            tenant_key,
            include_completed_today=False,
        )
        if task is None or not _is_due(task.due_date):
            return None
        task.status = TaskStatus.COMPLETED.value
        task.completed_at = datetime.now(UTC)
        self._task_repo.update_task(task.key or "", task)
        return task

    def complete_care_task_with_log(
        self,
        task_key: str,
        plant_key: str,
        reminder_type: ReminderType,
        tenant_key: str = "",
    ) -> None:
        """Create a WateringLog when a watering/fertilizing task is completed via task queue.

        ``tenant_key`` (the completing request's tenant, #580) is stamped onto the
        log so the task-queue completion path — like the dashboard-confirmation
        path — yields a tenant-bound log the global Gießprotokoll view surfaces
        instead of dropping as an empty-tenant orphan. When the caller omits it the
        tenant is resolved from the plant so the log is never left unbound.
        """
        if self._watering_log_repo is None:
            return
        if reminder_type not in (ReminderType.WATERING, ReminderType.FERTILIZING):
            return

        now = datetime.now(UTC)
        slot_keys = self._resolve_slot_keys(plant_key)
        watering_log = WateringLog(
            tenant_key=tenant_key or self._resolve_tenant_key(plant_key),
            logged_at=now,
            application_method=ApplicationMethod.DRENCH,
            volume_liters=1.0,
            slot_keys=slot_keys or ["default"],
            plant_keys=[plant_key],
            notes=f"Auto-created from task completion ({task_key}).",
        )
        self._watering_log_repo.create(watering_log)

    def snooze_reminder(
        self,
        plant_key: str,
        reminder_type: ReminderType,
        snooze_days: int = 1,
    ) -> CareConfirmation:
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            profile = self.get_or_create_profile(plant_key)

        confirmation = CareConfirmation(
            plant_key=plant_key,
            care_profile_key=profile.key or "",
            reminder_type=reminder_type,
            action=ConfirmAction.SNOOZED,
            confirmed_at=datetime.now(UTC),
            snooze_days=snooze_days,
        )
        created = self._repo.create_confirmation(confirmation)
        if created.key and profile.key:
            self._repo.create_confirmation_edges(created.key, profile.key, plant_key)
        return created

    def get_care_dashboard(
        self,
        plant_data: list[dict],
        hemisphere: str = "north",
    ) -> list[CareDashboardEntry]:
        """Build care dashboard from plant data.

        plant_data: list of dicts with keys: plant_key, plant_name, species_name,
                    botanical_family, current_phase, has_nutrient_plan,
                    frost_sensitivity, cultivar_traits
        """
        entries: list[CareDashboardEntry] = []

        for plant in plant_data:
            plant_key = plant["plant_key"]
            profile = self.get_or_create_profile(
                plant_key,
                species_name=plant.get("species_name"),
                botanical_family=plant.get("botanical_family"),
            )

            # REQ-022 §3.2 — the winter-protection reminder types are gated by the
            # plant's OverwinteringProfile + frost sensitivity; without these the
            # engine suppresses every winter reminder (B1).
            overwintering_profile = self._resolve_overwintering_profile(plant_key)
            frost_sensitivity = plant.get("frost_sensitivity")
            cultivar_traits = plant.get("cultivar_traits")

            for rt in ReminderType:
                if not self._engine.should_generate_reminder(
                    profile,
                    rt,
                    plant.get("current_phase"),
                    hemisphere,
                    has_nutrient_plan=plant.get("has_nutrient_plan", False),
                    overwintering_profile=overwintering_profile,
                    frost_sensitivity=frost_sensitivity,
                    cultivar_traits=cultivar_traits,
                    irrigation_demand_capped_mm=plant.get("irrigation_demand_capped_mm"),
                ):
                    continue

                last = self._repo.get_last_confirmation(plant_key, rt)
                due_date = self._engine.calculate_due_date(
                    profile,
                    rt,
                    last,
                    plant.get("current_phase"),
                    hemisphere,
                    overwintering_profile=overwintering_profile,
                )
                urgency = self._engine.calculate_urgency(due_date)

                if urgency in ("overdue", "due_today", "upcoming"):
                    entries.append(
                        CareDashboardEntry(
                            plant_key=plant_key,
                            plant_name=plant.get("plant_name", ""),
                            species_name=plant.get("species_name"),
                            reminder_type=rt,
                            urgency=urgency,
                            due_date=due_date.isoformat() if due_date else None,
                            care_profile_key=profile.key or "",
                        )
                    )

        # Sort: overdue first, then due_today, then upcoming
        urgency_order = {"overdue": 0, "due_today": 1, "upcoming": 2}
        entries.sort(key=lambda e: urgency_order.get(e.urgency, 3))
        return entries

    def get_care_dashboard_for_tenant(
        self,
        tenant_key: str,
        hemisphere: str = "north",
    ) -> list[CareDashboardEntry]:
        """Build the care dashboard for all active plants of a tenant.

        Loads the tenant's plant instances (excluding removed plants), resolves
        the contextual data each plant needs (species name, current growth phase,
        nutrient-plan assignment) and delegates to :meth:`get_care_dashboard`.

        Tenant isolation is enforced by passing ``tenant_key`` to the plant
        repository; plants of other tenants are never loaded.
        """
        plant_data = self._build_plant_data_for_tenant(tenant_key)
        return self.get_care_dashboard(plant_data, hemisphere)

    def _build_plant_data_for_tenant(self, tenant_key: str) -> list[dict]:
        """Assemble ``plant_data`` dicts for the tenant's active plants.

        Each dict carries the fields :meth:`get_care_dashboard` consumes:
        ``plant_key``, ``plant_name``, ``species_name``, ``botanical_family``,
        ``current_phase`` and ``has_nutrient_plan``. Missing context resolves to
        ``None``/``False`` so a single broken record never aborts the dashboard.
        """
        if self._plant_repo is None:
            return []

        plants, _total = self._plant_repo.get_all(offset=0, limit=500, tenant_key=tenant_key)
        active_plants = [p for p in plants if p.removed_on is None]

        species_cache: dict[str, Species | None] = {}
        cultivar_traits_cache: dict[str, list[str]] = {}
        plant_data: list[dict] = []

        for plant in active_plants:
            plant_key = plant.key or ""
            if not plant_key:
                continue

            species = self._resolve_species(plant.species_key, species_cache)
            plant_data.append(
                {
                    "plant_key": plant_key,
                    "plant_name": plant.plant_name or plant.instance_id or "",
                    "species_name": (species.common_names[0] if species and species.common_names else None),
                    "botanical_family": None,
                    "current_phase": self._resolve_current_phase_name(plant.current_phase_key),
                    "has_nutrient_plan": self._has_nutrient_plan(plant_key, plant.tenant_key),
                    # REQ-022 §3.2 winter-reminder gating context (B1).
                    "frost_sensitivity": (species.frost_sensitivity if species else None),
                    "cultivar_traits": self._resolve_cultivar_traits(plant.cultivar_key, cultivar_traits_cache),
                }
            )

        return plant_data

    def _resolve_species(self, species_key: str | None, cache: dict[str, Species | None]) -> Species | None:
        """Resolve (and cache per call) the full species record."""
        if not species_key or self._species_repo is None:
            return None
        if species_key not in cache:
            cache[species_key] = self._species_repo.get_by_key(species_key)
        return cache[species_key]

    def _resolve_cultivar_traits(self, cultivar_key: str | None, cache: dict[str, list[str]]) -> list[str] | None:
        """Resolve a cultivar's traits as strings (drives the deadheading guard, B1)."""
        if not cultivar_key or self._species_repo is None:
            return None
        if cultivar_key not in cache:
            cultivar = self._species_repo.get_cultivar_by_key(cultivar_key)
            cache[cultivar_key] = [t.value for t in cultivar.traits] if cultivar else []
        return cache[cultivar_key]

    def resolve_overwintering_profile(self, plant_key: str) -> OverwinteringProfile | None:
        """Public accessor for the per-instance/shared-template overwintering profile.

        Encapsulates the N:1 template fallback so collaborators (e.g. the season
        state service) no longer reach into the private resolver (C3).
        """
        return self._resolve_overwintering_profile(plant_key)

    def ensure_seasonal_winter_tasks(self, plant_key: str, season_phase: SeasonPhase) -> list[Task]:
        """REQ-047 §3.2 — create the winter/spring tasks a SeasonState transition owns.

        Primary trigger for ``winter_protection`` / ``tuber_dig`` (on ``pre_winter``)
        and ``spring_uncover`` (on ``pre_spring``): the season phase drives them, not
        the calendar month. Idempotent — an equivalent active/recent task is never
        duplicated. The month-based path in the engine stays the fallback for sites
        without a SeasonState. Returns the tasks that were created.
        """
        if self._task_repo is None or self._plant_repo is None:
            return []
        reminder_types = _SEASON_PHASE_REMINDERS.get(season_phase, ())
        if not reminder_types:
            return []

        plant = self._plant_repo.get_by_key(plant_key)
        if plant is None or plant.removed_on is not None:
            return []

        profile = self._repo.get_profile_by_plant_key(plant_key) or self.get_or_create_profile(plant_key)
        overwintering_profile = self._resolve_overwintering_profile(plant_key)
        species = self._resolve_species(plant.species_key, {})
        frost_sensitivity = species.frost_sensitivity if species else None
        cultivar_traits = self._resolve_cultivar_traits(plant.cultivar_key, {})

        created: list[Task] = []
        for reminder_type in reminder_types:
            if not self._engine.should_generate_reminder(
                profile,
                reminder_type,
                overwintering_profile=overwintering_profile,
                frost_sensitivity=frost_sensitivity,
                cultivar_traits=cultivar_traits,
                season_phase=season_phase,
            ):
                continue
            task = self._ensure_care_task(plant, reminder_type)
            if task is not None:
                created.append(task)
        return created

    def _ensure_care_task(self, plant, reminder_type: ReminderType) -> Task | None:  # noqa: ANN001 — PlantInstance
        """Create one care-reminder Task idempotently (single tenant-aware dedup).

        Skips when the tenant-scoped dedup helper reports an equivalent task that
        is already PENDING/IN_PROGRESS or was completed today — the same predicate
        the daily ``generate_due_care_reminders`` producer uses (#509).
        """
        if self._task_repo is None:
            return None
        plant_key = plant.key or ""
        if self._task_repo.find_open_care_task(plant_key, reminder_type, plant.tenant_key) is not None:
            return None

        plant_label = plant.plant_name or plant.instance_id or plant_key
        today = today_utc()
        task = build_care_reminder_task(
            plant_key=plant_key,
            plant_label=plant_label,
            tenant_key=plant.tenant_key,
            reminder_type=reminder_type,
            due_date=datetime(today.year, today.month, today.day, tzinfo=UTC),
        )
        return create_care_reminder_task(self._task_repo, task)

    def _resolve_overwintering_profile(self, plant_key: str) -> OverwinteringProfile | None:
        """Load the plant's overwintering profile (one lookup per subject, B1).

        A per-instance profile wins (user override); otherwise the plant may reuse a
        shared species-level template (N:1), which is adapted into a transient
        profile so the winter-reminder gates fire identically for shared and
        per-instance subjects.
        """
        if self._overwintering_repo is not None:
            profile = self._overwintering_repo.get_profile_by_plant_key(plant_key)
            if profile is not None:
                return profile
        if self._overwintering_template_repo is not None:
            template = self._overwintering_template_repo.get_template_for_subject(plant_key=plant_key)
            return _template_to_profile(template, plant_key)
        return None

    def _resolve_current_phase_name(self, phase_key: str | None) -> str | None:
        """Resolve a plant's current growth-phase name (used for dormancy detection)."""
        if not phase_key or self._lifecycle_repo is None:
            return None
        phase = self._lifecycle_repo.get_phase_by_key(phase_key)
        return phase.name if phase else None

    def _has_nutrient_plan(self, plant_key: str, tenant_key: str) -> bool:
        """Return whether the plant has a nutrient plan assigned.

        ``tenant_key`` is the plant's own, forwarded to the tenant-scoped
        repository lookup (#927). Without one the answer is ``False`` rather than
        an unscoped read.
        """
        if self._nutrient_plan_repo is None or not tenant_key:
            return False
        return self._nutrient_plan_repo.get_plant_plan(plant_key, tenant_key=tenant_key) is not None

    def reset_profile(
        self,
        plant_key: str,
        species_name: str | None = None,
        botanical_family: str | None = None,
    ) -> CareProfile:
        """Reset profile to species/family defaults."""
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            raise NotFoundError("CareProfile", plant_key)

        new_profile = self._engine.auto_generate_profile(
            species_name=species_name,
            botanical_family=botanical_family,
            plant_key=plant_key,
        )
        new_data = new_profile.model_dump(exclude={"key", "created_at", "updated_at"})
        reset = CareProfile(**{**profile.model_dump(), **new_data})
        return self._repo.update_profile(profile.key or "", reset)

    def get_confirmation_history(
        self,
        plant_key: str,
        reminder_type: ReminderType | None = None,
        limit: int = 50,
    ) -> list[CareConfirmation]:
        return self._repo.get_confirmations_by_plant(plant_key, reminder_type, limit)

    def ensure_next_watering_task(
        self,
        profile: CareProfile,
        last_confirmation: CareConfirmation | None = None,
        hemisphere: str = "north",
        phase_watering_interval: int | None = None,
        *,
        just_completed_task: Task | None = None,
    ) -> Task | None:
        """Ensure exactly one pending watering task exists for this plant.

        Called after watering confirmation and by the daily Celery task.

        Args:
            profile: The plant's care profile (supplies the watering cadence).
            last_confirmation: Confirmation the next due date is measured from;
                looked up when omitted.
            hemisphere: Hemisphere used for the seasonal interval.
            phase_watering_interval: Growth-phase override of the interval.
            just_completed_task: The watering task the *calling operation itself*
                closed a moment ago (dashboard confirmation, watering log, task
                queue). Its presence narrows the dedup question to "is another
                task still open?" — see the guard below (#761/#768). Every caller
                that did not close a task leaves it ``None`` and keeps the
                completed-today recency rule (#509), which is what the producer
                paths (daily Celery run, interval edit) rely on.

        **Concurrency (#1301).** The dedup lookup below plus the create is a
        read-then-create, which holds sequentially and not concurrently: the 06:00
        beat and a manual ``POST /t/{slug}/tasks/generate-care-reminders`` are
        different processes, so no in-process lock spans them and both used to read
        "none open" and both insert. The promise in this docstring's first line is
        therefore enforced in *storage*, by the unique sparse index over the open
        care-reminder dedup key (``ensure_care_task_dedup_index``); the loser of
        the race is turned back into "another task already satisfies the reminder"
        by :func:`create_care_reminder_task`. The lookup below stays — it is what
        keeps the normal, uncontended case free of a rejected insert.

        Returns:
            The created task, or ``None`` when another task already satisfies the
            reminder (whether the lookup found it or the storage constraint did) or
            no due date can be computed.
        """
        if self._task_repo is None:
            return None

        plant_key = profile.plant_key

        # Resolve the plant's display name + tenant up front: the tenant_key scopes
        # the dedup lookup, so it must be known before the idempotency check (#509).
        plant_label = plant_key
        plant_tenant_key = ""
        if self._plant_repo is not None:
            plant = self._plant_repo.get_by_key(plant_key)
            if plant is not None:
                plant_label = plant.plant_name or plant.instance_id or plant_key
                plant_tenant_key = plant.tenant_key

        # Single tenant-aware dedup: skip when an equivalent watering task is
        # already open or was completed today (#509 recency rule).
        #
        # #761/#768 — when the caller closed the satisfying task itself in this very
        # operation, that recency rule is self-blocking: the "task completed today"
        # it would find IS the task just closed, so the follow-up the advance exists
        # to schedule would never be created. In that case the dedup question
        # narrows to "is another task still OPEN?"; a task completed today no longer
        # counts, because the occurrence being scheduled is due in the *future*, not
        # today. Only callers that closed a task opt in — the daily producer and the
        # interval reschedule keep the recency rule unchanged.
        existing = self._task_repo.find_open_care_task(
            plant_key,
            ReminderType.WATERING,
            plant_tenant_key,
            include_completed_today=just_completed_task is None,
        )
        if existing is not None:
            return None

        # Calculate next due date
        if last_confirmation is None:
            last_confirmation = self._repo.get_last_confirmation(
                plant_key,
                ReminderType.WATERING,
            )

        due_dt = self._next_watering_due_date(
            profile,
            last_confirmation,
            hemisphere=hemisphere,
            phase_watering_interval=phase_watering_interval,
        )
        if due_dt is None:
            return None

        interval = self._engine._get_interval_days(profile, ReminderType.WATERING, hemisphere)

        task = build_care_reminder_task(
            plant_key=plant_key,
            plant_label=plant_label,
            tenant_key=plant_tenant_key,
            reminder_type=ReminderType.WATERING,
            due_date=due_dt,
            instruction=f"Water {plant_label} (every {interval} days).",
        )
        return create_care_reminder_task(self._task_repo, task)

    def _next_watering_due_date(
        self,
        profile: CareProfile,
        last_confirmation: CareConfirmation | None,
        *,
        hemisphere: str,
        phase_watering_interval: int | None,
    ) -> datetime | None:
        """Compute the next watering due date, reusing the Task recurrence engine.

        For the fixed-interval case — a prior ``CONFIRMED`` confirmation exists —
        the cadence is expressed as a ``FREQ=DAILY;INTERVAL=n`` rule and advanced
        by the shared :class:`RecurrenceEngine`, the same machinery the generic
        recurring-task path uses (#510). The care engine stays the interval
        authority: it still computes the season/phase/adaptive interval ``n``.

        The two cases a static RRULE cannot express stay with the care engine
        (documented boundary): a ``SNOOZED`` last confirmation (due = snooze base +
        snooze days) and the no-confirmation bootstrap (due immediately at the
        profile's creation date). Behaviour is identical to the previous
        ``calculate_due_date`` path — the RRULE ``after`` a date midpoint at
        midnight equals ``base + n days``.
        """
        is_fixed_interval = last_confirmation is not None and not (
            last_confirmation.action == ConfirmAction.SNOOZED and last_confirmation.snooze_days
        )
        if is_fixed_interval:
            interval_days = self._engine._get_interval_days(
                profile,
                ReminderType.WATERING,
                hemisphere,
                phase_watering_interval=phase_watering_interval,
            )
            rule = self._recurrence.fixed_interval_rule(interval_days)
            if rule is None:
                return None
            base = last_confirmation.confirmed_at.date()
            base_dt = datetime(base.year, base.month, base.day, tzinfo=UTC)
            return self._recurrence.next_occurrence(rule, base_dt)

        # Snooze / bootstrap: not a static recurrence — keep the care engine.
        due_date = self._engine.calculate_due_date(
            profile,
            ReminderType.WATERING,
            last_confirmation,
            hemisphere=hemisphere,
            phase_watering_interval=phase_watering_interval,
        )
        if due_date is None:
            return None
        return datetime(due_date.year, due_date.month, due_date.day, tzinfo=UTC)

    def _get_current_interval(self, profile: CareProfile, reminder_type: ReminderType) -> int | None:
        if reminder_type == ReminderType.WATERING:
            return profile.watering_interval_learned or profile.watering_interval_days
        if reminder_type == ReminderType.FERTILIZING:
            return profile.fertilizing_interval_learned or profile.fertilizing_interval_days
        return None
