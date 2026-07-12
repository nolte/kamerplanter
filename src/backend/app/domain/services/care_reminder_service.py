from datetime import UTC, date, datetime

from app.common.enums import (
    ApplicationMethod,
    ConfirmAction,
    ReminderType,
    SeasonPhase,
    TaskCategory,
    TaskPriority,
    TaskStatus,
)
from app.common.exceptions import NotFoundError
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

#: Which winter/spring reminder types a SeasonState transition into a given phase
#: owns (REQ-047 §3.2). Used to create them the moment the site enters the phase.
_SEASON_PHASE_REMINDERS: dict[SeasonPhase, tuple[ReminderType, ...]] = {
    SeasonPhase.PRE_WINTER: (ReminderType.WINTER_PROTECTION, ReminderType.TUBER_DIG),
    SeasonPhase.PRE_SPRING: (ReminderType.SPRING_UNCOVER,),
}


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
    ) -> None:
        self._repo = care_repo
        self._engine = engine
        self._recurrence = recurrence or RecurrenceEngine()
        self._task_repo = task_repo
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

    def update_profile(self, plant_key: str, updates: dict) -> CareProfile:
        profile = self._repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            raise NotFoundError("CareProfile", plant_key)

        data = profile.model_dump()
        data.update(updates)
        updated = CareProfile(**data)
        return self._repo.update_profile(profile.key or "", updated)

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
    ) -> CareConfirmation:
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
        self._complete_pending_care_task(plant_key, reminder_type)

        # Auto-create next watering task if opted in
        if reminder_type == ReminderType.WATERING and profile.auto_create_watering_task:
            phase_interval = self._get_phase_watering_interval(plant_key)
            self.ensure_next_watering_task(profile, created, phase_watering_interval=phase_interval)

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
    ) -> None:
        """Auto-complete the matching pending care task when confirmed via dashboard.

        Routes through the single tenant-aware dedup helper
        (:meth:`ITaskRepository.find_open_care_task`) so it can only ever complete
        a still-open task belonging to the plant's own tenant (#509). A task that
        was already completed earlier today is intentionally excluded here
        (``include_completed_today=False``): only an open task is completed.
        """
        if self._task_repo is None:
            return
        tenant_key = self._resolve_tenant_key(plant_key)
        task = self._task_repo.find_open_care_task(
            plant_key,
            reminder_type,
            tenant_key,
            include_completed_today=False,
        )
        if task is None:
            return
        task.status = TaskStatus.COMPLETED.value
        task.completed_at = datetime.now(UTC)
        self._task_repo.update_task(task.key or "", task)

    def complete_care_task_with_log(
        self,
        task_key: str,
        plant_key: str,
        reminder_type: ReminderType,
    ) -> None:
        """Create a WateringLog when a watering/fertilizing task is completed via task queue."""
        if self._watering_log_repo is None:
            return
        if reminder_type not in (ReminderType.WATERING, ReminderType.FERTILIZING):
            return

        now = datetime.now(UTC)
        slot_keys = self._resolve_slot_keys(plant_key)
        watering_log = WateringLog(
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
                    "has_nutrient_plan": self._has_nutrient_plan(plant_key),
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
        today = date.today()
        task = build_care_reminder_task(
            plant_key=plant_key,
            plant_label=plant_label,
            tenant_key=plant.tenant_key,
            reminder_type=reminder_type,
            due_date=datetime(today.year, today.month, today.day, tzinfo=UTC),
        )
        return self._task_repo.create_task(task)

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

    def _has_nutrient_plan(self, plant_key: str) -> bool:
        """Return whether the plant has a nutrient plan assigned."""
        if self._nutrient_plan_repo is None:
            return False
        return self._nutrient_plan_repo.get_plant_plan(plant_key) is not None

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
    ) -> Task | None:
        """Ensure exactly one pending watering task exists for this plant.

        Called after watering confirmation and by the daily Celery task.
        Returns the created task or None if one already exists.
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
        # already open or was completed today.
        if self._task_repo.find_open_care_task(plant_key, ReminderType.WATERING, plant_tenant_key) is not None:
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
        return self._task_repo.create_task(task)

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
