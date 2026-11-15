"""#2955 — a pest names its languages in ``common_names_i18n``, the shape diseases use (#2936).

``Pest.common_name_de`` stays readable for stored rows and API consumers, but it is no
second truth: the model derives it from the map's ``de`` entry, and a row or request
that only carries ``common_name_de`` seeds that entry. The service keeps the pair in
step on an update.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.domain.models.ipm import Pest, sync_german_name
from app.domain.models.species_names import localized_catalog_name
from app.domain.services.ipm_service import IpmService

_MITES = {"en": ["Spider Mites"], "de": ["Spinnmilben"]}


def _pest(**fields: object) -> Pest:
    return Pest.model_validate(
        {"_key": "p1", "scientific_name": "Tetranychus urticae", "common_name": "Spider Mites", **fields}
    )


class TestTheModelHoldsOneGermanName:
    def test_the_map_derives_the_german_compatibility_field(self) -> None:
        pest = _pest(common_names_i18n=_MITES)

        assert pest.common_name_de == "Spinnmilben"

    def test_a_row_from_before_the_map_gains_its_german_entry(self) -> None:
        pest = _pest(common_name_de=" Spinnmilben ")

        assert pest.common_names_i18n == {"de": ["Spinnmilben"]}
        assert pest.common_name_de == "Spinnmilben"

    def test_the_map_wins_over_a_conflicting_german_field(self) -> None:
        pest = _pest(common_name_de="Rote Spinne", common_names_i18n=_MITES)

        assert pest.common_name_de == "Spinnmilben"
        assert pest.common_names_i18n == _MITES

    def test_no_german_name_anywhere_stays_empty(self) -> None:
        pest = _pest(common_name_de="  ", common_names_i18n={"en": ["Spider Mites"]})

        assert pest.common_name_de is None
        assert pest.common_names_i18n == {"en": ["Spider Mites"]}

    def test_an_invalid_language_key_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _pest(common_names_i18n={"DE": ["Spinnmilben"]})

    def test_sync_german_name_keeps_the_map_untouched_without_german(self) -> None:
        assert sync_german_name(None, {"en": ["Spider Mites"]}) == (None, {"en": ["Spider Mites"]})


class TestThePestIsNamedInTheUiLanguage:
    @pytest.mark.parametrize(
        ("language", "expected"),
        [("de", "Spinnmilben"), ("en", "Spider Mites"), ("fr", "Spinnmilben"), ("de-DE", "Spinnmilben")],
    )
    def test_the_language_map_picks_the_name(self, language: str, expected: str) -> None:
        pest = _pest(common_names_i18n=_MITES)

        assert localized_catalog_name(pest.common_name, pest.common_names_i18n, language) == expected

    def test_a_pest_without_a_map_shows_its_stored_name(self) -> None:
        pest = _pest()

        assert localized_catalog_name(pest.common_name, pest.common_names_i18n, "de") == "Spider Mites"


def _service(stored: Pest) -> IpmService:
    repo = MagicMock()
    repo.get_pest_or_raise.side_effect = lambda key: stored.model_copy(deep=True)
    repo.update_pest.side_effect = lambda key, pest: pest
    return IpmService(repo, MagicMock(), MagicMock(), MagicMock())


class TestAnUpdateKeepsTheNamesOneTruth:
    def test_a_map_sent_replaces_the_stored_one_and_derives_the_german_field(self) -> None:
        service = _service(_pest(common_names_i18n=_MITES))

        updated = service.update_pest(
            "p1", {"common_names_i18n": {"de": ["Gemeine Spinnmilbe"]}}, is_platform_admin=True
        )

        assert updated.common_names_i18n == {"de": ["Gemeine Spinnmilbe"]}
        assert updated.common_name_de == "Gemeine Spinnmilbe"

    def test_a_map_without_german_clears_the_german_field(self) -> None:
        service = _service(_pest(common_names_i18n=_MITES))

        updated = service.update_pest("p1", {"common_names_i18n": {"en": ["Spider Mites"]}}, is_platform_admin=True)

        assert updated.common_names_i18n == {"en": ["Spider Mites"]}
        assert updated.common_name_de is None

    def test_a_german_field_sent_alone_replaces_the_maps_german_entry(self) -> None:
        service = _service(_pest(common_names_i18n=_MITES))

        updated = service.update_pest("p1", {"common_name_de": "Gemeine Spinnmilbe"}, is_platform_admin=True)

        assert updated.common_names_i18n == {"en": ["Spider Mites"], "de": ["Gemeine Spinnmilbe"]}
        assert updated.common_name_de == "Gemeine Spinnmilbe"

    def test_a_blank_german_field_sent_alone_removes_the_german_entry(self) -> None:
        service = _service(_pest(common_names_i18n=_MITES))

        updated = service.update_pest("p1", {"common_name_de": ""}, is_platform_admin=True)

        assert updated.common_names_i18n == {"en": ["Spider Mites"]}
        assert updated.common_name_de is None

    def test_a_rename_moves_an_english_entry_that_was_the_stored_name(self) -> None:
        service = _service(_pest(common_names_i18n=_MITES))

        updated = service.update_pest("p1", {"common_name": "Two-spotted Spider Mite"}, is_platform_admin=True)

        assert updated.common_names_i18n == {"en": ["Two-spotted Spider Mite"], "de": ["Spinnmilben"]}

    def test_a_rename_leaves_an_english_entry_that_differs_from_the_stored_name(self) -> None:
        service = _service(_pest(common_names_i18n={"en": ["Red spider"], "de": ["Spinnmilben"]}))

        updated = service.update_pest("p1", {"common_name": "Mites"}, is_platform_admin=True)

        assert updated.common_names_i18n == {"en": ["Red spider"], "de": ["Spinnmilben"]}

    def test_an_update_without_a_name_leaves_the_names_alone(self) -> None:
        service = _service(_pest(common_names_i18n=_MITES))

        updated = service.update_pest("p1", {"description": "webbing"}, is_platform_admin=True)

        assert updated.common_names_i18n == _MITES
        assert updated.common_name_de == "Spinnmilben"
