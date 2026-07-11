"""REQ-008 Post-Harvest — service, state machine and calculator tests."""

from datetime import datetime

import pytest

from app.common.enums import (
    DryingMethod,
    MoldAlertSeverity,
    PostHarvestStage,
    StorageAromaQuality,
    StorageVisualCondition,
)
from app.common.exceptions import (
    InvalidStatusTransitionError,
    NotFoundError,
    ValidationError,
)
from app.domain.calculators import drying_calculator
from app.domain.engines import post_harvest_stage_engine as stage_engine
from app.domain.models.harvest import HarvestBatch
from app.domain.models.post_harvest import (
    PostHarvestBatch,
    StorageObservation,
)
from app.domain.services.post_harvest_service import PostHarvestService

TENANT = "tenant_a"
OTHER = "tenant_b"


class FakePostHarvestRepo:
    """In-memory stand-in honouring the tenant-scope contract of the real repo."""

    def __init__(self):
        self.batches: dict[str, PostHarvestBatch] = {}
        self.drying: dict[str, list] = {}
        self.observations: dict[str, list] = {}
        self.alerts: dict[str, list] = {}
        self._seq = 0

    def _next_key(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}_{self._seq}"

    def create_batch(self, batch: PostHarvestBatch) -> PostHarvestBatch:
        batch.key = self._next_key("ph")
        batch.created_at = datetime.now()
        self.batches[batch.key] = batch
        return batch

    def get_batch_or_raise(self, key: str) -> PostHarvestBatch:
        batch = self.batches.get(key)
        if batch is None:
            raise NotFoundError("PostHarvestBatch", key)
        return batch

    def get_batch_by_key(self, key: str) -> PostHarvestBatch | None:
        return self.batches.get(key)

    def update_batch(self, key: str, batch: PostHarvestBatch) -> PostHarvestBatch:
        self.batches[key] = batch
        return batch

    def delete_batch(self, key: str) -> bool:
        return self.batches.pop(key, None) is not None

    def list_batches(self, tenant_key, offset=0, limit=50):
        if not tenant_key:
            raise ValueError("tenant_key required")
        items = [b for b in self.batches.values() if b.tenant_key == tenant_key]
        return items[offset : offset + limit], len(items)

    def list_for_harvest_batch(self, harvest_batch_key, tenant_key):
        if not tenant_key:
            raise ValueError("tenant_key required")
        return [
            b for b in self.batches.values() if b.harvest_batch_key == harvest_batch_key and b.tenant_key == tenant_key
        ]

    def create_drying_progress(self, progress):
        progress.key = self._next_key("dp")
        self.drying.setdefault(progress.batch_key, []).insert(0, progress)
        return progress

    def get_latest_drying_progress(self, batch_key):
        items = self.drying.get(batch_key, [])
        return items[0] if items else None

    def list_drying_progress(self, batch_key):
        return self.drying.get(batch_key, [])

    def create_observation(self, observation):
        observation.key = self._next_key("obs")
        self.observations.setdefault(observation.batch_key, []).insert(0, observation)
        return observation

    def list_observations(self, batch_key):
        return self.observations.get(batch_key, [])

    def create_mold_alert(self, alert):
        alert.key = self._next_key("alert")
        self.alerts.setdefault(alert.batch_key, []).insert(0, alert)
        return alert

    def list_mold_alerts(self, batch_key):
        return self.alerts.get(batch_key, [])

    def create_burping_event(self, event):
        event.key = self._next_key("burp")
        return event

    def list_burping_events(self, batch_key):
        return []


class FakeHarvestRepo:
    def __init__(self, batches: dict[str, HarvestBatch]):
        self._batches = batches

    def get_batch_or_raise(self, key: str) -> HarvestBatch:
        batch = self._batches.get(key)
        if batch is None:
            raise NotFoundError("HarvestBatch", key)
        return batch


def _harvest_batch(key: str, *, tenant: str = TENANT, wet: float = 450.0) -> HarvestBatch:
    return HarvestBatch(_key=key, tenant_key=tenant, plant_key="plant_1", wet_weight_g=wet)


def _service(harvest_batches: dict[str, HarvestBatch] | None = None):
    repo = FakePostHarvestRepo()
    harvest_repo = FakeHarvestRepo(harvest_batches or {"hb_1": _harvest_batch("hb_1")})
    return PostHarvestService(repo, harvest_repo=harvest_repo), repo


# ── Calculator ──


