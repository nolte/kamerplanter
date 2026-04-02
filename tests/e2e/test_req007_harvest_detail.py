"""E2E tests for REQ-007 — Erntemanagement: Detail, Edit, Quality, Yield.

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-007.md):
  TC-REQ-007-001  ->  TC-007-014  Detailseite laden (Happy Path) -- Tabs sichtbar
  TC-REQ-007-002  ->  TC-007-014  Tab 'Details' ist standardmaessig aktiv
  TC-REQ-007-003  ->  TC-007-015  Details-Tab zeigt Batch-Felder
  TC-REQ-007-004  ->  TC-007-016  Navigieren zu unbekanntem Schluessel zeigt Fehlermeldung
  TC-REQ-007-005  ->  TC-007-017  Bearbeiten-Tab zeigt vorbefuelltes Formular
  TC-REQ-007-006  ->  TC-007-019  Speichern-Button deaktiviert bei unveraenderten Daten
  TC-REQ-007-007  ->  TC-007-017  Batch bearbeiten -- Erntehelfer aendern und speichern
  TC-REQ-007-008  ->  TC-007-021  Negativer Gewichtswert zeigt Validierungsfehler
  TC-REQ-007-009  ->  TC-007-022  Qualitaets-Tab zeigt Formular oder Tabelle
  TC-REQ-007-010  ->  TC-007-023  Qualitaetsformular ohne Bewerter zeigt Validierungsfehler
  TC-REQ-007-011  ->  TC-007-022  Qualitaetsbewertung erstellen (Happy Path)
  TC-REQ-007-012  ->  TC-007-025  Maengel-Chips hinzufuegen
  TC-REQ-007-013  ->  TC-007-028  Ertrags-Tab zeigt Formular oder Tabelle
  TC-REQ-007-014  ->  TC-007-028  Ertragsmetriken erstellen (Happy Path)
  TC-REQ-007-015  ->  TC-007-030  Verschnitt > 100% zeigt Validierungsfehler
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import time  # kept for MUI animation waits

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
    """Harvest batch detail page, tabs, fields (Spec: TC-007-014, TC-007-015, TC-007-016)."""

    @pytest.mark.smoke
    def test_detail_page_loads_with_tabs(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-001: Detail page loads with 4 tabs visible.

        Spec: TC-007-014 -- Detailseite laden (Happy Path).
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        screenshot(
            "TC-REQ-007-001_detail-page-loaded",
            "Harvest batch detail page after initial load",
        )

        title = harvest_detail.get_page_title_text()
        assert title, (
            f"TC-REQ-007-001 FAIL: Expected non-empty page title, got: '{title}'"
        )

        tabs = harvest_detail.get_tab_labels()
        assert len(tabs) == 4, (
            f"TC-REQ-007-001 FAIL: Expected 4 tabs, got {len(tabs)}: {tabs}"
        )

    @pytest.mark.smoke
    def test_detail_tab_is_default(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-002: Tab 'Details' (index 0) is active by default.

        Spec: TC-007-014 -- Detailseite laden -- Tab 'Details' standardmaessig aktiv.
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)

        active = harvest_detail.get_active_tab_index()
        assert active == 0, (
            f"TC-REQ-007-002 FAIL: Expected tab 0 to be active by default, got {active}"
        )
        screenshot(
            "TC-REQ-007-002_details-tab-active",
            "Details tab is active by default",
        )

    @pytest.mark.core_crud
    def test_detail_tab_shows_fields(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-003: Details tab shows batch fields in table format.

        Spec: TC-007-015 -- Details-Tab zeigt Batch-Felder.
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)

        table_text = harvest_detail.get_detail_table_text()
        screenshot(
            "TC-REQ-007-003_detail-fields",
            "Detail tab showing batch fields in table format",
        )

        # The table should contain at least some of the expected labels
        assert table_text, (
            "TC-REQ-007-003 FAIL: Expected detail table to contain text"
        )

    @pytest.mark.core_crud
    def test_detail_page_404_for_unknown_key(
        self,
        harvest_detail: HarvestBatchDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-004: Navigating to unknown batch key shows error display.

        Spec: TC-007-016 -- Nicht gefunden (404).
        """
        harvest_detail.open("does-not-exist-99999")
        screenshot(
            "TC-REQ-007-004_404-error",
            "Error display for unknown batch key",
        )

        assert harvest_detail.is_error_displayed(), (
            "TC-REQ-007-004 FAIL: Expected error display for unknown batch key"
        )


# -- TC-007-017 to TC-007-021: Edit Tab (Tab 3) ----------------------------


