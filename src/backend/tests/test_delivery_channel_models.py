"""Tests for DeliveryChannel domain models (REQ-004 Multi-Channel Delivery)."""

import pytest
from pydantic import ValidationError

from app.common.enums import ApplicationMethod, PhaseName, ScheduleMode
from app.domain.models.nutrient_plan import (
    DeliveryChannel,
    DrenchParams,
    FertigationParams,
    FertilizerDosage,
    FoliarParams,
    NutrientPlan,
    NutrientPlanPhaseEntry,
    TopDressParams,
    WateringSchedule,
)


class TestMethodParams:
    def test_fertigation_params_defaults(self):
        p = FertigationParams()
        assert p.method == "fertigation"
        assert p.runs_per_day == 1
        assert p.duration_seconds == 300
        assert p.flow_rate_ml_min is None

    def test_fertigation_params_custom(self):
        p = FertigationParams(runs_per_day=4, duration_seconds=600)
        assert p.runs_per_day == 4
        assert p.duration_seconds == 600

    def test_fertigation_params_bounds(self):
        with pytest.raises(ValidationError):
            FertigationParams(runs_per_day=0)
        with pytest.raises(ValidationError):
            FertigationParams(runs_per_day=25)
        with pytest.raises(ValidationError):
            FertigationParams(duration_seconds=0)
        with pytest.raises(ValidationError):
            FertigationParams(duration_seconds=7201)

    def test_drench_params(self):
        p = DrenchParams()
        assert p.method == "drench"
        assert p.volume_per_feeding_liters == 1.0

    def test_drench_params_validation(self):
        with pytest.raises(ValidationError):
            DrenchParams(volume_per_feeding_liters=0)
        with pytest.raises(ValidationError):
            DrenchParams(volume_per_feeding_liters=101)

    def test_foliar_params(self):
        p = FoliarParams(volume_per_spray_liters=0.25)
        assert p.method == "foliar"
        assert p.volume_per_spray_liters == 0.25

    def test_top_dress_params(self):
        p = TopDressParams(grams_per_plant=5.0, grams_per_m2=10.0)
        assert p.method == "top_dress"
        assert p.grams_per_plant == 5.0
        assert p.grams_per_m2 == 10.0


class TestDeliveryChannel:
    def test_minimal_channel(self):
        ch = DeliveryChannel(
            channel_id="fert-main",
            application_method=ApplicationMethod.FERTIGATION,
        )
        assert ch.channel_id == "fert-main"
        assert ch.label == ""
        assert ch.enabled is True
        assert ch.schedule is None
        assert ch.fertilizer_dosages == []
        assert ch.method_params is None

    def test_full_channel(self):
        ch = DeliveryChannel(
            channel_id="foliar-weekly",
            label="Weekly foliar spray",
            application_method=ApplicationMethod.FOLIAR,
            enabled=True,
            notes="Apply in evening",
            schedule=WateringSchedule(
                schedule_mode=ScheduleMode.INTERVAL,
                interval_days=7,
                application_method=ApplicationMethod.FOLIAR,
            ),
            target_ec_ms=0.5,
            target_ph=6.2,
            fertilizer_dosages=[
                FertilizerDosage(fertilizer_key="f1", ml_per_liter=2.0),
            ],
            method_params=FoliarParams(volume_per_spray_liters=0.5),
        )
        assert ch.channel_id == "foliar-weekly"
        assert ch.label == "Weekly foliar spray"
        assert ch.schedule is not None
        assert ch.schedule.interval_days == 7
        assert len(ch.fertilizer_dosages) == 1
        assert ch.method_params is not None
        assert ch.method_params.method == "foliar"

    def test_channel_id_min_length(self):
        with pytest.raises(ValidationError):
            DeliveryChannel(
                channel_id="",
                application_method=ApplicationMethod.DRENCH,
            )

    def test_channel_with_fertigation_schedule(self):
        """Channel-level schedules CAN use FERTIGATION (unlike plan-level)."""
        ch = DeliveryChannel(
            channel_id="fert-auto",
            application_method=ApplicationMethod.FERTIGATION,
            schedule=WateringSchedule(
                schedule_mode=ScheduleMode.INTERVAL,
                interval_days=1,
                application_method=ApplicationMethod.FERTIGATION,
            ),
        )
        assert ch.schedule is not None
        assert ch.schedule.application_method == ApplicationMethod.FERTIGATION

    def test_discriminated_method_params(self):
        """Discriminated union resolves correct type from dict."""
        ch = DeliveryChannel(
            channel_id="test",
            application_method=ApplicationMethod.FERTIGATION,
            method_params={"method": "fertigation", "runs_per_day": 3},
        )
        assert isinstance(ch.method_params, FertigationParams)
        assert ch.method_params.runs_per_day == 3


