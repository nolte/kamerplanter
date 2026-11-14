"""#2936 — renaming a disease carries the map's English entry along when that entry IS the stored name.

The display prefers ``common_names_i18n`` over ``common_name``. A seeded disease lists its
stored name as ``en``, so a rename that left the map alone would keep showing the old name
in the English UI and the edit would look lost.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.common.enums import PathogenType
from app.domain.models.ipm import Disease
from app.domain.services.ipm_service import IpmService


def _service(stored: Disease) -> IpmService:
    repo = MagicMock()
    repo.get_disease_or_raise.side_effect = lambda key: stored.model_copy(deep=True)
    repo.update_disease.side_effect = lambda key, disease: disease
    return IpmService(repo, MagicMock(), MagicMock(), MagicMock())


def _mildew(names: dict[str, list[str]]) -> Disease:
    return Disease(
        _key="d1",
        scientific_name="Erysiphe spp.",
        common_name="Powdery Mildew",
        pathogen_type=PathogenType.FUNGAL,
        common_names_i18n=names,
    )


def test_a_rename_moves_an_english_entry_that_was_the_stored_name() -> None:
    service = _service(_mildew({"en": ["Powdery Mildew"], "de": ["Echter Mehltau"]}))

    updated = service.update_disease("d1", {"common_name": "Powdery mildew (Erysiphe)"}, is_platform_admin=True)

    assert updated.common_names_i18n == {"en": ["Powdery mildew (Erysiphe)"], "de": ["Echter Mehltau"]}


def test_a_rename_leaves_an_english_entry_that_differs_from_the_stored_name() -> None:
    service = _service(_mildew({"en": ["Oidium"], "de": ["Echter Mehltau"]}))

    updated = service.update_disease("d1", {"common_name": "Mildew"}, is_platform_admin=True)

    assert updated.common_names_i18n == {"en": ["Oidium"], "de": ["Echter Mehltau"]}


def test_a_rename_with_an_explicit_map_keeps_the_map_it_was_given() -> None:
    service = _service(_mildew({"en": ["Powdery Mildew"]}))

    updated = service.update_disease(
        "d1", {"common_name": "Mildew", "common_names_i18n": {"de": ["Mehltau"]}}, is_platform_admin=True
    )

    assert updated.common_names_i18n == {"de": ["Mehltau"]}


def test_an_update_without_a_rename_leaves_the_map_alone() -> None:
    service = _service(_mildew({"en": ["Powdery Mildew"]}))

    updated = service.update_disease("d1", {"description": "white coating"}, is_platform_admin=True)

    assert updated.common_names_i18n == {"en": ["Powdery Mildew"]}
