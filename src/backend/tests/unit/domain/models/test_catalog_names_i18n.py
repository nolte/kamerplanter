"""Names per language for catalogue entities with ONE stored name — IPM diseases and beneficials (#2936).

``Disease.common_name`` is the seed's English name, ``Beneficial.common_name`` the taxon's
German one. ``common_names_i18n`` says which name belongs to which language, and
``localized_catalog_name`` shows: UI language -> ``de`` -> the stored name.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.common.enums import PathogenType
from app.domain.models.beneficial import Beneficial
from app.domain.models.ipm import Disease
from app.domain.models.species_names import localized_catalog_name, normalize_names_i18n

_MILDEW = {"en": ["Powdery Mildew"], "de": ["Echter Mehltau"]}


class TestLocalizedCatalogName:
    @pytest.mark.parametrize(
        ("language", "expected"),
        [("de", "Echter Mehltau"), ("en", "Powdery Mildew"), ("de-DE", "Echter Mehltau"), ("EN_us", "Powdery Mildew")],
    )
    def test_the_ui_language_picks_its_name(self, language: str, expected: str) -> None:
        assert localized_catalog_name("Powdery Mildew", _MILDEW, language) == expected

    def test_a_language_without_a_name_falls_back_to_german(self) -> None:
        assert localized_catalog_name("Powdery Mildew", _MILDEW, "fr") == "Echter Mehltau"

    def test_without_a_german_name_the_german_ui_shows_the_stored_name(self) -> None:
        assert localized_catalog_name("Bacterial Spot", {"en": ["Bacterial Spot"]}, "de") == "Bacterial Spot"

    def test_without_an_english_name_the_english_ui_shows_the_german_one(self) -> None:
        names = {"de": ["Schlupfwespe (Encarsia formosa)"]}

        assert (
            localized_catalog_name("Schlupfwespe (Encarsia formosa)", names, "en") == "Schlupfwespe (Encarsia formosa)"
        )

    @pytest.mark.parametrize("names_i18n", [{}, None])
    def test_without_a_map_the_stored_name_is_shown(self, names_i18n: dict[str, list[str]] | None) -> None:
        assert localized_catalog_name("Rust", names_i18n, "de") == "Rust"

    def test_a_blank_language_list_is_skipped(self) -> None:
        assert localized_catalog_name("Rust", {"de": ["  "], "en": ["Rust"]}, "de") == "Rust"


class TestNormalize:
    def test_names_are_stripped_deduplicated_and_empty_languages_dropped(self) -> None:
        assert normalize_names_i18n({"de": [" Feuerbrand ", "Feuerbrand"], "en": []}) == {"de": ["Feuerbrand"]}

    @pytest.mark.parametrize("key", ["DE", "de_DE", "d", ""])
    def test_a_key_that_is_not_a_lowercase_language_code_is_rejected(self, key: str) -> None:
        with pytest.raises(ValueError, match="lowercase language code"):
            normalize_names_i18n({key: ["Feuerbrand"]})

    def test_an_empty_name_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty name"):
            normalize_names_i18n({"de": [" "]})


class TestModels:
    def test_a_disease_keeps_its_map_and_defaults_to_none(self) -> None:
        disease = Disease(
            scientific_name="Erysiphe spp.",
            common_name="Powdery Mildew",
            pathogen_type=PathogenType.FUNGAL,
            common_names_i18n={"de": [" Echter Mehltau "]},
        )

        assert disease.common_names_i18n == {"de": ["Echter Mehltau"]}
        assert Disease(scientific_name="X", common_name="Y", pathogen_type=PathogenType.FUNGAL).common_names_i18n == {}

    def test_a_disease_with_an_invalid_key_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="lowercase language code"):
            Disease(
                scientific_name="X", common_name="Y", pathogen_type=PathogenType.FUNGAL, common_names_i18n={"DE": ["Z"]}
            )

    def test_a_beneficial_keeps_its_map(self) -> None:
        beneficial = Beneficial(
            slug="predatory_mite",
            common_name="Raubmilben",
            scientific_name="Phytoseiidae",
            common_names_i18n={"de": ["Raubmilben"], "en": ["Predatory mites"]},
        )

        assert localized_catalog_name(beneficial.common_name, beneficial.common_names_i18n, "en") == "Predatory mites"
