from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import (
    FillType,
    IrrigationSystem,
    MaintenancePriority,
    MaintenanceType,
    TankType,
    WaterSource,
)
from app.domain.engines.tank_engine import TankEngine
from app.domain.models.tank import MaintenanceLog, MaintenanceSchedule, Tank, TankFillEvent, TankState


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
    """Adapted tests for the enhanced alert engine with tank-type-specific thresholds."""

    def test_no_alerts_normal_values(self, engine):
        tank = _make_tank(has_lid=True, is_light_proof=True)
        state = _make_state(ph=6.0, ec_ms=1.5, water_temp_celsius=20.0, fill_level_percent=80.0)
        alerts = engine.check_alerts(tank, state)
        assert len(alerts) == 0

    def test_ph_low_alert(self, engine):
        tank = _make_tank()  # NUTRIENT: range 5.5–6.5
        state = _make_state(ph=4.5)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "ph_out_of_range" for a in alerts)
        # 4.5 < 5.5 - 0.5 = 5.0 → critical
        assert alerts[0]["severity"] == "critical"

    def test_ph_high_alert(self, engine):
        tank = _make_tank()  # NUTRIENT: range 5.5–6.5
        state = _make_state(ph=7.5)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "ph_out_of_range" for a in alerts)

    def test_ph_within_range_no_alert(self, engine):
        tank = _make_tank()  # NUTRIENT: range 5.5–6.5
        state = _make_state(ph=6.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "ph_out_of_range" for a in alerts)

    def test_ph_reservoir_wide_range(self, engine):
        tank = _make_tank(tank_type=TankType.RESERVOIR)  # range 5.0–8.0
        state = _make_state(ph=7.5)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "ph_out_of_range" for a in alerts)

    def test_ec_high_nutrient_tank(self, engine):
        tank = _make_tank(tank_type=TankType.NUTRIENT)
        state = _make_state(ec_ms=3.5)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "ec_high" for a in alerts)

    def test_ec_high_irrigation_tank(self, engine):
        tank = _make_tank(tank_type=TankType.IRRIGATION)
        state = _make_state(ec_ms=2.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "ec_high" for a in alerts)

    def test_ec_high_reservoir_no_alert(self, engine):
        tank = _make_tank(tank_type=TankType.RESERVOIR)
        state = _make_state(ec_ms=3.5)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "ec_high" for a in alerts)

    def test_temp_warm_critical_nutrient(self, engine):
        tank = _make_tank(has_lid=True, is_light_proof=True)  # NUTRIENT: warm_crit=26
        state = _make_state(water_temp_celsius=27.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "temperature_warm_critical" and a["severity"] == "critical" for a in alerts)

    def test_temp_warm_warning_nutrient(self, engine):
        tank = _make_tank(has_lid=True, is_light_proof=True)  # NUTRIENT: warm_warn=22
        state = _make_state(water_temp_celsius=23.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "temperature_warm_warning" and a["severity"] == "medium" for a in alerts)

    def test_algae_risk_no_lid_warm_nutrient(self, engine):
        # Not light-proof (default), no lid, warm, nutrient = 3 factors → high
        tank = _make_tank(has_lid=False)
        state = _make_state(water_temp_celsius=23.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "algae_risk" for a in alerts)

    def test_no_algae_risk_light_proof(self, engine):
        tank = _make_tank(is_light_proof=True, has_lid=False)
        state = _make_state(water_temp_celsius=23.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "algae_risk" for a in alerts)

    def test_fill_level_low(self, engine):
        tank = _make_tank()
        state = _make_state(fill_level_percent=15.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "fill_level_low" for a in alerts)

    def test_fill_level_ok(self, engine):
        tank = _make_tank()
        state = _make_state(fill_level_percent=50.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "fill_level_low" for a in alerts)

    def test_multiple_alerts(self, engine):
        tank = _make_tank(has_lid=False, tank_type=TankType.NUTRIENT)
        state = _make_state(ph=4.0, ec_ms=4.0, water_temp_celsius=30.0, fill_level_percent=10.0)
        alerts = engine.check_alerts(tank, state)
        alert_types = {a["type"] for a in alerts}
        assert "ph_out_of_range" in alert_types
        assert "ec_high" in alert_types
        assert "temperature_warm_critical" in alert_types
        assert "fill_level_low" in alert_types
        assert "algae_risk" in alert_types

    def test_none_values_no_alerts(self, engine):
        tank = _make_tank(is_light_proof=True)
        state = _make_state()
        alerts = engine.check_alerts(tank, state)
        assert len(alerts) == 0


