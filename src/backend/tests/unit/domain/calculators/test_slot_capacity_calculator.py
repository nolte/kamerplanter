import pytest

from app.common.enums import LayoutStrategy
from app.domain.calculators.slot_capacity_calculator import (
    TRIANGULAR_ROW_FACTOR,
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
    """REQ-053 GP-FR-073 (W-003): density honours row spacing and layout strategy."""

    def test_30cm_spacing(self):
        density = calculate_plants_per_m2(30.0)
        assert abs(density - 11.11) < 0.1

    def test_zero_spacing(self):
        assert calculate_plants_per_m2(0.0) == 0.0

    def test_negative_spacing(self):
        assert calculate_plants_per_m2(-5.0) == 0.0

    def test_existing_callers_keep_the_grid_result(self):
        """The one-argument call of ``router.py`` keeps returning ``1/spacing²``."""
        assert calculate_plants_per_m2(60.0) == pytest.approx(1.0 / 0.36)
        assert calculate_plants_per_m2(60.0) == pytest.approx(calculate_plants_per_m2(60.0, None, "grid"))

    def test_tomato_60x80_rows_is_2_08_not_2_78(self):
        """Tomato 60 × 80 cm → 1 / (0.6 × 0.8) = 2.08/m², not the 1/spacing² = 2.78 of W-003."""
        density = calculate_plants_per_m2(60.0, 80.0, LayoutStrategy.ROWS)
        assert density == pytest.approx(2.0833, abs=1e-3)
        assert round(density, 2) == 2.08
        assert density != pytest.approx(2.78, abs=1e-2)

    def test_rows_accepts_the_strategy_as_a_plain_string(self):
        assert calculate_plants_per_m2(60.0, 80.0, "rows") == pytest.approx(2.0833, abs=1e-3)

    def test_rows_without_row_spacing_raises_instead_of_computing_the_grid(self):
        """No silent default (GP-FR-061): ``rows`` with no row spacing must not yield the W-003 2.78."""
        with pytest.raises(ValueError, match="row_spacing_cm"):
            calculate_plants_per_m2(60.0, None, LayoutStrategy.ROWS)

    @pytest.mark.parametrize("row_spacing", [0.0, -1.0, float("nan")])
    def test_rows_with_an_unusable_row_spacing_yields_zero(self, row_spacing):
        """Same shape as an unusable ``spacing_cm``: ``0.0``, never a plausible positive density."""
        assert calculate_plants_per_m2(60.0, row_spacing, LayoutStrategy.ROWS) == 0.0

    def test_nan_spacing_yields_zero(self):
        assert calculate_plants_per_m2(float("nan")) == 0.0

    def test_grid_ignores_a_row_spacing(self):
        """GP-FR-060: ``grid`` sets ``row_spacing = spacing``, whatever the caller passes."""
        assert calculate_plants_per_m2(60.0, 80.0, LayoutStrategy.GRID) == pytest.approx(1.0 / 0.36)

    def test_triangular_is_one_over_spacing_squared_times_0_866(self):
        spacing = 50.0
        density = calculate_plants_per_m2(spacing, None, LayoutStrategy.TRIANGULAR)
        assert TRIANGULAR_ROW_FACTOR == 0.866
        assert density == pytest.approx(1.0 / (0.5 * 0.5 * 0.866))
        assert density > calculate_plants_per_m2(spacing)  # staggered rows pack tighter

    def test_triangular_ignores_a_row_spacing(self):
        """GP-FR-060: ``triangular`` derives its row spacing; a passed value is not used."""
        assert calculate_plants_per_m2(50.0, 80.0, LayoutStrategy.TRIANGULAR) == pytest.approx(
            calculate_plants_per_m2(50.0, None, LayoutStrategy.TRIANGULAR)
        )

    @pytest.mark.parametrize("strategy", [LayoutStrategy.ZONE, LayoutStrategy.FREE])
    def test_zone_and_free_use_the_nominal_grid_density(self, strategy):
        assert calculate_plants_per_m2(40.0, 60.0, strategy) == pytest.approx(1.0 / 0.16)

    def test_unknown_strategy_raises(self):
        with pytest.raises(ValueError, match="hexagonal"):
            calculate_plants_per_m2(60.0, 80.0, "hexagonal")

    def test_every_layout_strategy_is_handled(self):
        """A value added to the enum must be routed by the calculator, not fall through."""
        for strategy in LayoutStrategy:
            assert calculate_plants_per_m2(60.0, 80.0, strategy) > 0.0
