"""REQ-053 E-17 variant A (#2654): the field-soil conductivity is only a salt-limit hint "check salt content".

Review acceptance (EC / E-17): ``ec_ms_cm`` above the configured threshold (default ``null`` = no assessment) gives
the hint, never a dose; no conversion between extraction methods. The thresholds below are **test values, not
agronomy**.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.common.enums import EcMethod
from app.domain.engines import soil_salinity_hint
from app.domain.engines.soil_salinity_hint import DEFAULT_SALINITY_CONFIG, SoilSalinityConfig, needs_salt_check
from app.domain.models.site import SoilProfile

TEST_SOURCE = "test threshold, not agronomy"
ACTIVE = SoilSalinityConfig(threshold_ms_cm=2.0, ec_method=EcMethod.SATURATED_PASTE, source=TEST_SOURCE)


def _profile(ec: float | None, method: EcMethod | None = EcMethod.SATURATED_PASTE) -> SoilProfile:
    return SoilProfile(ec_ms_cm=ec, ec_method=method)


class TestDefaultIsInert:
    def test_the_default_configuration_is_inactive(self) -> None:
        assert DEFAULT_SALINITY_CONFIG.active is False
        assert DEFAULT_SALINITY_CONFIG.threshold_ms_cm is None
        assert DEFAULT_SALINITY_CONFIG.ec_method is None
        assert DEFAULT_SALINITY_CONFIG.source is None

    def test_the_default_gives_no_hint_even_for_a_very_salty_soil(self) -> None:
        assert needs_salt_check(_profile(50.0)) is False


class TestActiveRule:
    def test_above_the_threshold_with_the_matching_method_and_a_source_gives_the_hint(self) -> None:
        assert needs_salt_check(_profile(2.5), ACTIVE) is True

    def test_below_the_threshold_gives_no_hint(self) -> None:
        assert needs_salt_check(_profile(1.5), ACTIVE) is False

    def test_the_threshold_itself_is_not_above_it(self) -> None:
        assert needs_salt_check(_profile(2.0), ACTIVE) is False

    @pytest.mark.parametrize("method", [EcMethod.RATIO_1_2, EcMethod.RATIO_1_5, EcMethod.SENSOR, EcMethod.UNKNOWN])
    def test_another_extraction_method_is_never_compared(self, method: EcMethod) -> None:
        """No conversion between methods (U-002): a 1:5 value of 9 mS/cm is not an ECe of 9."""
        assert needs_salt_check(_profile(9.0, method), ACTIVE) is False

    def test_a_profile_without_a_conductivity_gives_no_hint(self) -> None:
        assert needs_salt_check(SoilProfile(), ACTIVE) is False

    def test_no_profile_gives_no_hint(self) -> None:
        assert needs_salt_check(None, ACTIVE) is False


class TestNoSourceNoRule:
    @pytest.mark.parametrize("source", [None, "", "   "])
    def test_a_threshold_without_a_source_takes_no_part(self, source: str | None) -> None:
        config = SoilSalinityConfig(threshold_ms_cm=2.0, ec_method=EcMethod.SATURATED_PASTE, source=source)
        assert config.active is False
        assert needs_salt_check(_profile(9.0), config) is False

    def test_a_threshold_without_its_method_takes_no_part(self) -> None:
        config = SoilSalinityConfig(threshold_ms_cm=2.0, ec_method=None, source=TEST_SOURCE)
        assert config.active is False
        assert needs_salt_check(_profile(9.0), config) is False

    def test_a_source_without_a_threshold_takes_no_part(self) -> None:
        config = SoilSalinityConfig(threshold_ms_cm=None, ec_method=EcMethod.SATURATED_PASTE, source=TEST_SOURCE)
        assert needs_salt_check(_profile(9.0), config) is False


class TestConfigValidation:
    def test_unknown_cannot_carry_a_threshold(self) -> None:
        with pytest.raises(ValueError, match="unknown"):
            SoilSalinityConfig(threshold_ms_cm=2.0, ec_method=EcMethod.UNKNOWN, source=TEST_SOURCE)

    @pytest.mark.parametrize("value", [0.0, -1.0])
    def test_the_threshold_is_positive(self, value: float) -> None:
        with pytest.raises(ValueError, match="positive"):
            SoilSalinityConfig(threshold_ms_cm=value, ec_method=EcMethod.SATURATED_PASTE, source=TEST_SOURCE)


def test_the_module_holds_no_agronomic_number() -> None:
    """Static: the salt limit is configuration (E-10), the module names none of its own."""
    tree = ast.parse(Path(soil_salinity_hint.__file__).read_text(encoding="utf-8"))
    numbers = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)
    }
    # 0 is the "<= 0" bound check and the "or 0" of an inactive value.
    assert numbers <= {0}, numbers
