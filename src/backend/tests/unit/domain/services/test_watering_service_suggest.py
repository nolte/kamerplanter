"""Service-level tests for WateringService.suggest_volume consuming the phase
resource resolver, the waterlogging cap, the live soil-moisture sensor override
(REQ-005) and the ET seam (REQ-037). Issue #383."""

from types import SimpleNamespace

import pytest

from app.common.enums import IrrigationStrategy, SubstrateType, WaterRetention
from app.common.exceptions import NotFoundError
from app.domain.engines.watering_engine import WateringEngine
from app.domain.engines.watering_volume_engine import WateringVolumeEngine
from app.domain.models.substrate import Substrate
from app.domain.services.watering_service import WateringService

#: The caller's tenant. ``suggest_volume`` takes it as a required keyword-only
#: argument since #952 — it used to read the tenant off the record it had just
#: loaded from the URL key, which made the downstream filters compare a row with
#: itself.
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"


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

    def get_slot_for_plant(self, plant_key, *, tenant_key):  # noqa: ARG002
        # Mirrors the real signature: ``tenant_key`` is required and keyword-only
        # (#927), so a service that forgot to forward it fails here loudly.
        assert tenant_key, "get_slot_for_plant must be called with a tenant (#927)"
        if self._location_key is None:
            return None
        return SimpleNamespace(location_key=self._location_key, tenant_key=tenant_key)


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
        # The soil-moisture override resolves plant → slot → location, and that
        # slot lookup is tenant-scoped since #927 — a tenantless plant resolves to
        # "no slot" and the override never fires.
        tenant_key=TENANT_KEY,
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
        base = _service(plant, _species(waterlogging_tolerance=None)).suggest_volume("p1", tenant_key=TENANT_KEY)
        capped = _service(plant, _species(waterlogging_tolerance="sensitive")).suggest_volume(
            "p1", tenant_key=TENANT_KEY
        )
        assert capped.volume_ml < base.volume_ml


class TestSoilMoistureOverride:
    def test_wet_soil_suppresses_watering(self):
        plant = _plant()
        svc = _service(plant, _species(), sensor_service=_SensorService(moisture_percent=85.0))
        result = svc.suggest_volume("p1", tenant_key=TENANT_KEY)
        assert result.volume_ml == 0  # saturated → skip
        assert result.source == "sensor_soil_moisture"
        assert any("soil_moisture=85%" in a for a in result.adjustments)

    def test_dry_soil_keeps_full_volume(self):
        plant = _plant()
        no_sensor = _service(plant, _species()).suggest_volume("p1", tenant_key=TENANT_KEY)
        dry = _service(plant, _species(), sensor_service=_SensorService(moisture_percent=20.0)).suggest_volume(
            "p1", tenant_key=TENANT_KEY
        )
        assert dry.volume_ml == no_sensor.volume_ml  # factor 1.0 → unchanged

    def test_mid_moisture_reduces_volume(self):
        plant = _plant()
        no_sensor = _service(plant, _species()).suggest_volume("p1", tenant_key=TENANT_KEY)
        mid = _service(plant, _species(), sensor_service=_SensorService(moisture_percent=50.0)).suggest_volume(
            "p1", tenant_key=TENANT_KEY
        )
        assert 0 < mid.volume_ml < no_sensor.volume_ml

    def test_no_reading_falls_back_to_static(self):
        plant = _plant()
        no_sensor = _service(plant, _species()).suggest_volume("p1", tenant_key=TENANT_KEY)
        unavailable = _service(plant, _species(), sensor_service=_SensorService(moisture_percent=None)).suggest_volume(
            "p1", tenant_key=TENANT_KEY
        )
        assert unavailable.volume_ml == no_sensor.volume_ml
        assert unavailable.source == no_sensor.source

    def test_no_sensor_service_is_inert(self):
        plant = _plant()
        result = _service(plant, _species(), sensor_service=None).suggest_volume("p1", tenant_key=TENANT_KEY)
        assert result.source == "species_watering_guide"


