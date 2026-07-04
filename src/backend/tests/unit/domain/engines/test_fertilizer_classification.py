"""Unit tests for structural fertilizer classification (DOM-6)."""

import pytest

from app.common.enums import FertilizerType
from app.domain.engines.fertilizer_classification import (
    is_calmag,
    is_silicate,
    is_sulfate_bearing,
    matches_calmag_name,
    normalize_name,
)
from app.domain.models.fertilizer import Fertilizer


def _fert(name: str, ftype: FertilizerType = FertilizerType.SUPPLEMENT) -> Fertilizer:
    return Fertilizer(product_name=name, fertilizer_type=ftype)


class TestNormalizeName:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Cal-Mag Plus", "calmagplus"),
            ("CaliMagic", "calimagic"),
            ("Epsom Salt", "epsomsalt"),
            ("Ca/Mg 3.2%", "camg32"),
        ],
    )
    def test_normalize(self, raw, expected):
        assert normalize_name(raw) == expected


class TestIsCalmag:
    def test_hyphenated_name_matches(self):
        assert is_calmag(_fert("Cal-Mag Plus")) is True

    def test_calimagic_name_matches(self):
        assert is_calmag(_fert("CaliMagic")) is True

    def test_type_matches_regardless_of_name(self):
        assert is_calmag(_fert("Mystery Bottle", FertilizerType.CALMAG)) is True

    def test_calcium_and_magnesium_combined_matches(self):
        assert is_calmag(_fert("Calcium Magnesium Supplement")) is True

    def test_calgon_is_not_calmag(self):
        # Pure "Calgon" must not be a false positive.
        assert is_calmag(_fert("Calgon")) is False

    def test_calcium_nitrate_alone_is_not_calmag(self):
        assert is_calmag(_fert("Calcium Nitrate", FertilizerType.BASE)) is False

    def test_matches_calmag_name_pure_function(self):
        assert matches_calmag_name("Cal-Mag") is True
        assert matches_calmag_name("Calgon") is False


class TestSulfateAndSilicate:
    def test_epsom_is_sulfate(self):
        assert is_sulfate_bearing(_fert("Epsom Salt")) is True

    def test_bittersalz_is_sulfate(self):
        assert is_sulfate_bearing(_fert("Bittersalz")) is True

    def test_plain_base_is_not_sulfate(self):
        assert is_sulfate_bearing(_fert("Grow Base A", FertilizerType.BASE)) is False

    def test_silicate_by_type(self):
        assert is_silicate(_fert("Rhino Skin", FertilizerType.SILICATE)) is True

    def test_non_silicate(self):
        assert is_silicate(_fert("Rhino Skin", FertilizerType.SUPPLEMENT)) is False
