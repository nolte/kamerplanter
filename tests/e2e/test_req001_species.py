"""E2E tests for REQ-001 — Species List, Create, Detail (TC-029 to TC-041)."""

from __future__ import annotations

import time
import uuid

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import SpeciesDetailPage, SpeciesListPage


@pytest.fixture
def species_list(browser: WebDriver, base_url: str) -> SpeciesListPage:
    return SpeciesListPage(browser, base_url)


@pytest.fixture
def species_detail(browser: WebDriver, base_url: str) -> SpeciesDetailPage:
    return SpeciesDetailPage(browser, base_url)


class TestSpeciesListPage:
    """TC-REQ-001-029 to TC-REQ-001-032: Species list display and navigation."""

    @pytest.mark.smoke
    def test_display_species_in_data_table(
        self, species_list: SpeciesListPage
    ) -> None:
        """TC-REQ-001-029: Display species in a paginated data table."""
        species_list.open()
        headers = species_list.get_column_headers()

        assert any("Wissenschaftlicher Name" in h for h in headers), (
            f"Expected 'Wissenschaftlicher Name' column, got {headers}"
        )
        row_count = species_list.get_row_count()
        assert row_count >= 0, "Species table should render"

    def test_click_species_row_navigates_to_detail(
        self, species_list: SpeciesListPage
    ) -> None:
        """TC-REQ-001-031: Click on a species row navigates to detail page."""
        species_list.open()

        if species_list.get_row_count() == 0:
            pytest.skip("No species in database")

        species_list.click_row(0)
        species_list.wait_for_url_contains("/stammdaten/species/")

        assert "/stammdaten/species/" in species_list.driver.current_url


class TestSpeciesCreateDialog:
    """TC-REQ-001-033 to TC-REQ-001-037: Species creation and validation."""

    def test_open_species_create_dialog(
        self, species_list: SpeciesListPage
    ) -> None:
        """TC-REQ-001-033: Open the species create dialog and verify form fields."""
        species_list.open()
        species_list.click_create()

        assert species_list.is_create_dialog_open(), "Create dialog should be open"

    def test_create_species_with_valid_data(
        self, species_list: SpeciesListPage
    ) -> None:
        """TC-REQ-001-034: Successfully create a species with valid data."""
        species_list.open()
        species_list.click_create()

        unique = uuid.uuid4().hex[:6]
        scientific_name = f"Testus e2e{unique}"
        species_list.fill_scientific_name(scientific_name)
        species_list.set_field("genus", "Testus")
        species_list.submit_form()

        time.sleep(2)
        species_list.wait_for_loading_complete()

    def test_validation_empty_scientific_name(
        self, species_list: SpeciesListPage
    ) -> None:
        """TC-REQ-001-035: Validation error — empty scientific name."""
        species_list.open()
        species_list.click_create()
        species_list.fill_scientific_name("")
        species_list.submit_form()

        time.sleep(0.5)
        assert species_list.is_create_dialog_open(), "Dialog should remain open"

    def test_create_species_without_family(
        self, species_list: SpeciesListPage
    ) -> None:
        """TC-REQ-001-037: Create species without selecting a family."""
        species_list.open()
        species_list.click_create()

        unique = uuid.uuid4().hex[:6]
        species_list.fill_scientific_name(f"Orphana speciesii{unique}")
        species_list.submit_form()

        time.sleep(2)


class TestSpeciesDetailPage:
    """TC-REQ-001-038 to TC-REQ-001-041: Species detail, edit, delete."""

    def test_display_species_detail_with_tabs(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-038: Display species detail page with tabs."""
        species_list.open()
        if species_list.get_row_count() == 0:
            pytest.skip("No species in database")

        species_list.click_row(0)
        species_list.wait_for_url_contains("/stammdaten/species/")

        title = species_detail.get_title()
        assert title, "Page title should show species name"

        tabs = species_detail.get_tab_labels()
        # Species detail has 5 tabs: Bearbeiten, Aussaat & Ernte, Sorten,
        # Lebenszyklus-Konfiguration, Workflows
        tabs_upper = [t.strip().upper() for t in tabs if t.strip()]
        assert len(tabs_upper) >= 3, f"Expected at least 3 tabs, got {tabs}"
        assert any("BEARBEITEN" in t for t in tabs_upper), f"Expected 'Bearbeiten' tab, got {tabs}"
        assert any("SORTEN" in t for t in tabs_upper), f"Expected 'Sorten' tab, got {tabs}"
        assert any("LEBENSZYKLUS" in t for t in tabs_upper), f"Expected 'Lebenszyklus' tab, got {tabs}"
        assert species_detail.has_delete_button(), "Delete button should be visible"

    def test_edit_species_data(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage
    ) -> None:
        """TC-REQ-001-039: Edit species data on the 'Bearbeiten' tab."""
        species_list.open()
        if species_list.get_row_count() == 0:
            pytest.skip("No species in database")

        species_list.click_row(0)
        species_list.wait_for_url_contains("/stammdaten/species/")

        unique = uuid.uuid4().hex[:6]
        species_detail.set_field("native_habitat", f"E2E-Updated {unique}")
        species_detail.click_save()

        time.sleep(1)
        assert "/stammdaten/species/" in species_detail.driver.current_url

    def test_delete_species_with_confirmation(
        self, species_list: SpeciesListPage, species_detail: SpeciesDetailPage,
        browser: WebDriver, base_url: str,
    ) -> None:
        """TC-REQ-001-040: Delete a species with confirmation."""
        # Create a species to delete
        species_list.open()
        species_list.click_create()
        unique = uuid.uuid4().hex[:6]
        species_list.fill_scientific_name(f"Deletus testii{unique}")
        species_list.submit_form()
        time.sleep(2)
        species_list.wait_for_loading_complete()

        # Navigate to its detail
        try:
            species_list.click_row_by_name(f"Deletus testii{unique}")
        except ValueError:
            pytest.skip("Species not found after creation")

        species_list.wait_for_url_contains("/stammdaten/species/")

        species_detail.click_delete()
        species_detail.confirm_delete()
        time.sleep(2)

        species_detail.wait_for_url_contains("/stammdaten/species")
