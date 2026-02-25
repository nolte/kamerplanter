from app.domain.calculators.slot_capacity_calculator import (
    calculate_max_capacity,
    calculate_optimal_range,
    calculate_plants_per_m2,
)


class TestMaxCapacity:
    def test_1m2_30cm_spacing(self):
        cap = calculate_max_capacity(1.0, 30.0)
        assert cap == 11  # 1.0 / 0.09 = 11.11

    def test_4m2_50cm_spacing(self):
        cap = calculate_max_capacity(4.0, 50.0)
        assert cap == 16

    def test_zero_area(self):
        assert calculate_max_capacity(0.0, 30.0) == 0

    def test_zero_spacing(self):
        assert calculate_max_capacity(1.0, 0.0) == 0


class TestOptimalRange:
    def test_typical(self):
        low, high = calculate_optimal_range(4.0, 50.0)
        max_cap = calculate_max_capacity(4.0, 50.0)
        assert low < high
        assert low >= 1
        assert high <= max_cap


class TestPlantsPerM2:
    def test_30cm_spacing(self):
        density = calculate_plants_per_m2(30.0)
        assert abs(density - 11.11) < 0.1

    def test_zero_spacing(self):
        assert calculate_plants_per_m2(0.0) == 0.0
