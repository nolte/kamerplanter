"""REQ-008 Post-Harvest service.

Orchestrates the per-batch drying → curing → storage → released workflow that
follows a HarvestBatch (REQ-007). Enforces tenant isolation (REQ-024) on every
read/write, drives the forward-only stage state machine (REQ-008 §5 U-006) and
computes drying progress + mold alerts through the pure domain helpers.
"""

from __future__ import annotations

from app.common.datetimes import now_utc
from app.common.enums import (
    DryingMethod,
    MoldAlertSeverity,
    PostHarvestSpeciesType,
    PostHarvestStage,
)
from app.common.exceptions import ValidationError
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.calculators import drying_calculator
from app.domain.engines import post_harvest_stage_engine as stage_engine
from app.domain.interfaces.harvest_repository import IHarvestRepository
from app.domain.interfaces.post_harvest_repository import IPostHarvestRepository
from app.domain.models.post_harvest import (
    DryingProgress,
    MoldAlert,
    PostHarvestBatch,
    StorageObservation,
)


class PostHarvestService:
    """Business logic for the post-harvest batch lifecycle (REQ-008)."""

    def __init__(
        self,
        repo: IPostHarvestRepository,
        harvest_repo: IHarvestRepository | None = None,
    ) -> None:
        self._repo = repo
        # Optional so the state-machine unit tests can build the service with a
        # fake repo only; ``start_drying`` requires it to validate the source
        # HarvestBatch and its tenant ownership.
        self._harvest_repo = harvest_repo

    # ── Batches ──

    def list_batches(
        self,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PostHarvestBatch], int]:
        return self._repo.list_batches(tenant_key, offset, limit)

    def list_for_batch(self, harvest_batch_key: str, tenant_key: str) -> list[PostHarvestBatch]:
        """Return all post-harvest batches tracked for a HarvestBatch."""
        return self._repo.list_for_harvest_batch(harvest_batch_key, tenant_key)

    def get_batch(self, key: str, tenant_key: str) -> PostHarvestBatch:
        batch = self._repo.get_batch_or_raise(key)
        verify_tenant_ownership(batch, tenant_key, "PostHarvestBatch")
        return batch

    def start_drying(
        self,
        tenant_key: str,
        harvest_batch_key: str,
        *,
        species_type: PostHarvestSpeciesType = PostHarvestSpeciesType.FLOWER,
        drying_method: DryingMethod = DryingMethod.HANG_DRY,
        start_weight_g: float | None = None,
        target_moisture_percent: float = 10.0,
        notes: str | None = None,
    ) -> PostHarvestBatch:
        """Take a HarvestBatch into post-harvest tracking at stage ``drying``.

        Verifies the source HarvestBatch exists and belongs to the caller's
        tenant (SEC-B4 cross-tenant guard). The starting weight defaults to the
        HarvestBatch wet weight when not supplied explicitly.
        """
        if self._harvest_repo is None:
            raise RuntimeError("start_drying requires a harvest_repo to be wired")

        harvest_batch = self._harvest_repo.get_batch_or_raise(harvest_batch_key)
        verify_tenant_ownership(harvest_batch, tenant_key, "HarvestBatch")

        resolved_weight = start_weight_g if start_weight_g is not None else harvest_batch.wet_weight_g
        now = now_utc()
        batch = PostHarvestBatch(
            tenant_key=tenant_key,
            harvest_batch_key=harvest_batch_key,
            plant_key=harvest_batch.plant_key,
            stage=PostHarvestStage.DRYING,
            species_type=species_type,
            drying_method=drying_method,
            start_weight_g=resolved_weight,
            current_weight_g=resolved_weight,
            target_moisture_percent=target_moisture_percent,
            started_at=now,
            drying_started_at=now,
            notes=notes,
        )
        return self._repo.create_batch(batch)

    def advance_stage(
        self,
        key: str,
        tenant_key: str,
        target_stage: PostHarvestStage,
    ) -> PostHarvestBatch:
        """Advance a batch to the next stage (forward-only state machine).

        Rejects backward transitions and stage skips with 422 (via the stage
        engine). The ``drying → curing`` step additionally requires the drying
        criterion to be met (``ready_for_curing``, i.e. dryness >= 95 %).
        """
        batch = self.get_batch(key, tenant_key)
        stage_engine.validate_transition(batch.stage, target_stage)

        drying_to_curing = batch.stage == PostHarvestStage.DRYING and target_stage == PostHarvestStage.CURING
        if drying_to_curing and not batch.ready_for_curing:
            raise ValidationError(
                "Batch is not ready for curing: drying progress must reach 95% "
                f"(current: {batch.dryness_progress_percent}%)."
            )

        now = now_utc()
        batch.stage = target_stage
        if target_stage == PostHarvestStage.CURING:
            batch.curing_started_at = now
        elif target_stage == PostHarvestStage.STORED:
            batch.stored_at = now
        elif target_stage == PostHarvestStage.RELEASED:
            batch.released_at = now
            batch.completed_at = now

        return self._repo.update_batch(key, batch)

    # ── Drying progress ──

    def record_drying_progress(
        self,
        key: str,
        tenant_key: str,
        current_weight_g: float,
        *,
        water_activity: float | None = None,
        co2_ppm: int | None = None,
        snap_test_passed: bool | None = None,
        notes: str | None = None,
    ) -> DryingProgress:
        """Record a drying measurement and update the batch drying summary."""
        batch = self.get_batch(key, tenant_key)
        start_weight = batch.start_weight_g or current_weight_g

        # A current weight above the starting weight is invalid input (the batch
        # can only lose water while drying). Reject it as 422 here — mirroring the
        # ``advance_stage`` guard — instead of letting the calculator raise a bare
        # ValueError that would surface as an opaque 500 (NFR-006, SEC-002).
        if current_weight_g > start_weight:
            raise ValidationError(
                "current_weight_g cannot exceed the batch start weight "
                f"({start_weight} g): a drying batch only loses weight."
            )

        report = drying_calculator.calculate_dryness_progress(
            start_weight,
            current_weight_g,
            batch.target_moisture_percent,
            batch.drying_method,
        )

        progress = DryingProgress(
            batch_key=key,
            start_weight_g=start_weight,
            current_weight_g=current_weight_g,
            target_weight_g=report["target_weight_g"],
            weight_loss_percent=report["weight_loss_percent"],
            dryness_progress_percent=report["dryness_progress_percent"],
            snap_test_ready=report["snap_test_ready"],
            snap_test_passed=snap_test_passed,
            over_dried=report["over_dried"],
            estimated_days_remaining=report["estimated_days_remaining"],
            next_action=report["next_action"],
            water_activity=water_activity,
            co2_ppm_current=co2_ppm,
            recorded_at=now_utc(),
            notes=notes,
        )
        created = self._repo.create_drying_progress(progress)

        # Roll the latest measurement up onto the batch so the stage gate and the
        # list view can read progress without re-querying children.
        batch.current_weight_g = current_weight_g
        batch.dryness_progress_percent = report["dryness_progress_percent"]
        batch.ready_for_curing = report["ready_for_curing"]
        if snap_test_passed is not None:
            batch.snap_test_passed = snap_test_passed
        if water_activity is not None:
            batch.water_activity = water_activity
        self._repo.update_batch(key, batch)

        return created

    def get_latest_drying_progress(self, key: str, tenant_key: str) -> DryingProgress | None:
        self.get_batch(key, tenant_key)
        return self._repo.get_latest_drying_progress(key)

    def list_drying_progress(self, key: str, tenant_key: str) -> list[DryingProgress]:
        self.get_batch(key, tenant_key)
        return self._repo.list_drying_progress(key)

    # ── Storage observations (with mold-alert auto-raise) ──

    def record_observation(
        self,
        key: str,
        tenant_key: str,
        observation: StorageObservation,
    ) -> StorageObservation:
        """Persist a storage observation, auto-raising a MoldAlert on risk."""
        batch = self.get_batch(key, tenant_key)
        observation.batch_key = key
        created = self._repo.create_observation(observation)

        risk = drying_calculator.assess_mold_risk(
            observation.rh_percent,
            observation.temperature_c,
            observation.water_activity,
        )
        if risk["risk_level"] in ("warning", "critical"):
            severity = MoldAlertSeverity.CRITICAL if risk["risk_level"] == "critical" else MoldAlertSeverity.WARNING
            self._repo.create_mold_alert(
                MoldAlert(
                    batch_key=key,
                    severity=severity,
                    trigger_reason=risk["reason"],
                    affected_location=batch.storage_location or "",
                    triggered_at=now_utc(),
                )
            )
        return created

    def list_observations(self, key: str, tenant_key: str) -> list[StorageObservation]:
        self.get_batch(key, tenant_key)
        return self._repo.list_observations(key)

    def list_mold_alerts(self, key: str, tenant_key: str) -> list[MoldAlert]:
        self.get_batch(key, tenant_key)
        return self._repo.list_mold_alerts(key)

    # ── Admin ──

    def delete_batch(self, key: str, tenant_key: str) -> None:
        self.get_batch(key, tenant_key)
        self._repo.delete_batch(key)
