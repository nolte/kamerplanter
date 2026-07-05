"""Service-level tests for WateringService.suggest_volume consuming the phase
resource resolver, the waterlogging cap, the live soil-moisture sensor override
(REQ-005) and the ET seam (REQ-037). Issue #383."""

from types import SimpleNamespace

import pytest

from app.domain.engines.watering_engine import WateringEngine
from app.domain.engines.watering_volume_engine import WateringVolumeEngine
from app.domain.services.watering_service import WateringService


class _PlantRepo:
    def __init__(self, plant) -> None:
        self._plant = plant

    def get_by_key(self, key):  # noqa: ARG002
        return self._plant


class _SpeciesRepo:
    """No get_cultivar_by_key attr → cultivar branch is skipped."""

    def __init__(self, species) -> None:
        self._species = species

    def get_by_key(self, key):  # noqa: ARG002
        return self._species


class _SiteRepo:
    def __init__(self, location_key: str | None) -> None:
        self._location_key = location_key

    def get_slot_for_plant(self, plant_key):  # noqa: ARG002
        if self._location_key is None:
            return None
        return SimpleNamespace(location_key=self._location_key)


class _SensorService:
    """Fake sensor service returning a single soil-moisture reading."""

    def __init__(self, moisture_percent: float | None, metric: str = "soil_moisture") -> None:
        self._moisture = moisture_percent
        self._metric = metric

    def get_sensors_for_location(self, location_key):  # noqa: ARG002
        return [SimpleNamespace(metric_type=self._metric, is_active=True, ha_entity_id="sensor.soil")]

    def get_live_state_for_sensors(self, sensors):  # noqa: ARG002
        if self._moisture is None:
            return {"values": {}, "source": "unavailable"}
        return {"values": {"soil_moisture": {"value": self._moisture}}, "source": "ha_live"}


def _plant(**kw):
    defaults = dict(
        species_key="sp1",
        cultivar_key=None,
        substrate_key=None,
        substrate_type_override=None,
        current_phase_key=None,
        container_volume_liters=None,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _species(waterlogging_tolerance=None, vol_min=200, vol_max=400):
    guide = SimpleNamespace(volume_ml_min=vol_min, volume_ml_max=vol_max, seasonal_adjustments=None)
    return SimpleNamespace(waterlogging_tolerance=waterlogging_tolerance, watering_guide=guide)


def _service(plant, species, *, location_key="loc1", sensor_service=None):
    return WateringService(
        repo=SimpleNamespace(),
        engine=WateringEngine(),
        site_repo=_SiteRepo(location_key),
        volume_engine=WateringVolumeEngine(),
        plant_repo=_PlantRepo(plant),
        species_repo=_SpeciesRepo(species),
        sensor_service=sensor_service,
    )


class TestWaterloggingCap:
    def test_sensitive_species_caps_volume(self):
        plant = _plant(current_phase_key=None)
        base = _service(plant, _species(waterlogging_tolerance=None)).suggest_volume("p1")
        capped = _service(plant, _species(waterlogging_tolerance="sensitive")).suggest_volume("p1")
        assert capped.volume_ml < base.volume_ml


class TestSoilMoistureOverride:
    def test_wet_soil_suppresses_watering(self):
        plant = _plant()
        svc = _service(plant, _species(), sensor_service=_SensorService(moisture_percent=85.0))
        result = svc.suggest_volume("p1")
        assert result.volume_ml == 0  # saturated → skip
        assert result.source == "sensor_soil_moisture"
        assert any("soil_moisture=85%" in a for a in result.adjustments)

    def test_dry_soil_keeps_full_volume(self):
        plant = _plant()
        no_sensor = _service(plant, _species()).suggest_volume("p1")
        dry = _service(plant, _species(), sensor_service=_SensorService(moisture_percent=20.0)).suggest_volume("p1")
        assert dry.volume_ml == no_sensor.volume_ml  # factor 1.0 → unchanged

    def test_mid_moisture_reduces_volume(self):
        plant = _plant()
        no_sensor = _service(plant, _species()).suggest_volume("p1")
        mid = _service(plant, _species(), sensor_service=_SensorService(moisture_percent=50.0)).suggest_volume("p1")
        assert 0 < mid.volume_ml < no_sensor.volume_ml

    def test_no_reading_falls_back_to_static(self):
        plant = _plant()
        no_sensor = _service(plant, _species()).suggest_volume("p1")
        unavailable = _service(plant, _species(), sensor_service=_SensorService(moisture_percent=None)).suggest_volume(
            "p1"
        )
        assert unavailable.volume_ml == no_sensor.volume_ml
        assert unavailable.source == no_sensor.source

    def test_no_sensor_service_is_inert(self):
        plant = _plant()
        result = _service(plant, _species(), sensor_service=None).suggest_volume("p1")
        assert result.source == "species_watering_guide"


class TestEtSeam:
    def test_et_override_replaces_static_volume(self):
        plant = _plant()
        result = _service(plant, _species()).suggest_volume("p1", et_net_demand_ml=1234.0)
        assert result.volume_ml == 1234
        assert result.source == "evapotranspiration_demand"

    def test_et_seam_defaults_inert(self):
        plant = _plant()
        result = _service(plant, _species()).suggest_volume("p1")
        assert result.source == "species_watering_guide"


class TestFlushRegimeSurfacing:
    def test_flush_phase_marks_water_only(self):
        # phase resolution needs a phase name; use lifecycle repo fallback.
        plant = _plant(current_phase_key="phase1")

        class _Lifecycle:
            def get_phase_by_key(self, key):  # noqa: ARG002
                return SimpleNamespace(name="flushing")

        svc = WateringService(
            repo=SimpleNamespace(),
            engine=WateringEngine(),
            site_repo=_SiteRepo("loc1"),
            volume_engine=WateringVolumeEngine(),
            plant_repo=_PlantRepo(plant),
            species_repo=_SpeciesRepo(_species()),
            lifecycle_repo=_Lifecycle(),
        )
        result = svc.suggest_volume("p1")
        assert result.water_only is True
        assert "flush" in result.regime_note


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-q"])