class TestHarvestBatchEdit:
    """Edit tab operations (Spec: TC-007-017, TC-007-019, TC-007-021)."""

    @pytest.mark.core_crud
    def test_edit_tab_shows_prefilled_form(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-005: Edit tab shows a prefilled form with current batch values.

        Spec: TC-007-017 -- Batch bearbeiten -- Erntetyp und Qualitaetsstufe aendern.
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(3)  # Edit tab
        harvest_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-007-005_edit-tab-loaded",
            "Edit tab loaded with prefilled form",
        )

        # The form should be visible with submit button
        assert harvest_detail.is_form_submit_visible(), (
            "TC-REQ-007-005 FAIL: Expected form submit button on edit tab"
        )

    @pytest.mark.core_crud
    def test_save_button_disabled_when_no_changes(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-006: Save button is disabled when form is not dirty.

        Spec: TC-007-019 -- 'Speichern'-Button inaktiv bei unveraenderten Daten.
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(3)
        harvest_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-007-006_save-disabled",
            "Save button disabled when no changes made",
        )

        assert harvest_detail.is_submit_disabled(), (
            "TC-REQ-007-006 FAIL: Expected save button to be disabled when "
            "no changes have been made"
        )

    @pytest.mark.core_crud
    def test_edit_batch_save_success(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-007: Edit batch -- change harvester and save.

        Spec: TC-007-017 -- Batch bearbeiten -- Erntetyp und Qualitaetsstufe aendern.
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(3)
        harvest_detail.wait_for_loading_complete()

        screenshot(
            "TC-REQ-007-007_before-edit",
            "Edit tab before changing harvester",
        )
        harvest_detail.fill_edit_harvester("E2E-Tester")
        screenshot(
            "TC-REQ-007-007_after-edit",
            "Edit tab after changing harvester to 'E2E-Tester'",
        )

        harvest_detail.submit_form()
        harvest_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-007-007_after-save",
            "Detail page after saving edited batch",
        )

    @pytest.mark.core_crud
    def test_edit_batch_negative_weight_validation(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-008: Negative weight value shows validation error on edit tab.

        Spec: TC-007-021 -- Negativer Gewichtswert (Validierung).
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(3)
        harvest_detail.wait_for_loading_complete()

        harvest_detail.fill_edit_wet_weight(-5)
        screenshot(
            "TC-REQ-007-008_negative-weight",
            "Negative weight value entered in edit form",
        )

        harvest_detail.submit_form()
        harvest_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-007-008_validation-error",
            "Validation error for negative weight value",
        )

        # Either the form shows a validation error or the submit is prevented
        # Both are acceptable behaviors
        assert (
            harvest_detail.has_validation_error("wet_weight_g")
            or harvest_detail.is_submit_disabled()
        ), (
            "TC-REQ-007-008 FAIL: Expected validation error or disabled submit "
            "for negative weight"
        )


# -- TC-007-022 to TC-007-027: Quality Tab (Tab 1) -------------------------


class TestHarvestQualityAssessment:
    """Quality assessment tab operations (Spec: TC-007-022, TC-007-023, TC-007-025, TC-007-027)."""

    @pytest.mark.core_crud
    def test_quality_tab_shows_form_or_table(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-009: Quality tab shows either create form or display table.

        Spec: TC-007-022 / TC-007-027 -- Qualitaets-Tab Formular oder Anzeige.
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(1)  # Quality tab
        harvest_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-007-009_quality-tab",
            "Quality tab loaded showing form or display table",
        )

        has_form = harvest_detail.is_quality_form_visible()
        has_table = harvest_detail.is_quality_table_visible()

        assert has_form or has_table, (
            "TC-REQ-007-009 FAIL: Expected either quality create form or "
            "quality display table on Quality tab"
        )

    @pytest.mark.core_crud
    def test_quality_form_validation_assessed_by_required(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-010: Submitting quality form without 'assessed_by' shows error.

        Spec: TC-007-023 -- Pflichtfeld 'Bewertet von' fehlt.
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(1)
        harvest_detail.wait_for_loading_complete()

        if not harvest_detail.is_quality_form_visible():
            pytest.skip("Quality already exists -- form not visible")

        # Fill scores but leave assessed_by empty
        harvest_detail.fill_quality_appearance(80)
        harvest_detail.fill_quality_aroma(75)
        harvest_detail.fill_quality_color(70)

        screenshot(
            "TC-REQ-007-010_before-submit-no-assessor",
            "Quality form filled without assessed_by",
        )
        harvest_detail.submit_form()
        harvest_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-007-010_validation-assessed-by",
            "Validation error: assessed_by field required",
        )

        assert harvest_detail.has_validation_error("assessed_by"), (
            "TC-REQ-007-010 FAIL: Expected validation error for assessed_by field"
        )

    @pytest.mark.core_crud
    def test_quality_create_happy_path(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-011: Create quality assessment with valid scores.

        Spec: TC-007-022 -- Qualitaetsbewertung erstellen (Happy Path).
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(1)
        harvest_detail.wait_for_loading_complete()

        if not harvest_detail.is_quality_form_visible():
            pytest.skip("Quality already exists -- cannot test creation")

        harvest_detail.fill_quality_assessed_by("Dr. E2E Tester")
        harvest_detail.fill_quality_appearance(95)
        harvest_detail.fill_quality_aroma(90)
        harvest_detail.fill_quality_color(92)
        screenshot(
            "TC-REQ-007-011_quality-form-filled",
            "Quality form filled with valid scores",
        )

        harvest_detail.submit_form()
        harvest_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-007-011_quality-created",
            "Quality assessment created -- display table visible",
        )

        # After creation, the form should be replaced by the display table
        assert harvest_detail.is_quality_table_visible(), (
            "TC-REQ-007-011 FAIL: Expected quality display table after "
            "successful creation"
        )

    @pytest.mark.core_crud
    def test_quality_defect_chips(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-012: Defect chips can be added via the chip input.

        Spec: TC-007-025 -- Maengel als Chips hinzufuegen.
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(1)
        harvest_detail.wait_for_loading_complete()

        if not harvest_detail.is_quality_form_visible():
            pytest.skip("Quality already exists -- cannot test defect chip input")

        harvest_detail.fill_quality_assessed_by("Defect Tester")
        harvest_detail.fill_quality_appearance(60)
        harvest_detail.fill_quality_aroma(60)
        harvest_detail.fill_quality_color(60)
        harvest_detail.add_defect("Schimmelfleck")
        time.sleep(0.3)  # MUI animation
        harvest_detail.add_defect("Verfaerbung")
        time.sleep(0.3)  # MUI animation
        screenshot(
            "TC-REQ-007-012_defect-chips-added",
            "Quality form with defect chips added",
        )

        harvest_detail.submit_form()
        harvest_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-007-012_quality-with-defects",
            "Quality assessment created with defect chips",
        )