class TestDryingCalculator:
    def test_scenario1_cannabis_slow_dry(self):
        """REQ-008 §6 Szenario 1: 450g → 180g, target 10% moisture.

        60% weight loss over a 90-point target loss → 66.7% dryness progress
        (matches the documented ``DryingProtocol.calculate_dryness_progress``
        formula); snap test is recommended (>=70% not yet), curing not ready.
        """
        report = drying_calculator.calculate_dryness_progress(450, 180, 10, DryingMethod.HANG_DRY)
        assert report["weight_loss_percent"] == pytest.approx(60.0, abs=0.1)
        assert report["dryness_progress_percent"] == pytest.approx(66.7, abs=0.2)
        assert report["ready_for_curing"] is False

    def test_ready_for_curing_at_95_percent(self):
        report = drying_calculator.calculate_dryness_progress(450, 60, 10, DryingMethod.HANG_DRY)
        assert report["ready_for_curing"] is True
        assert report["estimated_days_remaining"] == 0

    def test_over_dried_flag(self):
        report = drying_calculator.calculate_dryness_progress(450, 40, 10, DryingMethod.RACK_DRY)
        assert report["over_dried"] is True
        assert report["next_action"] == "over_dried"

    def test_rejects_weight_gain(self):
        with pytest.raises(ValueError):
            drying_calculator.calculate_dryness_progress(200, 300, 10)

    def test_rejects_non_positive_weight(self):
        with pytest.raises(ValueError):
            drying_calculator.calculate_dryness_progress(0, 0, 10)

    def test_snap_test_interpretation(self):
        assert drying_calculator.interpret_snap_test(True, False)["result"] == "optimal"
        assert drying_calculator.interpret_snap_test(True, True)["result"] == "overdried"
        assert drying_calculator.interpret_snap_test(False, False)["result"] == "underdried"

    def test_mold_risk_prefers_water_activity(self):
        assert drying_calculator.assess_mold_risk(50, 20, 0.70)["risk_level"] == "critical"
        assert drying_calculator.assess_mold_risk(90, 30, 0.50)["risk_level"] == "ok"

    def test_mold_risk_rh_fallback(self):
        assert drying_calculator.assess_mold_risk(68, 19, None)["risk_level"] == "critical"
        assert drying_calculator.assess_mold_risk(63, 19, None)["risk_level"] == "warning"
        assert drying_calculator.assess_mold_risk(40, 19, None)["risk_level"] == "ok"

    def test_dew_point_monotonic(self):
        assert drying_calculator.calculate_dew_point(20, 80) > drying_calculator.calculate_dew_point(20, 40)


# ── Stage engine ──


class TestStageEngine:
    def test_forward_single_step_allowed(self):
        stage_engine.validate_transition(PostHarvestStage.DRYING, PostHarvestStage.CURING)
        stage_engine.validate_transition(PostHarvestStage.CURING, PostHarvestStage.STORED)
        stage_engine.validate_transition(PostHarvestStage.STORED, PostHarvestStage.RELEASED)

    def test_backward_rejected(self):
        with pytest.raises(InvalidStatusTransitionError):
            stage_engine.validate_transition(PostHarvestStage.STORED, PostHarvestStage.CURING)

    def test_skip_rejected(self):
        with pytest.raises(InvalidStatusTransitionError):
            stage_engine.validate_transition(PostHarvestStage.DRYING, PostHarvestStage.STORED)

    def test_noop_rejected(self):
        with pytest.raises(InvalidStatusTransitionError):
            stage_engine.validate_transition(PostHarvestStage.CURING, PostHarvestStage.CURING)

    def test_terminal_has_no_next(self):
        assert stage_engine.next_stage(PostHarvestStage.RELEASED) is None


# ── Service ──


class TestStartDrying:
    def test_creates_batch_in_drying_stage_with_wet_weight(self):
        service, _ = _service()
        batch = service.start_drying(TENANT, "hb_1")
        assert batch.stage == PostHarvestStage.DRYING
        assert batch.start_weight_g == 450.0
        assert batch.current_weight_g == 450.0
        assert batch.plant_key == "plant_1"
        assert batch.drying_started_at is not None

    def test_explicit_start_weight_overrides_wet_weight(self):
        service, _ = _service()
        batch = service.start_drying(TENANT, "hb_1", start_weight_g=500.0)
        assert batch.start_weight_g == 500.0

    def test_unknown_harvest_batch_raises_not_found(self):
        service, _ = _service()
        with pytest.raises(NotFoundError):
            service.start_drying(TENANT, "missing")

    def test_cross_tenant_harvest_batch_rejected(self):
        service, _ = _service({"hb_x": _harvest_batch("hb_x", tenant=OTHER)})
        with pytest.raises(NotFoundError):
            service.start_drying(TENANT, "hb_x")

    def test_requires_harvest_repo(self):
        repo = FakePostHarvestRepo()
        service = PostHarvestService(repo)
        with pytest.raises(RuntimeError):
            service.start_drying(TENANT, "hb_1")


