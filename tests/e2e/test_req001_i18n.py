"""E2E tests for REQ-001 — i18n and Display.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-093  ->  TC-001-053  i18n — Deutsche und englische Familiennamen werden korrekt angezeigt
  TC-REQ-001-094  ->  TC-001-053  i18n — Wuchsform- und Wurzeltyp-Enums in deutscher Uebersetzung
  TC-REQ-001-095  ->  TC-001-053  i18n — Cultivar-Trait-Chips zeigen deutsche Uebersetzungen
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import BotanicalFamilyListPage, SpeciesDetailPage, SpeciesListPage


@pytest.fixture
def family_list(browser: WebDriver, base_url: str) -> BotanicalFamilyListPage:
    return BotanicalFamilyListPage(browser, base_url)


@pytest.fixture
def species_list(browser: WebDriver, base_url: str) -> SpeciesListPage:
    return SpeciesListPage(browser, base_url)


@pytest.fixture
def species_detail(browser: WebDriver, base_url: str) -> SpeciesDetailPage:
    return SpeciesDetailPage(browser, base_url)


# German enum translations for verification
NUTRIENT_DEMAND_DE = {"Schwachzehrer", "Mittelzehrer", "Starkzehrer"}
FROST_TOLERANCE_DE = {"Empfindlich", "Moderat", "Hardy", "Sehr hardy"}
ROOT_DEPTH_DE = {"Flach", "Mittel", "Tief"}
GROWTH_HABIT_DE = {"Kraut", "Strauch", "Baum", "Ranke", "Bodendecker"}
ROOT_TYPE_DE = {"Faserig", "Pfahlwurzel", "Knollig", "Zwiebel"}
TRAIT_DE = {
    "Krankheitsresistent",
    "Ertragreich",
    "Kompakt",
    "Hitzeverträglich",
    "Kältetolerant",
    "Schädlingsresistent",
    "Trockenheitstolerant",
}


class TestBotanicalFamilyEnumTranslations:
    """All enum values displayed in German translation (Spec: TC-001-053)."""

    @pytest.mark.smoke
    def test_botanical_family_enums_in_german(
        self, family_list: BotanicalFamilyListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-093: Enum values in botanical family table are displayed in German.

        Spec: TC-001-053 -- i18n — Deutsche und englische Familiennamen werden korrekt angezeigt.
        """
        family_list.open()

        if family_list.get_row_count() == 0:
            pytest.skip("No botanical families in database")

        screenshot("TC-REQ-001-093_family-table", "Botanical family table with enum columns")

        row_data = family_list.get_row_texts()
        if not row_data:
            pytest.skip("No row data available")

        headers = family_list.get_column_headers()

        # Map raw English enum keys to the columns they can appear in.
        # The botanical family table columns are:
        # 0: Name, 1: Common name, 2: Nutrient demand, 3: Frost tolerance,
        # 4: Root depth, 5: Species count, 6: Rotation category
        # Only check enum-specific columns (indices 2, 3, 4) to avoid
        # false positives from names, descriptions or other text columns.
        raw_english_enums_by_column: dict[int, set[str]] = {
            2: {"light", "medium", "heavy"},         # nutrient demand
            3: {"sensitive", "moderate", "very_hardy"},  # frost tolerance
            4: {"shallow", "deep"},                   # root depth
        }
        # Note: "hardy" is excluded because DE translation is also "Hardy"
        # (same word in both languages). "medium" in column 4 (root depth)
        # is distinct from column 2 (nutrient demand) — Mittel vs Mittelzehrer.

        for row in row_data:
            for col_idx, enum_set in raw_english_enums_by_column.items():
                if col_idx < len(row):
                    cell_value = row[col_idx].strip().lower()
                    if cell_value in enum_set:
                        pytest.fail(
                            f"TC-REQ-001-093 FAIL: Raw English enum '{cell_value}' found in column "
                            f"{col_idx} ({headers[col_idx] if col_idx < len(headers) else '?'}). "
                            "Expected German translation."
                        )


class TestSpeciesEnumTranslations:
    """Growth habit enums displayed in German on species list (Spec: TC-001-053)."""

    @pytest.mark.smoke
    def test_species_enums_in_german(
        self, species_list: SpeciesListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-REQ-001-094: Growth habit and root type enums in German.

        Spec: TC-001-053 -- i18n — Wuchsform- und Wurzeltyp-Enums in deutscher Uebersetzung.
        """
        species_list.open()

        if species_list.get_row_count() == 0:
            pytest.skip("No species in database")

        screenshot("TC-REQ-001-094_species-table", "Species table with enum columns")

        headers = species_list.get_column_headers()

        # Find growth habit and root type columns
        rows = species_list.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='data-table-row']"
        )

        raw_english_enums = {
            "herb", "shrub", "tree", "vine", "ground_cover",  # growth habit
            "fibrous", "taproot", "tuberous", "bulb",  # root type
        }

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            for cell in cells:
                cell_text = cell.text.strip().lower()
                if cell_text in raw_english_enums:
                    pytest.fail(
                        f"TC-REQ-001-094 FAIL: Raw English enum '{cell_text}' found in species table. "
                        "Expected German translation."
                    )


class TestCultivarTraitTranslations:
    """Cultivar trait chips show German translations (Spec: TC-001-053)."""

    @pytest.mark.smoke
    def test_cultivar_traits_in_german(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-001-095: Cultivar trait chips show German translations.

        Spec: TC-001-053 -- i18n — Cultivar-Trait-Chips zeigen deutsche Uebersetzungen.
        """
        species_list.open()

        if species_list.get_row_count() == 0:
            pytest.skip("No species in database")

        species_list.click_row(0)
        species_list.wait_for_url_contains("/stammdaten/species/")

        species_detail.click_tab_by_label("Sorten")
        species_detail.wait_for_loading_complete()
        screenshot("TC-REQ-001-095_cultivar-tab", "Species cultivar tab with trait chips")

        if species_detail.get_cultivar_count() == 0:
            pytest.skip("No cultivars for this species")

        # Find chip elements in the cultivar table
        chips = species_detail.driver.find_elements(
            By.CSS_SELECTOR, ".MuiChip-label"
        )

        raw_trait_keys = {
            "disease_resistant", "high_yield", "compact",
            "heat_tolerant", "cold_tolerant", "pest_resistant",
            "drought_tolerant",
        }

        for chip in chips:
            chip_text = chip.text.strip().lower()
            if chip_text in raw_trait_keys:
                pytest.fail(
                    f"TC-REQ-001-095 FAIL: Raw trait key '{chip_text}' found as chip label. "
                    "Expected German translation (e.g., 'Krankheitsresistent')."
                )
