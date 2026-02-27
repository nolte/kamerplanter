from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import (
    IrrigationSystem,
    MaintenancePriority,
    MaintenanceType,
    TankType,
)
from app.domain.engines.tank_engine import TankEngine
from app.domain.models.tank import MaintenanceLog, MaintenanceSchedule, Tank, TankState


@pytest.fixture
def engine():
    return TankEngine()


def _make_tank(**kwargs) -> Tank:
    defaults = {"name": "Test Tank", "tank_type": TankType.NUTRIENT, "volume_liters": 50.0}
    defaults.update(kwargs)
    return Tank(**defaults)


def _make_state(**kwargs) -> TankState:
    defaults = {"tank_key": "t1"}
    defaults.update(kwargs)
    return TankState(**defaults)


class TestCheckAlerts:
    def test_no_alerts_normal_values(self, engine):
        tank = _make_tank(has_lid=True)
        state = _make_state(ph=6.0, ec_ms=1.5, water_temp_celsius=20.0, fill_level_percent=80.0)
        alerts = engine.check_alerts(tank, state)
        assert len(alerts) == 0

    def test_ph_low_alert(self, engine):
        tank = _make_tank()
        state = _make_state(ph=4.5)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "ph_low" for a in alerts)
        assert alerts[0]["severity"] == "high"

    def test_ph_high_alert(self, engine):
        tank = _make_tank()
        state = _make_state(ph=7.5)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "ph_high" for a in alerts)

    def test_ph_boundary_no_alert(self, engine):
        tank = _make_tank()
        state = _make_state(ph=5.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"].startswith("ph") for a in alerts)

        state2 = _make_state(ph=7.0)
        alerts2 = engine.check_alerts(tank, state2)
        assert not any(a["type"].startswith("ph") for a in alerts2)

    def test_ec_high_nutrient_tank(self, engine):
        tank = _make_tank(tank_type=TankType.NUTRIENT)
        state = _make_state(ec_ms=3.5)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "ec_high" for a in alerts)

    def test_ec_high_non_nutrient_tank_no_alert(self, engine):
        tank = _make_tank(tank_type=TankType.IRRIGATION)
        state = _make_state(ec_ms=3.5)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "ec_high" for a in alerts)

    def test_temp_critical(self, engine):
        tank = _make_tank(has_lid=True)
        state = _make_state(water_temp_celsius=29.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "temp_critical" and a["severity"] == "critical" for a in alerts)

    def test_temp_high_warning(self, engine):
        tank = _make_tank(has_lid=True)
        state = _make_state(water_temp_celsius=26.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "temp_high" and a["severity"] == "medium" for a in alerts)

    def test_algae_risk_no_lid(self, engine):
        tank = _make_tank(has_lid=False)
        state = _make_state(water_temp_celsius=23.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "algae_risk" for a in alerts)

    def test_no_algae_risk_with_lid(self, engine):
        tank = _make_tank(has_lid=True)
        state = _make_state(water_temp_celsius=23.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "algae_risk" for a in alerts)

    def test_fill_level_low(self, engine):
        tank = _make_tank()
        state = _make_state(fill_level_percent=15.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "fill_low" for a in alerts)

    def test_fill_level_ok(self, engine):
        tank = _make_tank()
        state = _make_state(fill_level_percent=50.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "fill_low" for a in alerts)

    def test_multiple_alerts(self, engine):
        tank = _make_tank(has_lid=False, tank_type=TankType.NUTRIENT)
        state = _make_state(ph=4.0, ec_ms=4.0, water_temp_celsius=30.0, fill_level_percent=10.0)
        alerts = engine.check_alerts(tank, state)
        alert_types = {a["type"] for a in alerts}
        assert "ph_low" in alert_types
        assert "ec_high" in alert_types
        assert "temp_critical" in alert_types
        assert "fill_low" in alert_types
        assert "algae_risk" in alert_types

    def test_none_values_no_alerts(self, engine):
        tank = _make_tank()
        state = _make_state()
        alerts = engine.check_alerts(tank, state)
        assert len(alerts) == 0


class TestCalculateNextMaintenance:
    def test_never_performed_due_soon(self, engine):
        schedule = MaintenanceSchedule(
            tank_key="t1", maintenance_type=MaintenanceType.WATER_CHANGE,
            interval_days=7, reminder_days_before=2,
        )
        now = datetime.now(UTC)
        result = engine.calculate_next_maintenance(schedule, None, now)
        # next_due == now → days_until ~= 0 → within reminder window
        assert result["status"] == "due_soon"
        assert result["days_until"] <= 0

    def test_recently_performed_ok(self, engine):
        schedule = MaintenanceSchedule(
            tank_key="t1", maintenance_type=MaintenanceType.WATER_CHANGE,
            interval_days=7, reminder_days_before=2,
        )
        now = datetime.now(UTC)
        last_log = MaintenanceLog(
            tank_key="t1", maintenance_type=MaintenanceType.WATER_CHANGE,
            performed_at=now - timedelta(days=1),
        )
        result = engine.calculate_next_maintenance(schedule, last_log, now)
        assert result["status"] == "ok"
        assert result["days_until"] > 0

    def test_due_soon(self, engine):
        schedule = MaintenanceSchedule(
            tank_key="t1", maintenance_type=MaintenanceType.CLEANING,
            interval_days=7, reminder_days_before=3,
        )
        now = datetime.now(UTC)
        last_log = MaintenanceLog(
            tank_key="t1", maintenance_type=MaintenanceType.CLEANING,
            performed_at=now - timedelta(days=5),
        )
        result = engine.calculate_next_maintenance(schedule, last_log, now)
        assert result["status"] == "due_soon"

    def test_overdue(self, engine):
        schedule = MaintenanceSchedule(
            tank_key="t1", maintenance_type=MaintenanceType.SANITIZATION,
            interval_days=30, reminder_days_before=5,
        )
        now = datetime.now(UTC)
        last_log = MaintenanceLog(
            tank_key="t1", maintenance_type=MaintenanceType.SANITIZATION,
            performed_at=now - timedelta(days=35),
        )
        result = engine.calculate_next_maintenance(schedule, last_log, now)
        assert result["status"] == "overdue"
        assert result["days_until"] < 0