class TestAdvanceStage:
    def test_drying_to_curing_blocked_until_ready(self):
        service, _ = _service()
        batch = service.start_drying(TENANT, "hb_1")
        with pytest.raises(ValidationError):
            service.advance_stage(batch.key, TENANT, PostHarvestStage.CURING)

    def test_drying_to_curing_allowed_when_ready(self):
        service, _ = _service()
        batch = service.start_drying(TENANT, "hb_1")
        # Drive weight down to reach >=95% dryness progress.
        service.record_drying_progress(batch.key, TENANT, 60.0)
        advanced = service.advance_stage(batch.key, TENANT, PostHarvestStage.CURING)
        assert advanced.stage == PostHarvestStage.CURING
        assert advanced.curing_started_at is not None

    def test_backward_transition_rejected(self):
        service, _ = _service()
        batch = service.start_drying(TENANT, "hb_1")
        service.record_drying_progress(batch.key, TENANT, 60.0)
        service.advance_stage(batch.key, TENANT, PostHarvestStage.CURING)
        service.advance_stage(batch.key, TENANT, PostHarvestStage.STORED)
        with pytest.raises(InvalidStatusTransitionError):
            service.advance_stage(batch.key, TENANT, PostHarvestStage.CURING)

    def test_released_sets_completed_at(self):
        service, _ = _service()
        batch = service.start_drying(TENANT, "hb_1")
        service.record_drying_progress(batch.key, TENANT, 60.0)
        service.advance_stage(batch.key, TENANT, PostHarvestStage.CURING)
        service.advance_stage(batch.key, TENANT, PostHarvestStage.STORED)
        released = service.advance_stage(batch.key, TENANT, PostHarvestStage.RELEASED)
        assert released.completed_at is not None

    def test_cross_tenant_access_rejected(self):
        service, _ = _service()
        batch = service.start_drying(TENANT, "hb_1")
        with pytest.raises(NotFoundError):
            service.advance_stage(batch.key, OTHER, PostHarvestStage.CURING)


class TestDryingProgressRollup:
    def test_progress_updates_batch_summary(self):
        service, _ = _service()
        batch = service.start_drying(TENANT, "hb_1")
        service.record_drying_progress(batch.key, TENANT, 180.0, snap_test_passed=True)
        refreshed = service.get_batch(batch.key, TENANT)
        assert refreshed.current_weight_g == 180.0
        assert refreshed.dryness_progress_percent > 0
        assert refreshed.snap_test_passed is True

    def test_current_weight_above_start_weight_is_validation_error(self):
        # SEC-002: a weight above the start weight is invalid input → 422
        # (ValidationError), not a bare calculator ValueError surfacing as 500.
        service, _ = _service()
        batch = service.start_drying(TENANT, "hb_1")  # start weight 450 g
        with pytest.raises(ValidationError):
            service.record_drying_progress(batch.key, TENANT, 600.0)


class TestObservationsAndMoldAlerts:
    def test_high_rh_observation_raises_mold_alert(self):
        service, repo = _service()
        batch = service.start_drying(TENANT, "hb_1")
        obs = StorageObservation(
            rh_percent=68,
            temperature_c=19,
            visual_condition=StorageVisualCondition.CONCERNING,
            aroma_quality=StorageAromaQuality.OFF,
        )
        service.record_observation(batch.key, TENANT, obs)
        alerts = service.list_mold_alerts(batch.key, TENANT)
        assert len(alerts) == 1
        assert alerts[0].severity == MoldAlertSeverity.CRITICAL

    def test_safe_observation_raises_no_alert(self):
        service, _ = _service()
        batch = service.start_drying(TENANT, "hb_1")
        obs = StorageObservation(rh_percent=45, temperature_c=18)
        service.record_observation(batch.key, TENANT, obs)
        assert service.list_mold_alerts(batch.key, TENANT) == []


class TestListing:
    def test_list_for_batch_is_tenant_scoped(self):
        service, _ = _service()
        service.start_drying(TENANT, "hb_1")
        assert len(service.list_for_batch("hb_1", TENANT)) == 1
        assert service.list_for_batch("hb_1", OTHER) == []

    def test_delete_batch(self):
        service, repo = _service()
        batch = service.start_drying(TENANT, "hb_1")
        service.delete_batch(batch.key, TENANT)
        assert repo.get_batch_by_key(batch.key) is None


class TestPostHarvestModel:
    def test_default_stage_is_drying(self):
        b = PostHarvestBatch(harvest_batch_key="hb-1")
        assert b.stage == PostHarvestStage.DRYING
