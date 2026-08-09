"""Tests for the substrate mix engine's physics-correct weighting.

Covers issue #1099 defects 2 (pH must be buffering-weighted, not volume-averaged)
and 3 (CEC must be mass-weighted, not volume-weighted). The reference values are
author-verified against the seed catalogue: BioBizz Light·Mix + Blähton 8-16mm.
"""

from app.common.enums import BufferCapacity, SubstrateType, WaterRetention
from app.domain.engines.substrate_mix_engine import calculate_mix_properties
from app.domain.models.substrate import MixComponent, Substrate


def _make_substrate(key: str, **overrides) -> Substrate:
    defaults = {
        "_key": key,
        "type": SubstrateType.SOIL,
        "ph_base": 6.5,
        "ec_base_ms": 0.5,
        "water_retention": WaterRetention.MEDIUM,
        "air_porosity_percent": 25.0,
        "buffer_capacity": BufferCapacity.MEDIUM,
        "cec_meq_per_100g": 10.0,
        "bulk_density_g_per_l": 400.0,
    }
    defaults.update(overrides)
    return Substrate(**defaults)


def _light_mix() -> Substrate:
    """BioBizz Light·Mix — limed peat, the buffering component."""
    return _make_substrate(
        "16547923",
        type=SubstrateType.SOIL,
        ph_base=6.2,
        ec_base_ms=1.2,
        air_porosity_percent=30.0,
        buffer_capacity=BufferCapacity.MEDIUM,
        cec_meq_per_100g=12.0,
        bulk_density_g_per_l=400.0,
    )


def _clay_pebbles() -> Substrate:
    """Blähton 8-16mm — inert diluent: negligible CEC, low buffer, zero EC."""
    return _make_substrate(
        "16547889",
        type=SubstrateType.CLAY_PEBBLES,
        ph_base=7.0,
        ec_base_ms=0.0,
        water_retention=WaterRetention.LOW,
        air_porosity_percent=45.0,
        buffer_capacity=BufferCapacity.LOW,
        cec_meq_per_100g=0.2,
        bulk_density_g_per_l=350.0,
    )


def _half_half(a: Substrate, b: Substrate) -> dict:
    components = [
        MixComponent(substrate_key=a.key, fraction=0.5),
        MixComponent(substrate_key=b.key, fraction=0.5),
    ]
    return calculate_mix_properties(components, {a.key: a, b.key: b})


# ── WP-3: pH is buffering-weighted, not volume-averaged ───────────────


class TestBufferingWeightedPh:
    def test_inert_diluent_dilutes_toward_buffered_set_point(self):
        """50/50 Light·Mix (pH 6.2, buffered) + Blähton (pH 7.0, inert).

        Volume averaging yields 6.6; the physically correct blend is governed
        by the buffering fraction and lands at ≈6.3–6.4 (issue #1099, defect 2).
        """
        result = _half_half(_light_mix(), _clay_pebbles())

        assert 6.3 <= result["ph_base"] <= 6.4
        # Explicitly reject the arithmetic mean the volume method produced.
        assert result["ph_base"] < 6.6

    def test_equal_buffering_still_averages(self):
        """Control: two equally-buffered components average arithmetically.

        When both components carry the same CEC, buffering weight cancels and
        the blend pH is the volume-weighted mean — proving the fix only shifts
        the result when buffering differs.
        """
        acid = _make_substrate("acid", ph_base=6.0, cec_meq_per_100g=10.0, bulk_density_g_per_l=400.0)
        base = _make_substrate("base", ph_base=7.0, cec_meq_per_100g=10.0, bulk_density_g_per_l=400.0)

        result = _half_half(acid, base)

        assert result["ph_base"] == 6.5


# ── WP-4: CEC is mass-weighted, not volume-weighted ───────────────────


class TestMassWeightedCec:
    def test_cec_uses_mass_fractions_not_volume_fractions(self):
        """50/50 volume blend of media with different bulk densities.

        0.5 l × 400 g/l = 200 g Light·Mix → 53.3 % by mass
        0.5 l × 350 g/l = 175 g Blähton   → 46.7 % by mass
        0.533 × 12 + 0.467 × 0.2 ≈ 6.5 meq/100 g  (issue #1099, defect 3).
        The volume method wrongly returns (12 + 0.2) / 2 = 6.1.
        """
        result = _half_half(_light_mix(), _clay_pebbles())

        assert result["cec_meq_per_100g"] == 6.5
        assert result["cec_meq_per_100g"] != 6.1

    def test_mass_weighting_diverges_from_volume_on_high_density_spread(self):
        """A high density spread makes the volume method visibly wrong.

        cec 5 @ 600 g/l + cec 20 @ 350 g/l, 50/50 by volume:
          mass fractions 0.632 / 0.368 → 0.632×5 + 0.368×20 ≈ 10.5 meq/100 g,
        whereas the old volume method returns (5 + 20) / 2 = 12.5.
        """
        dense_low_cec = _make_substrate("dense", ph_base=6.5, cec_meq_per_100g=5.0, bulk_density_g_per_l=600.0)
        light_high_cec = _make_substrate("light", ph_base=6.5, cec_meq_per_100g=20.0, bulk_density_g_per_l=350.0)

        result = _half_half(dense_low_cec, light_high_cec)

        assert result["cec_meq_per_100g"] == 10.5
        assert result["cec_meq_per_100g"] != 12.5

    def test_bulk_density_stays_volume_weighted(self):
        """bulk_density is genuinely per-volume — it must NOT change.

        The issue confirms 375.0 (= 0.5×400 + 0.5×350) is already correct.
        """
        result = _half_half(_light_mix(), _clay_pebbles())

        assert result["bulk_density_g_per_l"] == 375.0
