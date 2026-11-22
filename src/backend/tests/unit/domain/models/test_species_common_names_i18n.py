"""``Species.common_names_i18n`` — the language map of the vernacular names (REQ-001, #2902).

``common_names`` is a flat, language-mixed list whose order carries no language
meaning; ``common_names_i18n`` says which of those names belong to which language.
The map never introduces a name of its own, so a name outside ``common_names`` is
rejected rather than silently appended.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.models.species import (
    Species,
    prune_common_names_i18n,
    validate_common_names_i18n,
)


def _species(common_names: list[str], names_i18n: dict[str, list[str]]) -> Species:
    return Species(scientific_name="Daucus carota", common_names=common_names, common_names_i18n=names_i18n)


class TestValidation:
    def test_a_map_naming_only_listed_names_is_kept_in_preference_order(self) -> None:
        species = _species(["Carrot", "Karotte", "Möhre"], {"de": ["Möhre", "Karotte"], "en": ["Carrot"]})

        assert species.common_names_i18n == {"de": ["Möhre", "Karotte"], "en": ["Carrot"]}

    def test_the_map_defaults_to_empty(self) -> None:
        assert Species(scientific_name="Daucus carota", common_names=["Carrot"]).common_names_i18n == {}

    def test_a_name_outside_common_names_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="'Mohrrübe' is not in common_names"):
            _species(["Carrot", "Möhre"], {"de": ["Möhre", "Mohrrübe"]})

    @pytest.mark.parametrize("key", ["DE", "deu-x", "d", "de_DE", ""])
    def test_a_key_that_is_not_a_lowercase_language_code_is_rejected(self, key: str) -> None:
        with pytest.raises(ValidationError, match="lowercase language code"):
            _species(["Möhre"], {key: ["Möhre"]})

    def test_a_three_letter_code_is_accepted(self) -> None:
        assert _species(["Möhre"], {"deu": ["Möhre"]}).common_names_i18n == {"deu": ["Möhre"]}

    def test_an_empty_name_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="empty name"):
            _species(["Möhre"], {"de": ["  "]})

    def test_names_are_stripped_and_deduplicated(self) -> None:
        species = _species(["Möhre", "Karotte"], {"de": [" Möhre ", "Möhre", "Karotte"]})

        assert species.common_names_i18n == {"de": ["Möhre", "Karotte"]}

    def test_a_language_without_names_is_dropped(self) -> None:
        assert _species(["Möhre"], {"de": ["Möhre"], "en": []}).common_names_i18n == {"de": ["Möhre"]}

    def test_a_name_shared_by_two_languages_may_sit_in_both(self) -> None:
        species = _species(["Zucchini", "Courgette"], {"de": ["Zucchini"], "en": ["Zucchini", "Courgette"]})

        assert species.common_names_i18n["de"] == ["Zucchini"]
        assert species.common_names_i18n["en"] == ["Zucchini", "Courgette"]

    def test_the_helper_raises_value_error_for_callers_outside_a_model(self) -> None:
        with pytest.raises(ValueError, match="not in common_names"):
            validate_common_names_i18n(["Pea"], {"de": ["Erbse"]})


class TestPrune:
    def test_a_name_removed_from_common_names_leaves_the_map(self) -> None:
        pruned = prune_common_names_i18n(["Möhre"], {"de": ["Möhre", "Karotte"], "en": ["Carrot"]})

        assert pruned == {"de": ["Möhre"]}

    def test_a_map_within_common_names_is_unchanged(self) -> None:
        names_i18n = {"de": ["Erbse"], "en": ["Pea"]}

        assert prune_common_names_i18n(["Pea", "Erbse"], names_i18n) == names_i18n
