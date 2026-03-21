"""Tests for SubstrateEcAdapter — EC target conversion between substrate types."""

import pytest

from app.domain.engines.substrate_ec_adapter import SubstrateEcAdapter


@pytest.fixture
def adapter() -> SubstrateEcAdapter:
    return SubstrateEcAdapter()


# ── Same substrate — no conversion ────────────────────────────────────


class TestNoConversion:
    def test_same_substrate_returns_unchanged(self, adapter: SubstrateEcAdapter) -> None:
        assert adapter.convert_ec(1.0, "soil", "soil", "vegetative") == 1.0

    def test_same_class_hydro_variants(self, adapter: SubstrateEcAdapter) -> None:
        assert adapter.convert_ec(2.0, "hydro_solution", "clay_pebbles", "vegetative") == 2.0

    def test_same_class_coco_variants(self, adapter: SubstrateEcAdapter) -> None:
        assert adapter.convert_ec(1.5, "coco", "sphagnum", "flowering") == 1.5

    def test_zero_ec_returns_zero(self, adapter: SubstrateEcAdapter) -> None:
        assert adapter.convert_ec(0.0, "soil", "hydro_solution", "vegetative") == 0.0

    def test_negative_ec_returns_zero(self, adapter: SubstrateEcAdapter) -> None:
        assert adapter.convert_ec(-0.5, "soil", "hydro_solution", "vegetative") == 0.0


# ── SOIL -> HYDRO conversion ──────────────────────────────────────────


class TestSoilToHydro:
    def test_vegetative(self, adapter: SubstrateEcAdapter) -> None:
        # SOIL veg factor = 0.55, HYDRO veg factor = 1.0
        # hydro_ec = 1.0 / 0.55 = 1.818..., effective = 1.818 * 1.0 = 1.82
        result = adapter.convert_ec(1.0, "soil", "hydro_solution", "vegetative")
        assert result == pytest.approx(1.82, abs=0.01)

    def test_flowering(self, adapter: SubstrateEcAdapter) -> None:
        # SOIL flower factor = 0.57, HYDRO flower factor = 1.0
        result = adapter.convert_ec(1.3, "soil", "hydro_solution", "flowering")
        assert result == pytest.approx(2.28, abs=0.01)

    def test_seedling(self, adapter: SubstrateEcAdapter) -> None:
        # SOIL seedling factor = 0.50, HYDRO seedling factor = 1.0
        result = adapter.convert_ec(0.5, "soil", "hydro_solution", "seedling")
        assert result == pytest.approx(1.0, abs=0.01)


# ── HYDRO -> SOIL conversion ──────────────────────────────────────────


class TestHydroToSoil:
    def test_vegetative(self, adapter: SubstrateEcAdapter) -> None:
        result = adapter.convert_ec(2.0, "hydro_solution", "soil", "vegetative")
        assert result == pytest.approx(1.1, abs=0.01)

    def test_flowering(self, adapter: SubstrateEcAdapter) -> None:
        result = adapter.convert_ec(2.3, "hydro_solution", "soil", "flowering")
        assert result == pytest.approx(1.31, abs=0.01)


# ── SOIL -> COCO conversion ──────────────────────────────────────────


class TestSoilToCoco:
    def test_vegetative(self, adapter: SubstrateEcAdapter) -> None:
        # SOIL veg=0.55, COCO veg=0.90 -> hydro_ec = 1.0/0.55, eff = hydro * 0.90
        result = adapter.convert_ec(1.0, "soil", "coco", "vegetative")
        assert result == pytest.approx(1.64, abs=0.01)


# ── COCO -> SOIL conversion ──────────────────────────────────────────


class TestCocoToSoil:
    def test_vegetative(self, adapter: SubstrateEcAdapter) -> None:
        result = adapter.convert_ec(1.8, "coco", "soil", "vegetative")
        assert result == pytest.approx(1.1, abs=0.01)


# ── Roundtrip tests ──────────────────────────────────────────────────


class TestRoundtrip:
    def test_soil_hydro_roundtrip(self, adapter: SubstrateEcAdapter) -> None:
        original = 1.0
        hydro = adapter.convert_ec(original, "soil", "hydro_solution", "vegetative")
        back = adapter.convert_ec(hydro, "hydro_solution", "soil", "vegetative")
        assert back == pytest.approx(original, abs=0.02)

    def test_coco_soil_roundtrip(self, adapter: SubstrateEcAdapter) -> None:
        original = 1.5
        soil = adapter.convert_ec(original, "coco", "soil", "flowering")
        back = adapter.convert_ec(soil, "soil", "coco", "flowering")
        assert back == pytest.approx(original, abs=0.02)


# ── Living soil bypass ───────────────────────────────────────────────


class TestLivingSoil:
    def test_to_living_soil_returns_zero(self, adapter: SubstrateEcAdapter) -> None:
        assert adapter.convert_ec(1.5, "soil", "living_soil", "vegetative") == 0.0

    def test_from_living_soil_returns_unchanged(self, adapter: SubstrateEcAdapter) -> None:
        assert adapter.convert_ec(1.5, "living_soil", "coco", "vegetative") == 1.5

    def test_living_soil_factor_is_zero(self, adapter: SubstrateEcAdapter) -> None:
        assert adapter.get_factor("living_soil", "vegetative") == 0.0


# ── Unknown substrate defaults to soil ────────────────────────────────


class TestUnknownSubstrate:
    def test_unknown_treated_as_soil(self, adapter: SubstrateEcAdapter) -> None:
        result = adapter.convert_ec(1.0, "unknown_substrate", "hydro_solution", "vegetative")
        expected = adapter.convert_ec(1.0, "soil", "hydro_solution", "vegetative")
        assert result == expected


# ── Phase fallback ───────────────────────────────────────────────────


class TestPhaseFallback:
    def test_unknown_phase_uses_default(self, adapter: SubstrateEcAdapter) -> None:
        result = adapter.convert_ec(1.0, "soil", "hydro_solution", "custom_phase")
        # default soil factor = 0.55, hydro default = 1.0
        assert result == pytest.approx(1.82, abs=0.01)


# ── get_factor ───────────────────────────────────────────────────────


class TestGetFactor:
    def test_hydro_factor_is_one(self, adapter: SubstrateEcAdapter) -> None:
        assert adapter.get_factor("hydro_solution", "vegetative") == 1.0

    def test_soil_vegetative(self, adapter: SubstrateEcAdapter) -> None:
        assert adapter.get_factor("soil", "vegetative") == 0.55

    def test_coco_flowering(self, adapter: SubstrateEcAdapter) -> None:
        assert adapter.get_factor("coco", "flowering") == 0.91
