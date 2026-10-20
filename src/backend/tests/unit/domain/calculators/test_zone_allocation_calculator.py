"""REQ-053 WP 7.3 - dividing a watering round over the beds of a zone: shares add up to the total."""

from __future__ import annotations

import pytest

from app.domain.calculators.zone_allocation_calculator import divide_volume


class TestDivideVolume:
    def test_it_splits_in_proportion_to_the_weights(self) -> None:
        assert divide_volume(60.0, [2.0, 1.0]) == [40.0, 20.0]

    def test_the_last_share_takes_the_rounding_remainder(self) -> None:
        shares = divide_volume(10.0, [1.0, 1.0, 1.0])

        assert shares == [3.333, 3.333, 3.334]
        assert sum(shares) == pytest.approx(10.0, abs=1e-9)

    @pytest.mark.parametrize("total", [0.5, 7.0, 123.456, 99_999.999])
    @pytest.mark.parametrize("weights", [[1.0], [3.7, 1.2], [0.8, 2.4, 1.0, 1.0, 5.5], [1.0] * 17])
    def test_the_shares_always_add_up_to_the_total(self, total: float, weights: list[float]) -> None:
        shares = divide_volume(total, weights)

        assert len(shares) == len(weights)
        assert sum(shares) == pytest.approx(total, abs=1e-6)
        assert all(share > 0 for share in shares)

    @pytest.mark.parametrize(("total", "weights"), [(0.0, [1.0]), (-1.0, [1.0]), (5.0, []), (5.0, [1.0, 0.0])])
    def test_a_total_or_weight_that_is_not_positive_is_refused(self, total: float, weights: list[float]) -> None:
        with pytest.raises(ValueError, match="positive"):
            divide_volume(total, weights)