class TestPHDriftAlerts:
    def test_no_drift_without_fill_event(self, engine):
        tank = _make_tank()
        state = _make_state(ph=6.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "ph_drift" for a in alerts)

    def test_drift_above_threshold(self, engine):
        tank = _make_tank()
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, measured_ph=6.0,
        )
        state = _make_state(ph=6.6)  # drift 0.6 > 0.5 default
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert any(a["type"] == "ph_drift" for a in alerts)

    def test_no_drift_within_threshold(self, engine):
        tank = _make_tank()
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, measured_ph=6.0,
        )
        state = _make_state(ph=6.4)  # drift 0.4 < 0.5
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert not any(a["type"] == "ph_drift" for a in alerts)

    def test_recirc_stricter_threshold(self, engine):
        tank = _make_tank(tank_type=TankType.RECIRCULATION, is_light_proof=True)
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, measured_ph=6.0,
        )
        state = _make_state(ph=6.35)  # drift 0.35 > 0.3 recirc threshold
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert any(a["type"] == "ph_drift" for a in alerts)

    def test_drift_high_severity_large_drift(self, engine):
        tank = _make_tank()
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, measured_ph=6.0,
        )
        state = _make_state(ph=7.2)  # drift 1.2 > 0.5*2 → high
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        drift_alert = next(a for a in alerts if a["type"] == "ph_drift")
        assert drift_alert["severity"] == "high"


class TestECPlanRelativeAlerts:
    def test_ec_deviation_warning_20pct(self, engine):
        tank = _make_tank()
        state = _make_state(ec_ms=1.25)  # 25% deviation from 1.0
        alerts = engine.check_alerts(tank, state, target_ec_ms=1.0)
        assert any(a["type"] == "ec_deviation_warning" for a in alerts)

    def test_ec_deviation_alarm_30pct(self, engine):
        tank = _make_tank()
        state = _make_state(ec_ms=1.35)  # 35% deviation from 1.0
        alerts = engine.check_alerts(tank, state, target_ec_ms=1.0)
        assert any(a["type"] == "ec_deviation_alarm" for a in alerts)

    def test_ec_no_deviation_within_20pct(self, engine):
        tank = _make_tank()
        state = _make_state(ec_ms=1.15)  # 15% deviation from 1.0
        alerts = engine.check_alerts(tank, state, target_ec_ms=1.0)
        assert not any(a["type"].startswith("ec_deviation") for a in alerts)

    def test_ec_no_plan_no_deviation_alerts(self, engine):
        tank = _make_tank()
        state = _make_state(ec_ms=5.0)
        alerts = engine.check_alerts(tank, state)  # no target_ec_ms
        assert not any(a["type"].startswith("ec_deviation") for a in alerts)


