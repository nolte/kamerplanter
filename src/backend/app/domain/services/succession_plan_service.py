from collections.abc import Callable
from typing import Any

import structlog
from pydantic import ValidationError as PydanticValidationError

from app.common.datetimes import today_utc
from app.common.enums import PlantingRunStatus, SuccessionPlanStatus
from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.engines.succession_plan_engine import SuccessionPlanEngine
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.succession_plan_repository import ISuccessionPlanRepository, SuccessionPlanKey
from app.domain.models.planting_run import PlantingRun
from app.domain.models.succession_plan import SuccessionPlan
from app.domain.services.location_ownership import resolve_owned_location
from app.domain.services.planting_reservation_service import BatchWindow, PlantingReservationService
from app.domain.services.planting_run_service import PlantingRunService

logger = structlog.get_logger()

#: Plan fields whose change makes the reservations of the not yet sown batches stale (GP-FR-074).
_RESERVATION_FIELDS = frozenset(
    {"interval_days", "start_date", "end_date", "plants_per_batch", "batch_duration_days", "location_key"}
)
#: Runs read per page when the plan's batches are looked up.
_BATCH_PAGE = 200
#: A plan in one of these states sows nothing more: its future batches release their slots.
_ENDED_PLAN_STATUSES = frozenset({SuccessionPlanStatus.COMPLETED, SuccessionPlanStatus.CANCELLED})


