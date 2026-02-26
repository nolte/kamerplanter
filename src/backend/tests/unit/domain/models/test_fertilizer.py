from datetime import date

import pytest
from pydantic import ValidationError

from app.common.enums import ApplicationMethod, Bioavailability, FertilizerType, PhEffect
from app.domain.models.fertilizer import Fertilizer, FertilizerStock


class TestFertilizer:
    def test_valid_fertilizer(self):
        fert = Fertilizer(
            product_name="CalMag Plus",
            brand="GHE",
            fertilizer_type=FertilizerType.SUPPLEMENT,
            npk_ratio=(0.0, 0.0, 0.0),
        )
        assert fert.product_name == "CalMag Plus"
        assert fert.fertilizer_type == FertilizerType.SUPPLEMENT
        assert fert.is_organic is False
        assert fert.tank_safe is True

    def test_key_alias(self):
        fert = Fertilizer(
            product_name="Test", fertilizer_type=FertilizerType.BASE,
            **{"_key": "abc123"},
        )
        assert fert.key == "abc123"

    def test_product_name_too_short(self):
        with pytest.raises(ValidationError):
            Fertilizer(product_name="", fertilizer_type=FertilizerType.BASE)

    def test_npk_negative_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            Fertilizer(
                product_name="Test", fertilizer_type=FertilizerType.BASE,
                npk_ratio=(-1.0, 5.0, 5.0),
            )

    def test_npk_sum_exceeds_100(self):
        with pytest.raises(ValidationError, match="exceeds 100"):
            Fertilizer(
                product_name="Test", fertilizer_type=FertilizerType.BASE,
                npk_ratio=(40.0, 40.0, 30.0),
            )

    def test_npk_sum_exactly_100(self):
        fert = Fertilizer(
            product_name="Test", fertilizer_type=FertilizerType.BASE,
            npk_ratio=(30.0, 30.0, 40.0),
        )
        assert sum(fert.npk_ratio) == 100.0

    def test_ec_contribution_negative_raises(self):
        with pytest.raises(ValidationError):
            Fertilizer(
                product_name="Test", fertilizer_type=FertilizerType.BASE,
                ec_contribution_per_ml=-0.1,
            )

    def test_mixing_priority_bounds(self):
        Fertilizer(product_name="Test", fertilizer_type=FertilizerType.BASE, mixing_priority=1)
        Fertilizer(product_name="Test", fertilizer_type=FertilizerType.BASE, mixing_priority=100)
        with pytest.raises(ValidationError):
            Fertilizer(product_name="Test", fertilizer_type=FertilizerType.BASE, mixing_priority=0)
        with pytest.raises(ValidationError):
            Fertilizer(product_name="Test", fertilizer_type=FertilizerType.BASE, mixing_priority=101)

    def test_tank_safe_fertigation_conflict(self):
        with pytest.raises(ValidationError, match="tank-safe"):
            Fertilizer(
                product_name="Test", fertilizer_type=FertilizerType.BASE,
                tank_safe=False, recommended_application=ApplicationMethod.FERTIGATION,
            )

    def test_tank_safe_non_fertigation_ok(self):
        fert = Fertilizer(
            product_name="Test", fertilizer_type=FertilizerType.BASE,
            tank_safe=False, recommended_application=ApplicationMethod.FOLIAR,
        )
        assert fert.tank_safe is False

    def test_storage_temp_invalid_range(self):
        with pytest.raises(ValidationError, match="storage_temp_min"):
            Fertilizer(
                product_name="Test", fertilizer_type=FertilizerType.BASE,
                storage_temp_min=30.0, storage_temp_max=20.0,
            )

    def test_storage_temp_valid_range(self):
        fert = Fertilizer(
            product_name="Test", fertilizer_type=FertilizerType.BASE,
            storage_temp_min=5.0, storage_temp_max=30.0,
        )
        assert fert.storage_temp_min == 5.0
        assert fert.storage_temp_max == 30.0

    def test_all_fertilizer_types(self):
        for ft in FertilizerType:
            fert = Fertilizer(product_name="Test", fertilizer_type=ft)
            assert fert.fertilizer_type == ft

    def test_defaults(self):
        fert = Fertilizer(product_name="Test", fertilizer_type=FertilizerType.BASE)
        assert fert.brand == ""
        assert fert.ph_effect == PhEffect.NEUTRAL
        assert fert.bioavailability == Bioavailability.IMMEDIATE
        assert fert.mixing_priority == 50
        assert fert.recommended_application == ApplicationMethod.ANY

    def test_shelf_life_positive(self):
        with pytest.raises(ValidationError):
            Fertilizer(
                product_name="Test", fertilizer_type=FertilizerType.BASE,
                shelf_life_days=0,
            )


class TestFertilizerStock:
    def test_valid_stock(self):
        stock = FertilizerStock(
            fertilizer_key="f1",
            current_volume_ml=500.0,
            purchase_date=date(2025, 1, 1),
            expiry_date=date(2026, 1, 1),
        )
        assert stock.current_volume_ml == 500.0

    def test_expiry_before_purchase_raises(self):
        with pytest.raises(ValidationError, match="expiry_date"):
            FertilizerStock(
                fertilizer_key="f1",
                current_volume_ml=500.0,
                purchase_date=date(2025, 6, 1),
                expiry_date=date(2025, 1, 1),
            )

    def test_expiry_equals_purchase_raises(self):
        with pytest.raises(ValidationError, match="expiry_date"):
            FertilizerStock(
                fertilizer_key="f1",
                current_volume_ml=500.0,
                purchase_date=date(2025, 6, 1),
                expiry_date=date(2025, 6, 1),
            )

    def test_volume_zero_ok(self):
        stock = FertilizerStock(fertilizer_key="f1", current_volume_ml=0.0)
        assert stock.current_volume_ml == 0.0

    def test_volume_negative_raises(self):
        with pytest.raises(ValidationError):
            FertilizerStock(fertilizer_key="f1", current_volume_ml=-1.0)

    def test_cost_per_liter_negative_raises(self):
        with pytest.raises(ValidationError):
            FertilizerStock(
                fertilizer_key="f1", current_volume_ml=100.0,
                cost_per_liter=-5.0,
            )

    def test_no_dates_ok(self):
        stock = FertilizerStock(fertilizer_key="f1", current_volume_ml=100.0)
        assert stock.purchase_date is None
        assert stock.expiry_date is None
