"""Tests for DeliveryChannelValidator engine."""

from app.common.enums import ApplicationMethod, FertilizerType
from app.domain.engines.delivery_channel_engine import DeliveryChannelValidator
from app.domain.engines.nutrient_engine import MixingSafetyValidator
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import (
    DeliveryChannel,
    FertilizerDosage,
)


def _make_fert(
    key: str = "f1",
    name: str = "TestFert",
    ec: float = 0.5,
    tank_safe: bool = True,
    recommended: ApplicationMethod = ApplicationMethod.ANY,
) -> Fertilizer:
    return Fertilizer(
        product_name=name,
        brand="TestBrand",
        fertilizer_type=FertilizerType.BASE,
        ec_contribution_per_ml=ec,
        tank_safe=tank_safe,
        recommended_application=recommended,
        _key=key,
    )


class TestDeliveryChannelValidator:
    def setup_method(self):
        self.validator = DeliveryChannelValidator()

    def test_valid_channels(self):
        ferts = {"f1": _make_fert(key="f1", ec=0.5)}
        channels = [
            DeliveryChannel(
                channel_id="ch1",
                application_method=ApplicationMethod.DRENCH,
                target_ec_ms=1.0,
                fertilizer_dosages=[
                    FertilizerDosage(fertilizer_key="f1", ml_per_liter=2.0),
                ],
            ),
        ]
        result = self.validator.validate_channels(channels, ferts)
        assert result["valid"] is True
        assert len(result["channel_results"]) == 1
        assert result["channel_results"][0]["issues"] == []

    def test_ec_mismatch_warning(self):
        ferts = {"f1": _make_fert(key="f1", ec=0.1)}
        channels = [
            DeliveryChannel(
                channel_id="ch1",
                application_method=ApplicationMethod.DRENCH,
                target_ec_ms=2.0,
                fertilizer_dosages=[
                    FertilizerDosage(fertilizer_key="f1", ml_per_liter=1.0),
                ],
            ),
        ]
        result = self.validator.validate_channels(channels, ferts)
        assert result["valid"] is False
        assert any("EC mismatch" in i for i in result["channel_results"][0]["issues"])

    def test_tank_safe_check_fertigation(self):
        ferts = {"f1": _make_fert(key="f1", tank_safe=False, name="UnsafeFert")}
        channels = [
            DeliveryChannel(
                channel_id="fert-ch",
                application_method=ApplicationMethod.FERTIGATION,
                fertilizer_dosages=[
                    FertilizerDosage(fertilizer_key="f1", ml_per_liter=2.0),
                ],
            ),
        ]
        result = self.validator.validate_channels(channels, ferts)
        assert result["valid"] is False
        assert any("not tank-safe" in i for i in result["channel_results"][0]["issues"])

    def test_tank_safe_ok_for_drench(self):
        """Non-fertigation channels don't check tank_safe."""
        ferts = {"f1": _make_fert(key="f1", tank_safe=False)}
        channels = [
            DeliveryChannel(
                channel_id="drench-ch",
                application_method=ApplicationMethod.DRENCH,
                fertilizer_dosages=[
                    FertilizerDosage(fertilizer_key="f1", ml_per_liter=2.0),
                ],
            ),
        ]
        result = self.validator.validate_channels(channels, ferts)
        assert result["valid"] is True

    def test_recommended_application_mismatch(self):
        ferts = {
            "f1": _make_fert(
                key="f1",
                recommended=ApplicationMethod.FOLIAR,
                name="FoliarOnly",
            ),
        }
        channels = [
            DeliveryChannel(
                channel_id="drench-ch",
                application_method=ApplicationMethod.DRENCH,
                fertilizer_dosages=[
                    FertilizerDosage(fertilizer_key="f1", ml_per_liter=1.0),
                ],
            ),
        ]
        result = self.validator.validate_channels(channels, ferts)
        assert result["valid"] is False
        assert any("recommended for" in i for i in result["channel_results"][0]["issues"])

    def test_recommended_application_any_matches_all(self):
        ferts = {"f1": _make_fert(key="f1", recommended=ApplicationMethod.ANY)}
        channels = [
            DeliveryChannel(
                channel_id="ch1",
                application_method=ApplicationMethod.FERTIGATION,
                fertilizer_dosages=[
                    FertilizerDosage(fertilizer_key="f1", ml_per_liter=1.0),
                ],
            ),
        ]
        result = self.validator.validate_channels(channels, ferts)
        assert all("recommended for" not in i for r in result["channel_results"] for i in r["issues"])

    def test_unknown_fertilizer(self):
        channels = [
            DeliveryChannel(
                channel_id="ch1",
                application_method=ApplicationMethod.DRENCH,
                target_ec_ms=1.0,
                fertilizer_dosages=[
                    FertilizerDosage(fertilizer_key="nonexistent", ml_per_liter=1.0),
                ],
            ),
        ]
        result = self.validator.validate_channels(channels, {})
        assert result["valid"] is False
        assert any("Unknown fertilizer" in i for i in result["channel_results"][0]["issues"])

    def test_duplicate_channel_ids(self):
        channels = [
            DeliveryChannel(channel_id="dup", application_method=ApplicationMethod.DRENCH),
            DeliveryChannel(channel_id="dup", application_method=ApplicationMethod.FOLIAR),
        ]
        result = self.validator.validate_channels(channels, {})
        assert result["valid"] is False
        assert any("Duplicate" in i for r in result["channel_results"] for i in r["issues"])

    def test_channel_without_target_ec(self):
        """Channels without target_ec_ms skip EC validation."""
        ferts = {"f1": _make_fert(key="f1")}
        channels = [
            DeliveryChannel(
                channel_id="ch1",
                application_method=ApplicationMethod.DRENCH,
                target_ec_ms=None,
                fertilizer_dosages=[
                    FertilizerDosage(fertilizer_key="f1", ml_per_liter=1.0),
                ],
            ),
        ]
        result = self.validator.validate_channels(channels, ferts)
        assert result["valid"] is True
        assert result["channel_results"][0]["ec_budget"] is None

    def test_multiple_channels_mixed_validity(self):
        ferts = {
            "f1": _make_fert(key="f1", ec=0.5, tank_safe=True),
            "f2": _make_fert(key="f2", ec=0.5, tank_safe=False, name="BadFert"),
        }
        channels = [
            DeliveryChannel(
                channel_id="ok",
                application_method=ApplicationMethod.DRENCH,
                fertilizer_dosages=[
                    FertilizerDosage(fertilizer_key="f1", ml_per_liter=2.0),
                ],
            ),
            DeliveryChannel(
                channel_id="bad",
                application_method=ApplicationMethod.FERTIGATION,
                fertilizer_dosages=[
                    FertilizerDosage(fertilizer_key="f2", ml_per_liter=2.0),
                ],
            ),
        ]
        result = self.validator.validate_channels(channels, ferts)
        assert result["valid"] is False
        assert result["channel_results"][0]["issues"] == []
        assert len(result["channel_results"][1]["issues"]) > 0


class TestMixingSafetyValidatorChannel:
    def test_validate_channel_tank_safe(self):
        validator = MixingSafetyValidator()
        fert = _make_fert(key="f1", tank_safe=False, name="UnsafeFert")
        channel = DeliveryChannel(
            channel_id="fert-ch",
            application_method=ApplicationMethod.FERTIGATION,
        )
        result = validator.validate_channel(channel, [fert])
        assert result["safe"] is False
        assert any("not tank-safe" in w for w in result["warnings"])

    def test_validate_channel_non_fertigation_ok(self):
        validator = MixingSafetyValidator()
        fert = _make_fert(key="f1", tank_safe=False)
        channel = DeliveryChannel(
            channel_id="drench-ch",
            application_method=ApplicationMethod.DRENCH,
        )
        result = validator.validate_channel(channel, [fert])
        assert result["safe"] is True
