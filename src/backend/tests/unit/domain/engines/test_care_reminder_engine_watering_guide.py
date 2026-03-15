"""Tests for CareReminderEngine.auto_generate_profile with WateringGuide."""

import pytest

from app.common.enums import CareStyleType, WateringMethod
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.species import SeasonalWateringAdjustment, WateringGuide


@pytest.fixture
def engine() -> CareReminderEngine:
    return CareReminderEngine()


def test_auto_generate_without_guide(engine: CareReminderEngine) -> None:
    profile = engine.auto_generate_profile(botanical_family="Araceae", plant_key="p1")
    assert profile.care_style == CareStyleType.TROPICAL
    assert profile.watering_interval_days == 7
    assert profile.auto_generated is True


def test_auto_generate_with_guide_overrides_interval(
    engine: CareReminderEngine,
) -> None:
    guide = WateringGuide(
        interval_days=5,
        volume_ml_min=100,
        volume_ml_max=300,
        watering_method=WateringMethod.BOTTOM_WATER,
        water_quality_hint="Use filtered water",
        practical_tip="Check soil moisture with finger",
    )
    profile = engine.auto_generate_profile(
        botanical_family="Araceae",
        plant_key="p2",
        watering_guide=guide,
    )
    assert profile.watering_interval_days == 5
    assert profile.watering_method == WateringMethod.BOTTOM_WATER
    assert profile.water_quality_hint == "Use filtered water"
    assert profile.notes == "Check soil moisture with finger"
    assert profile.auto_generated is True


def test_auto_generate_with_guide_computes_winter_multiplier(
    engine: CareReminderEngine,
) -> None:
    guide = WateringGuide(
        interval_days=7,
        seasonal_adjustments=[
            SeasonalWateringAdjustment(
                months=[11, 12, 1, 2],
                interval_days=12,
                volume_ml_min=150,
                volume_ml_max=300,
                label="Winter",
            ),
        ],
    )
    profile = engine.auto_generate_profile(
        botanical_family="Araceae",
        plant_key="p3",
        watering_guide=guide,
    )
    # 12 / 7 = 1.71
    assert profile.winter_watering_multiplier == 1.71


def test_auto_generate_with_guide_no_seasonal_keeps_family_multiplier(
    engine: CareReminderEngine,
) -> None:
    guide = WateringGuide(interval_days=5)
    profile = engine.auto_generate_profile(
        botanical_family="Cactaceae",
        plant_key="p4",
        watering_guide=guide,
    )
    # No seasonal adjustments → keeps the Cactus preset multiplier (4.0)
    assert profile.winter_watering_multiplier == 4.0
    # But interval is overridden
    assert profile.watering_interval_days == 5


def test_watering_guide_model_validation() -> None:
    guide = WateringGuide(
        interval_days=14,
        volume_ml_min=200,
        volume_ml_max=500,
        watering_method=WateringMethod.SOAK,
        practical_tip="Soak for 15 minutes",
        seasonal_adjustments=[
            SeasonalWateringAdjustment(
                months=[6, 7, 8],
                interval_days=7,
                volume_ml_min=300,
                volume_ml_max=600,
                label="Summer",
            ),
        ],
    )
    assert guide.interval_days == 14
    assert len(guide.seasonal_adjustments) == 1
    assert guide.seasonal_adjustments[0].label == "Summer"


def test_watering_guide_invalid_month() -> None:
    with pytest.raises(ValueError, match="Month must be between 1 and 12"):
        SeasonalWateringAdjustment(
            months=[0, 13],
            interval_days=10,
        )
