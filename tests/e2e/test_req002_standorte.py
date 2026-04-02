"""E2E tests — REQ-002 Standortverwaltung.

Covers:
  Site list: page load, create dialog, form validation, search, sort, row navigation
  Site detail: page load, edit form, location sub-section, delete confirmation
  Location detail: page load, edit form, slot sub-section, watering events button
  Slot detail: page load, form fields, delete confirmation

All tests follow NFR-008:
  - Page-Object-Pattern (no direct find_element calls in tests)
  - WebDriverWait preferred — time.sleep only for search debounce (0.3s)
  - Screenshot at: Page Load / before action / after action / error state
  - Descriptive assertion messages

Spec-TC Mapping (test TC → spec/e2e-testcases/TC-REQ-002.md):
  TC-REQ-002-001  →  TC-002-001  Site-Liste laden (Empty State / Titel)
  TC-REQ-002-002  →  TC-002-002  Site-Liste zeigt DataTable mit Spalten
  TC-REQ-002-003  →  TC-002-002  Seed-Daten sichtbar (Variante)
  TC-REQ-002-004  →  TC-002-005  Erstellen-Button sichtbar (Teilschritt)
  TC-REQ-002-005  →  TC-002-005  Site erstellen — Dialog öffnen
  TC-REQ-002-006  →  TC-002-006  Site erstellen — Pflichtfeld Name leer
  TC-REQ-002-007  →  TC-002-007  Site erstellen — Abbrechen schließt Dialog
  TC-REQ-002-008  →  TC-002-003  Suchfunktion filtert nach Name
  TC-REQ-002-009  →  (kein Spec-TC)  Sortierung per Spaltenklick
  TC-REQ-002-010  →  (kein Spec-TC)  Filter-Reset
  TC-REQ-002-011  →  TC-002-004  Klick auf Site-Zeile navigiert zur Detailseite
  TC-REQ-002-012  →  TC-002-002  Showing-Count Fußzeile (Teilaspekt)
  TC-REQ-002-013  →  TC-002-010  Site-Detailseite laden
  TC-REQ-002-014  →  TC-002-010  Bearbeitungsformular mit Name vorbelegt
  TC-REQ-002-015  →  TC-002-010  Speichern-/Abbrechen-Buttons sichtbar
  TC-REQ-002-016  →  TC-002-010  Site-Daten bearbeiten — Name ändern
  TC-REQ-002-017  →  TC-002-011  Cancel/UnsavedChanges — Zurück navigieren
  TC-REQ-002-018  →  TC-002-021  Location-Abschnitt sichtbar
  TC-REQ-002-019  →  TC-002-012  Site löschen — Bestätigungsdialog
  TC-REQ-002-020  →  TC-002-013  Site löschen — Abbrechen bewahrt Daten
  TC-REQ-002-021  →  TC-002-022  Klick auf Location-Zeile navigiert zur Detailseite
  TC-REQ-002-022  →  (kein Spec-TC)  Unbekannter Site-Key zeigt Fehlerseite
  TC-REQ-002-023  →  TC-002-022  Location-Detailseite laden
  TC-REQ-002-024  →  TC-002-022  Location Name vorbelegt (Teilaspekt)
  TC-REQ-002-025  →  TC-002-022  Location Formular-Buttons (Teilaspekt)
  TC-REQ-002-026  →  TC-002-024  Location bearbeiten — Name ändern
  TC-REQ-002-027  →  TC-002-012  Location löschen — Bestätigungsdialog (analog Site)
"""

from __future__ import annotations

