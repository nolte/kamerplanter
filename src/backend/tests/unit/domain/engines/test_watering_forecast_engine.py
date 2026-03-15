"""Tests for WateringForecastEngine."""

from datetime import date

import pytest

from app.domain.engines.watering_forecast_engine import PhaseInterval, WateringForecastEngine
from app.domain.models.care_reminder import CareProfile


@pytest.fixture
def engine() -> WateringForecastEngine:
    return WateringForecastEngine()


@pytest.fixture
def profile() -> CareProfile:
    return CareProfile(
        watering_interval_days=7,
        winter_watering_multiplier=1.5,
        plant_key="test-plant",
    )


def test_basic_forecast(engine: WateringForecastEngine, profile: CareProfile) -> None:
    dates = engine.generate_forecast(
        profile=profile,
        last_watering_date=date(2026, 3, 1),
        forecast_start=date(2026, 3, 1),
        forecast_end=date(2026, 3, 31),
    )
    assert len(dates) == 4  # Mar 8, 15, 22, 29
    assert dates[0] == date(2026, 3, 8)
    assert dates[-1] == date(2026, 3, 29)


def test_winter_interval_adjustment(
    engine: WateringForecastEngine, profile: CareProfile,
) -> None:
    dates = engine.generate_forecast(
        profile=profile,
        last_watering_date=date(2026, 12, 1),
        forecast_start=date(2026, 12, 1),
        forecast_end=date(2026, 12, 31),
    )
    # Winter: 7 * 1.5 = 10.5 → 10 days
    assert dates[0] == date(2026, 12, 11)
    assert dates[1] == date(2026, 12, 21)
    assert dates[2] == date(2026, 12, 31)


def test_empty_range(engine: WateringForecastEngine, profile: CareProfile) -> None:
    dates = engine.generate_forecast(
        profile=profile,
        last_watering_date=date(2026, 3, 1),
        forecast_start=date(2026, 3, 31),
        forecast_end=date(2026, 3, 1),
    )
    assert dates == []


def test_learned_interval_used(engine: WateringForecastEngine) -> None:
    profile = CareProfile(
        watering_interval_days=7,
        watering_interval_learned=5,
        winter_watering_multiplier=2.0,
        plant_key="test",
    )
    dates = engine.generate_forecast(
        profile=profile,
        last_watering_date=date(2026, 6, 1),
        forecast_start=date(2026, 6, 1),
        forecast_end=date(2026, 6, 30),
    )
    # Learned interval of 5 days: Jun 6, 11, 16, 21, 26
    assert len(dates) == 5
    assert dates[0] == date(2026, 6, 6)


def test_southern_hemisphere(engine: WateringForecastEngine, profile: CareProfile) -> None:
    # July is winter in southern hemisphere
    dates = engine.generate_forecast(
        profile=profile,
        last_watering_date=date(2026, 7, 1),
        forecast_start=date(2026, 7, 1),
        forecast_end=date(2026, 7, 31),
        hemisphere="south",
    )
    # Winter: 7 * 1.5 = 10 days
    assert dates[0] == date(2026, 7, 11)


def test_phase_intervals_override_profile(
    engine: WateringForecastEngine, profile: CareProfile,
) -> None:
    """Phase-specific interval overrides CareProfile base."""
    phase_intervals = [
        PhaseInterval(
            phase_name="seedling",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 14),
            interval_days=3,  # seedlings need more frequent watering
        ),
        PhaseInterval(
            phase_name="vegetative",
            start_date=date(2026, 3, 15),
            end_date=date(2026, 4, 15),
            interval_days=5,
        ),
    ]
    dates = engine.generate_forecast(
        profile=profile,  # base interval is 7 days
        last_watering_date=date(2026, 3, 1),
        forecast_start=date(2026, 3, 1),
        forecast_end=date(2026, 3, 31),
        phase_intervals=phase_intervals,
    )
    # Interval is resolved from the date we step FROM:
    # seedling (3d): Mar 4, 7, 10, 13 (Mar 13 still steps from seedling range)
    # transition: from Mar 13 +3d = Mar 16 (now in vegetative)
    # vegetative (5d): Mar 16, 21, 26, 31
    assert dates[0] == date(2026, 3, 4)
    assert dates[1] == date(2026, 3, 7)
    assert dates[2] == date(2026, 3, 10)
    assert dates[3] == date(2026, 3, 13)
    assert dates[4] == date(2026, 3, 16)  # stepped from 13 (seedling) +3d
    assert dates[5] == date(2026, 3, 21)  # stepped from 16 (vegetative) +5d
    assert dates[6] == date(2026, 3, 26)


def test_phase_intervals_fallback_to_profile(
    engine: WateringForecastEngine, profile: CareProfile,
) -> None:
    """Dates outside any phase interval fall back to CareProfile."""
    phase_intervals = [
        PhaseInterval(
            phase_name="seedling",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 10),
            interval_days=3,
        ),
    ]
    dates = engine.generate_forecast(
        profile=profile,  # base 7 days
        last_watering_date=date(2026, 3, 1),
        forecast_start=date(2026, 3, 1),
        forecast_end=date(2026, 3, 31),
        phase_intervals=phase_intervals,
    )
    # seedling (3d): Mar 4, 7, 10
    # from Mar 10 (still seedling) +3d = Mar 13 (outside phase → fallback 7d next)
    # from Mar 13 (no phase) +7d = Mar 20, 27
    assert dates[0] == date(2026, 3, 4)
    assert dates[1] == date(2026, 3, 7)
    assert dates[2] == date(2026, 3, 10)
    assert dates[3] == date(2026, 3, 13)  # last step from seedling range
    assert dates[4] == date(2026, 3, 20)  # fallback to profile 7d
    assert dates[5] == date(2026, 3, 27)
