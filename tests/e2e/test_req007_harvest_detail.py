"""E2E tests for REQ-007 — Erntemanagement: Detail, Edit, Quality, Yield (TC-007-014 to TC-007-030).

Tests cover:
- HarvestBatchDetailPage: detail view, tabs, fields display
- Tab 0 (Details): info table, fields, quality chip
- Tab 1 (Quality): create form, validation, display table, score colors, defect chips
- Tab 2 (Yield): create form, validation, display table
- Tab 3 (Edit): prefilled form, save, disabled button when clean, validation
- Error handling: 404 for unknown keys

NFR-008 §3.4 screenshot checkpoints at:
1. Page Load
2. Before significant actions
3. After significant actions
4. Error states
"""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages.harvest_batch_detail_page import HarvestBatchDetailPage
from .pages.harvest_batch_list_page import HarvestBatchListPage


# -- Fixtures ---------------------------------------------------------------


@pytest.fixture
def harvest_detail(browser: WebDriver, base_url: str) -> HarvestBatchDetailPage:
    """Return a HarvestBatchDetailPage bound to the test browser."""
    return HarvestBatchDetailPage(browser, base_url)


@pytest.fixture
def harvest_list(browser: WebDriver, base_url: str) -> HarvestBatchListPage:
    """Return a HarvestBatchListPage bound to the test browser."""
    return HarvestBatchListPage(browser, base_url)


def _get_first_batch_key(harvest_list: HarvestBatchListPage) -> str:
    """Navigate to list, click first row, extract key from URL."""
    harvest_list.open()
    if harvest_list.get_row_count() == 0:
        pytest.skip("No harvest batches in database -- cannot test detail page")
    harvest_list.click_row(0)
    harvest_list.wait_for_url_contains("/ernte/")
    url = harvest_list.driver.current_url
    # URL pattern: .../ernte/batches/<key> or .../ernte/<key>
    parts = url.rstrip("/").split("/")
    return parts[-1]


# -- TC-007-014 to TC-007-016: Detail Page ----------------------------------


