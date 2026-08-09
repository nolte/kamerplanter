"""E2E tests for REQ-004 — Giessprotokoll (Watering Log).

Covers the watering log list page, create dialog, and detail page.
The watering log is a daily-use feature for documenting irrigation events
including volume, EC/pH measurements, and fertilizer usage.

Spec-TC Mapping:
  TC-004-101  List page renders with data-testid + create button + table/empty state + count
  TC-004-102  Create dialog opens on button click
  TC-004-103  Create watering log — Happy Path (generic, no self-provisioning)
  TC-004-104  Pflichtfeld-Validierung (volume > 0)
  TC-004-105  Cancel closes dialog without changes
  TC-004-106  Add-fertilizer button adds a dynamic fertilizer row
  TC-004-107  Search filters table rows
  TC-004-108  Click on row navigates to detail page
  TC-004-109  Detail page shows two tabs (Details, Edit)
  TC-004-110  Detail page — details tab shows measurement cards
  TC-004-111  Detail page — analyze-runoff button visible
  TC-004-112  Detail page — delete opens confirmation dialog
  TC-004-113  Detail page — edit tab shows pre-filled form
  TC-004-114  Pflichtfeld-Validierung (Ziel: Pflanze oder Slot)

These generic list/dialog/detail mechanics are distinct from the
self-provisioning Core-Lifecycle-Journey cases (TC-004-089, TC-004-090,
TC-004-092 in spec/e2e-testcases/TC-REQ-004.md, covered by
test_req004_watering_cross_view_consistency*.py), which require a specific
plant `JOURNEY-004` and assert the concrete success message.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .pages.watering_log_detail_page import WateringLogDetailPage
from .pages.watering_log_list_page import WateringLogListPage

# Feature-axis marker(s) for machine-selectable test identification
# (see conftest.py::KNOWN_FEATURE_MARKERS / pytest -m <feature>).
FEATURES = ("watering",)


# -- Fixtures -----------------------------------------------------------------


@pytest.fixture
def watering_list(browser: WebDriver, base_url: str) -> WateringLogListPage:
    """Return a WateringLogListPage bound to the test browser."""
    return WateringLogListPage(browser, base_url)


@pytest.fixture
def watering_detail(browser: WebDriver, base_url: str) -> WateringLogDetailPage:
    """Return a WateringLogDetailPage bound to the test browser."""
    return WateringLogDetailPage(browser, base_url)


# -- TC-004-101: List Page -----------------------------------------------------


class TestWateringLogListPage:
    """Watering log list display and interactions (Spec: TC-004-101)."""

    @pytest.mark.smoke
    def test_list_page_renders_with_correct_testid(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-101: WateringLogListPage renders with data-testid='watering-log-list-page'.

        Verifies that the page loads and the root container element is visible.

        Spec: TC-004-101 -- Giessprotokoll-Liste aufrufen und Grundstruktur
        pruefen.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W001_watering-log-list-loaded",
            "Watering log list page after initial load",
        )

        page_el = watering_list.wait_for_element(WateringLogListPage.PAGE)
        assert page_el.is_displayed(), (
            "TC-REQ-004-W001 FAIL: Expected [data-testid='watering-log-list-page'] to be visible"
        )

    @pytest.mark.smoke
    def test_create_button_is_visible(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-101: Create button is visible on the watering log list page.

        The create button allows users to add a new watering log entry.

        Spec: TC-004-101 -- Giessprotokoll-Liste aufrufen und Grundstruktur
        pruefen.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W002_create-button-visible",
            "Watering log list showing create button",
        )

        create_btn = watering_list.wait_for_element(WateringLogListPage.CREATE_BUTTON)
        assert create_btn.is_displayed(), (
            "TC-REQ-004-W002 FAIL: Expected create button to be visible"
        )

    @pytest.mark.smoke
    def test_list_displays_data_table_or_empty_state(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-101: Page shows either a DataTable or the empty-state illustration.

        When no watering logs exist, the empty state should be displayed.
        When logs exist, the DataTable should be visible.

        Spec: TC-004-101 -- Giessprotokoll-Liste aufrufen und Grundstruktur
        pruefen.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W001b_table-or-empty",
            "Watering log list — table or empty state",
        )

        has_table = watering_list.has_table()
        has_empty = watering_list.has_empty_state()

        assert has_table or has_empty, (
            "TC-REQ-004-W001b FAIL: Expected either a DataTable or empty-state illustration"
        )

    @pytest.mark.core_crud
    def test_showing_count_when_rows_exist(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-101: Showing count text is displayed when rows are present.

        Skips if no watering log entries exist yet.

        Spec: TC-004-101 -- Giessprotokoll-Liste aufrufen und Grundstruktur
        pruefen.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W001c_showing-count",
            "Watering log list showing count",
        )

        if watering_list.get_row_count() == 0:
            pytest.skip("No rows — showing count not displayed for empty table")

        count_text = watering_list.get_showing_count_text()
        assert count_text, "TC-REQ-004-W001c FAIL: Expected non-empty showing count text"


# -- TC-004-102 to TC-004-106: Create Dialog -----------------------------------


class TestWateringLogCreateDialog:
    """Watering log create dialog operations (Spec: TC-004-102, TC-004-103,
    TC-004-104, TC-004-105, TC-004-106).
    """

    @pytest.mark.core_crud
    def test_create_dialog_opens_on_button_click(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-102: Clicking create button opens the WateringLogCreateDialog.

        Verifies dialog presence and that plant autocomplete is visible.

        Spec: TC-004-102 -- Giessprotokoll-Erstellen-Dialog oeffnet sich.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W003_before-open-dialog",
            "Watering log list before opening create dialog",
        )

        watering_list.click_create()
        screenshot(
            "TC-REQ-004-W003_dialog-open",
            "Watering log create dialog opened",
        )

        assert watering_list.is_create_dialog_open(), (
            "TC-REQ-004-W003 FAIL: Expected WateringLogCreateDialog to be open"
        )

        # Verify the plant autocomplete input is present
        assert watering_list.has_plant_autocomplete(), (
            "TC-REQ-004-W003 FAIL: Expected plant-keys-autocomplete to be present in dialog"
        )

        watering_list.cancel_create_form()

    @pytest.mark.core_crud
    def test_create_watering_log_happy_path(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-103: Create a watering log with valid data; verify it appears in list.

        Happy path: fill volume, submit, confirm list updates. This is the
        generic UI-mechanics variant against an arbitrary existing plant --
        distinct from TC-004-089's self-provisioned `JOURNEY-004` journey,
        which also asserts the concrete "Bewaesserung erfasst" success message.

        Spec: TC-004-103 -- Giessvorgang erfassen -- Happy Path (generisch).
        """
        watering_list.open()
        initial_count = watering_list.get_row_count()
        screenshot(
            "TC-REQ-004-W004_before-create",
            "Watering log list before creating entry",
        )

        watering_list.click_create()
        screenshot(
            "TC-REQ-004-W004_dialog-open",
            "Watering log create dialog opened",
        )

        # Select a plant (required by the backend service)
        if not watering_list.select_first_plant():
            pytest.skip("No plants available -- cannot test watering log creation")

        # Fill required field: volume_liters (defaults: application_method=drench, volume=1)
        watering_list.fill_volume(2.5)

        # Fill optional measurement fields for a realistic entry
        watering_list.fill_ec_before(1.2)
        watering_list.fill_ph_before(6.0)

        screenshot(
            "TC-REQ-004-W004_form-filled",
            "Watering log create form filled before submit",
        )

        watering_list.submit_create_form()

        # Wait for dialog to close and list to reload
        WebDriverWait(watering_list.driver, 15).until(
            EC.invisibility_of_element_located(WateringLogListPage.CREATE_DIALOG)
        )
        watering_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-004-W004_after-create",
            "Watering log list after creation",
        )

        final_count = watering_list.get_row_count()
        assert final_count > initial_count, (
            f"TC-REQ-004-W004 FAIL: Expected row count to increase. "
            f"Initial: {initial_count}, final: {final_count}"
        )

    @pytest.mark.core_crud
    def test_create_dialog_validation_volume_required(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-104: Submitting with volume cleared triggers validation; dialog stays open.

        The volume_liters field must be > 0. Clearing it and submitting should
        keep the dialog open (NFR-006 error display).

        Spec: TC-004-104 -- Giessvorgang erfassen -- Pflichtfeld-Validierung
        (Volumen).
        """
        watering_list.open()
        watering_list.click_create()

        # Clear the volume field (default is 1)
        volume_el = watering_list.wait_for_element_clickable(WateringLogListPage.FORM_VOLUME)
        watering_list.clear_and_fill(volume_el, "0")

        screenshot(
            "TC-REQ-004-W005_before-submit-invalid",
            "Create dialog with volume=0 before submit",
        )

        watering_list.submit_create_form()
        message = watering_list.wait_for_validation_error("volume_liters")
        screenshot(
            "TC-REQ-004-W005_validation-error",
            "Validation error after submitting with volume=0",
        )

        # Asserting the *message* rather than `is_create_dialog_open()`. That
        # predicate is also satisfied by a crash, by a submit button that was
        # disabled, and by a click the dialog swallowed — three states in which
        # the user is told nothing at all, and the one the test claims to
        # observe is only one of them (#970).
        #
        # The exact German text is asserted now (#1016): the constraint no longer
        # renders zod's English default, it is routed through the global i18n
        # error map, so `volume_liters > 0` shows the German `validation.numberGt`
        # message. Pinning the text is what proves the German string reaches the
        # user — the previous non-empty check passed even on the English default
        # this issue removed.
        assert message == "Muss größer als 0 sein.", (
            "TC-REQ-004-W005 FAIL: Expected the volume field to show the German "
            f"validation message 'Muss größer als 0 sein.', got {message!r}. An "
            "English zod default here is the #1016 defect; an empty string means "
            "the field carried no message at all (#970)."
        )

        watering_list.cancel_create_form()

    @pytest.mark.core_crud
    def test_create_dialog_validation_target_required(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-114: Submitting with neither plant nor slot shows a field-level error.

        The domain rule "at least one of slot_keys or plant_keys must be
        provided" is a *cross-field* rule, so no single input can carry it and
        the form's per-field constraints cannot catch it. This is the path that
        went uncovered: a valid volume plus no target submits, the API answers
        422 with the offending fields named, and until #970 the user was shown
        only a generic "check your input" toast that named neither field.

        Spec: TC-004-114 -- Giessvorgang erfassen -- Pflichtfeld-Validierung
        (Pflanze oder Slot).
        """
        watering_list.open()
        watering_list.click_create()

        # Deliberately touch nothing: the dialog opens with no plant selected,
        # an empty slot field and a valid default volume — exactly the state the
        # rule is about.
        screenshot(
            "TC-REQ-004-W014_before-submit-no-target",
            "Create dialog with a valid volume but neither plant nor slot",
        )

        watering_list.submit_create_form()

        plant_message = watering_list.wait_for_validation_error("plant_keys")
        slot_message = watering_list.wait_for_validation_error("slot_keys_input")
        screenshot(
            "TC-REQ-004-W014_validation-error",
            "Field-level validation error for the missing watering target",
        )

        # Both fields, because the rule is about both and the user may satisfy
        # it through either one. Marking only one would send the user to fix a
        # field they were free to leave empty.
        assert plant_message, (
            "TC-REQ-004-W014 FAIL: Expected the plant field to name the missing "
            "watering target, got no message. A generic toast does not tell the "
            "user which field to fill."
        )
        assert slot_message, (
            "TC-REQ-004-W014 FAIL: Expected the slot field to name the missing "
            "watering target, got no message."
        )
        # One content probe on the rule's subject, so "some error appeared"
        # cannot pass for "the right error appeared". Kept to a single stem
        # rather than the full sentence: the wording is owned by the i18n
        # catalogue and may be edited, the subject may not.
        assert "pflanze" in plant_message.lower(), (
            "TC-REQ-004-W014 FAIL: Expected the message under the plant field to be "
            f"about the missing plant/slot target, got {plant_message!r}"
        )

        watering_list.cancel_create_form()

    @pytest.mark.core_crud
    def test_create_dialog_cancel_closes_without_saving(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-105: Cancel in create dialog closes it without creating a log entry.

        Verifies that the row count remains unchanged after cancelling.

        Spec: TC-004-105 -- Giessprotokoll-Erstellen-Dialog -- Abbrechen ohne
        Speichern.
        """
        watering_list.open()
        initial_count = watering_list.get_row_count()

        watering_list.click_create()
        watering_list.fill_volume(99.9)
        screenshot(
            "TC-REQ-004-W006_before-cancel",
            "Create dialog filled before cancel",
        )

        watering_list.cancel_create_form()
        watering_list.wait_for_loading_complete()
        screenshot(
            "TC-REQ-004-W006_after-cancel",
            "Watering log list after cancelling dialog",
        )

        assert not watering_list.is_create_dialog_open(), (
            "TC-REQ-004-W006 FAIL: Expected create dialog to be closed after cancel"
        )
        final_count = watering_list.get_row_count()
        assert final_count == initial_count, (
            f"TC-REQ-004-W006 FAIL: Expected row count to stay {initial_count}, got {final_count}"
        )

    @pytest.mark.core_crud
    def test_create_dialog_add_fertilizer_button(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-106: Add-fertilizer button adds a fertilizer row to the form.

        Verifies that the dynamic fertilizer field array can be extended.

        Spec: TC-004-106 -- Giessprotokoll-Erstellen-Dialog -- Duenger-Zeile
        dynamisch hinzufuegen.
        """
        watering_list.open()
        watering_list.click_create()
        screenshot(
            "TC-REQ-004-W004b_before-add-fertilizer",
            "Create dialog before adding fertilizer",
        )

        watering_list.click_add_fertilizer()
        screenshot(
            "TC-REQ-004-W004b_after-add-fertilizer",
            "Create dialog after adding fertilizer row",
        )

        # Verify at least one remove-fertilizer button appeared
        assert watering_list.has_remove_fertilizer_button(), (
            "TC-REQ-004-W004b FAIL: Expected remove-fertilizer-0 button after adding fertilizer"
        )

        watering_list.cancel_create_form()


# -- TC-004-107: Search/Filter -------------------------------------------------


class TestWateringLogSearch:
    """Watering log search and filter interactions (Spec: TC-004-107)."""

    @pytest.mark.core_crud
    def test_search_filters_table_rows(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-107: Typing into the search field filters visible rows.

        Skips if no watering logs exist (nothing to filter).

        Spec: TC-004-107 -- Giessprotokoll-Liste -- Freitextsuche filtert
        Zeilen.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W007_before-search",
            "Watering log list before search",
        )

        row_count = watering_list.get_row_count()
        if row_count == 0:
            pytest.skip("No watering log rows to search/filter")

        # Search for a term no watering log can carry.
        term = "zzz-no-match-expected"
        watering_list.search(term)
        # Not the stale "debounce handled inside the page object" claim that
        # stood here: `WateringLogListPage.search()` only nudges past *most*
        # of the 300 ms debounce with a fixed sleep, it does not settle the
        # table (see its docstring). A `get_row_count()` read taken right
        # after it can still land on the *previous*, unfiltered rows, which
        # also satisfied the disjunction this replaces via `has_search_chip()`
        # alone -- the chip renders as soon as a non-empty term is typed,
        # independent of whether the filter has actually run (#946's debounce
        # trap). `wait_for_no_search_results` can only become true once the
        # filter has run *and* found nothing to show.
        watering_list.wait_for_no_search_results(term, what="watering log list")
        screenshot(
            "TC-REQ-004-W007_after-search",
            "Watering log list after search with non-matching term",
        )

        filtered_count = watering_list.get_row_count()
        assert filtered_count == 0, (
            f"TC-REQ-004-W007 FAIL: Searching for {term!r} must leave the watering "
            f"log list empty, but {filtered_count} of the {row_count} rows are "
            f"still listed. The no-search-results panel is already showing, so the "
            f"filter has run -- a surviving row count therefore means some column's "
            f"`searchValue` matches this term, not that the search never arrived."
        )

        # Clear search to restore
        watering_list.clear_search()  # debounce handled inside the page object


# -- TC-004-108 to TC-004-113: Detail Page -------------------------------------


class TestWateringLogDetailPage:
    """Watering log detail page display and navigation (Spec: TC-004-108,
    TC-004-109, TC-004-110, TC-004-111, TC-004-112, TC-004-113).
    """

    @pytest.mark.smoke
    def test_click_row_navigates_to_detail(
        self,
        watering_list: WateringLogListPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-108: Clicking a row in the list navigates to the detail page.

        Skips if no watering log entries exist.

        Spec: TC-004-108 -- Giessprotokoll -- Klick auf Zeile navigiert zur
        Detailseite.
        """
        watering_list.open()
        screenshot(
            "TC-REQ-004-W008_list-before-click",
            "Watering log list before clicking row",
        )

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows to click")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        screenshot(
            "TC-REQ-004-W008_detail-after-click",
            "Watering log detail page after row click",
        )

        detail_el = watering_list.wait_for_element(WateringLogDetailPage.PAGE, timeout=15)
        assert detail_el.is_displayed(), (
            "TC-REQ-004-W008 FAIL: Expected watering-log-detail-page to be visible after row click"
        )

    @pytest.mark.smoke
    def test_detail_page_has_two_tabs(
        self,
        watering_list: WateringLogListPage,
        watering_detail: WateringLogDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-109: Detail page shows 2 tabs (Details, Edit).

        Navigates via list row click, then verifies tab count and labels.

        Spec: TC-004-109 -- Giessprotokoll-Detailseite zeigt zwei Tabs.
        """
        watering_list.open()

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows — cannot test detail page")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        watering_detail.wait_for_element(WateringLogDetailPage.PAGE)
        screenshot(
            "TC-REQ-004-W009_detail-tabs",
            "Watering log detail page showing tabs",
        )

        tab_count = watering_detail.get_tab_count()
        assert tab_count == 2, f"TC-REQ-004-W009 FAIL: Expected 2 tabs, got {tab_count}"

    @pytest.mark.core_crud
    def test_detail_page_shows_measurement_cards(
        self,
        watering_list: WateringLogListPage,
        watering_detail: WateringLogDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-110: Details tab shows at least one MUI Card with watering data.

        Verifies that the details tab renders measurement/info cards.

        Spec: TC-004-110 -- Giessprotokoll-Detailseite -- Detail-Tab zeigt
        Messwert-Karten.
        """
        watering_list.open()

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows — cannot test detail page cards")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        watering_detail.wait_for_element(WateringLogDetailPage.PAGE)
        screenshot(
            "TC-REQ-004-W009b_detail-cards",
            "Watering log detail page — measurement cards",
        )

        card_count = watering_detail.get_detail_card_count()
        assert card_count >= 1, (
            f"TC-REQ-004-W009b FAIL: Expected at least 1 detail card, got {card_count}"
        )

    @pytest.mark.core_crud
    def test_detail_page_has_analyze_runoff_button(
        self,
        watering_list: WateringLogListPage,
        watering_detail: WateringLogDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-111: Details tab shows the 'Analyze Runoff' button.

        This button triggers backend runoff analysis for the watering event.

        Spec: TC-004-111 -- Giessprotokoll-Detailseite -- Button "Runoff
        analysieren" sichtbar.
        """
        watering_list.open()

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows — cannot test runoff button")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        watering_detail.wait_for_element(WateringLogDetailPage.PAGE)
        screenshot(
            "TC-REQ-004-W009c_runoff-button",
            "Watering log detail — analyze runoff button",
        )

        assert watering_detail.has_analyze_runoff_button(), (
            "TC-REQ-004-W009c FAIL: Expected analyze-runoff button to be visible"
        )

    @pytest.mark.core_crud
    def test_detail_page_delete_dialog_opens(
        self,
        watering_list: WateringLogListPage,
        watering_detail: WateringLogDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-112: Delete button on detail page opens confirmation dialog.

        Verifies the ConfirmDialog appears and can be cancelled.

        Spec: TC-004-112 -- Giessprotokoll-Detailseite -- Loeschen oeffnet
        Bestaetigungsdialog.
        """
        watering_list.open()

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows — cannot test delete dialog")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        watering_detail.wait_for_element(WateringLogDetailPage.PAGE)

        watering_detail.click_delete()
        screenshot(
            "TC-REQ-004-W009d_delete-dialog",
            "Watering log detail — delete confirmation dialog",
        )

        assert watering_detail.is_confirm_dialog_visible(), (
            "TC-REQ-004-W009d FAIL: Expected ConfirmDialog to be visible"
        )

        # Cancel the delete to avoid data loss
        watering_detail.cancel_delete()

    @pytest.mark.core_crud
    def test_detail_page_edit_tab_shows_form(
        self,
        watering_list: WateringLogListPage,
        watering_detail: WateringLogDetailPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-004-113: Edit tab on detail page shows the edit form with pre-filled values.

        Navigates to the edit tab and verifies the volume field is present and pre-filled.

        Spec: TC-004-113 -- Giessprotokoll-Detailseite -- Bearbeiten-Tab zeigt
        vorbefuelltes Formular.
        """
        watering_list.open()

        if watering_list.get_row_count() == 0:
            pytest.skip("No watering log rows — cannot test edit tab")

        watering_list.click_row(0)
        watering_list.wait_for_url_contains("/giessprotokoll/")
        watering_detail.wait_for_element(WateringLogDetailPage.PAGE)

        watering_detail.click_edit_tab()
        screenshot(
            "TC-REQ-004-W009e_edit-tab",
            "Watering log detail — edit tab form",
        )

        assert watering_detail.is_edit_form_visible(), (
            "TC-REQ-004-W009e FAIL: Expected edit form to be visible on edit tab"
        )

        volume_val = watering_detail.get_volume_value()
        assert volume_val, (
            "TC-REQ-004-W009e FAIL: Expected volume field to be pre-filled with a value"
        )