class TestTemperatureTypeSpecific:
    def test_nutrient_warm_warn_22(self, engine):
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        state = _make_state(water_temp_celsius=23.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "temperature_warm_warning" for a in alerts)

    def test_nutrient_cold_warn_15(self, engine):
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        state = _make_state(water_temp_celsius=14.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "temperature_cold_warning" for a in alerts)

    def test_nutrient_cold_crit_10(self, engine):
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        state = _make_state(water_temp_celsius=9.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "temperature_cold_critical" for a in alerts)

    def test_irrigation_warm_warn_28(self, engine):
        tank = _make_tank(tank_type=TankType.IRRIGATION, is_light_proof=True)
        state = _make_state(water_temp_celsius=29.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "temperature_warm_warning" for a in alerts)

    def test_irrigation_no_warn_at_25(self, engine):
        tank = _make_tank(tank_type=TankType.IRRIGATION, is_light_proof=True)
        state = _make_state(water_temp_celsius=25.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"].startswith("temperature") for a in alerts)

    def test_recirc_warm_crit_25(self, engine):
        tank = _make_tank(tank_type=TankType.RECIRCULATION, is_light_proof=True)
        state = _make_state(water_temp_celsius=26.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "temperature_warm_critical" for a in alerts)

    def test_reservoir_very_wide_range(self, engine):
        tank = _make_tank(tank_type=TankType.RESERVOIR, is_light_proof=True)
        state = _make_state(water_temp_celsius=25.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"].startswith("temperature") for a in alerts)


class TestDOAlerts:
    def test_do_critical_below_4(self, engine):
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        state = _make_state(dissolved_oxygen_mgl=3.5)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "do_critical" for a in alerts)

    def test_do_suboptimal_below_6(self, engine):
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        state = _make_state(dissolved_oxygen_mgl=5.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "do_suboptimal" for a in alerts)

    def test_do_ok_above_6(self, engine):
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        state = _make_state(dissolved_oxygen_mgl=8.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"].startswith("do_") for a in alerts)

    def test_do_ignored_for_irrigation(self, engine):
        tank = _make_tank(tank_type=TankType.IRRIGATION, is_light_proof=True)
        state = _make_state(dissolved_oxygen_mgl=3.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"].startswith("do_") for a in alerts)

    def test_compound_temp_do(self, engine):
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        state = _make_state(water_temp_celsius=23.0, dissolved_oxygen_mgl=5.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "compound_temp_do" for a in alerts)

    def test_no_compound_when_do_ok(self, engine):
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        state = _make_state(water_temp_celsius=23.0, dissolved_oxygen_mgl=7.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "compound_temp_do" for a in alerts)


class TestORPAlerts:
    def test_orp_pathogen_risk(self, engine):
        tank = _make_tank(
            tank_type=TankType.RECIRCULATION, has_uv_sterilizer=True, is_light_proof=True,
        )
        state = _make_state(orp_mv=200)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "orp_pathogen_risk" for a in alerts)

    def test_orp_sterilization_low(self, engine):
        tank = _make_tank(
            tank_type=TankType.RECIRCULATION, has_ozone_generator=True, is_light_proof=True,
        )
        state = _make_state(orp_mv=500)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "orp_sterilization_low" for a in alerts)

    def test_orp_ok_above_650(self, engine):
        tank = _make_tank(
            tank_type=TankType.RECIRCULATION, has_uv_sterilizer=True, is_light_proof=True,
        )
        state = _make_state(orp_mv=700)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"].startswith("orp_") for a in alerts)

    def test_orp_ignored_without_uv_ozone(self, engine):
        tank = _make_tank(tank_type=TankType.RECIRCULATION, is_light_proof=True)
        state = _make_state(orp_mv=100)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"].startswith("orp_") for a in alerts)

    def test_orp_ignored_for_nutrient_tank(self, engine):
        tank = _make_tank(
            tank_type=TankType.NUTRIENT, has_uv_sterilizer=True, is_light_proof=True,
        )
        state = _make_state(orp_mv=100)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"].startswith("orp_") for a in alerts)


class TestAlgaeRiskMultifactor:
    def test_light_proof_blocks_algae_risk(self, engine):
        tank = _make_tank(is_light_proof=True, has_lid=False)
        state = _make_state(water_temp_celsius=25.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "algae_risk" for a in alerts)

    def test_two_factors_medium(self, engine):
        # Not light-proof + no lid + warm (2 non-nutrient factors + irrigaton type = 2 factors)
        tank = _make_tank(tank_type=TankType.IRRIGATION, has_lid=False)
        state = _make_state(water_temp_celsius=23.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "algae_risk" and a["severity"] == "medium" for a in alerts)

    def test_three_factors_high(self, engine):
        # Not light-proof + no lid + warm + nutrient = 3 factors → high
        tank = _make_tank(tank_type=TankType.NUTRIENT, has_lid=False)
        state = _make_state(water_temp_celsius=23.0)
        alerts = engine.check_alerts(tank, state)
        assert any(a["type"] == "algae_risk" and a["severity"] == "high" for a in alerts)

    def test_only_one_factor_no_alert(self, engine):
        # Not light-proof + has lid + cool + reservoir → only 0 factors
        tank = _make_tank(tank_type=TankType.RESERVOIR, has_lid=True)
        state = _make_state(water_temp_celsius=18.0)
        alerts = engine.check_alerts(tank, state)
        assert not any(a["type"] == "algae_risk" for a in alerts)


class TestSolutionAge:
    def test_mineral_solution_old(self, engine):
        now = datetime.now(UTC)
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, is_organic_fertilizers=False,
            filled_at=now - timedelta(days=12),
        )
        state = _make_state(water_temp_celsius=20.0)
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert any(a["type"] == "solution_age" for a in alerts)

    def test_mineral_solution_fresh(self, engine):
        now = datetime.now(UTC)
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, is_organic_fertilizers=False,
            filled_at=now - timedelta(days=5),
        )
        state = _make_state(water_temp_celsius=20.0)
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert not any(a["type"] == "solution_age" for a in alerts)

    def test_organic_solution_shorter_life(self, engine):
        now = datetime.now(UTC)
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, is_organic_fertilizers=True,
            filled_at=now - timedelta(days=6),
        )
        state = _make_state(water_temp_celsius=20.0)
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert any(a["type"] == "solution_age" for a in alerts)

    def test_q10_warm_temperature_reduces_life(self, engine):
        now = datetime.now(UTC)
        tank = _make_tank(tank_type=TankType.NUTRIENT, is_light_proof=True)
        # Mineral at 30°C: base 10d / Q10^1.0 = 10/2 = 5d effective max
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, is_organic_fertilizers=False,
            filled_at=now - timedelta(days=6),
        )
        state = _make_state(water_temp_celsius=30.0)
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert any(a["type"] == "solution_age" for a in alerts)

    def test_not_checked_for_irrigation_tank(self, engine):
        now = datetime.now(UTC)
        tank = _make_tank(tank_type=TankType.IRRIGATION, is_light_proof=True)
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, is_organic_fertilizers=True,
            filled_at=now - timedelta(days=30),
        )
        state = _make_state(water_temp_celsius=20.0)
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert not any(a["type"] == "solution_age" for a in alerts)