class TestEtSeam:
    def test_et_override_replaces_static_volume(self):
        plant = _plant()
        result = _service(plant, _species()).suggest_volume("p1", et_net_demand_ml=1234.0, tenant_key=TENANT_KEY)
        assert result.volume_ml == 1234
        assert result.source == "evapotranspiration_demand"

    def test_et_seam_defaults_inert(self):
        plant = _plant()
        result = _service(plant, _species()).suggest_volume("p1", tenant_key=TENANT_KEY)
        assert result.source == "species_watering_guide"

    def test_et_zero_demand_means_no_water(self):
        # ET demand of 0 = "irrigate nothing" — must not be floored to 10 ml.
        plant = _plant()
        result = _service(plant, _species()).suggest_volume("p1", et_net_demand_ml=0.0, tenant_key=TENANT_KEY)
        assert result.volume_ml == 0
        assert result.source == "evapotranspiration_demand"


class _RunRepo:
    def __init__(self, run_key: str | None, plant_count: int = 1) -> None:
        self._run_key = run_key
        self._plant_count = plant_count

    def get_runs_for_plant(self, plant_key):  # noqa: ARG002
        if self._run_key is None:
            return []
        return [SimpleNamespace(key=self._run_key)]

    def get_run_plants(self, run_key, include_detached=False):  # noqa: ARG002
        return [{"_key": f"pl{i}"} for i in range(self._plant_count)]


class _DemandRepo:
    def __init__(self, recommended_volume_liters: float | None) -> None:
        self._liters = recommended_volume_liters

    def get_latest_for_run(self, run_key, tenant_key):  # noqa: ARG002
        # The demand read is tenant-scoped; #952 requires the *caller's* tenant
        # to arrive here, not one read back off the plant record.
        assert tenant_key == TENANT_KEY
        if self._liters is None:
            return None
        return SimpleNamespace(recommended_volume_liters=self._liters)


def _service_with_demand(plant, species, *, run_repo=None, demand_repo=None):
    return WateringService(
        repo=SimpleNamespace(),
        engine=WateringEngine(),
        site_repo=_SiteRepo("loc1"),
        run_repo=run_repo,
        volume_engine=WateringVolumeEngine(),
        plant_repo=_PlantRepo(plant),
        species_repo=_SpeciesRepo(species),
        irrigation_demand_repo=demand_repo,
    )


class TestEtDemandAutoLookup:
    def test_latest_demand_drives_volume_when_not_supplied(self):
        # 2 L for the whole run, split across 2 plants → 1 L = 1000 ml per plant.
        plant = _plant(key="p1")
        svc = _service_with_demand(
            plant, _species(), run_repo=_RunRepo("run1", plant_count=2), demand_repo=_DemandRepo(2.0)
        )
        result = svc.suggest_volume("p1", tenant_key=TENANT_KEY)
        assert result.volume_ml == 1000
        assert result.source == "evapotranspiration_demand"

    def test_zero_demand_suppresses_watering(self):
        plant = _plant(key="p1")
        svc = _service_with_demand(
            plant, _species(), run_repo=_RunRepo("run1", plant_count=1), demand_repo=_DemandRepo(0.0)
        )
        result = svc.suggest_volume("p1", tenant_key=TENANT_KEY)
        assert result.volume_ml == 0
        assert result.source == "evapotranspiration_demand"

    def test_no_demand_record_stays_inert(self):
        plant = _plant(key="p1")
        svc = _service_with_demand(plant, _species(), run_repo=_RunRepo("run1"), demand_repo=_DemandRepo(None))
        result = svc.suggest_volume("p1", tenant_key=TENANT_KEY)
        assert result.source == "species_watering_guide"

    def test_no_repo_wired_stays_inert(self):
        plant = _plant(key="p1")
        result = _service_with_demand(plant, _species()).suggest_volume("p1", tenant_key=TENANT_KEY)
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
        result = svc.suggest_volume("p1", tenant_key=TENANT_KEY)
        assert result.water_only is True
        assert "flush" in result.regime_note


