"""REQ-048 Stufe 1 — unit tests for :func:`normalize_scientific_name`.

Pure string logic: the canonical dedup key must collapse hybrid-marker (× ↔ x),
casing and whitespace differences onto one value while preserving distinct taxa.
"""

from __future__ import annotations

import pytest

from app.domain.calculators.scientific_name import normalize_scientific_name


class TestHybridMarker:
    def test_multiplication_sign_and_ascii_x_collapse(self):
        assert normalize_scientific_name("Fragaria × ananassa") == normalize_scientific_name("Fragaria x ananassa")

    def test_hybrid_key_value(self):
        assert normalize_scientific_name("Fragaria × ananassa") == "fragaria x ananassa"

    def test_attached_and_spaced_multiplication_sign_collapse(self):
        # ×ananassa (no space) and × ananassa (spaced) yield the same token.
        assert normalize_scientific_name("Fragaria ×ananassa") == "fragaria x ananassa"

    def test_genus_hybrid_prefix_unified(self):
        assert normalize_scientific_name("× Chitalpa tashkentensis") == normalize_scientific_name(
            "x Chitalpa tashkentensis"
        )
        assert normalize_scientific_name("×Chitalpa tashkentensis") == "x chitalpa tashkentensis"

    def test_letter_x_inside_name_is_untouched(self):
        # A regular 'x' in a genus/epithet must not be treated as a hybrid marker.
        assert normalize_scientific_name("Maxillaria tenuifolia") == "maxillaria tenuifolia"


class TestCasing:
    def test_casefold_lowercases(self):
        assert normalize_scientific_name("SOLANUM Lycopersicum") == "solanum lycopersicum"

    def test_mixed_case_variants_collapse(self):
        assert normalize_scientific_name("Solanum lycopersicum") == normalize_scientific_name("solanum LYCOPERSICUM")


class TestWhitespace:
    def test_internal_runs_collapse(self):
        assert normalize_scientific_name("Solanum   lycopersicum") == "solanum lycopersicum"

    def test_leading_and_trailing_stripped(self):
        assert normalize_scientific_name("  Solanum lycopersicum  ") == "solanum lycopersicum"

    def test_tabs_and_newlines_collapse(self):
        assert normalize_scientific_name("Solanum\tlycopersicum\n") == "solanum lycopersicum"


class TestEdgeCases:
    @pytest.mark.parametrize("value", ["", "   ", "\t\n"])
    def test_empty_or_whitespace_only_returns_empty(self, value: str):
        assert normalize_scientific_name(value) == ""

    def test_distinct_species_do_not_collapse(self):
        assert normalize_scientific_name("Fragaria vesca") != normalize_scientific_name("Fragaria × ananassa")