class TestWaterChemistryAlerts:
    def test_chlorine_warning_with_organic(self, engine):
        tank = _make_tank(is_light_proof=True)
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, is_organic_fertilizers=True,
            chlorine_ppm=1.0,
        )
        state = _make_state()
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert any(a["type"] == "chlorine_warning" for a in alerts)

    def test_no_chlorine_warning_without_organic(self, engine):
        tank = _make_tank(is_light_proof=True)
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, is_organic_fertilizers=False,
            chlorine_ppm=1.0,
        )
        state = _make_state()
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert not any(a["type"] == "chlorine_warning" for a in alerts)

    def test_chloramine_warning_always(self, engine):
        tank = _make_tank(is_light_proof=True)
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, chloramine_ppm=0.8,
        )
        state = _make_state()
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert any(a["type"] == "chloramine_warning" for a in alerts)


class TestBiofilmRisk:
    def test_biofilm_risk_all_conditions(self, engine):
        now = datetime.now(UTC)
        tank = _make_tank(tank_type=TankType.RECIRCULATION, is_light_proof=True)
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, is_organic_fertilizers=True,
            filled_at=now - timedelta(days=5),
        )
        state = _make_state(water_temp_celsius=24.0)
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert any(a["type"] == "biofilm_risk" for a in alerts)

    def test_no_biofilm_with_uv(self, engine):
        now = datetime.now(UTC)
        tank = _make_tank(
            tank_type=TankType.RECIRCULATION, has_uv_sterilizer=True, is_light_proof=True,
        )
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, is_organic_fertilizers=True,
            filled_at=now - timedelta(days=5),
        )
        state = _make_state(water_temp_celsius=24.0)
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert not any(a["type"] == "biofilm_risk" for a in alerts)

    def test_no_biofilm_non_organic(self, engine):
        now = datetime.now(UTC)
        tank = _make_tank(tank_type=TankType.RECIRCULATION, is_light_proof=True)
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, is_organic_fertilizers=False,
            filled_at=now - timedelta(days=5),
        )
        state = _make_state(water_temp_celsius=24.0)
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert not any(a["type"] == "biofilm_risk" for a in alerts)

    def test_no_biofilm_cool_water(self, engine):
        now = datetime.now(UTC)
        tank = _make_tank(tank_type=TankType.RECIRCULATION, is_light_proof=True)
        fill = TankFillEvent(
            tank_key="t1", fill_type=FillType.FULL_CHANGE,
            volume_liters=50.0, is_organic_fertilizers=True,
            filled_at=now - timedelta(days=5),
        )
        state = _make_state(water_temp_celsius=20.0)
        alerts = engine.check_alerts(tank, state, last_fill_event=fill)
        assert not any(a["type"] == "biofilm_risk" for a in alerts)


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

    def test_stock_solution_any_system_raises(self, engine):
        with pytest.raises(ValueError, match="Stock solution"):
            engine.validate_tank_assignment(TankType.STOCK_SOLUTION, IrrigationSystem.HYDRO)

    def test_stock_solution_none_system_raises(self, engine):
        with pytest.raises(ValueError, match="Stock solution"):
            engine.validate_tank_assignment(TankType.STOCK_SOLUTION, None)

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

    def test_stock_solution_has_2_schedules(self, engine):
        defaults = engine.get_default_schedules(TankType.STOCK_SOLUTION)
        assert len(defaults) == 2

    def test_stock_solution_cleaning_90d(self, engine):
        defaults = engine.get_default_schedules(TankType.STOCK_SOLUTION)
        cleaning = next(d for d in defaults if d["type"] == MaintenanceType.CLEANING)
        assert cleaning["interval_days"] == 90
        assert cleaning["priority"] == MaintenancePriority.MEDIUM

    def test_stock_solution_calibration_28d(self, engine):
        defaults = engine.get_default_schedules(TankType.STOCK_SOLUTION)
        cal = next(d for d in defaults if d["type"] == MaintenanceType.CALIBRATION)
        assert cal["interval_days"] == 28
        assert cal["priority"] == MaintenancePriority.LOW

    def test_each_schedule_has_required_keys(self, engine):
        for tank_type in TankType:
            defaults = engine.get_default_schedules(tank_type)
            for d in defaults:
                assert "type" in d
                assert "interval_days" in d
                assert "priority" in d