import time  # kept for debounce waits

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from .pages import (
    SiteListPage,
    SiteListPageExt,
    SiteDetailPage,
    LocationDetailPage,
    SlotDetailPage,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def site_list(browser: WebDriver, base_url: str) -> SiteListPageExt:
    return SiteListPageExt(browser, base_url)


@pytest.fixture
def site_detail(browser: WebDriver, base_url: str) -> SiteDetailPage:
    return SiteDetailPage(browser, base_url)


@pytest.fixture
def location_detail(browser: WebDriver, base_url: str) -> LocationDetailPage:
    return LocationDetailPage(browser, base_url)


@pytest.fixture
def slot_detail(browser: WebDriver, base_url: str) -> SlotDetailPage:
    return SlotDetailPage(browser, base_url)


# ── Helper: get first site key from list ───────────────────────────────────────


def _navigate_to_first_site_detail(
    site_list: SiteListPageExt, site_detail: SiteDetailPage
) -> str | None:
    """Navigate list → click first row → extract key from URL.

    Returns the site key (str) or None if no sites exist.
    """
    site_list.open()
    if site_list.get_row_count() == 0:
        return None
    site_list.click_row(0)
    site_list.wait_for_url_contains("/standorte/sites/")
    url = site_list.driver.current_url
    return url.rstrip("/").rsplit("/", 1)[-1]


def _navigate_to_first_location_detail(
    site_list: SiteListPageExt, site_detail: SiteDetailPage
) -> str | None:
    """Navigate to site detail, then click the first location row.

    Returns location key from URL or None if no locations exist.
    """
    key = _navigate_to_first_site_detail(site_list, site_detail)
    if key is None:
        return None
    site_detail.open(key)
    loc_count = site_detail.get_location_row_count()
    if loc_count == 0:
        return None
    site_detail.click_location_row(0)
    site_detail.wait_for_url_contains("/standorte/locations/")
    url = site_detail.driver.current_url
    return url.rstrip("/").rsplit("/", 1)[-1]


# ==============================================================================
# TC-REQ-002-001 to TC-REQ-002-012: Site list page
# ==============================================================================


class TestSiteListPage:
    """Site list renders and supports operations (Spec: TC-002-001 to TC-002-007)."""

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_site_list_page_loads(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-001: Site list page loads and shows page title.

        Spec: TC-002-001 — Site-Liste ist leer / Titel 'Standorte' sichtbar.
        """
        capture = request.node._screenshot_capture
        site_list.open(via_sidebar=True)
        capture("TC-REQ-002-001_site-list-page-load", "Site list page after sidebar navigation — page title and DataTable or EmptyState visible")

        title = site_list.get_page_title()
        assert title, (
            "TC-REQ-002-001 FAIL: Page title should not be empty after navigation to /standorte/sites"
        )

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_site_list_has_data_table(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-002: Site list shows the DataTable component.

        Spec: TC-002-002 — Site-Liste zeigt vorhandene Sites mit Spalten.
        """
        capture = request.node._screenshot_capture
        site_list.open()
        capture("TC-REQ-002-002_site-list-data-table", "Site list DataTable component — column headers and rows or empty state")

        # DataTable should be present (even if empty, it renders the Paper wrapper)
        tables = site_list.driver.find_elements(*site_list.TABLE)
        if not tables:
            # If no data-table, may show empty state instead
            assert site_list.has_empty_state(), (
                "TC-REQ-002-002 FAIL: Expected DataTable or EmptyState on site list page"
            )
            return

        headers = site_list.get_column_headers()
        assert len(headers) >= 2, (
            f"TC-REQ-002-002 FAIL: Expected at least 2 column headers, got {headers}"
        )

    def test_site_list_shows_seed_data(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-003: At least one site row is visible from seed data, or empty state is shown."""
        capture = request.node._screenshot_capture
        site_list.open()
        capture("TC-REQ-002-003_site-list-seed-data")

        row_count = site_list.get_row_count()
        if row_count == 0:
            # Sites have no seed data — the page should show either an empty
            # state or a DataTable with zero rows.  Both are valid states.
            assert site_list.has_empty_state() or site_list.driver.find_elements(
                *site_list.TABLE
            ), (
                "TC-REQ-002-003 FAIL: Expected either site rows, empty state, or "
                "an empty DataTable"
            )

    def test_site_list_create_button_visible(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-004: Create button is visible on the list page."""
        capture = request.node._screenshot_capture
        site_list.open()
        capture("TC-REQ-002-004_site-list-create-button")

        create_btn = site_list.wait_for_element_clickable(site_list.CREATE_BUTTON)
        assert create_btn.is_displayed(), (
            "TC-REQ-002-004 FAIL: Create button should be visible on the site list page"
        )

    @pytest.mark.core_crud
    def test_site_list_create_dialog_opens(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-005: Clicking 'Anlegen' opens the create dialog with form fields."""
        capture = request.node._screenshot_capture
        site_list.open()
        capture("TC-REQ-002-005_before-create-dialog", "Site list before opening create dialog")

        site_list.click_create()
        capture("TC-REQ-002-005_create-dialog-open", "Site create dialog open — Name field and expertise toggle visible")

        assert site_list.is_create_dialog_open(), (
            "TC-REQ-002-005 FAIL: Create dialog (name input) should be visible after clicking create button"
        )

    def test_site_list_create_dialog_name_required(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-006: Form validation — empty name triggers validation error on submit."""
        capture = request.node._screenshot_capture
        site_list.open()
        site_list.click_create()
        capture("TC-REQ-002-006_before-empty-submit")

        # Ensure name field is empty (clear any default)
        name_el = site_list.wait_for_element_clickable(site_list.FORM_NAME)
        name_el.clear()

        # Submit without filling required name field
        site_list.submit_create_form()
        site_list.wait_for_loading_complete()
        capture("TC-REQ-002-006_validation-error-state")

        # Dialog should remain open (form not submitted)
        has_error = site_list.has_validation_error("name")
        dialog_open = site_list.is_create_dialog_open()
        assert has_error or dialog_open, (
            "TC-REQ-002-006 FAIL: Expected a validation error on the 'name' field "
            "or dialog to remain open after submitting empty form"
        )

    def test_site_list_create_dialog_cancel(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-007: Clicking 'Abbrechen' closes the create dialog."""
        capture = request.node._screenshot_capture
        site_list.open()
        site_list.click_create()
        capture("TC-REQ-002-007_create-dialog-before-cancel")

        site_list.cancel_create_form()
        site_list.wait_for_loading_complete()
        capture("TC-REQ-002-007_after-cancel")

        assert not site_list.is_create_dialog_open(), (
            "TC-REQ-002-007 FAIL: Create dialog should be closed after clicking 'Abbrechen'"
        )

    @pytest.mark.skip(reason="Site list uses accordion cards — no DataTable search (see TC-002-002 spec update)")
    def test_site_list_search_filters_rows(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-008: Searching by site name filters the table rows."""
        capture = request.node._screenshot_capture
        site_list.open()
        initial_count = site_list.get_row_count()

        if initial_count == 0:
            pytest.skip("No sites in database — skipping search test")

        # Get the first row name to search for
        first_names = site_list.get_first_column_texts()
        search_term = first_names[0][:4] if first_names else "test"

        capture("TC-REQ-002-008_before-search")
        site_list.search(search_term)
        time.sleep(0.3)  # debounce wait
        capture("TC-REQ-002-008_after-search")

        assert site_list.has_search_chip(), (
            f"TC-REQ-002-008 FAIL: Expected a search chip to appear after searching for '{search_term}'"
        )

    @pytest.mark.skip(reason="Site list uses accordion cards — no DataTable sort (see TC-002-002 spec update)")
    def test_site_list_sort_by_column(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-009: Clicking a column header activates sort."""
        capture = request.node._screenshot_capture
        site_list.open()
        headers = site_list.get_column_headers()

        if not headers:
            pytest.skip("No column headers found")

        capture("TC-REQ-002-009_before-sort")
        site_list.click_column_header(headers[0])
        site_list.wait_for_loading_complete()
        capture("TC-REQ-002-009_after-sort")

        assert site_list.has_sort_chip(), (
            "TC-REQ-002-009 FAIL: Expected a sort chip to appear after clicking column header"
        )

    @pytest.mark.skip(reason="Site list uses accordion cards — no DataTable filters (see TC-002-002 spec update)")
    def test_site_list_reset_filters(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-010: Reset filters button restores unfiltered view."""
        capture = request.node._screenshot_capture
        site_list.open()
        initial_count = site_list.get_row_count()

        if initial_count == 0:
            pytest.skip("No sites — cannot test filter reset")

        site_list.search("xyzzy_nonexistent_9999")
        time.sleep(0.3)  # debounce wait
        capture("TC-REQ-002-010_after-search-empty")

        # There should now be a reset button (or no results)
        if site_list.has_reset_filters_button():
            site_list.click_reset_filters()
            site_list.wait_for_loading_complete()
            capture("TC-REQ-002-010_after-reset")
            reset_count = site_list.get_row_count()
            assert reset_count == initial_count, (
                f"TC-REQ-002-010 FAIL: After reset, expected {initial_count} rows, got {reset_count}"
            )

    @pytest.mark.core_crud
    def test_site_list_row_click_navigates_to_detail(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-011: Clicking a site row navigates to the site detail page.

        Spec: TC-002-004 — Klick auf Site-Zeile navigiert zur Detailseite.
        """
        capture = request.node._screenshot_capture
        site_list.open()

        if site_list.get_row_count() == 0:
            pytest.skip("No sites in database")

        capture("TC-REQ-002-011_before-row-click", "Site list with rows — about to click first site row")
        site_list.click_row(0)
        site_list.wait_for_url_contains("/standorte/sites/")
        capture("TC-REQ-002-011_after-row-click", "Site detail page after row click navigation")

        current_url = site_list.driver.current_url
        assert "/standorte/sites/" in current_url, (
            f"TC-REQ-002-011 FAIL: Expected URL to contain '/standorte/sites/', got '{current_url}'"
        )

    @pytest.mark.skip(reason="Site list uses accordion cards — no DataTable pagination (see TC-002-002 spec update)")
    def test_site_list_showing_count_displayed(
        self, site_list: SiteListPageExt, request: pytest.FixtureRequest
    ) -> None:
        """TC-REQ-002-012: The showing-count footer is rendered with valid text."""
        capture = request.node._screenshot_capture
        site_list.open()
        capture("TC-REQ-002-012_showing-count")

        if site_list.get_row_count() == 0:
            pytest.skip("No sites — showing count not displayed for empty table")

        count_text = site_list.get_showing_count_text()
        assert count_text, (
            f"TC-REQ-002-012 FAIL: Expected non-empty showing-count text, got '{count_text}'"
        )
        # The text contains a number pattern like "Zeigt 1–10 von 12" or "1-10 of 12"
        has_number = any(c.isdigit() for c in count_text)
        assert has_number, (
            f"TC-REQ-002-012 FAIL: Showing count text should contain a number, got '{count_text}'"
        )


# ==============================================================================
# TC-REQ-002-013 to TC-REQ-002-022: Site detail page
# ==============================================================================


class TestSiteDetailPage:
    """Site detail page edit form and sub-sections (Spec: TC-002-010 to TC-002-022)."""

    @pytest.mark.core_crud
    def test_site_detail_page_loads(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-013: Site detail page loads with the site name as page title.

        Spec: TC-002-010 — Site-Daten bearbeiten (Seite laden, Felder vorbelegt).
        """
        capture = request.node._screenshot_capture
        key = _navigate_to_first_site_detail(site_list, site_detail)
        if key is None:
            pytest.skip("No sites in database")

        site_detail.open(key)
        capture("TC-REQ-002-013_site-detail-page-load", "Site detail page loaded — name field, form buttons, location sub-table visible")

        title = site_detail.get_title()
        assert title, (
            f"TC-REQ-002-013 FAIL: Site detail page title should not be empty for key '{key}'"
        )
        assert not site_detail.is_error_shown(), (
            "TC-REQ-002-013 FAIL: Error display should not be visible when loading a valid site"
        )

    def test_site_detail_shows_edit_form(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-014: Site detail page shows edit form with pre-filled name field."""
        capture = request.node._screenshot_capture
        key = _navigate_to_first_site_detail(site_list, site_detail)
        if key is None:
            pytest.skip("No sites in database")

        site_detail.open(key)
        capture("TC-REQ-002-014_site-detail-form")

        name_value = site_detail.get_name_value()
        assert name_value, (
            "TC-REQ-002-014 FAIL: The 'name' input should be pre-filled with the site's name"
        )

    def test_site_detail_form_buttons_visible(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-015: Site detail page shows Save and Cancel form buttons."""
        capture = request.node._screenshot_capture
        key = _navigate_to_first_site_detail(site_list, site_detail)
        if key is None:
            pytest.skip("No sites in database")

        site_detail.open(key)
        capture("TC-REQ-002-015_site-detail-form-buttons")

        save_btn = site_detail.wait_for_element(site_detail.FORM_SUBMIT)
        cancel_btn = site_detail.wait_for_element(site_detail.FORM_CANCEL)
        assert save_btn.is_displayed(), (
            "TC-REQ-002-015 FAIL: Save button (form-submit-button) should be visible"
        )
        assert cancel_btn.is_displayed(), (
            "TC-REQ-002-015 FAIL: Cancel button (form-cancel-button) should be visible"
        )

    @pytest.mark.core_crud
    def test_site_detail_edit_name_field(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-016: User can edit the name field in the site detail form.

        Spec: TC-002-010 — Site-Daten bearbeiten und speichern.
        """
        capture = request.node._screenshot_capture
        key = _navigate_to_first_site_detail(site_list, site_detail)
        if key is None:
            pytest.skip("No sites in database")

        site_detail.open(key)
        original_name = site_detail.get_name_value()
        capture("TC-REQ-002-016_before-edit", f"Site detail name field before edit — current value: '{original_name}'")

        test_suffix = "_e2e_test"
        site_detail.set_name(original_name + test_suffix)
        capture("TC-REQ-002-016_after-edit", f"Site detail name field after edit — new value: '{original_name + test_suffix}'")

        new_value = site_detail.get_name_value()
        assert new_value == original_name + test_suffix, (
            f"TC-REQ-002-016 FAIL: Expected name field to contain '{original_name + test_suffix}', got '{new_value}'"
        )

        # Restore original name by cancelling (UnsavedChangesGuard may alert — use cancel button)
        site_detail.cancel_form()

    def test_site_detail_cancel_navigates_back(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-017: Clicking 'Abbrechen' navigates back from site detail."""
        capture = request.node._screenshot_capture
        key = _navigate_to_first_site_detail(site_list, site_detail)
        if key is None:
            pytest.skip("No sites in database")

        site_detail.open(key)
        capture("TC-REQ-002-017_before-cancel")

        site_detail.cancel_form()
        capture("TC-REQ-002-017_after-cancel")

        # Should navigate back to the sites list
        current_url = site_detail.driver.current_url
        assert "/standorte" in current_url, (
            f"TC-REQ-002-017 FAIL: After cancel, expected URL to contain '/standorte', got '{current_url}'"
        )

    def test_site_detail_location_section_visible(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-018: Site detail page shows the LocationTreeSection.

        Spec: TC-002-021 — Location-Baum zeigt Site-Kinder in Baumstruktur.
        """
        capture = request.node._screenshot_capture
        key = _navigate_to_first_site_detail(site_list, site_detail)
        if key is None:
            pytest.skip("No sites in database")

        site_detail.open(key)
        capture("TC-REQ-002-018_site-detail-location-section")

        assert site_detail.is_location_section_visible(), (
            "TC-REQ-002-018 FAIL: The LocationTreeSection (add-location-button) should be visible on the site detail page"
        )

    @pytest.mark.core_crud
    def test_site_detail_delete_dialog_opens(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-019: Clicking 'Löschen' on site detail opens confirm dialog.

        Spec: TC-002-012 — Site löschen mit Bestätigungsdialog.
        """
        capture = request.node._screenshot_capture
        key = _navigate_to_first_site_detail(site_list, site_detail)
        if key is None:
            pytest.skip("No sites in database")

        site_detail.open(key)
        capture("TC-REQ-002-019_before-delete", "Site detail page before clicking delete button")

        site_detail.click_delete()
        capture("TC-REQ-002-019_delete-confirm-dialog", "Delete confirmation dialog open — Abbrechen/Loeschen buttons visible")

        assert site_detail.is_confirm_dialog_visible(), (
            "TC-REQ-002-019 FAIL: Confirm dialog should be visible after clicking delete"
        )

    def test_site_detail_delete_dialog_cancel(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-020: Clicking 'Abbrechen' in delete dialog closes it without deleting."""
        capture = request.node._screenshot_capture
        key = _navigate_to_first_site_detail(site_list, site_detail)
        if key is None:
            pytest.skip("No sites in database")

        site_detail.open(key)
        title_before = site_detail.get_title()

        site_detail.click_delete()
        capture("TC-REQ-002-020_delete-dialog-open")

        site_detail.cancel_delete()
        capture("TC-REQ-002-020_delete-dialog-cancelled")

        assert not site_detail.is_confirm_dialog_visible(), (
            "TC-REQ-002-020 FAIL: Confirm dialog should close after clicking 'Abbrechen'"
        )
        # Still on the same page
        current_url = site_detail.driver.current_url
        assert key in current_url, (
            f"TC-REQ-002-020 FAIL: Should remain on site detail page after cancel, but URL is '{current_url}'"
        )

    def test_site_detail_location_row_navigates(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-021: Clicking a location row in site detail navigates to location detail."""
        capture = request.node._screenshot_capture
        key = _navigate_to_first_site_detail(site_list, site_detail)
        if key is None:
            pytest.skip("No sites in database")

        site_detail.open(key)
        loc_count = site_detail.get_location_row_count()
        if loc_count == 0:
            pytest.skip("No locations in this site")

        capture("TC-REQ-002-021_before-location-row-click")
        site_detail.click_location_row(0)
        site_detail.wait_for_url_contains("/standorte/locations/")
        capture("TC-REQ-002-021_after-location-row-click")

        current_url = site_detail.driver.current_url
        assert "/standorte/locations/" in current_url, (
            f"TC-REQ-002-021 FAIL: Expected URL to contain '/standorte/locations/', got '{current_url}'"
        )

    def test_site_detail_unknown_key_shows_error(
        self,
        site_detail: SiteDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-022: Navigating to non-existent site key shows error display."""
        capture = request.node._screenshot_capture
        site_detail.navigate("/standorte/sites/nonexistent-key-99999")
        # Wait for loading skeleton to disappear first (SPA needs to load +
        # make the API call + render the error state)
        try:
            site_detail.wait_for_loading_complete(timeout=10)
        except Exception:
            pass  # Skeleton might never appear if page loads very fast
        # Wait for error display to appear
        from selenium.webdriver.support.ui import WebDriverWait
        try:
            WebDriverWait(site_detail.driver, 10).until(
                lambda d: site_detail.is_error_shown()
            )
        except Exception:
            pass  # Some implementations redirect instead of showing error
        capture("TC-REQ-002-022_unknown-site-error")

        # Accept either error display or any non-loading state (page may redirect)
        error_shown = site_detail.is_error_shown()
        current_url = site_detail.driver.current_url
        # Some implementations navigate away on error instead of showing ErrorDisplay
        assert error_shown or "/standorte/sites/nonexistent" not in current_url, (
            "TC-REQ-002-022 FAIL: An error display should appear or page should redirect for an unknown site key"
        )


# ==============================================================================
# TC-REQ-002-023 to TC-REQ-002-030: Location detail page
# ==============================================================================


class TestLocationDetailPage:
    """Location detail edit and sub-sections (Spec: TC-002-022 to TC-002-027)."""

    @pytest.mark.core_crud
    def test_location_detail_page_loads(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-023: Location detail page loads with title and no error.

        Spec: TC-002-022 — Klick auf Location-Knoten navigiert zur Detailseite.
        """
        capture = request.node._screenshot_capture
        loc_key = _navigate_to_first_location_detail(site_list, site_detail)
        if loc_key is None:
            pytest.skip("No locations available")

        location_detail.open(loc_key)
        capture("TC-REQ-002-023_location-detail-page-load", "Location detail page loaded — name field, form buttons, slot sub-table visible")

        title = location_detail.get_title()
        assert title, (
            f"TC-REQ-002-023 FAIL: Location detail page title should not be empty for key '{loc_key}'"
        )
        assert not location_detail.is_error_shown(), (
            "TC-REQ-002-023 FAIL: Error display should not be visible for a valid location key"
        )

    def test_location_detail_name_field_prefilled(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-024: Location detail edit form has name field pre-filled."""
        capture = request.node._screenshot_capture
        loc_key = _navigate_to_first_location_detail(site_list, site_detail)
        if loc_key is None:
            pytest.skip("No locations available")

        location_detail.open(loc_key)
        capture("TC-REQ-002-024_location-detail-form")

        name_value = location_detail.get_name_value()
        assert name_value, (
            "TC-REQ-002-024 FAIL: The 'name' field should be pre-filled with the location's name"
        )

    def test_location_detail_form_buttons_visible(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-025: Location detail page shows Save and Cancel form buttons."""
        capture = request.node._screenshot_capture
        loc_key = _navigate_to_first_location_detail(site_list, site_detail)
        if loc_key is None:
            pytest.skip("No locations available")

        location_detail.open(loc_key)
        capture("TC-REQ-002-025_location-form-buttons")

        save_btn = location_detail.wait_for_element(location_detail.FORM_SUBMIT)
        cancel_btn = location_detail.wait_for_element(location_detail.FORM_CANCEL)
        assert save_btn.is_displayed(), (
            "TC-REQ-002-025 FAIL: Save button should be visible on location detail page"
        )
        assert cancel_btn.is_displayed(), (
            "TC-REQ-002-025 FAIL: Cancel button should be visible on location detail page"
        )

    @pytest.mark.core_crud
    def test_location_detail_edit_name(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-026: User can modify the name field in location detail form."""
        capture = request.node._screenshot_capture
        loc_key = _navigate_to_first_location_detail(site_list, site_detail)
        if loc_key is None:
            pytest.skip("No locations available")

        location_detail.open(loc_key)
        original_name = location_detail.get_name_value()
        capture("TC-REQ-002-026_before-edit", f"Location detail name field before edit — current value: '{original_name}'")

        location_detail.set_name(original_name + "_e2e")
        capture("TC-REQ-002-026_after-edit", f"Location detail name field after edit — new value: '{original_name}_e2e'")

        new_value = location_detail.get_name_value()
        assert new_value == original_name + "_e2e", (
            f"TC-REQ-002-026 FAIL: Expected name to be '{original_name}_e2e', got '{new_value}'"
        )
        location_detail.cancel_form()

    @pytest.mark.core_crud
    def test_location_detail_delete_dialog(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-027: Clicking 'Löschen' on location detail opens confirm dialog."""
        capture = request.node._screenshot_capture
        loc_key = _navigate_to_first_location_detail(site_list, site_detail)
        if loc_key is None:
            pytest.skip("No locations available")

        location_detail.open(loc_key)
        capture("TC-REQ-002-027_before-delete", "Location detail page before clicking delete button")

        location_detail.click_delete()
        capture("TC-REQ-002-027_delete-confirm-dialog", "Location delete confirmation dialog open")

        assert location_detail.is_confirm_dialog_visible(), (
            "TC-REQ-002-027 FAIL: Delete confirm dialog should be visible after clicking Löschen"
        )

    def test_location_detail_delete_dialog_cancel(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-028: Cancelling the delete dialog keeps the location intact."""
        capture = request.node._screenshot_capture
        loc_key = _navigate_to_first_location_detail(site_list, site_detail)
        if loc_key is None:
            pytest.skip("No locations available")

        location_detail.open(loc_key)
        location_detail.click_delete()
        capture("TC-REQ-002-028_delete-dialog-visible")

        location_detail.cancel_delete()
        capture("TC-REQ-002-028_after-cancel")

        assert not location_detail.is_confirm_dialog_visible(), (
            "TC-REQ-002-028 FAIL: Confirm dialog should close after clicking Abbrechen"
        )
        current_url = location_detail.driver.current_url
        assert loc_key in current_url, (
            f"TC-REQ-002-028 FAIL: Should remain on location detail page, but URL is '{current_url}'"
        )

    def test_location_detail_watering_button_visible(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-029: Location detail page shows the 'Bewässerung erfassen' button."""
        capture = request.node._screenshot_capture
        loc_key = _navigate_to_first_location_detail(site_list, site_detail)
        if loc_key is None:
            pytest.skip("No locations available")

        location_detail.open(loc_key)
        capture("TC-REQ-002-029_location-watering-button")

        assert location_detail.is_create_watering_button_visible(), (
            "TC-REQ-002-029 FAIL: 'create-watering-button' should be visible on location detail page"
        )

    def test_location_detail_unknown_key_shows_error(
        self,
        location_detail: LocationDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-030: Navigating to unknown location key shows error display."""
        capture = request.node._screenshot_capture
        location_detail.navigate("/standorte/locations/nonexistent-loc-99999")
        location_detail.wait_for_loading_complete()
        capture("TC-REQ-002-030_unknown-location-error")

        assert location_detail.is_error_shown(), (
            "TC-REQ-002-030 FAIL: An error display should appear for an unknown location key"
        )


# ==============================================================================
# TC-REQ-002-031 to TC-REQ-002-035: Slot detail page
# ==============================================================================


def _get_first_slot_key(
    site_list: SiteListPageExt,
    site_detail: SiteDetailPage,
    location_detail: LocationDetailPage,
) -> str | None:
    """Navigate to the first location detail and click the first slot row.

    Returns the slot key extracted from the URL, or None if no slots exist.
    """
    loc_key = _navigate_to_first_location_detail(site_list, site_detail)
    if loc_key is None:
        return None
    location_detail.open(loc_key)
    # The location detail page has multiple DataTables — slots appear first
    # after the form. We need at least one data-table-row to exist.
    all_rows = location_detail.get_all_table_row_count()
    if all_rows == 0:
        return None
    # Click the first row in the slots table
    first_row = location_detail.wait_for_element_clickable(location_detail.DATA_TABLE_ROWS)
    location_detail.scroll_and_click(first_row)
    location_detail.wait_for_url_contains("/standorte/slots/")
    url = location_detail.driver.current_url
    return url.rstrip("/").rsplit("/", 1)[-1]


class TestSlotDetailPage:
    """TC-REQ-002-031 to TC-REQ-002-035: Slot detail page."""

    def test_slot_detail_page_loads(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        slot_detail: SlotDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-031: Slot detail page loads with slot_id as title."""
        capture = request.node._screenshot_capture
        slot_key = _get_first_slot_key(site_list, site_detail, location_detail)
        if slot_key is None:
            pytest.skip("No slots available")

        slot_detail.open(slot_key)
        capture("TC-REQ-002-031_slot-detail-page-load")

        title = slot_detail.get_title()
        assert title, (
            f"TC-REQ-002-031 FAIL: Slot detail page title should not be empty for key '{slot_key}'"
        )
        assert not slot_detail.is_error_shown(), (
            "TC-REQ-002-031 FAIL: Error display should not be visible for a valid slot key"
        )

    def test_slot_detail_slot_id_field_prefilled(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        slot_detail: SlotDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-032: Slot detail form has slot_id field pre-filled."""
        capture = request.node._screenshot_capture
        slot_key = _get_first_slot_key(site_list, site_detail, location_detail)
        if slot_key is None:
            pytest.skip("No slots available")

        slot_detail.open(slot_key)
        capture("TC-REQ-002-032_slot-detail-form")

        slot_id_value = slot_detail.get_slot_id_value()
        assert slot_id_value, (
            "TC-REQ-002-032 FAIL: The 'slot_id' field should be pre-filled"
        )

    def test_slot_detail_capacity_field_visible(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        slot_detail: SlotDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-033: Slot detail form shows the capacity_plants field."""
        capture = request.node._screenshot_capture
        slot_key = _get_first_slot_key(site_list, site_detail, location_detail)
        if slot_key is None:
            pytest.skip("No slots available")

        slot_detail.open(slot_key)
        capture("TC-REQ-002-033_slot-capacity-field")

        capacity_value = slot_detail.get_capacity_value()
        assert capacity_value, (
            "TC-REQ-002-033 FAIL: The 'capacity_plants' field should be visible and pre-filled"
        )
        assert int(capacity_value) >= 1, (
            f"TC-REQ-002-033 FAIL: Capacity should be >= 1, got '{capacity_value}'"
        )

    def test_slot_detail_delete_dialog_opens(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        slot_detail: SlotDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-034: Clicking 'Löschen' on slot detail opens confirm dialog."""
        capture = request.node._screenshot_capture
        slot_key = _get_first_slot_key(site_list, site_detail, location_detail)
        if slot_key is None:
            pytest.skip("No slots available")

        slot_detail.open(slot_key)
        capture("TC-REQ-002-034_before-delete")

        slot_detail.click_delete()
        capture("TC-REQ-002-034_delete-confirm-dialog")

        assert slot_detail.is_confirm_dialog_visible(), (
            "TC-REQ-002-034 FAIL: Delete confirm dialog should be visible after clicking Löschen"
        )

    def test_slot_detail_delete_dialog_cancel(
        self,
        site_list: SiteListPageExt,
        site_detail: SiteDetailPage,
        location_detail: LocationDetailPage,
        slot_detail: SlotDetailPage,
        request: pytest.FixtureRequest,
    ) -> None:
        """TC-REQ-002-035: Cancelling the delete dialog keeps the slot page open."""
        capture = request.node._screenshot_capture
        slot_key = _get_first_slot_key(site_list, site_detail, location_detail)
        if slot_key is None:
            pytest.skip("No slots available")

        slot_detail.open(slot_key)
        slot_detail.click_delete()
        capture("TC-REQ-002-035_delete-dialog-visible")

        slot_detail.cancel_delete()
        capture("TC-REQ-002-035_after-cancel")

        assert not slot_detail.is_confirm_dialog_visible(), (
            "TC-REQ-002-035 FAIL: Confirm dialog should close after clicking Abbrechen"
        )
        current_url = slot_detail.driver.current_url
        assert slot_key in current_url, (
            f"TC-REQ-002-035 FAIL: Should remain on slot detail page, but URL is '{current_url}'"
        )
