from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.common.enums import ApplicationMethod, ConfirmAction, ReminderType, TaskStatus
from app.common.exceptions import ValidationError
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.engines.nutrient_engine import RunoffAnalyzer
from app.domain.engines.watering_engine import WateringEngine
from app.domain.interfaces.care_reminder_repository import ICareReminderRepository
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.interfaces.nutrient_plan_repository import INutrientPlanRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.planting_run_repository import IPlantingRunRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.task_repository import ITaskRepository
from app.domain.interfaces.watering_log_repository import IWateringLogRepository
from app.domain.models.care_reminder import CareConfirmation
from app.domain.models.watering_log import (
    WateringLog,
    WateringLogFertilizer,
    find_watering_log_violations,
)
from app.domain.services.feeding_references import (
    FillEventAnchors,
    require_owned_fill_event,
    require_readable_nutrient_plan,
)
from app.domain.services.fertilizer_references import assert_fertilizers_visible
from app.domain.services.location_ownership import resolve_owned_slot
from app.domain.services.watering_confirmation_scope import own_task_or_none, require_confirmable_run

if TYPE_CHECKING:
    from app.domain.services.care_reminder_service import CareReminderService


class WateringLogService:
    def __init__(
        self,
        repo: IWateringLogRepository,
        engine: WateringEngine,
        site_repo: ISiteRepository,
        run_repo: IPlantingRunRepository | None = None,
        task_repo: ITaskRepository | None = None,
        nutrient_plan_repo: INutrientPlanRepository | None = None,
        care_repo: ICareReminderRepository | None = None,
        care_service: CareReminderService | None = None,
        plant_repo: IPlantInstanceRepository | None = None,
        fertilizer_repo: IFertilizerRepository | None = None,
        fill_event_anchors: FillEventAnchors | None = None,
    ) -> None:
        self._repo = repo
        # #1872 C6: a fill event's tenant is its tank's.
        self._fill_event_anchors = fill_event_anchors
        self._fertilizer_repo = fertilizer_repo
        self._engine = engine
        self._site_repo = site_repo
        self._run_repo = run_repo
        self._task_repo = task_repo
        self._nutrient_plan_repo = nutrient_plan_repo
        self._care_repo = care_repo
        self._care_service = care_service
        self._plant_repo = plant_repo
        self._runoff_analyzer = RunoffAnalyzer()

    # ── CRUD ─────────────────────────────────────────────────────────────

    def create_log(self, log: WateringLog) -> dict:
        """Create a watering log and return it with any warnings.

        Every ``fertilizers_used`` key must name a fertilizer the log's tenant can
        see — own or global — or the log is refused with 422 before anything is
        written (#1713).
        """
        self._assert_fertilizers_visible(log)
        # The stored references under the log's tenant (#1872 C6, C7).
        if log.tank_fill_event_key:
            require_owned_fill_event(self._fill_event_anchors, log.tank_fill_event_key, log.tenant_key)
        if log.nutrient_plan_key:
            require_readable_nutrient_plan(self._nutrient_plan_repo, log.nutrient_plan_key, log.tenant_key)
        # Every slot under the log's tenant, before anything is read through it
        # or written (#1871 B4): the slots were taken as given — LOG_SLOT edges to
        # any tenant's slots, and the first one's location, read unscoped, shaped
        # the warnings (an oracle). resolve_owned_slot answers 404 alike for a
        # foreign and an unknown slot.
        owned = [resolve_owned_slot(self._site_repo, key, log.tenant_key) for key in log.slot_keys]
        irrigation_system = owned[0][1].irrigation_system if owned else None

        # Reuse WateringEngine for validation
        plant_keys = log.plant_keys if log.plant_keys else ["_compat"]
        from app.domain.models.watering_event import WateringEvent

        compat_event = WateringEvent(
            watered_at=log.logged_at,
            application_method=log.application_method,
            volume_liters=log.volume_liters,
            plant_keys=plant_keys,
        )
        warnings = self._engine.validate_and_warn(compat_event, irrigation_system)

        created = self._repo.create(log)

        # Record the confirmation for each plant so "Zuletzt gegossen" updates, then
        # advance the watering care-reminder task exactly like the task-queue
        # completion bridge (#548): complete the open watering task and schedule the
        # next occurrence. Without this the Gießprotokoll path left the task
        # ``pending`` forever, so the activity plan / dashboard kept showing a stale
        # open task even though watering had been logged.
        if self._care_repo and log.plant_keys:
            now = datetime.now(UTC)
            for plant_key in log.plant_keys:
                if plant_key == "_compat":
                    continue
                # Fail-closed tenant guard (SEC-001): resolve the plant and skip the
                # whole care-state block for a missing or foreign-tenant plant_key
                # *before* any confirmation/edge is written. Tenant isolation must
                # not rely on key-unguessability, so a tenant-A caller supplying a
                # tenant-B plant_key writes no CareConfirmation into tenant B's care
                # graph. Mirrors the defense-in-depth guard in
                # ``care_reminder_service.confirm_reminder`` / ``advance_watering_
                # task_after_log`` (silent skip, never a 403 that leaks existence).
                plant = self._plant_repo.get_by_key(plant_key) if self._plant_repo else None
                if plant is None or plant.tenant_key != log.tenant_key:
                    continue
                profile = self._care_repo.get_profile_by_plant_key(plant_key)
                if profile is None:
                    continue
                confirmation = CareConfirmation(
                    plant_key=plant_key,
                    care_profile_key=profile.key or "",
                    reminder_type=ReminderType.WATERING,
                    action=ConfirmAction.CONFIRMED,
                    confirmed_at=now,
                    watering_log_key=created.key,
                )
                saved = self._care_repo.create_confirmation(confirmation)
                if saved.key and profile.key:
                    self._care_repo.create_confirmation_edges(saved.key, profile.key, plant_key)
                # Tenant-scoped, idempotent task advancement through the shared CARE
                # helpers. ``log.tenant_key`` gates it so a foreign-tenant plant is
                # never touched.
                if self._care_service is not None:
                    self._care_service.advance_watering_task_after_log(
                        plant_key,
                        saved,
                        tenant_key=log.tenant_key,
                    )

        return {"log": created, "warnings": warnings}

    def _assert_fertilizers_visible(self, log: WateringLog) -> None:
        assert_fertilizers_visible(
            self._fertilizer_repo,
            (f.fertilizer_key for f in log.fertilizers_used),
            tenant_key=log.tenant_key,
            field="fertilizers_used",
            owner="WateringLogService",
        )

    def get_log(self, key: str, tenant_key: str = "") -> WateringLog:
        log = self._repo.get_or_raise(key)
        if tenant_key:
            verify_tenant_ownership(log, tenant_key, "WateringLog")
        return log

    def list_logs(
        self,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str = "",
    ) -> tuple[list[WateringLog], int]:
        return self._repo.get_all(offset, limit, tenant_key=tenant_key)

    def update_log(self, key: str, data: dict) -> WateringLog:
        """Apply a partial update to a watering log.

        Args:
            key: Document key of the log.
            data: Field subset to change; unknown and ``None`` values are dropped.

        Returns:
            The updated log (or the unchanged one, when nothing applies).

        Raises:
            ValidationError: The patch would break a cross-field rule of the log.
        """
        existing = self.get_log(key)
        allowed_fields = {
            "application_method",
            "is_supplemental",
            "volume_liters",
            "ec_before",
            "ec_after",
            "ph_before",
            "ph_after",
            "runoff_ec",
            "runoff_ph",
            "runoff_volume_liters",
            "notes",
        }
        update_fields = {k: v for k, v in data.items() if k in allowed_fields and v is not None}
        if not update_fields:
            return existing

        # A patch is only ever valid against the *merged* state: ``is_supplemental``
        # and ``application_method`` can each arrive alone, so no request schema can
        # judge the pair. Checking here matters because the repository writes the
        # document first and rebuilds the domain model from it afterwards — an
        # invalid combination was persisted *and* answered with a 500, poisoning
        # every later read of that log (#970). Same rules as everywhere else, read
        # from the one place that states them.
        violations = find_watering_log_violations(
            is_supplemental=update_fields.get("is_supplemental", existing.is_supplemental),
            application_method=update_fields.get("application_method", existing.application_method),
            slot_keys=existing.slot_keys,
            plant_keys=existing.plant_keys,
        )
        if violations:
            raise ValidationError(
                violations[0].message,
                details=[
                    {"field": field, "reason": violation.message, "code": violation.code}
                    for violation in violations
                    for field in violation.fields
                ],
            )
        return self._repo.update_fields(key, update_fields)

    def delete_log(self, key: str) -> bool:
        self.get_log(key)
        return self._repo.delete(key)

    # ── Queries ──────────────────────────────────────────────────────────

    def get_by_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str = "",
    ) -> list[WateringLog]:
        """List a plant's watering logs, tenant-scoped (SEC-B4, #580).

        The per-plant Gießprotokoll view is tenant-bound just like the global list:
        ``tenant_key`` is forwarded to the repository so a caller can neither read
        another tenant's logs nor the orphaned empty-tenant logs the pre-fix
        care/task path produced.
        """
        return self._repo.get_by_plant(plant_key, offset, limit, tenant_key=tenant_key)

    def get_by_slot(
        self,
        slot_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> list[WateringLog]:
        """A slot's watering logs, scoped to ``tenant_key`` (#927)."""
        return self._repo.get_by_slot(slot_key, offset, limit, tenant_key=tenant_key)

    def get_by_location(
        self,
        location_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> list[WateringLog]:
        """A location's watering logs, scoped to ``tenant_key`` (#927)."""
        return self._repo.get_by_location(location_key, offset, limit, tenant_key=tenant_key)

    def get_stats(self, location_key: str, *, tenant_key: str) -> dict:
        """A location's watering-log statistics, scoped to ``tenant_key`` (#927)."""
        return self._repo.get_stats_by_location(location_key, tenant_key=tenant_key)

    def resolve_plant_names(self, plant_keys: list[str], *, tenant_key: str) -> dict[str, str]:
        """Batch-resolve plant keys → display names, inside ``tenant_key`` (#952)."""
        return self._repo.resolve_plant_names(plant_keys, tenant_key=tenant_key)

    def resolve_fertilizer_names(self, fert_keys: list[str], *, tenant_key: str) -> dict[str, str]:
        """Batch-resolve fertilizer keys → display names, visible to ``tenant_key`` (#1708)."""
        return self._repo.resolve_fertilizer_names(fert_keys, tenant_key=tenant_key)

    # ── Runoff analysis ──────────────────────────────────────────────────

    def analyze_runoff(self, key: str) -> dict:
        log = self.get_log(key)

        if (
            log.ec_before is None
            or log.runoff_ec is None
            or log.ph_before is None
            or log.runoff_ph is None
            or log.runoff_volume_liters is None
        ):
            return {"error": "Insufficient runoff data for analysis"}

        return self._runoff_analyzer.analyze(
            input_ec_ms=log.ec_before,
            runoff_ec_ms=log.runoff_ec,
            input_ph=log.ph_before,
            runoff_ph=log.runoff_ph,
            input_volume_liters=log.volume_liters,
            runoff_volume_liters=log.runoff_volume_liters,
        )

    # ── Confirm / Quick-confirm ──────────────────────────────────────────

    def confirm_watering(
        self,
        run_key: str,
        task_key: str,
        measured_ec: float | None = None,
        measured_ph: float | None = None,
        volume_liters: float | None = None,
        overrides: dict | None = None,
        channel_id: str | None = None,
        *,
        tenant_key: str,
    ) -> dict:
        """Confirm a scheduled watering task: create ONE WateringLog, complete task.

        ``tenant_key`` (the confirming request's tenant, #580) is stamped onto the
        created ``WateringLog`` so this task-confirmation path — like the direct
        create path — produces a tenant-bound log that the global Gießprotokoll
        view (which filters strictly on ``tenant_key``) surfaces instead of
        silently dropping as an empty-tenant orphan.
        """
        if self._run_repo is None or self._task_repo is None:
            raise ValueError("confirm_watering requires run_repo and task_repo")
        # The run comes from the request body: resolve it under the tenant before
        # anything is read through it or written (#1864 sweep, L8).
        require_confirmable_run(self._run_repo, run_key, tenant_key=tenant_key)

        # Get run and plan info
        plan_key = self._run_repo.get_run_nutrient_plan_key(run_key)
        plan = None
        watering_schedule = None
        if plan_key and self._nutrient_plan_repo:
            plan = self._nutrient_plan_repo.get_by_key(plan_key)
            if plan and hasattr(plan, "watering_schedule"):
                watering_schedule = plan.watering_schedule

        # Get plants in the run
        plants = self._run_repo.get_run_plants(run_key, include_detached=False)
        plant_keys = [p["_key"] for p in plants if p.get("_key")]
        slot_keys = list({p.get("slot_key", "") for p in plants if p.get("slot_key")})
        if not slot_keys:
            slot_keys = ["default"]

        # Build fertilizers list from overrides or plan
        fertilizers_used: list[WateringLogFertilizer] = []
        if overrides and "fertilizers" in overrides:
            for f in overrides["fertilizers"]:
                fertilizers_used.append(
                    WateringLogFertilizer(
                        fertilizer_key=f["fertilizer_key"],
                        ml_per_liter=f["ml_per_liter"],
                    )
                )

        now = datetime.now(UTC)
        application_method = watering_schedule.application_method if watering_schedule else ApplicationMethod.DRENCH

        watering_log = WateringLog(
            tenant_key=tenant_key,
            logged_at=now,
            application_method=application_method,
            volume_liters=volume_liters or 1.0,
            slot_keys=slot_keys,
            plant_keys=plant_keys,
            nutrient_plan_key=plan_key,
            ec_before=measured_ec,
            ph_before=measured_ph,
            task_key=task_key,
            channel_id=channel_id,
            fertilizers_used=fertilizers_used,
        )
        # The override lines come from the request (#1713): checked before the
        # log is written, like the direct create path.
        self._assert_fertilizers_visible(watering_log)
        created_log = self._repo.create(watering_log)

        # Complete the task
        task_completed = False
        # Only the tenant's own task is completed; a foreign one is treated as
        # missing — same answer, nothing changed (#1864 sweep, L8).
        task_doc = own_task_or_none(self._task_repo, task_key, tenant_key=tenant_key)
        if task_doc:
            self._task_repo.update_fields(
                task_key,
                {
                    "status": TaskStatus.COMPLETED.value,
                    "completed_at": now.isoformat(),
                },
            )
            task_completed = True

        # Create care confirmation for each plant
        if self._care_repo:
            for plant_key in plant_keys:
                confirmation = CareConfirmation(
                    plant_key=plant_key,
                    reminder_type=ReminderType.WATERING,
                    action=ConfirmAction.CONFIRMED,
                    confirmed_at=now,
                    task_key=task_key,
                    watering_log_key=created_log.key,
                )
                self._care_repo.create_confirmation(confirmation)

        return {
            "watering_log_key": created_log.key or "",
            "task_completed": task_completed,
            "warnings": [],
        }

    def quick_confirm_watering(self, run_key: str, task_key: str, *, tenant_key: str) -> dict:
        """Quick confirm using plan defaults -- no overrides."""
        return self.confirm_watering(run_key, task_key, tenant_key=tenant_key)
