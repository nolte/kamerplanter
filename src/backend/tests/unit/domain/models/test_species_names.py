"""#2902 — the one display rule for a species' vernacular name (REQ-001 v4.14, UI-NFR-007 R-009a)."""

from __future__ import annotations

import pytest

from app.domain.models.species_names import (
    CANONICAL_NAME_LANGUAGE,
    localized_common_name,
    localized_vernacular_name,
    normalize_name_language,
)

#: As in species.yaml: the English name first, the map says which is which.
TOMATO_NAMES = ["Tomato", "Tomate", "Paradeiser"]
TOMATO_I18N = {"en": ["Tomato"], "de": ["Tomate", "Paradeiser"]}
TOMATO_SCIENTIFIC = "Solanum lycopersicum"


class TestNormalizeNameLanguage:
    @pytest.mark.parametrize(
        ("language", "expected"),
        [
            ("de", "de"),
            ("en", "en"),
            ("de-DE", "de"),
            ("en-US", "en"),
            ("en_GB", "en"),
            ("EN", "en"),
            (" fr-CA ", "fr"),
            ("", CANONICAL_NAME_LANGUAGE),
            (None, CANONICAL_NAME_LANGUAGE),
            ("   ", CANONICAL_NAME_LANGUAGE),
        ],
    )
    def test_maps_a_locale_onto_the_key_of_the_language_map(self, language: str | None, expected: str) -> None:
        assert normalize_name_language(language) == expected

    def test_canonical_language_is_german(self) -> None:
        assert CANONICAL_NAME_LANGUAGE == "de"


class TestLocalizedCommonName:
    def test_requested_language_wins_over_list_order(self) -> None:
        assert localized_common_name(TOMATO_NAMES, TOMATO_I18N, TOMATO_SCIENTIFIC, "de") == "Tomate"
        assert localized_common_name(TOMATO_NAMES, TOMATO_I18N, TOMATO_SCIENTIFIC, "en") == "Tomato"

    def test_a_regional_locale_resolves_its_language(self) -> None:
        assert localized_common_name(TOMATO_NAMES, TOMATO_I18N, TOMATO_SCIENTIFIC, "de-AT") == "Tomate"
        assert localized_common_name(TOMATO_NAMES, TOMATO_I18N, TOMATO_SCIENTIFIC, "en-US") == "Tomato"

    def test_a_language_without_names_falls_back_to_german(self) -> None:
        assert localized_common_name(TOMATO_NAMES, TOMATO_I18N, TOMATO_SCIENTIFIC, "fr") == "Tomate"

    def test_no_language_is_the_canonical_one(self) -> None:
        assert localized_common_name(TOMATO_NAMES, TOMATO_I18N, TOMATO_SCIENTIFIC, None) == "Tomate"

    def test_a_map_without_requested_and_german_names_falls_back_to_the_scientific_name(self) -> None:
        # The map knows only English: the flat list's first entry would only be a guess.
        assert localized_common_name(["Tomato"], {"en": ["Tomato"]}, TOMATO_SCIENTIFIC, "de") == TOMATO_SCIENTIFIC

    def test_without_a_map_the_first_listed_name_stands(self) -> None:
        # A tenant-created or CSV-imported species: the list is all the record says.
        assert localized_common_name(["Meine Tomate", "Tom"], {}, TOMATO_SCIENTIFIC, "en") == "Meine Tomate"
        assert localized_common_name(["Meine Tomate"], None, TOMATO_SCIENTIFIC, "de") == "Meine Tomate"

    def test_without_any_name_the_scientific_name_stands(self) -> None:
        assert localized_common_name([], {}, TOMATO_SCIENTIFIC, "de") == TOMATO_SCIENTIFIC
        assert localized_common_name(None, None, TOMATO_SCIENTIFIC, "en") == TOMATO_SCIENTIFIC

    def test_a_blank_first_name_counts_as_none(self) -> None:
        assert localized_common_name(["  "], {}, TOMATO_SCIENTIFIC, "de") == TOMATO_SCIENTIFIC
        assert localized_common_name([" Tomate "], {}, TOMATO_SCIENTIFIC, "de") == "Tomate"

    def test_empty_when_the_species_carries_no_name_at_all(self) -> None:
        assert localized_common_name([], {}, None, "de") == ""


class TestLocalizedVernacularName:
    def test_same_rule_without_the_scientific_fallback(self) -> None:
        assert localized_vernacular_name(TOMATO_NAMES, TOMATO_I18N, "de") == "Tomate"
        assert localized_vernacular_name(TOMATO_NAMES, TOMATO_I18N, "en") == "Tomato"
        assert localized_vernacular_name(["Meine Tomate"], {}, "en") == "Meine Tomate"

    def test_none_where_the_display_name_would_be_the_scientific_one(self) -> None:
        assert localized_vernacular_name(["Tomato"], {"en": ["Tomato"]}, "de") is None
        assert localized_vernacular_name([], {}, "de") is None
        assert localized_vernacular_name(None, None, None) is None