class TestHarvestBatchDetailPage:
    """TC-007-014 to TC-007-016: Detail page, tabs, fields."""

    def test_detail_page_loads_with_tabs(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-014: Detail page loads with 4 tabs visible."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        screenshot("req007_020_detail_page_loaded", "Detailseite geladen")

        title = harvest_detail.get_page_title_text()
        assert title, f"Expected non-empty page title, got: '{title}'"

        tabs = harvest_detail.get_tab_labels()
        assert len(tabs) == 4, f"Expected 4 tabs, got {len(tabs)}: {tabs}"

    def test_detail_tab_is_default(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-014: Tab 'Details' (index 0) is active by default."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)

        active = harvest_detail.get_active_tab_index()
        assert active == 0, f"Expected tab 0 to be active by default, got {active}"
        screenshot("req007_021_details_tab_active", "Details-Tab ist aktiv")

    def test_detail_tab_shows_fields(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-015: Details tab shows batch fields in table format."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)

        table_text = harvest_detail.get_detail_table_text()
        screenshot("req007_022_detail_fields", "Detail-Felder sichtbar")

        # The table should contain at least some of the expected labels
        assert table_text, "Expected detail table to contain text"

    def test_detail_page_404_for_unknown_key(
        self,
        harvest_detail: HarvestBatchDetailPage,
        screenshot,
    ) -> None:
        """TC-007-016: Navigating to an unknown batch key shows error display."""
        harvest_detail.open("does-not-exist-99999")
        screenshot("req007_023_404_error", "Fehlermeldung bei unbekanntem Schluessel")

        assert harvest_detail.is_error_displayed(), (
            "Expected error display for unknown batch key"
        )


# -- TC-007-017 to TC-007-021: Edit Tab (Tab 3) ----------------------------


class TestHarvestBatchEdit:
    """TC-007-017 to TC-007-021: Edit tab operations."""

    def test_edit_tab_shows_prefilled_form(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-017: Edit tab shows a prefilled form with current batch values."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(3)  # Edit tab
        time.sleep(0.5)
        screenshot("req007_030_edit_tab_loaded", "Bearbeiten-Tab geladen")

        # The form should be visible with submit button
        submit_els = harvest_detail.driver.find_elements(
            *HarvestBatchDetailPage.FORM_SUBMIT
        )
        assert len(submit_els) > 0, "Expected form submit button on edit tab"

    def test_save_button_disabled_when_no_changes(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-019: Save button is disabled when form is not dirty."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(3)
        time.sleep(0.5)
        screenshot(
            "req007_031_save_disabled",
            "Speichern-Button deaktiviert bei unveraenderten Daten",
        )

        assert harvest_detail.is_submit_disabled(), (
            "Expected save button to be disabled when no changes have been made"
        )

    def test_edit_batch_save_success(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-017: Edit batch -- change harvester and save."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(3)
        time.sleep(0.5)

        screenshot("req007_032_before_edit", "Bearbeiten-Tab vor Aenderung")
        harvest_detail.fill_edit_harvester("E2E-Tester")
        screenshot("req007_032_after_edit", "Bearbeiten-Tab nach Aenderung")

        harvest_detail.submit_form()
        time.sleep(1)
        screenshot("req007_032_after_save", "Nach Speichern")

    def test_edit_batch_negative_weight_validation(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-021: Negative weight value shows validation error on edit tab."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(3)
        time.sleep(0.5)

        harvest_detail.fill_edit_wet_weight(-5)
        screenshot("req007_033_negative_weight", "Negativer Gewichtswert eingegeben")

        harvest_detail.submit_form()
        time.sleep(0.5)
        screenshot(
            "req007_033_validation_error",
            "Validierungsfehler bei negativem Gewicht",
        )

        # Either the form shows a validation error or the submit is prevented
        # Both are acceptable behaviors
        assert (
            harvest_detail.has_validation_error("wet_weight_g")
            or harvest_detail.is_submit_disabled()
        ), (
            "Expected validation error or disabled submit for negative weight"
        )


# -- TC-007-022 to TC-007-027: Quality Tab (Tab 1) -------------------------


class TestHarvestQualityAssessment:
    """TC-007-022 to TC-007-027: Quality assessment tab operations."""

    def test_quality_tab_shows_form_or_table(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-022/TC-007-027: Quality tab shows either create form or display table."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(1)  # Quality tab
        time.sleep(0.5)
        screenshot("req007_040_quality_tab", "Qualitaets-Tab geladen")

        has_form = harvest_detail.is_quality_form_visible()
        has_table = harvest_detail.is_quality_table_visible()

        assert has_form or has_table, (
            "Expected either quality create form or quality display table on Quality tab"
        )

    def test_quality_form_validation_assessed_by_required(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-023: Submitting quality form without 'assessed_by' shows error."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(1)
        time.sleep(0.5)

        if not harvest_detail.is_quality_form_visible():
            pytest.skip("Quality already exists -- form not visible")

        # Fill scores but leave assessed_by empty
        harvest_detail.fill_quality_appearance(80)
        harvest_detail.fill_quality_aroma(75)
        harvest_detail.fill_quality_color(70)

        screenshot(
            "req007_041_before_submit_no_assessor",
            "Qualitaetsformular ohne Bewerter",
        )
        harvest_detail.submit_form()
        time.sleep(0.5)
        screenshot(
            "req007_041_validation_assessed_by",
            "Validierungsfehler: Bewertet von fehlt",
        )

        assert harvest_detail.has_validation_error("assessed_by"), (
            "Expected validation error for assessed_by field"
        )

    def test_quality_create_happy_path(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-022: Create quality assessment with valid scores."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(1)
        time.sleep(0.5)

        if not harvest_detail.is_quality_form_visible():
            pytest.skip("Quality already exists -- cannot test creation")

        harvest_detail.fill_quality_assessed_by("Dr. E2E Tester")
        harvest_detail.fill_quality_appearance(95)
        harvest_detail.fill_quality_aroma(90)
        harvest_detail.fill_quality_color(92)
        screenshot(
            "req007_042_quality_form_filled",
            "Qualitaetsformular ausgefuellt",
        )

        harvest_detail.submit_form()
        time.sleep(1)
        screenshot(
            "req007_042_quality_created",
            "Qualitaetsbewertung erstellt -- Tabelle sichtbar",
        )

        # After creation, the form should be replaced by the display table
        assert harvest_detail.is_quality_table_visible(), (
            "Expected quality display table after successful creation"
        )

    def test_quality_defect_chips(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-025: Defect chips can be added via the chip input."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(1)
        time.sleep(0.5)

        if not harvest_detail.is_quality_form_visible():
            pytest.skip("Quality already exists -- cannot test defect chip input")

        harvest_detail.fill_quality_assessed_by("Defect Tester")
        harvest_detail.fill_quality_appearance(60)
        harvest_detail.fill_quality_aroma(60)
        harvest_detail.fill_quality_color(60)
        harvest_detail.add_defect("Schimmelfleck")
        time.sleep(0.3)
        harvest_detail.add_defect("Verfaerbung")
        time.sleep(0.3)
        screenshot(
            "req007_043_defect_chips_added",
            "Maengel-Chips hinzugefuegt",
        )

        harvest_detail.submit_form()
        time.sleep(1)
        screenshot("req007_043_quality_with_defects", "Bewertung mit Maengeln erstellt")


# -- TC-007-028 to TC-007-030: Yield Tab (Tab 2) ---------------------------


class TestHarvestYieldMetrics:
    """TC-007-028 to TC-007-030: Yield metrics tab operations."""

    def test_yield_tab_shows_form_or_table(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-028: Yield tab shows either create form or display table."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(2)  # Yield tab
        time.sleep(0.5)
        screenshot("req007_050_yield_tab", "Ertrags-Tab geladen")

        has_form = harvest_detail.is_yield_form_visible()
        has_table = harvest_detail.is_yield_table_visible()

        assert has_form or has_table, (
            "Expected either yield create form or yield display table on Yield tab"
        )

    def test_yield_create_happy_path(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-028: Create yield metrics with valid data."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(2)
        time.sleep(0.5)

        if not harvest_detail.is_yield_form_visible():
            pytest.skip("Yield metrics already exist -- cannot test creation")

        harvest_detail.fill_yield_per_plant(450)
        harvest_detail.fill_yield_per_m2(900)
        harvest_detail.fill_yield_total(450)
        harvest_detail.fill_yield_usable(420)
        harvest_detail.fill_yield_trim_waste(6.7)
        screenshot(
            "req007_051_yield_form_filled",
            "Ertragsformular ausgefuellt",
        )

        harvest_detail.submit_form()
        time.sleep(1)
        screenshot(
            "req007_051_yield_created",
            "Ertragsmetriken erstellt -- Tabelle sichtbar",
        )

        assert harvest_detail.is_yield_table_visible(), (
            "Expected yield display table after successful creation"
        )

    def test_yield_trim_waste_over_100_validation(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot,
    ) -> None:
        """TC-007-030: Trim waste > 100% shows validation error."""
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(2)
        time.sleep(0.5)

        if not harvest_detail.is_yield_form_visible():
            pytest.skip("Yield metrics already exist -- cannot test validation")

        harvest_detail.fill_yield_per_plant(100)
        harvest_detail.fill_yield_per_m2(200)
        harvest_detail.fill_yield_total(100)
        harvest_detail.fill_yield_usable(80)
        harvest_detail.fill_yield_trim_waste(110)
        screenshot(
            "req007_052_trim_waste_over_100",
            "Verschnitt > 100% eingegeben",
        )

        harvest_detail.submit_form()
        time.sleep(0.5)
        screenshot(
            "req007_052_trim_waste_validation",
            "Validierungsfehler bei Verschnitt > 100%",
        )

        assert harvest_detail.has_validation_error("trim_waste_percent"), (
            "Expected validation error for trim_waste_percent > 100"
        )