def _make_fill_event(**kwargs) -> TankFillEvent:
    defaults = {
        "tank_key": "t1",
        "fill_type": FillType.FULL_CHANGE,
        "volume_liters": 50.0,
    }
    defaults.update(kwargs)
    return TankFillEvent(**defaults)


class TestValidateFillEvent:
    def test_no_warnings_normal(self, engine):
        tank = _make_tank(volume_liters=50.0)
        event = _make_fill_event(volume_liters=50.0)
        warnings = engine.validate_fill_event(tank, event)
        assert len(warnings) == 0

    def test_volume_exceeds_capacity_warning(self, engine):
        tank = _make_tank(volume_liters=50.0)
        event = _make_fill_event(fill_type=FillType.FULL_CHANGE, volume_liters=60.0)
        warnings = engine.validate_fill_event(tank, event)
        assert any("exceeds tank capacity" in w for w in warnings)

    def test_top_up_volume_exceeds_no_warning(self, engine):
        tank = _make_tank(volume_liters=50.0)
        event = _make_fill_event(fill_type=FillType.TOP_UP, volume_liters=60.0)
        warnings = engine.validate_fill_event(tank, event)
        assert not any("exceeds tank capacity" in w for w in warnings)

    def test_ec_deviation_warning(self, engine):
        tank = _make_tank()
        event = _make_fill_event(target_ec_ms=1.5, measured_ec_ms=2.0)
        warnings = engine.validate_fill_event(tank, event)
        assert any("EC deviation" in w for w in warnings)

    def test_ec_within_tolerance_no_warning(self, engine):
        tank = _make_tank()
        event = _make_fill_event(target_ec_ms=1.5, measured_ec_ms=1.7)
        warnings = engine.validate_fill_event(tank, event)
        assert not any("EC deviation" in w for w in warnings)

    def test_ph_deviation_warning(self, engine):
        tank = _make_tank()
        event = _make_fill_event(target_ph=6.0, measured_ph=6.5)
        warnings = engine.validate_fill_event(tank, event)
        assert any("pH deviation" in w for w in warnings)

    def test_ph_within_tolerance_no_warning(self, engine):
        tank = _make_tank()
        event = _make_fill_event(target_ph=6.0, measured_ph=6.2)
        warnings = engine.validate_fill_event(tank, event)
        assert not any("pH deviation" in w for w in warnings)

    def test_chlorine_with_organic_warning(self, engine):
        tank = _make_tank()
        event = _make_fill_event(is_organic_fertilizers=True, chlorine_ppm=1.0)
        warnings = engine.validate_fill_event(tank, event)
        assert any("Chlorine" in w for w in warnings)

    def test_chlorine_low_with_organic_no_warning(self, engine):
        tank = _make_tank()
        event = _make_fill_event(is_organic_fertilizers=True, chlorine_ppm=0.3)
        warnings = engine.validate_fill_event(tank, event)
        assert not any("Chlorine" in w for w in warnings)

    def test_chloramine_with_organic_warning(self, engine):
        tank = _make_tank()
        event = _make_fill_event(is_organic_fertilizers=True, chloramine_ppm=0.8)
        warnings = engine.validate_fill_event(tank, event)
        assert any("Chloramine" in w for w in warnings)

    def test_chlorine_without_organic_no_warning(self, engine):
        tank = _make_tank()
        event = _make_fill_event(is_organic_fertilizers=False, chlorine_ppm=1.0)
        warnings = engine.validate_fill_event(tank, event)
        assert not any("Chlorine" in w for w in warnings)

    def test_multiple_warnings(self, engine):
        tank = _make_tank(volume_liters=50.0)
        event = _make_fill_event(
            fill_type=FillType.FULL_CHANGE,
            volume_liters=60.0,
            target_ec_ms=1.0,
            measured_ec_ms=2.0,
            is_organic_fertilizers=True,
            chlorine_ppm=1.0,
        )
        warnings = engine.validate_fill_event(tank, event)
        assert len(warnings) == 3


