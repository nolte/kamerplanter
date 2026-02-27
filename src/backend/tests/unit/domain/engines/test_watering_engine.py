import pytest

from app.common.enums import ApplicationMethod, IrrigationSystem
from app.domain.engines.watering_engine import WateringEngine
from app.domain.models.watering_event import WateringEvent


@pytest.fixture
def engine():
    return WateringEngine()


def _make_event(**kwargs) -> WateringEvent:
    defaults = {
        "volume_liters": 5.0,
        "slot_keys": ["TENT01_A1"],
        "application_method": ApplicationMethod.DRENCH,
    }
    defaults.update(kwargs)
    return WateringEvent(**defaults)


class TestValidateAndWarn:
    def test_no_warnings_valid_manual_drench(self, engine):
        event = _make_event()
        warnings = engine.validate_and_warn(event, IrrigationSystem.MANUAL)
        assert len(warnings) == 0

    def test_no_warnings_valid_drip_fertigation(self, engine):
        event = _make_event(application_method=ApplicationMethod.FERTIGATION)
        warnings = engine.validate_and_warn(event, IrrigationSystem.DRIP)
        assert len(warnings) == 0

    def test_no_warnings_none_irrigation(self, engine):
        event = _make_event()
        warnings = engine.validate_and_warn(event, None)
        assert len(warnings) == 0

    def test_fertigation_on_manual_warns(self, engine):
        event = _make_event(application_method=ApplicationMethod.FERTIGATION)
        warnings = engine.validate_and_warn(event, IrrigationSystem.MANUAL)
        assert len(warnings) == 1
        assert warnings[0]["type"] == "fertigation_on_manual"

    def test_drench_on_hydro_without_supplemental_warns(self, engine):
        event = _make_event(
            application_method=ApplicationMethod.DRENCH,
            is_supplemental=False,
        )
        warnings = engine.validate_and_warn(event, IrrigationSystem.HYDRO)
        assert len(warnings) == 1
        assert warnings[0]["type"] == "drench_on_auto"

    def test_drench_on_nft_without_supplemental_warns(self, engine):
        event = _make_event(
            application_method=ApplicationMethod.DRENCH,
            is_supplemental=False,
        )
        warnings = engine.validate_and_warn(event, IrrigationSystem.NFT)
        assert any(w["type"] == "drench_on_auto" for w in warnings)

    def test_drench_on_ebb_flow_without_supplemental_warns(self, engine):
        event = _make_event(
            application_method=ApplicationMethod.DRENCH,
            is_supplemental=False,
        )
        warnings = engine.validate_and_warn(event, IrrigationSystem.EBB_FLOW)
        assert any(w["type"] == "drench_on_auto" for w in warnings)

    def test_drench_on_hydro_with_supplemental_no_warning(self, engine):
        event = _make_event(
            application_method=ApplicationMethod.DRENCH,
            is_supplemental=True,
        )
        warnings = engine.validate_and_warn(event, IrrigationSystem.HYDRO)
        assert not any(w["type"] == "drench_on_auto" for w in warnings)

    def test_drench_on_manual_no_drench_warning(self, engine):
        event = _make_event(
            application_method=ApplicationMethod.DRENCH,
            is_supplemental=False,
        )
        warnings = engine.validate_and_warn(event, IrrigationSystem.MANUAL)
        assert not any(w["type"] == "drench_on_auto" for w in warnings)

    def test_drench_on_drip_no_drench_warning(self, engine):
        event = _make_event(
            application_method=ApplicationMethod.DRENCH,
            is_supplemental=False,
        )
        warnings = engine.validate_and_warn(event, IrrigationSystem.DRIP)
        assert not any(w["type"] == "drench_on_auto" for w in warnings)

    def test_high_volume_warns(self, engine):
        event = _make_event(volume_liters=25.0, slot_keys=["TENT01_A1"])
        warnings = engine.validate_and_warn(event, IrrigationSystem.MANUAL)
        assert any(w["type"] == "high_volume" for w in warnings)

    def test_volume_at_threshold_no_warning(self, engine):
        event = _make_event(volume_liters=20.0, slot_keys=["TENT01_A1"])
        warnings = engine.validate_and_warn(event, IrrigationSystem.MANUAL)
        assert not any(w["type"] == "high_volume" for w in warnings)

    def test_high_volume_distributed_no_warning(self, engine):
        # 40L across 3 slots = 13.3 L/slot → under threshold
        event = _make_event(
            volume_liters=40.0,
            slot_keys=["TENT01_A1", "TENT01_A2", "TENT01_A3"],
        )
        warnings = engine.validate_and_warn(event, IrrigationSystem.MANUAL)
        assert not any(w["type"] == "high_volume" for w in warnings)

    def test_multiple_warnings(self, engine):
        # Fertigation on manual + high volume
        event = _make_event(
            application_method=ApplicationMethod.FERTIGATION,
            volume_liters=25.0,
            slot_keys=["TENT01_A1"],
        )
        warnings = engine.validate_and_warn(event, IrrigationSystem.MANUAL)
        types = {w["type"] for w in warnings}
        assert "fertigation_on_manual" in types
        assert "high_volume" in types
