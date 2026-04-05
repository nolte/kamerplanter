import pytest
from pydantic import ValidationError

from app.common.enums import ApplicationMethod, WaterSource
from app.domain.models.watering_event import FertilizerSnapshot, WateringEvent


class TestWateringEvent:
    def test_valid_event(self):
        event = WateringEvent(
            volume_liters=5.0,
            plant_keys=["plant01"],
            application_method=ApplicationMethod.DRENCH,
        )
        assert event.volume_liters == 5.0
        assert event.plant_keys == ["plant01"]
        assert event.is_supplemental is False

    def test_key_alias(self):
        event = WateringEvent(
            volume_liters=5.0,
            plant_keys=["plant01"],
            **{"_key": "abc123"},
        )
        assert event.key == "abc123"

    def test_multiple_plants(self):
        event = WateringEvent(
            volume_liters=10.0,
            plant_keys=["plant01", "plant02", "plant03"],
        )
        assert len(event.plant_keys) == 3

    def test_plant_keys_allows_empty(self):
        event = WateringEvent(volume_liters=5.0, plant_keys=[])
        assert event.plant_keys == []

    def test_volume_must_be_positive(self):
        with pytest.raises(ValidationError):
            WateringEvent(volume_liters=0, plant_keys=["plant01"])

    def test_volume_negative_raises(self):
        with pytest.raises(ValidationError):
            WateringEvent(volume_liters=-1.0, plant_keys=["plant01"])

    def test_supplemental_with_fertigation_raises(self):
        with pytest.raises(ValidationError, match="Supplemental"):
            WateringEvent(
                volume_liters=5.0,
                plant_keys=["plant01"],
                application_method=ApplicationMethod.FERTIGATION,
                is_supplemental=True,
            )

    def test_supplemental_with_drench_ok(self):
        event = WateringEvent(
            volume_liters=5.0,
            plant_keys=["plant01"],
            application_method=ApplicationMethod.DRENCH,
            is_supplemental=True,
        )
        assert event.is_supplemental is True

    def test_fertigation_without_supplemental_ok(self):
        event = WateringEvent(
            volume_liters=5.0,
            plant_keys=["plant01"],
            application_method=ApplicationMethod.FERTIGATION,
            is_supplemental=False,
        )
        assert event.application_method == ApplicationMethod.FERTIGATION

    def test_ph_bounds(self):
        WateringEvent(
            volume_liters=5.0,
            plant_keys=["plant01"],
            measured_ph=0.0,
        )
        WateringEvent(
            volume_liters=5.0,
            plant_keys=["plant01"],
            measured_ph=14.0,
        )
        with pytest.raises(ValidationError):
            WateringEvent(
                volume_liters=5.0,
                plant_keys=["plant01"],
                measured_ph=-0.1,
            )
        with pytest.raises(ValidationError):
            WateringEvent(
                volume_liters=5.0,
                plant_keys=["plant01"],
                measured_ph=14.1,
            )

    def test_ec_non_negative(self):
        WateringEvent(
            volume_liters=5.0,
            plant_keys=["plant01"],
            measured_ec=0.0,
        )
        with pytest.raises(ValidationError):
            WateringEvent(
                volume_liters=5.0,
                plant_keys=["plant01"],
                measured_ec=-1.0,
            )

    def test_all_water_sources(self):
        for source in WaterSource:
            event = WateringEvent(
                volume_liters=5.0,
                plant_keys=["plant01"],
                water_source=source,
            )
            assert event.water_source == source

    def test_all_application_methods_except_any(self):
        for method in ApplicationMethod:
            if method == ApplicationMethod.ANY:
                continue
            if method == ApplicationMethod.FERTIGATION:
                event = WateringEvent(
                    volume_liters=5.0,
                    plant_keys=["plant01"],
                    application_method=method,
                    is_supplemental=False,
                )
            else:
                event = WateringEvent(
                    volume_liters=5.0,
                    plant_keys=["plant01"],
                    application_method=method,
                )
            assert event.application_method == method

    def test_fertilizers_used(self):
        event = WateringEvent(
            volume_liters=5.0,
            plant_keys=["plant01"],
            fertilizers_used=[
                FertilizerSnapshot(product_name="CalMag", ml_per_liter=1.0),
                FertilizerSnapshot(
                    product_key="fert-123",
                    product_name="Bloom A",
                    ml_per_liter=2.5,
                ),
            ],
        )
        assert len(event.fertilizers_used) == 2
        assert event.fertilizers_used[0].product_key is None
        assert event.fertilizers_used[1].product_key == "fert-123"

    def test_optional_fields_default_none(self):
        event = WateringEvent(volume_liters=5.0, plant_keys=["plant01"])
        assert event.watered_at is None
        assert event.tank_fill_event_key is None
        assert event.nutrient_plan_key is None
        assert event.target_ec is None
        assert event.target_ph is None
        assert event.measured_ec is None
        assert event.measured_ph is None
        assert event.runoff_ec is None
        assert event.runoff_ph is None
        assert event.water_source is None
        assert event.performed_by is None
        assert event.notes is None


class TestFertilizerSnapshot:
    def test_valid_snapshot(self):
        snap = FertilizerSnapshot(product_name="CalMag", ml_per_liter=1.5)
        assert snap.product_name == "CalMag"
        assert snap.ml_per_liter == 1.5
        assert snap.product_key is None

    def test_ml_per_liter_must_be_positive(self):
        with pytest.raises(ValidationError):
            FertilizerSnapshot(product_name="CalMag", ml_per_liter=0)

    def test_ml_per_liter_negative_raises(self):
        with pytest.raises(ValidationError):
            FertilizerSnapshot(product_name="CalMag", ml_per_liter=-1.0)
