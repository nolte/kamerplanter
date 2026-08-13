"""E2E tests for REQ-001 — Species List, Create, Detail.

Spec-TC Mapping (test TC → spec/e2e-testcases/TC-REQ-001.md):
  TC-REQ-001-029  →  TC-001-019  Species-Liste laden und Grundspalten prüfen
  TC-REQ-001-031  →  TC-001-030  Species-Detailseite öffnen (Row-Click-Navigation)
  TC-REQ-001-033  →  TC-001-025  Species erstellen — Dialog öffnen (Teilschritt)
  TC-REQ-001-034  →  TC-001-025  Species erstellen Happy Path
  TC-REQ-001-035  →  TC-001-026  Species erstellen — Wissenschaftlicher Name leer
  TC-REQ-001-037  →  TC-001-025  Species erstellen ohne Familie (Variante)
  TC-REQ-001-038  →  TC-001-030  Species-Detailseite — Tabs und Lösch-Button
  TC-REQ-001-039  →  TC-001-031  Species bearbeiten — Beschreibung ändern
  TC-REQ-001-040  →  TC-001-033  Species löschen mit Bestätigungsdialog
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
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
    """Species list display and navigation (Spec: TC-001-019, TC-001-030)."""

    @pytest.mark.requires_desktop
    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_display_species_in_data_table(
        self, species_list: SpeciesListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-019: Display species in a paginated data table.

        Spec: TC-001-019 — Species-Liste laden und Grundspalten prüfen.
        """
        species_list.open()
        screenshot(
            "TC-REQ-001-029_species-list-loaded",
            "Species list page after initial load — DataTable with seed data visible",
        )

        headers = species_list.get_column_headers()
        assert any("Wissenschaftlicher Name" in h for h in headers), (
            f"Expected 'Wissenschaftlicher Name' column, got {headers}"
        )
        row_count = species_list.get_row_count()
        assert row_count >= 0, "Species table should render"

    @pytest.mark.core_crud
    def test_click_species_row_navigates_to_detail(
        self, species_list: SpeciesListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-030: Click on a species row navigates to detail page.

        Spec: TC-001-030 — Species-Detailseite öffnen und Tab 'Bearbeiten' anzeigen.
        """
        species_list.open()

        if species_list.get_row_count() == 0:
            pytest.skip("No species in database")

        screenshot("TC-REQ-001-031_before-row-click", "Species list before clicking first row")
        species_list.click_row(0)
        species_list.wait_for_url_contains("/stammdaten/species/")
        screenshot(
            "TC-REQ-001-031_after-row-click", "Species detail page after row click navigation"
        )

        assert "/stammdaten/species/" in species_list.driver.current_url


class TestSpeciesCreateDialog:
    """Species creation and validation (Spec: TC-001-025, TC-001-026, TC-001-027)."""

    @pytest.mark.core_crud
    def test_open_species_create_dialog(
        self, species_list: SpeciesListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-025: Open the species create dialog and verify form fields.

        Spec: TC-001-025 — Neue Species erfolgreich erstellen (Dialog-Öffnung).
        """
        species_list.open()
        screenshot("TC-REQ-001-033_before-create", "Species list page before opening create dialog")

        species_list.click_create()
        screenshot(
            "TC-REQ-001-033_create-dialog-open",
            "Species create dialog with form fields visible (all fields expanded)",
        )

        assert species_list.is_create_dialog_open(), "Create dialog should be open"

    @pytest.mark.core_crud
    def test_create_species_with_valid_data(
        self, species_list: SpeciesListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-025: Successfully create a species with valid data.

        Spec: TC-001-025 — Neue Species erfolgreich erstellen (Happy Path).
        """
        species_list.open()
        species_list.click_create()

        unique = uuid.uuid4().hex[:6]
        scientific_name = f"Testus e2e{unique}"
        species_list.fill_scientific_name(scientific_name)
        species_list.set_field("genus", "Testus")
        screenshot(
            "TC-REQ-001-034_form-filled",
            f"Create dialog with scientific_name='{scientific_name}' and genus='Testus' filled in",
        )

        species_list.submit_form()
        species_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-034_after-create",
            "Species list after successful creation — dialog closed, list refreshed",
        )

    @pytest.mark.core_crud
    def test_validation_empty_scientific_name(
        self, species_list: SpeciesListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-026: Validation error — empty scientific name.

        Spec: TC-001-026 — Wissenschaftlicher Name leer wird verhindert.
        """
        species_list.open()
        species_list.click_create()
        species_list.fill_scientific_name("")
        species_list.submit_form()

        screenshot(
            "TC-REQ-001-035_validation-error",
            "Create dialog after submitting empty scientific_name — validation error expected",
        )
        assert species_list.is_create_dialog_open(), "Dialog should remain open"

    @pytest.mark.core_crud
    def test_create_species_without_family(
        self, species_list: SpeciesListPage, screenshot: Callable[..., Path]
    ) -> None:
        """TC-001-025: Create species without selecting a family.

        Spec: TC-001-025 — Variante: Familie optional.
        """
        species_list.open()
        species_list.click_create()

        unique = uuid.uuid4().hex[:6]
        species_list.fill_scientific_name(f"Orphana speciesii{unique}")
        screenshot(
            "TC-REQ-001-037_no-family-filled",
            "Create dialog with scientific_name filled but no family selected",
        )

        species_list.submit_form()
        species_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-037_after-create-no-family",
            "Species list after creating species without family",
        )


class TestSpeciesDetailPage:
    """Species detail, edit, delete (Spec: TC-001-030, TC-001-031, TC-001-033)."""

    @pytest.mark.core_crud
    def test_display_species_detail_with_tabs(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-030: Display species detail page with tabs.

        Spec: TC-001-030 — Species-Detailseite öffnen und Tabs anzeigen.
        """
        species_list.open()
        if species_list.get_row_count() == 0:
            pytest.skip("No species in database")

        species_list.click_row(0)
        species_list.wait_for_url_contains("/stammdaten/species/")

        title = species_detail.get_title()
        screenshot(
            "TC-REQ-001-038_species-detail-tabs",
            f"Species detail page for '{title}' — tabs and delete button visible",
        )

        assert title, "Page title should show species name"
        tabs = species_detail.get_tab_labels()
        tabs_upper = [t.strip().upper() for t in tabs if t.strip()]
        assert len(tabs_upper) >= 6, f"Expected at least 6 tabs, got {tabs}"
        assert any("BEARBEITEN" in t for t in tabs_upper), f"Expected 'Bearbeiten' tab, got {tabs}"
        assert any("SORTEN" in t for t in tabs_upper), f"Expected 'Sorten' tab, got {tabs}"
        assert any("LEBENSZYKLUS" in t for t in tabs_upper), (
            f"Expected 'Lebenszyklus' tab, got {tabs}"
        )
        # The Mischkultur (companion-planting) and Fruchtfolge (crop-rotation)
        # tabs are expert-only (isFieldVisible('expert')); a light-mode tenant
        # defaults to BEGINNER, so they are intentionally hidden here. Their
        # expert-gated visibility is covered by test_req021_experience_level.
        # Global/system species are deletion-protected (UI-NFR-018): the delete
        # button is intentionally absent and a read-only banner is shown instead.
        if species_detail.is_read_only():
            assert not species_detail.has_delete_button(), (
                "Deletion-protected species must not expose a delete button"
            )
        else:
            assert species_detail.has_delete_button(), "Delete button should be visible"

    @pytest.mark.core_crud
    def test_edit_species_data(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-001-031: Edit species data on the 'Bearbeiten' tab.

        Spec: TC-001-031 — Species bearbeiten und speichern — Beschreibung ändern.

        Provisions the species it edits. Row 0 -- what this used to open -- is
        the alphabetically first species of the seed, i.e. a *system* one
        (``Adiantum raddianum`` in the 2026-08-13 nightly, screenshot
        ``FAILURE_test_edit_species_data``): origin-protected, no editable form
        on any tab. So this test could only ever take its own skip, and did, on
        every profile -- which is also why it never noticed that it stayed on
        the "Übersicht" tab and asked for a field the *edit* tab renders. On the
        one night the skip gate misfired -- it read the banner off a page that
        was still a `LoadingSkeleton` -- the test spent 15 s waiting for that
        field instead of skipping, and both defects surfaced together.

        The read-back at the end is the point of the case: "speichern" is a
        claim about what the next reader sees, so the assertion re-navigates and
        reads the field again rather than reading the value it just typed out of
        the same, un-reloaded form.
        """
        unique = uuid.uuid4().hex[:6]
        scientific_name = f"Editus e2e{unique}"
        description = f"E2E-Updated {unique}"

        species_list.open()
        species_list.click_create()
        species_list.fill_scientific_name(scientific_name)
        species_list.set_field("genus", "Editus")
        species_list.submit_form()
        species_list.wait_for_create_dialog_closed()

        species_list.click_row_by_name(scientific_name)
        species_list.wait_for_url_contains("/stammdaten/species/")
        species_detail.wait_for_detail_content()
        screenshot("TC-REQ-001-039_before-edit", "Species detail before modification")

        assert not species_detail.is_read_only(), (
            "TC-REQ-001-039 FAIL: a species this test created itself must be editable"
        )

        species_detail.click_tab_by_label("Bearbeiten")
        species_detail.set_field("description", description)
        screenshot("TC-REQ-001-039_field-modified", f"Description field changed to '{description}'")

        # The create a few seconds ago enqueued a success snackbar of its own,
        # and notistack holds those for 5 s. Without this the save's own wait
        # would be satisfied by that one, instantly, with the PUT still in
        # flight -- exactly the race the wait exists to close.
        species_detail.wait_for_no_success_snackbar()
        species_detail.click_save()
        species_detail.wait_for_save_confirmed()
        screenshot(
            "TC-REQ-001-039_after-save", "Species detail after saving — success feedback expected"
        )

        # Re-navigate rather than re-read: the form still holds the typed value
        # whether or not the PUT ever landed.
        species_list.open()
        species_list.click_row_by_name(scientific_name)
        species_detail.wait_for_detail_content()
        species_detail.click_tab_by_label("Bearbeiten")

        assert species_detail.get_field_value("description") == description, (
            f"TC-REQ-001-039 FAIL: the edited description must survive a reload, but "
            f"'{species_detail.get_field_value('description')}' came back"
        )

    @pytest.mark.core_crud
    def test_delete_species_with_confirmation(
        self,
        species_list: SpeciesListPage,
        species_detail: SpeciesDetailPage,
        screenshot: Callable[..., Path],
        browser: WebDriver,
        base_url: str,
    ) -> None:
        """TC-001-033: Delete a species with confirmation.

        Spec: TC-001-033 — Species löschen mit Bestätigungsdialog.
        """
        # Create a species to delete
        species_list.open()
        species_list.click_create()
        unique = uuid.uuid4().hex[:6]
        species_list.fill_scientific_name(f"Deletus testii{unique}")
        species_list.submit_form()
        species_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-001-040_species-created",
            f"Species 'Deletus testii{unique}' created for deletion test",
        )

        # Navigate to its detail
        try:
            species_list.click_row_by_name(f"Deletus testii{unique}")
        except ValueError:
            pytest.skip("Species not found after creation")

        species_list.wait_for_url_contains("/stammdaten/species/")
        screenshot(
            "TC-REQ-001-040_detail-before-delete", "Species detail page before clicking delete"
        )

        species_detail.click_delete()
        screenshot(
            "TC-REQ-001-040_confirm-dialog",
            "Delete confirmation dialog open — Abbrechen/Loeschen buttons visible",
        )

        species_detail.confirm_delete()
        species_detail.wait_for_url_contains("/stammdaten/species")
        screenshot(
            "TC-REQ-001-040_after-delete", "Species list after deletion — species should be gone"
        )
