"""REQ-039 — unit tests for the pure hardiness-zone resolver engine.

The classification is purely algorithmic (license-free USDA temperature-band
schema), so these tests pin the formula and its edge clamping without any DB /
external data.
"""

from datetime import UTC, datetime

import pytest

from app.domain.engines.hardiness_zone_resolver import (
    MAX_ZONE_INDEX,
    MIN_ZONE_INDEX,
    classify_from_minimum,
    derive_from_climate_normals,
    index_for_zone_label,
    mean_annual_minimum_from_normals,
    zone_bounds_c,
    zone_bounds_f,
    zone_label_for_index,
)
from app.domain.models.weather import ClimateNormal


def _normal(**overrides) -> ClimateNormal:
    data = {
        "site_key": "s1",
        "source": "nasa-power",
        "fetched_at": datetime.now(tz=UTC),
    }
    data.update(overrides)
    return ClimateNormal(**data)


class TestLabelIndexRoundtrip:
    @pytest.mark.parametrize(
        ("index", "label"),
        [(0, "1a"), (1, "1b"), (12, "7a"), (13, "7b"), (25, "13b")],
    )
    def test_label_for_index(self, index: int, label: str) -> None:
        assert zone_label_for_index(index) == label
        assert index_for_zone_label(label) == index

    def test_all_indices_roundtrip(self) -> None:
        for index in range(MIN_ZONE_INDEX, MAX_ZONE_INDEX + 1):
            assert index_for_zone_label(zone_label_for_index(index)) == index

    def test_out_of_range_index_raises(self) -> None:
        with pytest.raises(ValueError):
            zone_label_for_index(MAX_ZONE_INDEX + 1)

    def test_invalid_label_raises(self) -> None:
        with pytest.raises(ValueError):
            index_for_zone_label("7c")
        with pytest.raises(ValueError):
            index_for_zone_label("99a")


class TestBands:
    def test_zone_7a_bounds(self) -> None:
        # 7a spans 0–5 °F by schema.
        assert zone_bounds_f(12) == (0.0, 5.0)
        min_c, max_c = zone_bounds_c(12)
        assert min_c == pytest.approx(-17.78, abs=0.01)
        assert max_c == pytest.approx(-15.0, abs=0.01)

    def test_1a_and_13b_extremes(self) -> None:
        assert zone_bounds_f(0) == (-60.0, -55.0)
        assert zone_bounds_f(25) == (65.0, 70.0)


class TestClassifyFromMinimum:
    @pytest.mark.parametrize(
        ("temp_c", "expected"),
        [
            (-17.0, "7a"),  # 1.4 °F → 7a (0–5 °F)
            (-14.9, "7b"),  # ≈5.2 °F → 7b
            (-40.0, "3a"),  # −40 °C = −40 °F → 3a
            (-3.0, "9b"),  # 26.6 °F → 9b
        ],
    )
    def test_classification(self, temp_c: float, expected: str) -> None:
        assert classify_from_minimum(temp_c) == expected

    def test_clamps_below_range_to_1a(self) -> None:
        assert classify_from_minimum(-70.0) == "1a"

    def test_clamps_above_range_to_13b(self) -> None:
        assert classify_from_minimum(35.0) == "13b"


class TestDeriveFromClimateNormals:
    def test_prefers_coldest_month_min(self) -> None:
        normal = _normal(coldest_month_min_c=-17.0, monthly_temp_min_c=[0.0] * 12)
        result = derive_from_climate_normals(normal)
        assert result == ("7a", -17.0)

    def test_falls_back_to_monthly_min(self) -> None:
        normal = _normal(monthly_temp_min_c=[5.0, 2.0, -14.9, 8.0])
        assert mean_annual_minimum_from_normals(normal) == -14.9
        assert derive_from_climate_normals(normal) == ("7b", -14.9)

    def test_returns_none_without_usable_minimum(self) -> None:
        normal = _normal()  # neither coldest_month_min_c nor monthly_temp_min_c
        assert mean_annual_minimum_from_normals(normal) is None
        assert derive_from_climate_normals(normal) is None
