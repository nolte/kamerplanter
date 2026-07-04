from app.common.enums import SuccessionPlanStatus
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.engines.succession_plan_engine import SuccessionPlanEngine
from app.domain.interfaces.succession_plan_repository import ISuccessionPlanRepository, SuccessionPlanKey
from app.domain.models.planting_run import PlantingRun
from app.domain.models.succession_plan import SuccessionPlan
from app.domain.services.planting_run_service import PlantingRunService


class SuccessionPlanService:
    """REQ-013 §2 — CRUD plus run generation for succession (staggered sowing) plans.

    Generation delegates the actual PlantingRun/entry creation to
    :class:`PlantingRunService` (so runs are built exactly like any other run)
    and records ``has_succession_plan`` / ``succession_at`` graph edges.
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
    ) -> None:
        self._repo = repo
        self._run_service = run_service
        self._engine = engine or SuccessionPlanEngine()

    # ── CRUD ──────────────────────────────────────────────────────────

    def list_plans(self, offset: int = 0, limit: int = 50, tenant_key: str = "") -> tuple[list[SuccessionPlan], int]:
        return self._repo.get_all(offset, limit, tenant_key=tenant_key)

    def get_plan(self, key: SuccessionPlanKey, tenant_key: str = "") -> SuccessionPlan:
        plan = self._repo.get_or_raise(key)
        if tenant_key:
            verify_tenant_ownership(plan, tenant_key, "SuccessionPlan")
        return plan

    def create_plan(self, plan: SuccessionPlan) -> SuccessionPlan:
        plan.status = SuccessionPlanStatus.PLANNED
        plan.completed_batches = 0
        plan.total_batches = self._engine.compute_total_batches(plan.start_date, plan.end_date, plan.interval_days)
        return self._repo.create(plan)

    def update_plan(self, key: SuccessionPlanKey, data: dict, tenant_key: str = "") -> SuccessionPlan:
        plan = self.get_plan(key, tenant_key)
        patch = {field: value for field, value in data.items() if field in self._UPDATABLE_FIELDS}
        merged = SuccessionPlan.model_validate({**plan.model_dump(by_alias=False), **patch})
        # Keep the derived batch count consistent when the schedule changed.
        merged.total_batches = self._engine.compute_total_batches(
            merged.start_date, merged.end_date, merged.interval_days
        )
        return self._repo.update(key, merged)

    def delete_plan(self, key: SuccessionPlanKey, tenant_key: str = "") -> bool:
        self.get_plan(key, tenant_key)
        return self._repo.delete(key)

    # ── Run generation ────────────────────────────────────────────────

    def generate_runs(
        self, plan_key: SuccessionPlanKey, tenant_key: str = ""
    ) -> tuple[SuccessionPlan, list[PlantingRun]]:
        """Generate every remaining batch run for the plan and link the edges."""
        plan = self.get_plan(plan_key, tenant_key)
        total = self._engine.compute_total_batches(plan.start_date, plan.end_date, plan.interval_days)
        plan.total_batches = total

        created: list[PlantingRun] = []
        for run in self._engine.generate_batch_runs(plan):
            created.append(self._persist_run(plan_key, plan, run))

        if plan.location_key:
            self._repo.link_plan_to_location(plan_key, plan.location_key)

        plan.completed_batches = total
        plan.status = SuccessionPlanStatus.ACTIVE
        updated = self._repo.update(plan_key, plan)
        return updated, created

    def generate_next_run(
        self, plan_key: SuccessionPlanKey, tenant_key: str = ""
    ) -> tuple[SuccessionPlan, PlantingRun | None]:
        """Generate only the next not-yet-generated batch run, or nothing when done."""
        plan = self.get_plan(plan_key, tenant_key)
        if not plan.total_batches:
            plan.total_batches = self._engine.compute_total_batches(plan.start_date, plan.end_date, plan.interval_days)
        sequence = self._engine.next_batch_to_generate(plan)
        if sequence is None:
            return plan, None

        run = self._engine.generate_batch_run(plan, sequence, total=plan.total_batches)
        created = self._persist_run(plan_key, plan, run)

        if plan.location_key:
            self._repo.link_plan_to_location(plan_key, plan.location_key)

        plan.completed_batches = sequence
        if plan.status == SuccessionPlanStatus.PLANNED:
            plan.status = SuccessionPlanStatus.ACTIVE
        updated = self._repo.update(plan_key, plan)
        return updated, created

    def _persist_run(self, plan_key: SuccessionPlanKey, plan: SuccessionPlan, run: PlantingRun) -> PlantingRun:
        entry = self._engine.build_entry(plan)
        created = self._run_service.create_run(run, [entry])
        if created.key:
            self._repo.link_plan_to_run(plan_key, created.key)
        return created