class TestTheCallersTenantIsWhatCounts:
    """#952 — the plant is resolved against the caller, not against itself.

    ``suggest_volume`` used to load the plant straight from the URL key and then
    feed ``plant.tenant_key`` into the reads #947 had scoped, so the predicate
    compared the record's tenant with its own. The endpoint answered 200 for a
    foreign key with a recommendation derived from the other tenant's plant.
    """

    def test_a_foreign_plant_is_not_found_rather_than_answered(self):
        foreign = _plant(key="p1", tenant_key=FOREIGN_TENANT_KEY)
        svc = _service(foreign, _species())

        with pytest.raises(NotFoundError):
            svc.suggest_volume("p1", tenant_key=TENANT_KEY)

    def test_the_callers_own_plant_is_still_answered(self):
        svc = _service(_plant(), _species())

        assert svc.suggest_volume("p1", tenant_key=TENANT_KEY).volume_ml > 0

    def test_omitting_the_tenant_entirely_is_a_type_error(self):
        svc = _service(_plant(), _species())

        with pytest.raises(TypeError):
            svc.suggest_volume("p1")


class TestTheSubstrateRecordsEnumDecidesTheRetention:
    """#1368 — a real catalogue record carries both signals, and they disagree.

    The engine-level test pins the rule; this one pins that the *production* path
    reaches it. ``suggest_volume`` reads both fields off the stored ``Substrate``
    and hands them to the engine together, so a rule that only held when the
    number was absent would still be wrong for every seeded record — which is
    exactly the state #1368 found: no test was keyed to a seeded record, so the
    catalogue could flip the modifier by 1.74x without anything going red.

    The fixture is a real ``Substrate`` (not a namespace) so it cannot carry a
    field shape the model would reject.
    """

    #: The sphagnum case, verbatim from the catalogue apart from the WHC: the
    #: record declares ``water_retention: high`` and dried sphagnum's published
    #: container-capacity figure is 28 vol-% (EN 13041, pF 1), which falls in
    #: REQ-019's *low* band (< 30 %). Both statements are true of the medium.
    def _substrate(self, whc: float | None) -> Substrate:
        return Substrate(
            type=SubstrateType.SPHAGNUM,
            name_de="Sphagnum-Moos (getrocknet)",
            name_en="Sphagnum Moss (Dried)",
            ph_base=4.2,
            ec_base_ms=0.05,
            water_retention=WaterRetention.HIGH,
            air_porosity_percent=25.0,
            composition={"sphagnum": 1.0},
            water_holding_capacity_percent=whc,
            bulk_density_g_per_l=30.0,
            irrigation_strategy=IrrigationStrategy.MODERATE,
        )

    def _svc(self, substrate: Substrate) -> WateringService:
        return WateringService(
            repo=SimpleNamespace(),
            engine=WateringEngine(),
            site_repo=_SiteRepo(None),
            volume_engine=WateringVolumeEngine(),
            plant_repo=_PlantRepo(_plant(substrate_key="sub1")),
            species_repo=_SpeciesRepo(_species()),
            substrate_repo=SimpleNamespace(get_substrate_by_key=lambda key: substrate),  # noqa: ARG005
        )

    def test_the_declared_enum_wins_over_the_records_own_whc(self):
        result = self._svc(self._substrate(28.0)).suggest_volume("p1", tenant_key=TENANT_KEY)

        # Species guide 200–400 → 300 ml, then the enum's high → *0.80.
        assert result.volume_ml == 240
        assert any("retention=high→*0.8" in a for a in result.adjustments)

    def test_the_stored_whc_no_longer_changes_the_answer_at_all(self):
        """28 and 80 are the two published figures for the same medium.

        Before #1368 they produced *1.22 and *0.70 — a factor of 1.74 decided by
        which measurement method the catalogue happened to have recorded.
        """
        volumes = {
            whc: self._svc(self._substrate(whc)).suggest_volume("p1", tenant_key=TENANT_KEY).volume_ml
            for whc in (28.0, 80.0, None)
        }

        assert len(set(volumes.values())) == 1, volumes


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-q"])
