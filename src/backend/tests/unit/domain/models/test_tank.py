import pytest
from pydantic import ValidationError

from app.common.enums import MaintenancePriority, MaintenanceType, TankMaterial, TankType
from app.domain.models.tank import MaintenanceLog, MaintenanceSchedule, Tank, TankState


class TestTank:
    def test_valid_tank(self):
        tank = Tank(name="Nutrient Tank A", tank_type=TankType.NUTRIENT, volume_liters=50.0)
        assert tank.tank_type == TankType.NUTRIENT
        assert tank.volume_liters == 50.0
        assert tank.material == TankMaterial.PLASTIC

    def test_all_equipment_flags(self):
        tank = Tank(
            name="Full Tank",
            tank_type=TankType.RECIRCULATION,
            volume_liters=100.0,
            has_lid=True,
            has_air_pump=True,
            has_circulation_pump=True,
            has_heater=True,
        )
        assert tank.has_lid is True
        assert tank.has_air_pump is True
        assert tank.has_circulation_pump is True
        assert tank.has_heater is True

    def test_key_alias(self):
        tank = Tank(name="Test", tank_type=TankType.IRRIGATION, volume_liters=20.0, **{"_key": "abc123"})
        assert tank.key == "abc123"

    def test_name_too_short(self):
        with pytest.raises(ValidationError):
            Tank(name="", tank_type=TankType.NUTRIENT, volume_liters=10.0)

    def test_volume_zero_raises(self):
        with pytest.raises(ValidationError):
            Tank(name="Test", tank_type=TankType.NUTRIENT, volume_liters=0)

    def test_volume_negative_raises(self):
        with pytest.raises(ValidationError):
            Tank(name="Test", tank_type=TankType.NUTRIENT, volume_liters=-5.0)

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            Tank(name="Test", tank_type="invalid_type", volume_liters=10.0)

    def test_all_materials(self):
        for material in TankMaterial:
            tank = Tank(name="Test", tank_type=TankType.RESERVOIR, volume_liters=10.0, material=material)
            assert tank.material == material


class TestTankState:
    def test_valid_state(self):
        state = TankState(tank_key="t1", ph=6.0, ec_ms=1.5, water_temp_celsius=22.0)
        assert state.ph == 6.0
        assert state.ec_ms == 1.5

    def test_ph_bounds(self):
        TankState(tank_key="t1", ph=0.0)
        TankState(tank_key="t1", ph=14.0)
        with pytest.raises(ValidationError):
            TankState(tank_key="t1", ph=-0.1)
        with pytest.raises(ValidationError):
            TankState(tank_key="t1", ph=14.1)

    def test_ec_non_negative(self):
        TankState(tank_key="t1", ec_ms=0.0)
        with pytest.raises(ValidationError):
            TankState(tank_key="t1", ec_ms=-1.0)

    def test_temp_bounds(self):
        TankState(tank_key="t1", water_temp_celsius=0.0)
        TankState(tank_key="t1", water_temp_celsius=50.0)
        with pytest.raises(ValidationError):
            TankState(tank_key="t1", water_temp_celsius=-1.0)
        with pytest.raises(ValidationError):
            TankState(tank_key="t1", water_temp_celsius=51.0)

    def test_fill_level_percent_bounds(self):
        TankState(tank_key="t1", fill_level_percent=0.0)
        TankState(tank_key="t1", fill_level_percent=100.0)
        with pytest.raises(ValidationError):
            TankState(tank_key="t1", fill_level_percent=-1.0)
        with pytest.raises(ValidationError):
            TankState(tank_key="t1", fill_level_percent=101.0)

    def test_fill_level_liters_non_negative(self):
        TankState(tank_key="t1", fill_level_liters=0.0)
        with pytest.raises(ValidationError):
            TankState(tank_key="t1", fill_level_liters=-5.0)

    def test_all_none_values(self):
        state = TankState(tank_key="t1")
        assert state.ph is None
        assert state.ec_ms is None
        assert state.water_temp_celsius is None

    def test_source_default(self):
        state = TankState(tank_key="t1")
        assert state.source == "manual"


class TestMaintenanceLog:
    def test_valid_log(self):
        log = MaintenanceLog(
            tank_key="t1",
            maintenance_type=MaintenanceType.WATER_CHANGE,
            performed_by="User1",
            duration_minutes=30,
        )
        assert log.maintenance_type == MaintenanceType.WATER_CHANGE
        assert log.performed_by == "User1"

    def test_products_used(self):
        log = MaintenanceLog(
            tank_key="t1",
            maintenance_type=MaintenanceType.SANITIZATION,
            products_used=["H2O2 3%", "StarSan"],
        )
        assert len(log.products_used) == 2

    def test_duration_non_negative(self):
        MaintenanceLog(tank_key="t1", maintenance_type=MaintenanceType.CLEANING, duration_minutes=0)
        with pytest.raises(ValidationError):
            MaintenanceLog(tank_key="t1", maintenance_type=MaintenanceType.CLEANING, duration_minutes=-1)


class TestMaintenanceSchedule:
    def test_valid_schedule(self):
        schedule = MaintenanceSchedule(
            tank_key="t1",
            maintenance_type=MaintenanceType.WATER_CHANGE,
            interval_days=7,
            reminder_days_before=2,
        )
        assert schedule.interval_days == 7
        assert schedule.reminder_days_before == 2

    def test_reminder_must_be_less_than_interval(self):
        with pytest.raises(ValidationError, match="reminder_days_before"):
            MaintenanceSchedule(
                tank_key="t1",
                maintenance_type=MaintenanceType.CLEANING,
                interval_days=7,
                reminder_days_before=7,
            )

    def test_reminder_equal_to_interval_raises(self):
        with pytest.raises(ValidationError, match="reminder_days_before"):
            MaintenanceSchedule(
                tank_key="t1",
                maintenance_type=MaintenanceType.CLEANING,
                interval_days=5,
                reminder_days_before=5,
            )

    def test_reminder_greater_than_interval_raises(self):
        with pytest.raises(ValidationError, match="reminder_days_before"):
            MaintenanceSchedule(
                tank_key="t1",
                maintenance_type=MaintenanceType.CLEANING,
                interval_days=3,
                reminder_days_before=5,
            )

    def test_interval_zero_raises(self):
        with pytest.raises(ValidationError):
            MaintenanceSchedule(
                tank_key="t1",
                maintenance_type=MaintenanceType.CLEANING,
                interval_days=0,
            )

    def test_default_priority(self):
        schedule = MaintenanceSchedule(
            tank_key="t1",
            maintenance_type=MaintenanceType.FILTER_CHANGE,
            interval_days=30,
            reminder_days_before=3,
        )
        assert schedule.priority == MaintenancePriority.MEDIUM

    def test_all_maintenance_types(self):
        for mtype in MaintenanceType:
            schedule = MaintenanceSchedule(
                tank_key="t1",
                maintenance_type=mtype,
                interval_days=7,
                reminder_days_before=2,
            )
            assert schedule.maintenance_type == mtype