class TestNutrientPlanPhaseEntryChannels:
    def test_entry_default_no_channels(self):
        entry = NutrientPlanPhaseEntry(
            plan_key="p1",
            phase_name=PhaseName.VEGETATIVE,
            sequence_order=1,
            week_start=1,
            week_end=4,
        )
        assert entry.delivery_channels == []

    def test_entry_with_channels(self):
        entry = NutrientPlanPhaseEntry(
            plan_key="p1",
            phase_name=PhaseName.VEGETATIVE,
            sequence_order=1,
            week_start=1,
            week_end=4,
            delivery_channels=[
                DeliveryChannel(
                    channel_id="fert-1",
                    application_method=ApplicationMethod.FERTIGATION,
                ),
                DeliveryChannel(
                    channel_id="foliar-1",
                    application_method=ApplicationMethod.FOLIAR,
                ),
            ],
        )
        assert len(entry.delivery_channels) == 2

    def test_entry_rejects_duplicate_channel_ids(self):
        with pytest.raises(ValidationError, match="unique channel_id"):
            NutrientPlanPhaseEntry(
                plan_key="p1",
                phase_name=PhaseName.VEGETATIVE,
                sequence_order=1,
                week_start=1,
                week_end=4,
                delivery_channels=[
                    DeliveryChannel(
                        channel_id="dup",
                        application_method=ApplicationMethod.DRENCH,
                    ),
                    DeliveryChannel(
                        channel_id="dup",
                        application_method=ApplicationMethod.FOLIAR,
                    ),
                ],
            )

    def test_entry_serialization_roundtrip(self):
        entry = NutrientPlanPhaseEntry(
            plan_key="p1",
            phase_name=PhaseName.FLOWERING,
            sequence_order=2,
            week_start=5,
            week_end=10,
            delivery_channels=[
                DeliveryChannel(
                    channel_id="ch1",
                    application_method=ApplicationMethod.FERTIGATION,
                    method_params=FertigationParams(runs_per_day=3),
                    fertilizer_dosages=[
                        FertilizerDosage(fertilizer_key="f1", ml_per_liter=2.0),
                    ],
                ),
            ],
        )
        data = entry.model_dump(mode="json")
        restored = NutrientPlanPhaseEntry(**data)
        assert len(restored.delivery_channels) == 1
        assert restored.delivery_channels[0].channel_id == "ch1"
        assert isinstance(restored.delivery_channels[0].method_params, FertigationParams)
        assert restored.delivery_channels[0].method_params.runs_per_day == 3


class TestWateringScheduleFertigationFix:
    def test_watering_schedule_allows_non_fertigation(self):
        """Non-FERTIGATION methods are allowed on WateringSchedule."""
        ws = WateringSchedule(
            schedule_mode=ScheduleMode.WEEKDAYS,
            weekday_schedule=[0, 2, 4],
            application_method=ApplicationMethod.DRENCH,
        )
        assert ws.application_method == ApplicationMethod.DRENCH

    def test_watering_schedule_allows_fertigation(self):
        """FERTIGATION is now allowed on WateringSchedule itself (moved check to NutrientPlan)."""
        ws = WateringSchedule(
            schedule_mode=ScheduleMode.INTERVAL,
            interval_days=1,
            application_method=ApplicationMethod.FERTIGATION,
        )
        assert ws.application_method == ApplicationMethod.FERTIGATION

    def test_nutrient_plan_rejects_fertigation_schedule(self):
        """Plan-level watering schedule still rejects FERTIGATION."""
        with pytest.raises(ValidationError, match="FERTIGATION not allowed"):
            NutrientPlan(
                name="Test Plan",
                watering_schedule=WateringSchedule(
                    schedule_mode=ScheduleMode.INTERVAL,
                    interval_days=1,
                    application_method=ApplicationMethod.FERTIGATION,
                ),
            )

    def test_nutrient_plan_allows_drench_schedule(self):
        plan = NutrientPlan(
            name="Test Plan",
            watering_schedule=WateringSchedule(
                schedule_mode=ScheduleMode.WEEKDAYS,
                weekday_schedule=[0, 3],
                application_method=ApplicationMethod.DRENCH,
            ),
        )
        assert plan.watering_schedule is not None

    def test_nutrient_plan_allows_no_schedule(self):
        plan = NutrientPlan(name="No Schedule")
        assert plan.watering_schedule is None


class TestChannelIdOnEvents:
    def test_feeding_event_channel_id(self):
        from app.domain.models.feeding_event import FeedingEvent

        fe = FeedingEvent(
            plant_key="p1",
            volume_applied_liters=1.0,
            channel_id="fert-main",
        )
        assert fe.channel_id == "fert-main"

    def test_feeding_event_channel_id_default(self):
        from app.domain.models.feeding_event import FeedingEvent

        fe = FeedingEvent(plant_key="p1", volume_applied_liters=1.0)
        assert fe.channel_id is None

    def test_watering_event_channel_id(self):
        from app.domain.models.watering_event import WateringEvent

        we = WateringEvent(
            volume_liters=2.0,
            slot_keys=["s1"],
            channel_id="foliar-1",
        )
        assert we.channel_id == "foliar-1"

    def test_watering_event_channel_id_default(self):
        from app.domain.models.watering_event import WateringEvent

        we = WateringEvent(volume_liters=2.0, slot_keys=["s1"])
        assert we.channel_id is None
