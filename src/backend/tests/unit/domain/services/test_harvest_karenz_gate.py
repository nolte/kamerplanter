"""Regression tests for the Karenz-Gate (DOM-1) at the service level.

These tests reproduce the original defect where a tz-aware ``applied_at`` (as
stored by the DB) was compared against a naive ``planned_harvest_date`` produced
by the service default, raising ``TypeError`` and surfacing as HTTP 500 instead
of the intended business-level HTTP 422 (``KarenzViolationError``).
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.common.exceptions import KarenzViolationError
from app.domain.engines.resistance_engine import ResistanceManager
from app.domain.engines.safety_interval_engine import SafetyIntervalValidator
from app.domain.models.harvest import HarvestBatch
from app.domain.services.harvest_service import HarvestService
from app.domain.services.ipm_service import IpmService


class _FakeIpmRepo:
    """Minimal IPM repository returning a single active karenz period."""

    def __init__(self, karenz_periods: list[dict]) -> None:
        self._karenz_periods = karenz_periods

    def get_active_karenz_periods(self, plant_key: str) -> list[dict]:
        return self._karenz_periods


class _FakeHarvestRepo:
    """Minimal harvest repository; create_batch echoes the batch back."""

    def __init__(self) -> None:
        self.created: list[HarvestBatch] = []

    def create_batch(self, batch: HarvestBatch) -> HarvestBatch:
        self.created.append(batch)
        return batch

    def batch_id_exists(self, batch_id: str) -> bool:
        return any(b.batch_id == batch_id for b in self.created)


def _build_harvest_service(karenz_periods: list[dict]) -> tuple[HarvestService, _FakeHarvestRepo]:
    ipm_service = IpmService(
        repo=_FakeIpmRepo(karenz_periods),
        safety_validator=SafetyIntervalValidator(),
        resistance_mgr=ResistanceManager(),
        inspection_scheduler=None,
    )
    harvest_repo = _FakeHarvestRepo()
    service = HarvestService(
        repo=harvest_repo,
        ipm_service=ipm_service,
        readiness_engine=None,
        quality_engine=None,
    )
    return service, harvest_repo


def test_create_harvest_batch_blocked_by_active_karenz_raises_422():
    """Regression DOM-1: an active karenz period with a tz-aware ISO applied_at and
    a default (now) harvest date must raise KarenzViolationError (422), not crash
    with TypeError (500)."""
    karenz_periods = [
        {
            "active_ingredient": "Spinosad",
            # As returned by the AQL query: ISO with +00:00 offset.
            "applied_at": (datetime.now(UTC) - timedelta(days=2)).isoformat(),
            "safety_interval_days": 21,
        }
    ]
    service, harvest_repo = _build_harvest_service(karenz_periods)

    # harvest_date omitted -> service default (formerly naive datetime.now()).
    batch = HarvestBatch(plant_key="plant-1")

    with pytest.raises(KarenzViolationError) as exc_info:
        service.create_harvest_batch("plant-1", batch)

    assert exc_info.value.status_code == 422
    assert exc_info.value.error_code == "KARENZ_VIOLATION"
    assert harvest_repo.created == []


def test_create_harvest_batch_allowed_when_karenz_expired():
    """A karenz period that has fully elapsed does not block the harvest."""
    karenz_periods = [
        {
            "active_ingredient": "Neem Oil",
            "applied_at": (datetime.now(UTC) - timedelta(days=30)).isoformat(),
            "safety_interval_days": 14,
        }
    ]
    service, harvest_repo = _build_harvest_service(karenz_periods)
    batch = HarvestBatch(plant_key="plant-1")

    result = service.create_harvest_batch("plant-1", batch)

    assert result.plant_key == "plant-1"
    assert len(harvest_repo.created) == 1


def test_blank_batch_id_is_generated_deterministically():
    """Issue #744: a blank batch_id is auto-filled with a stable base identifier."""
    service, _ = _build_harvest_service([])
    harvest_date = datetime(2026, 7, 24, 10, 0, tzinfo=UTC)
    batch = HarvestBatch(plant_key="plant-1", harvest_date=harvest_date)

    result = service.create_harvest_batch("plant-1", batch)

    assert result.batch_id == "HARVEST-20260724-plant-1"


def test_second_blank_batch_same_plant_same_day_gets_suffix():
    """Issue #744: a second same-day batch must not collide -- it gains a -2 suffix."""
    service, _ = _build_harvest_service([])
    harvest_date = datetime(2026, 7, 24, 10, 0, tzinfo=UTC)

    first = service.create_harvest_batch("plant-1", HarvestBatch(plant_key="plant-1", harvest_date=harvest_date))
    second = service.create_harvest_batch("plant-1", HarvestBatch(plant_key="plant-1", harvest_date=harvest_date))
    third = service.create_harvest_batch("plant-1", HarvestBatch(plant_key="plant-1", harvest_date=harvest_date))

    assert first.batch_id == "HARVEST-20260724-plant-1"
    assert second.batch_id == "HARVEST-20260724-plant-1-2"
    assert third.batch_id == "HARVEST-20260724-plant-1-3"


def test_explicit_batch_id_is_never_overwritten():
    """A user-provided batch_id is used verbatim -- no generation kicks in."""
    service, _ = _build_harvest_service([])
    batch = HarvestBatch(plant_key="plant-1", batch_id="HARVEST-2026-001")

    result = service.create_harvest_batch("plant-1", batch)

    assert result.batch_id == "HARVEST-2026-001"
