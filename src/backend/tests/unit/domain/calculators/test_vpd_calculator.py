from app.domain.calculators.vpd_calculator import (
    calculate_leaf_vpd,
    calculate_svp,
    calculate_vpd,
    classify_vpd,
    target_humidity_for_vpd,
)


class TestCalculateSVP:
    def test_at_20c(self):
        svp = calculate_svp(20.0)
        assert abs(svp - 2.338) < 0.01

    def test_at_25c(self):
        svp = calculate_svp(25.0)
        assert abs(svp - 3.167) < 0.01

    def test_at_0c(self):
        svp = calculate_svp(0.0)
        assert abs(svp - 0.6108) < 0.01


class TestCalculateVPD:
    def test_typical_conditions(self):
        vpd = calculate_vpd(25.0, 60.0)
        expected = calculate_svp(25.0) * (1 - 60.0 / 100.0)
        assert abs(vpd - expected) < 0.001

    def test_100_percent_humidity(self):
        vpd = calculate_vpd(25.0, 100.0)
        assert abs(vpd) < 0.001

    def test_0_percent_humidity(self):
        vpd = calculate_vpd(25.0, 0.0)
        svp = calculate_svp(25.0)
        assert abs(vpd - svp) < 0.001

    def test_high_vpd(self):
        vpd = calculate_vpd(30.0, 30.0)
        assert vpd > 2.0


class TestClassifyVPD:
    def test_optimal_vegetative(self):
        status, _ = classify_vpd(1.0, "vegetative")
        assert status == "optimal"

    def test_low_seedling(self):
        status, _ = classify_vpd(0.2, "seedling")
        assert status == "low"

    def test_high_flowering(self):
        status, _ = classify_vpd(2.0, "flowering")
        assert status == "high"

    def test_recommendation_contains_phase(self):
        _, rec = classify_vpd(1.0, "vegetative")
        assert "vegetative" in rec


class TestLeafVPD:
    def test_leaf_colder_than_air(self):
        leaf_vpd = calculate_leaf_vpd(25.0, 23.0, 60.0)
        air_vpd = calculate_vpd(25.0, 60.0)
        assert leaf_vpd < air_vpd


class TestTargetHumidity:
    def test_roundtrip(self):
        target_vpd = 1.0
        temp = 25.0
        humidity = target_humidity_for_vpd(temp, target_vpd)
        actual_vpd = calculate_vpd(temp, humidity)
        assert abs(actual_vpd - target_vpd) < 0.01

    def test_clamps_to_100(self):
        humidity = target_humidity_for_vpd(25.0, -1.0)
        assert humidity == 100.0

    def test_clamps_to_0(self):
        humidity = target_humidity_for_vpd(25.0, 10.0)
        assert humidity == 0.0
