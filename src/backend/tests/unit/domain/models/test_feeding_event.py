import pytest
from pydantic import ValidationError

from app.common.enums import ApplicationMethod
from app.domain.models.feeding_event import FeedingEvent, FeedingEventFertilizer


class TestFeedingEventFertilizer:
    def test_valid(self):
        f = FeedingEventFertilizer(fertilizer_key="f1", ml_applied=5.0)
        assert f.ml_applied == 5.0

    def test_ml_applied_zero_raises(self):
        with pytest.raises(ValidationError):
            FeedingEventFertilizer(fertilizer_key="f1", ml_applied=0)

    def test_ml_applied_negative_raises(self):
        with pytest.raises(ValidationError):
            FeedingEventFertilizer(fertilizer_key="f1", ml_applied=-1.0)


class TestFeedingEvent:
    def test_valid_event(self):
        event = FeedingEvent(
            plant_key="p1",
            volume_applied_liters=2.0,
        )
        assert event.plant_key == "p1"
        assert event.application_method == ApplicationMethod.FERTIGATION
        assert event.is_supplemental is False

    def test_volume_zero_raises(self):
        with pytest.raises(ValidationError):
            FeedingEvent(plant_key="p1", volume_applied_liters=0)

    def test_with_fertilizers(self):
        event = FeedingEvent(
            plant_key="p1",
            volume_applied_liters=1.0,
            fertilizers_used=[
                FeedingEventFertilizer(fertilizer_key="f1", ml_applied=2.0),
                FeedingEventFertilizer(fertilizer_key="f2", ml_applied=1.5),
            ],
        )
        assert len(event.fertilizers_used) == 2

    def test_runoff_data(self):
        event = FeedingEvent(
            plant_key="p1",
            volume_applied_liters=2.0,
            measured_ec_before=1.2,
            measured_ec_after=1.4,
            runoff_ec=1.6,
            runoff_ph=6.2,
            runoff_volume_liters=0.4,
        )
        assert event.runoff_ec == 1.6

    def test_ph_bounds(self):
        FeedingEvent(plant_key="p1", volume_applied_liters=1.0, measured_ph_before=0.0)
        FeedingEvent(plant_key="p1", volume_applied_liters=1.0, measured_ph_before=14.0)
        with pytest.raises(ValidationError):
            FeedingEvent(plant_key="p1", volume_applied_liters=1.0, measured_ph_before=14.1)

    def test_key_alias(self):
        event = FeedingEvent(
            plant_key="p1", volume_applied_liters=1.0,
            **{"_key": "fe1"},
        )
        assert event.key == "fe1"

    def test_all_application_methods(self):
        for method in ApplicationMethod:
            event = FeedingEvent(
                plant_key="p1", volume_applied_liters=1.0,
                application_method=method,
            )
            assert event.application_method == method

    def test_defaults(self):
        event = FeedingEvent(plant_key="p1", volume_applied_liters=1.0)
        assert event.fertilizers_used == []
        assert event.timestamp is None
        assert event.measured_ec_before is None
        assert event.runoff_volume_liters is None
