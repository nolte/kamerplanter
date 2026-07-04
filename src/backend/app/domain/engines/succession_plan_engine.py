from datetime import date, timedelta

from app.common.enums import PlantingRunStatus, PlantingRunType
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.models.succession_plan import SuccessionPlan


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
        span_days = (end_date - start_date).days
        if span_days < 0:
            return 0
        return span_days // interval_days + 1

    def build_entry(self, plan: SuccessionPlan) -> PlantingRunEntry:
        """Build the single species entry each generated (monoculture) run carries."""
        return PlantingRunEntry(
            species_key=plan.species_key,
            cultivar_key=plan.cultivar_key,
            quantity=plan.plants_per_batch,
            id_prefix=self._derive_id_prefix(plan),
        )

    def generate_batch_runs(self, plan: SuccessionPlan) -> list[PlantingRun]:
        """Return one (unpersisted) PlantingRun per batch of the plan."""
        total = self.compute_total_batches(plan.start_date, plan.end_date, plan.interval_days)
        return [self.generate_batch_run(plan, sequence, total=total) for sequence in range(1, total + 1)]

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
        )

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