class TestResolveWaterDefaults:
    def test_explicit_values_used(self, engine):
        event_data = {"water_source": "ro", "water_mix_ratio_ro_percent": 100.0, "base_water_ec_ms": 0.02}
        result = engine.resolve_water_defaults(event_data)
        assert result["water_source"] == "ro"
        assert result["water_mix_ratio_ro_percent"] == 100.0
        assert result["base_water_ec_ms"] == 0.02
        assert result["water_defaults_source"] == "explicit"

    def test_nutrient_plan_fallback(self, engine):
        event_data = {}
        plan = {"water_source": "mixed", "water_mix_ratio_ro_percent": 60.0, "base_water_ec_ms": 0.3}
        result = engine.resolve_water_defaults(event_data, nutrient_plan=plan)
        assert result["water_source"] == "mixed"
        assert result["water_mix_ratio_ro_percent"] == 60.0
        assert result["water_defaults_source"] == "nutrient_plan"

    def test_site_profile_fallback(self, engine):
        event_data = {}
        site_config = {"water_source": "tap", "base_water_ec_ms": 0.5}
        result = engine.resolve_water_defaults(event_data, site_water_config=site_config)
        assert result["water_source"] == "tap"
        assert result["base_water_ec_ms"] == 0.5
        assert result["water_defaults_source"] == "site_profile"

    def test_manual_fallback_nothing_resolved(self, engine):
        result = engine.resolve_water_defaults({})
        assert result["water_defaults_source"] == "manual"
        assert "water_source" not in result

    def test_cascade_mixed_sources(self, engine):
        event_data = {"water_source": "ro"}
        plan = {"water_mix_ratio_ro_percent": 100.0, "base_water_ec_ms": 0.02}
        result = engine.resolve_water_defaults(event_data, nutrient_plan=plan)
        assert result["water_source"] == "ro"
        assert result["water_mix_ratio_ro_percent"] == 100.0
        assert result["water_defaults_source"] == "explicit"

    def test_explicit_overrides_plan(self, engine):
        event_data = {"water_source": "ro", "base_water_ec_ms": 0.01}
        plan = {"water_source": "tap", "base_water_ec_ms": 0.5}
        result = engine.resolve_water_defaults(event_data, nutrient_plan=plan)
        assert result["water_source"] == "ro"
        assert result["base_water_ec_ms"] == 0.01

    def test_plan_overrides_site(self, engine):
        plan = {"water_source": "mixed", "base_water_ec_ms": 0.3}
        site_config = {"water_source": "tap", "base_water_ec_ms": 0.5}
        result = engine.resolve_water_defaults({}, nutrient_plan=plan, site_water_config=site_config)
        assert result["water_source"] == "mixed"
        assert result["base_water_ec_ms"] == 0.3
        assert result["water_defaults_source"] == "nutrient_plan"
