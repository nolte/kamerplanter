"""REQ-036 §4.1 — unit tests for the curated symptom catalogue."""

from __future__ import annotations

from app.domain.models.diagnosis import SymptomCategory
from app.domain.services.symptom_catalog import SYMPTOM_CATALOG, SymptomCatalog


def test_catalog_has_at_least_30_symptoms() -> None:
    assert len(SYMPTOM_CATALOG) >= 30


def test_catalog_covers_all_seven_categories() -> None:
    categories = {e.category for e in SYMPTOM_CATALOG}
    assert categories == set(SymptomCategory)


def test_slugs_are_unique() -> None:
    slugs = [e.slug for e in SYMPTOM_CATALOG]
    assert len(slugs) == len(set(slugs))


def test_list_symptoms_filters_by_phase() -> None:
    catalog = SymptomCatalog()
    germination = catalog.list_symptoms(phase="germination")
    slugs = {e.slug for e in germination}
    # A germination-only symptom is present; a flowering-only one is not.
    assert "slow_seed_germination" in slugs
    assert "hermaphrodite_flowers" not in slugs


def test_list_symptoms_filters_by_category() -> None:
    catalog = SymptomCatalog()
    pests = catalog.list_symptoms(category="pest_visible")
    assert pests
    assert all(e.category == SymptomCategory.PEST_VISIBLE for e in pests)


def test_resolve_drops_unknown_slugs() -> None:
    catalog = SymptomCatalog()
    resolved = catalog.resolve(["leaf_spots", "does_not_exist"])
    assert [e.slug for e in resolved] == ["leaf_spots"]


def test_get_symptom_returns_none_for_unknown() -> None:
    assert SymptomCatalog().get_symptom("nope") is None
