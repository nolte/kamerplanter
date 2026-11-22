from datetime import date, timedelta

from app.common.enums import PlantingRunStatus, PlantingRunType
from app.common.exceptions import PlanError
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.models.succession_plan import (
    ERROR_SUCCESSION_QUOTA,
    MAX_SUCCESSION_BATCHES,
    SuccessionPlan,
    succession_batch_count,
)

#: ``PlantingRun.source`` of a batch run (REQ-013 §2, ``RUN_SOURCES``).
SOURCE_SUCCESSION = "succession"


class SuccessionPlanEngine:
    """Pure logic for succession (staggered-sowing) plans — no DB access.

    REQ-013 §2 (Szenario 4): a succession plan is expanded into one PlantingRun
    per batch. The number of batches and each batch's planned start date follow
    deterministically from the plan schedule (``start_date``, ``end_date``,
    ``interval_days``).
    """

    def compute_total_batches(self, start_date: date, end_date: date, interval_days: int) -> int:
        """Return the number of batches that fit into the sowing window.

        Batches are sown on ``start_date`` and then every ``interval_days`` up to
        (and including) ``end_date``: ``floor((end - start) / interval) + 1``.
        The window always contains at least the first batch.
        """
        return succession_batch_count(start_date, end_date, interval_days)

    def build_entry(self, plan: SuccessionPlan) -> PlantingRunEntry:
        """Build the single species entry each generated (monoculture) run carries."""
        return PlantingRunEntry(
            species_key=plan.species_key,
            cultivar_key=plan.cultivar_key,
            quantity=plan.plants_per_batch,
            id_prefix=self._derive_id_prefix(plan),
        )

    def generate_batch_runs(self, plan: SuccessionPlan, start_sequence: int = 1) -> list[PlantingRun]:
        """Return one (unpersisted) PlantingRun per still-missing batch of the plan.

        ``start_sequence`` (1-based) is the first batch to emit, so re-running
        generation for an already-partially-generated plan only produces the
        remaining batches (idempotency). When ``start_sequence`` exceeds the batch
        count the result is empty (no-op).
        """
        total = self.compute_total_batches(plan.start_date, plan.end_date, plan.interval_days)
        # Defensive: the model refuses such a schedule, but a stored legacy row is not re-validated on every path —
        # no generation builds more runs than the quota, whatever the plan says.
        if total > MAX_SUCCESSION_BATCHES:
            raise PlanError(
                ERROR_SUCCESSION_QUOTA,
                f"A succession plan may hold at most {MAX_SUCCESSION_BATCHES} batches.",
                status_code=422,
                field="interval_days",
                quota="batches",
                limit=MAX_SUCCESSION_BATCHES,
                current=total,
            )
        start = max(start_sequence, 1)
        return [self.generate_batch_run(plan, sequence, total=total) for sequence in range(start, total + 1)]

    def generate_batch_run(self, plan: SuccessionPlan, sequence: int, total: int | None = None) -> PlantingRun:
        """Build a single (unpersisted) PlantingRun for batch ``sequence`` (1-based)."""
        if total is None:
            total = self.compute_total_batches(plan.start_date, plan.end_date, plan.interval_days)
        planned_start = plan.start_date + timedelta(days=(sequence - 1) * plan.interval_days)
        return PlantingRun(
            name=f"{plan.name} {sequence}/{total}",
            run_type=PlantingRunType.MONOCULTURE,
            status=PlantingRunStatus.PLANNED,
            planned_start_date=planned_start,
            planned_quantity=plan.plants_per_batch,
            location_key=plan.location_key,
            tenant_key=plan.tenant_key,
            succession_plan_key=plan.key,
            succession_sequence=sequence,
            succession_total=total,
            source=SOURCE_SUCCESSION,
            # The batch's reservation window (GP-FR-065/074): from its sowing date for the plan's batch duration.
            planned_from=planned_start,
            planned_until=self.batch_until(plan, planned_start),
        )

    @staticmethod
    def batch_until(plan: SuccessionPlan, planned_start: date) -> date | None:
        """The last day a batch sown on ``planned_start`` holds its slots; ``None`` without a batch duration.

        Windows are closed (V-08): a batch of 60 days sown on 1 April holds through 30 May, and the next batch
        may take the same slots from 31 May on.
        """
        if plan.batch_duration_days is None:
            return None
        return planned_start + timedelta(days=plan.batch_duration_days - 1)

    def next_batch_to_generate(self, plan: SuccessionPlan) -> int | None:
        """Return the next 1-based batch sequence to generate, or ``None`` when done.

        Uses ``completed_batches`` as the count of batches already generated.
        """
        total = plan.total_batches or self.compute_total_batches(plan.start_date, plan.end_date, plan.interval_days)
        nxt = plan.completed_batches + 1
        return nxt if nxt <= total else None

    @staticmethod
    def _derive_id_prefix(plan: SuccessionPlan) -> str:
        """Derive a valid ``[A-Z]{2,5}`` id prefix from the plan's species/name."""
        source = plan.species_key.removeprefix("species_") or plan.name
        letters = "".join(c for c in source.upper() if "A" <= c <= "Z")
        prefix = letters[:3]
        if len(prefix) < 2:
            prefix = "SUC"
        return prefix
