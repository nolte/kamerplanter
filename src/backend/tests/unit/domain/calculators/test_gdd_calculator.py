from app.domain.calculators.gdd_calculator import (
    calculate_accumulated_gdd,
    calculate_daily_gdd,
    estimate_days_to_gdd_target,
)


class TestDailyGDD:
    def test_typical_day(self):
        gdd = calculate_daily_gdd(30.0, 20.0, 10.0)
        assert gdd == 15.0

    def test_cold_day_zero(self):
        gdd = calculate_daily_gdd(8.0, 2.0, 10.0)
        assert gdd == 0.0

    def test_at_base_temp(self):
        gdd = calculate_daily_gdd(15.0, 5.0, 10.0)
        assert gdd == 0.0


class TestAccumulatedGDD:
    def test_multiple_days(self):
        temps = [(30.0, 20.0), (28.0, 18.0), (25.0, 15.0)]
        gdd = calculate_accumulated_gdd(temps, 10.0)
        expected = 15.0 + 13.0 + 10.0
        assert abs(gdd - expected) < 0.01

    def test_empty_list(self):
        assert calculate_accumulated_gdd([], 10.0) == 0.0


class TestEstimateDays:
    def test_typical(self):
        days = estimate_days_to_gdd_target(100.0, 50.0, 10.0)
        assert days == 6

    def test_already_reached(self):
        days = estimate_days_to_gdd_target(100.0, 100.0, 10.0)
        assert days == 0

    def test_zero_avg(self):
        days = estimate_days_to_gdd_target(100.0, 50.0, 0.0)
        assert days is None
