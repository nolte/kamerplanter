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
        "cec_meq_per_100cm3": 10.0,
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
        cec_meq_per_100cm3=12.0,
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
        cec_meq_per_100cm3=0.2,
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
        acid = _make_substrate("acid", ph_base=6.0, cec_meq_per_100cm3=10.0, bulk_density_g_per_l=400.0)
        base = _make_substrate("base", ph_base=7.0, cec_meq_per_100cm3=10.0, bulk_density_g_per_l=400.0)

        result = _half_half(acid, base)

        assert result["ph_base"] == 6.5


# ── WP-4: CEC is mass-weighted, not volume-weighted ───────────────────


class TestVolumeWeightedCec:
    """CEC is weighted by volume, because the catalogue's values are per volume.

    This class previously asserted the opposite. #1099 read the old field name
    `cec_meq_per_100g` as a statement of fact and mass-weighted accordingly — but
    the values never supported that reading: seven of seven sampled materials land
    outside their literature band as written and inside it once divided by bulk
    density (peat 10 vs 100–200; vermiculite 15 vs 100–150; perlite 0.1 vs ≈1.5).

    The field is renamed to `cec_meq_per_100cm3` and the weighting follows the
    values rather than the old label (#1152 §F). The numbers below are the same
    fixtures #1099 used, with the expectations swapped — which is deliberate:
    keeping the fixtures makes the reversal legible instead of hiding it behind
    new data.
    """

    def test_cec_is_weighted_by_the_volume_fractions(self):
        """50/50 volume blend: (12 + 0.2) / 2 = 6.1.

        #1099 asserted 6.5 here, arrived at by converting to mass fractions
        (0.533 / 0.467). That conversion is exactly what turns a correct per-volume
        number into a wrong one.
        """
        result = _half_half(_light_mix(), _clay_pebbles())

        assert result["cec_meq_per_100cm3"] == 6.1

    def test_a_density_spread_no_longer_moves_the_result(self):
        """The divergence, from the other side.

        cec 5 @ 600 g/l + cec 20 @ 350 g/l, 50/50 by volume → (5 + 20) / 2 = 12.5.
        Mass-weighting returned 10.5. Asserting the volume answer *and* naming the
        mass one keeps the two distinguishable: an implementation that silently
        reverted would otherwise only fail by a rounded digit.
        """
        dense_low_cec = _make_substrate("dense", ph_base=6.5, cec_meq_per_100cm3=5.0, bulk_density_g_per_l=600.0)
        light_high_cec = _make_substrate("light", ph_base=6.5, cec_meq_per_100cm3=20.0, bulk_density_g_per_l=350.0)

        result = _half_half(dense_low_cec, light_high_cec)

        assert result["cec_meq_per_100cm3"] == 12.5
        assert result["cec_meq_per_100cm3"] != 10.5

    def test_the_worst_case_from_the_issue(self):
        """Perlite + worm humus, the pair #1152 measured: 15.1 by volume, 25.7 by mass.

        The 70 % gap is what makes the unit question consequential rather than
        pedantic, and this is the fixture that makes the decision hard to reverse
        by accident.
        """
        perlite = _make_substrate("perlite", ph_base=7.0, cec_meq_per_100cm3=0.1, bulk_density_g_per_l=100.0)
        humus = _make_substrate("humus", ph_base=7.0, cec_meq_per_100cm3=30.0, bulk_density_g_per_l=600.0)

        result = _half_half(perlite, humus)

        assert result["cec_meq_per_100cm3"] == 15.1

    def test_bulk_density_stays_volume_weighted(self):
        """bulk_density is genuinely per-volume — it must NOT change.

        The issue confirms 375.0 (= 0.5×400 + 0.5×350) is already correct.
        """
        result = _half_half(_light_mix(), _clay_pebbles())

        assert result["bulk_density_g_per_l"] == 375.0


# ── #1175: the two shapes the model change introduced ─────────────────


class TestAdditivesSurviveTheMix:
    """Additives merge as a union of names, because they carry no quantity.

    The reason this is asserted at all: additives left `composition` precisely
    because nothing downstream could read a lime *fraction* correctly. An engine
    that merged the bulk vector and dropped the names would have moved the loss
    one layer down rather than fixing it — a blend of a limed peat and an inert
    diluent is still limed, and an agent computing a dose off the MCP summary has
    no other way to learn that.
    """

    def test_a_limed_component_makes_the_blend_limed(self):
        limed = _make_substrate("limed", additives=["kalk"])
        inert = _make_substrate("inert", additives=[])

        assert _half_half(limed, inert)["additives"] == ["kalk"]

    def test_names_are_unioned_and_deduplicated_not_summed(self):
        """Two limed components give one `kalk`, not two and not a fraction."""
        a = _make_substrate("a", additives=["kalk", "spurenelemente"])
        b = _make_substrate("b", additives=["kalk"])

        assert _half_half(a, b)["additives"] == ["kalk", "spurenelemente"]

    def test_a_mix_of_plain_media_declares_no_additives(self):
        """Control: the key is always present and empty rather than absent."""
        assert _half_half(_light_mix(), _clay_pebbles())["additives"] == []


class TestPorosityIsOptional:
    """`air_porosity_percent` may be absent, and absent is not zero (#1175).

    Before the field was nullable, `Hydrokultur (kein Substrat)` carried 100.0 and
    this engine volume-weighted it, so any mix containing a hydro share was pulled
    toward a porosity that describes no pore space at all.
    """

    def test_a_component_without_a_porosity_does_not_drag_the_blend(self):
        """50/50 with a component that declines the field renormalises over the rest.

        30.0, not 15.0: the half that has no pore space contributes no pore space
        to average, rather than contributing zero of it. Naming 15.0 keeps a
        regression to `_weighted_avg`-with-a-`None`-as-0 distinguishable from the
        correct answer.
        """
        medium = _make_substrate("medium", air_porosity_percent=30.0)
        no_porosity = _make_substrate("solution", air_porosity_percent=None)

        result = _half_half(medium, no_porosity)

        assert result["air_porosity_percent"] == 30.0
        assert result["air_porosity_percent"] != 15.0

    def test_a_blend_of_components_that_all_decline_stays_absent(self):
        """Not 0.0 — there is still nothing to state."""
        a = _make_substrate("a", air_porosity_percent=None)
        b = _make_substrate("b", air_porosity_percent=None)

        assert _half_half(a, b)["air_porosity_percent"] is None

    def test_the_placeholder_would_have_moved_the_result(self):
        """The falsification: what the old 100.0 did to the same blend.

        Without this the two readings are indistinguishable on any mix that happens
        not to contain the hydro entry, which is most of them.
        """
        medium = _make_substrate("medium", air_porosity_percent=30.0)
        placeholder = _make_substrate("placeholder", air_porosity_percent=100.0)

        assert _half_half(medium, placeholder)["air_porosity_percent"] == 65.0