class TestValidateTankAssignment:
    def test_recirculation_with_hydro_ok(self, engine):
        engine.validate_tank_assignment(TankType.RECIRCULATION, IrrigationSystem.HYDRO)

    def test_recirculation_with_nft_ok(self, engine):
        engine.validate_tank_assignment(TankType.RECIRCULATION, IrrigationSystem.NFT)

    def test_recirculation_with_ebb_flow_ok(self, engine):
        engine.validate_tank_assignment(TankType.RECIRCULATION, IrrigationSystem.EBB_FLOW)

    def test_recirculation_with_drip_raises(self, engine):
        with pytest.raises(ValueError, match="hydro irrigation"):
            engine.validate_tank_assignment(TankType.RECIRCULATION, IrrigationSystem.DRIP)

    def test_recirculation_with_manual_raises(self, engine):
        with pytest.raises(ValueError, match="hydro irrigation"):
            engine.validate_tank_assignment(TankType.RECIRCULATION, IrrigationSystem.MANUAL)

    def test_recirculation_with_none_raises(self, engine):
        with pytest.raises(ValueError, match="hydro irrigation"):
            engine.validate_tank_assignment(TankType.RECIRCULATION, None)

    def test_non_recirculation_any_system_ok(self, engine):
        for tank_type in [TankType.NUTRIENT, TankType.IRRIGATION, TankType.RESERVOIR]:
            for system in IrrigationSystem:
                engine.validate_tank_assignment(tank_type, system)

    def test_non_recirculation_none_system_ok(self, engine):
        engine.validate_tank_assignment(TankType.NUTRIENT, None)


class TestValidateFillLevel:
    def test_liters_only_calculates_percent(self, engine):
        liters, percent = engine.validate_fill_level(100.0, 50.0, None)
        assert liters == 50.0
        assert percent == 50.0

    def test_percent_only_calculates_liters(self, engine):
        liters, percent = engine.validate_fill_level(200.0, None, 75.0)
        assert liters == 150.0
        assert percent == 75.0

    def test_both_consistent(self, engine):
        liters, percent = engine.validate_fill_level(100.0, 50.0, 50.0)
        assert liters == 50.0
        assert percent == 50.0

    def test_both_inconsistent_raises(self, engine):
        with pytest.raises(ValueError, match="Inconsistent"):
            engine.validate_fill_level(100.0, 50.0, 80.0)

    def test_both_none(self, engine):
        liters, percent = engine.validate_fill_level(100.0, None, None)
        assert liters is None
        assert percent is None

    def test_small_rounding_tolerance(self, engine):
        # 49L in a 100L tank = 49%, vs given 50% — difference is 1%, within tolerance
        liters, percent = engine.validate_fill_level(100.0, 49.0, 50.0)
        assert liters == 49.0
        assert percent == 50.0


class TestGetDefaultSchedules:
    def test_nutrient_has_5_schedules(self, engine):
        defaults = engine.get_default_schedules(TankType.NUTRIENT)
        assert len(defaults) == 5

    def test_irrigation_has_4_schedules(self, engine):
        defaults = engine.get_default_schedules(TankType.IRRIGATION)
        assert len(defaults) == 4

    def test_reservoir_has_3_schedules(self, engine):
        defaults = engine.get_default_schedules(TankType.RESERVOIR)
        assert len(defaults) == 3

    def test_recirculation_has_6_schedules(self, engine):
        defaults = engine.get_default_schedules(TankType.RECIRCULATION)
        assert len(defaults) == 6

    def test_nutrient_water_change_weekly(self, engine):
        defaults = engine.get_default_schedules(TankType.NUTRIENT)
        wc = next(d for d in defaults if d["type"] == MaintenanceType.WATER_CHANGE)
        assert wc["interval_days"] == 7
        assert wc["priority"] == MaintenancePriority.HIGH

    def test_recirculation_water_change_critical(self, engine):
        defaults = engine.get_default_schedules(TankType.RECIRCULATION)
        wc = next(d for d in defaults if d["type"] == MaintenanceType.WATER_CHANGE)
        assert wc["priority"] == MaintenancePriority.CRITICAL

    def test_each_schedule_has_required_keys(self, engine):
        for tank_type in TankType:
            defaults = engine.get_default_schedules(tank_type)
            for d in defaults:
                assert "type" in d
                assert "interval_days" in d
                assert "priority" in d
