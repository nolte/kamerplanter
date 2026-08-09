"""Page object for the Planting Run detail page (REQ-013)."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import DEFAULT_TIMEOUT, BasePage


class PlantingRunDetailPage(BasePage):
    """Interact with the Planting Run detail page (``/durchlaeufe/planting-runs/:key``)."""

    # ── Page-level locators ────────────────────────────────────────────
    PAGE = (By.CSS_SELECTOR, "[data-testid='planting-run-detail-page']")
    STATUS_CHIP = (By.CSS_SELECTOR, "[data-testid='status-chip']")

    # Action buttons — visibility depends on current status
    CREATE_PLANTS_BUTTON = (By.CSS_SELECTOR, "[data-testid='create-plants-button']")
    DELETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='delete-button']")
    BATCH_REMOVE_BUTTON = (By.CSS_SELECTOR, "[data-testid='batch-remove-button']")

    # ── Tab locators ───────────────────────────────────────────────────
    # MUI Tabs render as <button role="tab"> elements
    TABS = (By.CSS_SELECTOR, "button[role='tab']")

    # ── ConfirmDialog locators ─────────────────────────────────────────
    CONFIRM_DIALOG = (By.CSS_SELECTOR, "[data-testid='confirm-dialog']")
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-confirm']")
    CONFIRM_CANCEL = (By.CSS_SELECTOR, "[data-testid='confirm-dialog-cancel']")

    # ── Tab 0 – Details ────────────────────────────────────────────────
    # Detail info cards are rendered with MUI Card/CardContent — no testids needed;
    # locate by visible typography text.
    DETAILS_CARD = (By.CSS_SELECTOR, "[data-testid='planting-run-detail-page'] .MuiCard-root")
    ENTRIES_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    ENTRIES_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    # ── Tab 1 – Plants ─────────────────────────────────────────────────
    PLANTS_TABLE = (By.CSS_SELECTOR, "[data-testid='data-table']")
    PLANTS_ROWS = (By.CSS_SELECTOR, "[data-testid='data-table-row']")

    # ── Edit dialog (opened via edit button) ────────────────────────────
    EDIT_BUTTON = (By.CSS_SELECTOR, "[data-testid='edit-button']")
    EDIT_DIALOG = (By.CSS_SELECTOR, ".MuiDialog-root [role='dialog']")
    FORM_NAME = (
        By.CSS_SELECTOR,
        ".MuiDialog-root [role='dialog'] [data-testid='form-field-name'] input",
    )
    FORM_NOTES = (
        By.CSS_SELECTOR,
        ".MuiDialog-root [role='dialog'] [data-testid='form-field-notes'] input",
    )
    FORM_PLANNED_START = (
        By.CSS_SELECTOR,
        ".MuiDialog-root [role='dialog'] [data-testid='form-field-planned_start_date'] input",
    )
    FORM_SUBMIT = (
        By.CSS_SELECTOR,
        ".MuiDialog-root [role='dialog'] [data-testid='form-submit-button']",
    )
    FORM_CANCEL = (
        By.CSS_SELECTOR,
        ".MuiDialog-root [role='dialog'] [data-testid='form-cancel-button']",
    )

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self, run_key: str) -> PlantingRunDetailPage:
        """Navigate to the planting run detail page for *run_key*."""
        self.navigate(f"/durchlaeufe/planting-runs/{run_key}")
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    # ── Status ─────────────────────────────────────────────────────────

    def get_status(self) -> str:
        """Return the text of the status chip (e.g. 'Geplant', 'Aktiv')."""
        el = self.wait_for_element(self.STATUS_CHIP)
        return el.text

    def get_page_title(self) -> str:
        """Return the page title (run name).

        Waits for the detail page container first to avoid reading
        the list page title during client-side navigation.
        """
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        # The page-title inside the detail page container. The lookup is the
        # wait -- `get_text_stable` below re-finds the element, so binding the
        # result served no purpose, but dropping the call would drop the wait.
        self.wait_for_element(
            (By.CSS_SELECTOR, "[data-testid='planting-run-detail-page'] [data-testid='page-title']")
        )
        return self.get_text_stable(
            (By.CSS_SELECTOR, "[data-testid='planting-run-detail-page'] [data-testid='page-title']")
        )

    # ── Tab navigation ─────────────────────────────────────────────────

    def get_tab_labels(self) -> list[str]:
        """Return the labels of all tab buttons."""
        tabs = self.tab_elements(self.TABS)
        return [t.text for t in tabs]

    def click_tab(self, index: int) -> None:
        """Click the tab at *index* (0-based)."""
        tabs = self.tab_elements(self.TABS)
        if index < len(tabs):
            self.scroll_and_click(tabs[index])
        else:
            raise ValueError(f"Tab index {index} out of range (found {len(tabs)} tabs)")

    def get_active_tab_index(self) -> int:
        """Return the index of the currently selected tab."""
        tabs = self.tab_elements(self.TABS)
        for i, tab in enumerate(tabs):
            if tab.get_attribute("aria-selected") == "true":
                return i
        return -1

    # ── Details tab (tab=0) ────────────────────────────────────────────

    def get_detail_card_text(self) -> str:
        """Return the combined text content of all detail cards.

        No call site in this suite as of #946 wave 4 -- left unanchored
        rather than speculatively converted (dead code has no caller whose
        polarity or timing a fix could be verified against).
        """
        cards = self.driver.find_elements(*self.DETAILS_CARD)
        return " ".join(c.text for c in cards)

    def get_entries_row_count(self) -> int:
        """Return the number of entry rows in the Details tab entries table.

        No call site in this suite as of #946 wave 4 -- see
        :meth:`get_detail_card_text`.
        """
        rows = self.driver.find_elements(*self.ENTRIES_ROWS)
        return len(rows)

    # ── Plants tab (tab=1) ─────────────────────────────────────────────

    def get_plants_row_count(self) -> int:
        """Return the number of plant rows in the Plants tab.

        No call site in this suite as of #946 wave 4 -- see
        :meth:`get_detail_card_text`.
        """
        rows = self.driver.find_elements(*self.PLANTS_ROWS)
        return len(rows)

    def get_plant_rows_text(self) -> list[list[str]]:
        """Return the readable text fragments of every visible plant row.

        No call site in this suite as of #946 wave 4 -- see
        :meth:`get_detail_card_text`.
        """
        return [
            self.get_row_text_fragments(row) for row in self.driver.find_elements(*self.PLANTS_ROWS)
        ]

    def is_no_plants_message_visible(self) -> bool:
        """Return True if the 'no plants yet' message is displayed (tab=1, before batch create).

        No call site in this suite as of #946 wave 4 -- see
        :meth:`get_detail_card_text`.
        """
        elements = self.driver.find_elements(
            By.XPATH, "//*[contains(@class, 'MuiTypography-root')]"
        )
        for el in elements:
            # The translated key pages.plantingRuns.noPlantsYet renders as a message
            if el.text and len(el.text) > 0 and el.is_displayed():
                parent_testid = el.find_elements(
                    By.XPATH, "ancestor::*[@data-testid='planting-run-detail-page']"
                )
                if parent_testid:
                    return True
        # Fallback: check if the data-table is absent while we are on tab 1
        tables = self.driver.find_elements(*self.PLANTS_TABLE)
        return len(tables) == 0

    # ── State-machine action buttons ───────────────────────────────────

    def is_create_plants_button_visible(self) -> bool:
        """True when status is 'planned' — creates plant instances.

        Deliberately instantaneous, not anchored: every call site reads this
        right after :meth:`get_status`, which itself runs
        ``wait_for_element(self.STATUS_CHIP)`` -- a real wait. The status chip
        and this action-button set are keyed on the same fetched run and
        rendered in the same commit, after the same page-level loading gate
        (``PlantingRunDetailPage.tsx:507``), so a settled status chip means
        the button set has settled too.
        """
        return len(self.driver.find_elements(*self.CREATE_PLANTS_BUTTON)) > 0

    def is_delete_button_visible(self) -> bool:
        """True when status is 'planned' — allows deletion.

        See :meth:`is_create_plants_button_visible` for why this stays
        instantaneous.
        """
        return len(self.driver.find_elements(*self.DELETE_BUTTON)) > 0

    def is_batch_remove_button_visible(self) -> bool:
        """True when status is 'active' or 'harvesting'.

        Its one call site reads it negated (``assert not
        is_batch_remove_button_visible()``) alongside its two siblings above,
        at the same point in the same test -- see
        :meth:`is_create_plants_button_visible` for why the caller's prior
        :meth:`get_status` already anchors all three.
        """
        return len(self.driver.find_elements(*self.BATCH_REMOVE_BUTTON)) > 0

    def click_create_plants(self) -> None:
        """Click 'Create Plants' and wait for the confirmation dialog."""
        self.wait_and_click(self.CREATE_PLANTS_BUTTON)
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def click_delete(self) -> None:
        """Click 'Delete' and wait for the confirmation dialog."""
        self.wait_and_click(self.DELETE_BUTTON)
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def click_batch_remove(self) -> None:
        """Click 'Batch Remove' and wait for the confirmation dialog."""
        self.wait_and_click(self.BATCH_REMOVE_BUTTON)
        self.wait_for_element_visible(self.CONFIRM_DIALOG)

    def confirm_action(self) -> None:
        """Click the 'Confirm' button in the open ConfirmDialog."""
        self.wait_and_click(self.CONFIRM_BUTTON)

    def cancel_action(self) -> None:
        """Click the 'Cancel' button in the open ConfirmDialog."""
        self.wait_and_click(self.CONFIRM_CANCEL)

    def is_confirm_dialog_open(self) -> bool:
        """Return True if the ConfirmDialog is currently visible.

        Deliberately instantaneous, not anchored: its *presence* call sites
        read it right after ``click_create_plants()``/``click_delete()``,
        which already run ``wait_for_element_visible(self.CONFIRM_DIALOG)`` --
        the readiness has already been bought by the caller. For the
        *dismissal* check ("the dialog closed"), do not use this method --
        use :meth:`wait_for_confirm_dialog_closed`, which waits out the MUI
        exit transition instead of sampling once.
        """
        return len(self.driver.find_elements(*self.CONFIRM_DIALOG)) > 0

    def wait_for_confirm_dialog_closed(self, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Wait for the ConfirmDialog to actually leave the DOM.

        MUI's Dialog unmounts only after its exit transition finishes, so a
        raw ``not is_confirm_dialog_open()`` sampled right after clicking
        Confirm/Cancel can still see the dialog mid-fade-out and report it as
        open -- a guarded-dismissal gap, not a data-fetch one. Returns
        ``False`` (rather than raising) once the budget is spent, so a dialog
        that genuinely never closes still fails the caller's own assertion.
        """
        return self.is_absent_within(self.CONFIRM_DIALOG, timeout=timeout)

    # ── Edit dialog ───────────────────────────────────────────────────

    def open_edit_dialog(self) -> None:
        """Click the Edit button and wait for the edit dialog to open."""
        self.wait_and_click(self.EDIT_BUTTON)
        self.wait_for_element_visible(self.EDIT_DIALOG)

    def is_edit_dialog_open(self) -> bool:
        """Return True if the edit dialog is currently visible.

        Kept for symmetry/future presence reads; the one existing call site
        checks dismissal and now uses :meth:`wait_for_edit_dialog_closed`
        instead -- see :meth:`is_confirm_dialog_open` for why a raw negated
        read of a MUI Dialog's presence is a guarded-dismissal gap, not a
        genuine "closed" check.
        """
        return len(self.driver.find_elements(*self.EDIT_DIALOG)) > 0

    def wait_for_edit_dialog_closed(self, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Wait for the edit dialog to actually leave the DOM.

        See :meth:`wait_for_confirm_dialog_closed` for the exit-transition
        rationale; same shape, different dialog.
        """
        return self.is_absent_within(self.EDIT_DIALOG, timeout=timeout)

    def get_name_field_value(self) -> str:
        """Return the current value of the Name input in the edit form."""
        el = self.wait_for_element(self.FORM_NAME)
        return el.get_attribute("value") or ""

    def fill_name(self, name: str) -> None:
        """Set the Name field in the edit form."""
        el = self.wait_for_element_clickable(self.FORM_NAME)
        el.clear()
        el.send_keys(name)

    def fill_notes(self, notes: str) -> None:
        """Set the Notes field in the edit form."""
        el = self.wait_for_element_clickable(self.FORM_NOTES)
        el.clear()
        el.send_keys(notes)

    def submit_edit_form(self) -> None:
        """Submit the edit form."""
        self.wait_and_click(self.FORM_SUBMIT)

    def cancel_edit_form(self) -> None:
        """Cancel the edit form by clicking Cancel."""
        self.wait_and_click(self.FORM_CANCEL)

    def get_edit_form_name_value(self) -> str:
        """Return the current value in the edit form Name field."""
        el = self.wait_for_element(self.FORM_NAME)
        return el.get_attribute("value") or ""

    # ── Error display ──────────────────────────────────────────────────

    def is_error_displayed(self) -> bool:
        """Return True if an error display component is visible.

        Deliberately instantaneous, not anchored: its one call site
        (``test_nonexistent_run_key_shows_error``) reads it right after
        ``wait_for_any_present((ERROR_DISPLAY, PAGE), ...)`` -- the readiness
        this method reports has already been bought by the caller.
        """
        elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='error-display']")
        return len(elements) > 0 and elements[0].is_displayed()

    def is_page_rendered(self) -> bool:
        """Return True if the detail page container is present in the DOM.

        See :meth:`is_error_displayed` -- same call site, same anchor.
        """
        return len(self.driver.find_elements(*self.PAGE)) > 0