# -- TC-007-028 to TC-007-030: Yield Tab (Tab 2) ---------------------------


class TestHarvestYieldMetrics:
    """Yield metrics tab operations (Spec: TC-007-028, TC-007-030)."""

    @pytest.mark.core_crud
    def test_yield_tab_shows_form_or_table(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-013: Yield tab shows either create form or display table.

        Spec: TC-007-028 -- Ertrags-Tab zeigt Formular oder Tabelle.
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(2)  # Yield tab
        harvest_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-007-013_yield-tab",
            "Yield tab loaded showing form or display table",
        )

        has_form = harvest_detail.is_yield_form_visible()
        has_table = harvest_detail.is_yield_table_visible()

        assert has_form or has_table, (
            "TC-REQ-007-013 FAIL: Expected either yield create form or "
            "yield display table on Yield tab"
        )

    @pytest.mark.core_crud
    def test_yield_create_happy_path(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-014: Create yield metrics with valid data.

        Spec: TC-007-028 -- Ertragsmetriken erstellen (Happy Path).
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(2)
        harvest_detail.wait_for_loading_complete()

        if not harvest_detail.is_yield_form_visible():
            pytest.skip("Yield metrics already exist -- cannot test creation")

        harvest_detail.fill_yield_per_plant(450)
        harvest_detail.fill_yield_per_m2(900)
        harvest_detail.fill_yield_total(450)
        harvest_detail.fill_yield_usable(420)
        harvest_detail.fill_yield_trim_waste(6.7)
        screenshot(
            "TC-REQ-007-014_yield-form-filled",
            "Yield form filled with valid metric data",
        )

        harvest_detail.submit_form()
        harvest_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-007-014_yield-created",
            "Yield metrics created -- display table visible",
        )

        assert harvest_detail.is_yield_table_visible(), (
            "TC-REQ-007-014 FAIL: Expected yield display table after "
            "successful creation"
        )

    @pytest.mark.core_crud
    def test_yield_trim_waste_over_100_validation(
        self,
        harvest_detail: HarvestBatchDetailPage,
        harvest_list: HarvestBatchListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-007-015: Trim waste > 100% shows validation error.

        Spec: TC-007-030 -- Verschnitt > 100% zeigt Validierungsfehler.
        """
        key = _get_first_batch_key(harvest_list)
        harvest_detail.open_and_wait(key)
        harvest_detail.click_tab(2)
        harvest_detail.wait_for_loading_complete()

        if not harvest_detail.is_yield_form_visible():
            pytest.skip("Yield metrics already exist -- cannot test validation")

        harvest_detail.fill_yield_per_plant(100)
        harvest_detail.fill_yield_per_m2(200)
        harvest_detail.fill_yield_total(100)
        harvest_detail.fill_yield_usable(80)
        harvest_detail.fill_yield_trim_waste(110)
        screenshot(
            "TC-REQ-007-015_trim-waste-over-100",
            "Trim waste > 100% entered in yield form",
        )

        harvest_detail.submit_form()
        harvest_detail.wait_for_loading_complete()
        screenshot(
            "TC-REQ-007-015_trim-waste-validation",
            "Validation error for trim waste > 100%",
        )

        assert harvest_detail.has_validation_error("trim_waste_percent"), (
            "TC-REQ-007-015 FAIL: Expected validation error for "
            "trim_waste_percent > 100"
        )
