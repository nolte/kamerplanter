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


class TestTinyTotals:
    """#2522: a tiny total over many beds never gives a negative share and still adds up (to the millilitre)."""

    @pytest.mark.parametrize("total", [0.001, 0.002, 0.003, 0.0015, 0.0049, 0.01])
    @pytest.mark.parametrize("beds", [2, 3, 7, 40, 500])
    def test_no_share_is_negative_and_the_sum_is_exact(self, total: float, beds: int) -> None:
        shares = divide_volume(total, [1.0] * beds)

        assert len(shares) == beds
        assert min(shares) >= 0
        assert sum(shares) == pytest.approx(total, abs=0.0005 + 1e-9)  # whole millilitres

    def test_an_overshooting_remainder_is_redistributed_not_negated(self) -> None:
        # Plain rounding of 0.0015 over three beds gives 0.002 + 0.002 and a last share of -0.0025.
        assert sorted(divide_volume(0.0015, [1.0, 1.0, 1.0]), reverse=True) == [0.001, 0.001, 0.0]

    def test_the_weights_still_decide_who_gets_the_scarce_millilitres(self) -> None:
        shares = divide_volume(0.002, [1.0, 10.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

        assert min(shares) >= 0 and shares[1] == max(shares)