class SuccessionPlanService:
    """REQ-013 §2 — CRUD plus run generation for succession (staggered sowing) plans.

    Generation delegates the actual PlantingRun/entry creation to
    :class:`PlantingRunService` (so runs are built exactly like any other run)
    and records ``has_succession_plan`` / ``succession_at`` graph edges.

    **Slot reservation (REQ-053 GP-FR-074).** A batch that is generated for a
    bed with slots and is not yet due reserves its slots there for its window
    (``planned_from`` = sowing date, ``planned_until`` from
    ``batch_duration_days``), through :class:`PlantingReservationService` —
    the same V-08 rules and 409 ``slot.already_planned`` as ``plan-slots``.
    All batches of one generation are chosen before anything is written. A
    plan change that moves the schedule, the bed or the batch size, a plan
    that ends, and a deleted plan release the reservations of the batches that
    are still ``planned`` and not yet due; sown or started batches keep theirs.
    """

    _UPDATABLE_FIELDS = frozenset(
        {
            "name",
            "cultivar_key",
            "interval_days",
            "start_date",
            "end_date",
            "plants_per_batch",
            "reminder_days_before",
            "location_key",
            "notes",
            "status",
        }
    )

    def __init__(
        self,
        repo: ISuccessionPlanRepository,
        run_service: PlantingRunService,
        engine: SuccessionPlanEngine | None = None,
        site_repo: ISiteRepository | None = None,
        species_resolver: Callable[..., Any] | None = None,
        reservations: PlantingReservationService | None = None,
    ) -> None:
        self._repo = repo
        # Unwired (pure-domain tests), batches reserve nothing - generation behaves as before GP-FR-074.
        self._reservations = reservations
        # ``SpeciesService.get_species``-shaped: ``resolver(key, tenant_key=...)``
        # answers global, own or granted species and 404s the rest (#1872 C13).
        self._species_resolver = species_resolver
        self._run_service = run_service
        self._engine = engine or SuccessionPlanEngine()
        self._site_repo = site_repo

    # ── CRUD ──────────────────────────────────────────────────────────

    def list_plans(self, offset: int = 0, limit: int = 50, tenant_key: str = "") -> tuple[list[SuccessionPlan], int]:
        return self._repo.get_all(offset, limit, tenant_key=tenant_key)

    def list_plans_window(self, offset: int = 0, limit: int = 50, *, tenant_key: str) -> list[SuccessionPlan]:
        """One ``_key``-ordered page of the tenant's plans without the count query (MT-035, #2131)."""
        return self._repo.list_plans_window(offset, limit, tenant_key=tenant_key)

    def get_plan(self, key: SuccessionPlanKey, tenant_key: str = "") -> SuccessionPlan:
        plan = self._repo.get_or_raise(key)
        if tenant_key:
            verify_tenant_ownership(plan, tenant_key, "SuccessionPlan")
        return plan

    def _owned_plan(self, key: SuccessionPlanKey, *, tenant_key: str) -> SuccessionPlan:
        """The succession plan ``key`` of ``tenant_key``, or 404 — the load every write starts with (#2107).

        :meth:`get_plan` skips the check for an empty tenant, and the writes passed
        their defaulted ``tenant_key=""`` straight into it, so an omitted tenant
        switched the predicate off. Here it runs unconditionally.
        """
        plan = self._repo.get_or_raise(key)
        verify_tenant_ownership(plan, tenant_key, "SuccessionPlan")
        return plan

    def create_plan(self, plan: SuccessionPlan, *, tenant_key: str) -> SuccessionPlan:
        """Create a succession plan of ``tenant_key``.

        The tenant is stamped here and an empty one refused (#2107 review SEC-003):
        the location and species checks below skip an empty tenant.
        """
        if not tenant_key:
            raise ValueError("create_plan is tenant-scoped and requires a non-empty tenant_key (#2107).")
        plan.tenant_key = tenant_key
        plan.status = SuccessionPlanStatus.PLANNED
        plan.completed_batches = 0
        plan.total_batches = self._engine.compute_total_batches(plan.start_date, plan.end_date, plan.interval_days)
        self._verify_location_ownership(plan.location_key, plan.tenant_key)
        self._require_readable_species(plan.species_key, plan.tenant_key)
        return self._repo.create(plan)

    def update_plan(self, key: SuccessionPlanKey, data: dict, *, tenant_key: str) -> SuccessionPlan:
        plan = self._owned_plan(key, tenant_key=tenant_key)
        patch = {field: value for field, value in data.items() if field in self._UPDATABLE_FIELDS}
        # Reject a re-pointed location owned by another tenant before persisting.
        if "location_key" in patch:
            self._verify_location_ownership(patch["location_key"], plan.tenant_key)
        # The merged model runs ``validate_date_range``; a single-sided date change
        # (e.g. start_date after the stored end_date) raises a raw pydantic error.
        # Translate it to a 422 domain error instead of bubbling up as a 500.
        try:
            merged = SuccessionPlan.model_validate({**plan.model_dump(by_alias=False), **patch})
        except PydanticValidationError as exc:
            raise ValidationError(
                "The succession plan update is invalid.",
                details=[
                    {
                        "field": ".".join(str(loc) for loc in err["loc"]) or "body",
                        "reason": err["msg"],
                        "code": err["type"],
                    }
                    for err in exc.errors()
                ],
            ) from exc
        # Keep the derived batch count consistent when the schedule changed.
        merged.total_batches = self._engine.compute_total_batches(
            merged.start_date, merged.end_date, merged.interval_days
        )
        updated = self._repo.update(key, merged)
        if self._makes_reservations_stale(plan, merged):
            self._release_future_batches(key, tenant_key=plan.tenant_key)
        return updated

    def delete_plan(self, key: SuccessionPlanKey, *, tenant_key: str) -> bool:
        plan = self._owned_plan(key, tenant_key=tenant_key)
        self._release_future_batches(key, tenant_key=plan.tenant_key)
        return self._repo.delete(key)

    @staticmethod
    def _makes_reservations_stale(before: SuccessionPlan, after: SuccessionPlan) -> bool:
        if after.status in _ENDED_PLAN_STATUSES and before.status not in _ENDED_PLAN_STATUSES:
            return True
        return any(getattr(before, field) != getattr(after, field) for field in _RESERVATION_FIELDS)

    def _release_future_batches(self, plan_key: SuccessionPlanKey, *, tenant_key: str) -> list[str]:
        """Release the reservations of the plan's batches that are still ``planned`` and not yet due.

        A batch whose window has begun, or that was sown or started, is left alone: its slots carry what was
        planted. The runs themselves stay - deleting or moving them is the grower's decision (REQ-013).
        """
        if self._reservations is None:
            return []
        today = today_utc()
        released: list[str] = []
        for run in self._planned_batches(plan_key, tenant_key=tenant_key):
            start = run.planned_from or run.planned_start_date
            if not run.key or start is None or start <= today:
                continue
            if self._reservations.release_run_reservations(run.key, tenant_key=tenant_key):
                released += [run.key]
        if released:
            logger.info("succession_plan.batches_released", plan_key=plan_key, runs=len(released))
        return released

    def _planned_batches(self, plan_key: SuccessionPlanKey, *, tenant_key: str) -> list[PlantingRun]:
        """The tenant's ``planned`` runs generated by the plan, read page by page through the tenant-scoped window."""
        filters = {"succession_plan_key": plan_key, "status": PlantingRunStatus.PLANNED.value}
        runs: list[PlantingRun] = []
        offset = 0
        while True:
            page = self._run_service.list_runs_window(offset, _BATCH_PAGE, filters, tenant_key=tenant_key)
            runs += page
            if len(page) < _BATCH_PAGE:
                return runs
            offset += _BATCH_PAGE

    # ── Run generation ────────────────────────────────────────────────

    def generate_runs(
        self, plan_key: SuccessionPlanKey, *, tenant_key: str
    ) -> tuple[SuccessionPlan, list[PlantingRun]]:
        """Generate only the not-yet-generated batch runs and link their edges.

        Idempotent: a second call after every batch was generated is a no-op — it
        creates no additional runs and no duplicate ``has_succession_plan`` edges.
        """
        plan = self._owned_plan(plan_key, tenant_key=tenant_key)
        self._verify_location_ownership(plan.location_key, plan.tenant_key)
        total = self._engine.compute_total_batches(plan.start_date, plan.end_date, plan.interval_days)
        plan.total_batches = total

        start_sequence = plan.completed_batches + 1
        runs = self._engine.generate_batch_runs(plan, start_sequence=start_sequence)
        # Every batch's slots are chosen before the first run is stored: a refusal leaves nothing behind.
        picks = self._pick_slots(plan, runs)
        created: list[PlantingRun] = []
        try:
            for run, slot_keys in zip(runs, picks, strict=True):
                created += [self._persist_run(plan_key, plan, run, slot_keys)]
        except Exception:
            # A reservation placed between the choice and the write refused one batch; ``_persist_run`` took that
            # run back. The batches stored before it count, so a later call does not create them a second time.
            if created:
                self._record_progress(plan_key, plan, start_sequence - 1 + len(created))
            raise

        if created and plan.location_key:
            self._repo.link_plan_to_location(plan_key, plan.location_key)

        plan.completed_batches = total
        if total:
            plan.status = SuccessionPlanStatus.ACTIVE
        updated = self._repo.update(plan_key, plan)
        return updated, created

    def _record_progress(self, plan_key: SuccessionPlanKey, plan: SuccessionPlan, generated: int) -> None:
        if plan.location_key:
            self._repo.link_plan_to_location(plan_key, plan.location_key)
        plan.completed_batches = generated
        plan.status = SuccessionPlanStatus.ACTIVE
        self._repo.update(plan_key, plan)

    def generate_next_run(
        self, plan_key: SuccessionPlanKey, *, tenant_key: str
    ) -> tuple[SuccessionPlan, PlantingRun | None]:
        """Generate only the next not-yet-generated batch run, or nothing when done."""
        plan = self._owned_plan(plan_key, tenant_key=tenant_key)
        self._verify_location_ownership(plan.location_key, plan.tenant_key)
        if not plan.total_batches:
            plan.total_batches = self._engine.compute_total_batches(plan.start_date, plan.end_date, plan.interval_days)
        sequence = self._engine.next_batch_to_generate(plan)
        if sequence is None:
            return plan, None

        run = self._engine.generate_batch_run(plan, sequence, total=plan.total_batches)
        [slot_keys] = self._pick_slots(plan, [run])
        created = self._persist_run(plan_key, plan, run, slot_keys)

        if plan.location_key:
            self._repo.link_plan_to_location(plan_key, plan.location_key)

        plan.completed_batches = sequence
        if plan.status == SuccessionPlanStatus.PLANNED:
            plan.status = SuccessionPlanStatus.ACTIVE
        updated = self._repo.update(plan_key, plan)
        return updated, created

    def _verify_location_ownership(self, location_key: str | None, tenant_key: str) -> None:
        """Reject a location owned by another tenant (cross-tenant reference guard).

        Generated runs inherit ``location_key`` verbatim, so an unverified foreign
        location would let a plan write runs into another tenant's location. When no
        ``site_repo`` is wired the check is skipped (pure-domain / unit contexts).

        Anchored on the parent site (#1397). Written as
        ``location.tenant_key != tenant_key`` this refused **every** location,
        the caller's own included, because that field is persisted empty.
        """
        if not location_key or not tenant_key:
            return
        # Fail closed without the anchor (#1876 review, SEC-004).
        if self._site_repo is None:
            raise NotFoundError("Location", location_key)
        resolve_owned_location(self._site_repo, location_key, tenant_key)

    def _require_readable_species(self, species_key: str | None, tenant_key: str) -> None:
        """Refuse a plan species the tenant may not read (#1872 C13).

        The key was stored as given and later copied into every generated run
        entry. Skipped without a tenant (internal callers); fails closed when a
        tenant is given and no resolver is wired.
        """
        if not species_key or not tenant_key:
            return
        if self._species_resolver is None:
            raise NotFoundError("Species", species_key)
        self._species_resolver(species_key, tenant_key=tenant_key)

    def _pick_slots(self, plan: SuccessionPlan, runs: list[PlantingRun]) -> list[list[str]]:
        """The slots each batch reserves in the plan's bed, aligned with ``runs`` (GP-FR-074).

        A batch whose sowing date has passed reserves nothing: it is overdue, and where it went is the grower's
        call. Without a bed, or unwired, nothing is reserved either.
        """
        nothing: list[list[str]] = [[] for _ in runs]
        if self._reservations is None or not plan.location_key or not runs:
            return nothing
        today = today_utc()
        due = [index for index, run in enumerate(runs) if run.planned_from is not None and run.planned_from >= today]
        if not due:
            return nothing
        windows = [
            BatchWindow(
                planned_from=runs[index].planned_from or today,
                planned_until=runs[index].planned_until,
                needed=plan.plants_per_batch,
            )
            for index in due
        ]
        picks = self._reservations.pick_batch_slots(plan.location_key, windows, tenant_key=plan.tenant_key)
        for index, slot_keys in zip(due, picks, strict=True):
            nothing[index] = slot_keys
        return nothing

    def _persist_run(
        self, plan_key: SuccessionPlanKey, plan: SuccessionPlan, run: PlantingRun, slot_keys: list[str]
    ) -> PlantingRun:
        """Store one batch run with its entry and, when it has slots, its reservation.

        A refused reservation takes the run back, so a batch never exists without the slots it was meant to hold.
        """
        entry = self._engine.build_entry(plan)
        created = self._run_service.create_run(run, [entry], tenant_key=plan.tenant_key)
        if created.key and slot_keys and self._reservations is not None:
            try:
                stored_entries = self._run_service.list_entries(created.key)
                self._reservations.reserve_slots(
                    created.key,
                    tenant_key=plan.tenant_key,
                    entry_key=stored_entries[0].key or "",
                    slot_keys=slot_keys,
                )
            except Exception:
                self._run_service.delete_run(created.key, tenant_key=plan.tenant_key)
                raise
        if created.key:
            self._repo.link_plan_to_run(plan_key, created.key)
        return created
